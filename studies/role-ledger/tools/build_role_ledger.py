#!/usr/bin/env python3
"""Build the role-ledger aggregates from existing private telemetry.

Reads (read-only, never written):
  * the oss-factory agent-outcome ledger (`ledger.sqlite`, kvnloo/oss-factory#206 tools)
  * Hermes `state.db` files (interactive sessions only) for the HUMAN column
  * Jev routing decision logs (`logs/jev-decisions.jsonl`)
  * z0intelligence shadow receipts (`~/.z0int/shadow/*.json`)
  * `lane-priors.json` (dispatcher priors)

Writes aggregates only to `--out` (default: ../data). No prompts, responses,
titles, session ids, paths or hashes leave this script: every output value is a
count, rate, quantile, model id, or a fixed-vocabulary label.

Usage:
  python3 build_role_ledger.py --ledger <copy of ledger.sqlite> \
      --hermes-db ~/.hermes/state.db --hermes-db ~/.hermes/profiles/clean/state.db ...
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sqlite3
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
MIN_N = 5  # cells below this are pooled into "other" before publishing

INTERACTIVE = {"cli", "tui", "desktop", "telegram", "acp", "api_server", "local", "discord", "vscode"}
DELEGATED = {"subagent", "delegate_task", "advisor"}
VERIFIABLE_KINDS = {"code", "verify", "ops"}  # kinds where a test/PR/push can show up as evidence
TERMINAL = {"verified_success", "claimed_success", "failed", "killed", "abandoned"}


# ----------------------------------------------------------------------------- helpers

def wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 3), round(min(1.0, c + h), 3)]


def q(vals: list[float], p: float) -> float | None:
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    i = min(len(vals) - 1, max(0, int(round(p * (len(vals) - 1)))))
    return vals[i]


def rnd(x, n=3):
    return None if x is None else round(x, n)


def mode_of(harness: str, source_kind: str) -> str:
    if harness == "hermes-delegation" or source_kind in DELEGATED:
        return "delegated"
    if harness == "omp" and source_kind == "main":
        return "interactive"
    if source_kind in INTERACTIVE:
        return "interactive"
    return "batch"


def harness_label(harness: str) -> str:
    return {"hermes-delegation": "hermes"}.get(harness, harness)


def model_label(lane: str, model: str | None) -> str:
    m = (model or "").lower().split("/")[-1].replace("codex:", "")
    if lane == "sol":
        return "gpt-6.1-sol" if "6.1" in m else ("gpt-5.6-sol" if "5.6" in m else "sol-other")
    if lane in {"astra", "luna", "opus", "haiku", "fable", "spark", "grok", "jev", "cursor"}:
        return lane
    return lane  # free lanes and unknowns stay at lane granularity


# ----------------------------------------------------------------------------- role cells

def cell_stats(rows: list[sqlite3.Row], kind: str) -> dict:
    n = len(rows)
    oc = Counter(r["outcome"] for r in rows)
    term = sum(oc[k] for k in TERMINAL)
    ver = oc["verified_success"]
    done = ver + oc["claimed_success"]
    bad = oc["failed"] + oc["killed"]
    dur = [r["duration_s"] / 60 for r in rows if r["duration_s"] is not None and r["duration_s"] >= 0]
    fresh = [(r["input_tokens"] or 0) + (r["output_tokens"] or 0) for r in rows]
    cache = [r["cache_read_tokens"] or 0 for r in rows]
    cost = [r["cost_usd"] for r in rows if r["cost_usd"] is not None and r["cost_usd"] > 0]
    corr = [r["owner_corrections"] or 0 for r in rows]
    fails = Counter(r["failure_class"] for r in rows if r["failure_class"])
    verifiable = kind in VERIFIABLE_KINDS
    return {
        "n": n,
        "terminal": term,
        "outcomes": {k: oc[k] for k in sorted(oc)},
        "verified_applicable": verifiable,
        "verified_rate": rnd(ver / term) if term and verifiable else None,
        "verified_ci95": wilson(ver, term) if term and verifiable else None,
        "unverified_completion_rate": rnd(done / term) if term else None,
        "fail_or_killed_rate": rnd(bad / term) if term else None,
        "owner_corrections_per_run": rnd(sum(corr) / n) if n else None,
        "runs_with_owner_correction": sum(1 for c in corr if c),
        "rework_per_run": rnd(sum(r["rework_count"] or 0 for r in rows) / n) if n else None,
        "wall_min_p50": rnd(q(dur, 0.5), 1),
        "wall_min_p90": rnd(q(dur, 0.9), 1),
        "fresh_tokens_p50": q(fresh, 0.5),
        "fresh_tokens_mean": int(sum(fresh) / n) if n else None,
        "cache_read_tokens_p50": q(cache, 0.5),
        "api_equiv_usd_p50": rnd(q(cost, 0.5)),
        "api_equiv_usd_priced_runs": len(cost),
        "tool_error_rate": rnd(sum(r["tool_errors"] or 0 for r in rows) / max(1, sum(r["tool_calls"] or 0 for r in rows))),
        "top_failures": [[k, v] for k, v in fails.most_common(3)],
    }


def build_cells(db: Path, since: float | None) -> dict:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    sql = "select * from runs where dup_of is null and outcome != 'in_progress'"
    rows = con.execute(sql).fetchall()
    if since:
        rows = [r for r in rows if (r["started_at"] or r["ended_at"] or 0) >= since or r["harness"] == "kitchen"]
    groups: dict[tuple, list] = defaultdict(list)
    for r in rows:
        key = (harness_label(r["harness"]), mode_of(r["harness"], r["source_kind"] or ""),
               model_label(r["lane"] or "unknown", r["model"]), r["task_kind"] or "unknown")
        groups[key].append(r)
    cells, pooled = [], defaultdict(list)
    for key, rs in groups.items():
        if len(rs) >= MIN_N:
            cells.append({"harness": key[0], "mode": key[1], "model": key[2], "task_kind": key[3],
                          "billing_class": Counter(r["billing_class"] for r in rs).most_common(1)[0][0],
                          **cell_stats(rs, key[3])})
        else:
            pooled[(key[0], key[1])].extend(rs)
    other = [{"harness": h, "mode": m, "model": "other(<5/cell)", "task_kind": "mixed", **cell_stats(rs, "mixed")}
             for (h, m), rs in pooled.items() if len(rs) >= MIN_N]
    cells.sort(key=lambda c: -c["n"])
    # coarse rollup: model x task_kind (all harnesses), used by the routing table
    roll: dict[tuple, list] = defaultdict(list)
    for r in rows:
        roll[(model_label(r["lane"] or "unknown", r["model"]), r["task_kind"] or "unknown")].append(r)
    rollup = [{"model": k[0], "task_kind": k[1], **cell_stats(v, k[1])} for k, v in roll.items() if len(v) >= MIN_N]
    rollup.sort(key=lambda c: (c["task_kind"], -c["n"]))
    # harness x mode rollup for the "simplest harness" question
    hm: dict[tuple, list] = defaultdict(list)
    for r in rows:
        hm[(harness_label(r["harness"]), mode_of(r["harness"], r["source_kind"] or ""))].append(r)
    harness_modes = []
    for k, v in hm.items():
        vk = [r for r in v if r["task_kind"] in VERIFIABLE_KINDS]
        harness_modes.append({"harness": k[0], "mode": k[1], "n_all": len(v),
                              "all_kinds": cell_stats(v, "mixed"),
                              "verifiable_kinds_only": cell_stats(vk, "code") if len(vk) >= MIN_N else None})
    harness_modes.sort(key=lambda c: -c["n_all"])
    span = [r["started_at"] for r in rows if r["started_at"]]
    con.close()
    return {"runs": len(rows), "window": [time.strftime("%Y-%m-%d", time.gmtime(min(span))),
                                          time.strftime("%Y-%m-%d", time.gmtime(max(span)))] if span else None,
            "cells": cells, "pooled_other": other, "rollup_model_x_kind": rollup, "harness_x_mode": harness_modes}


# ----------------------------------------------------------------------------- HUMAN column

CORRECTION = re.compile(
    r"(\bwhy (?:is|are|did|does|do|isn'?t|aren'?t|can'?t|won'?t)\b[^\n]{0,80}\b(bug|broken|wrong|slow|fail|not|still|so|again)\w*)"
    r"|(\b(?:so|super|very|still) (?:buggy|broken|bad|wrong|slow)\b)"
    r"|(\b(?:does ?n[o']?t|doesnt|did ?n[o']?t|is ?n[o']?t|isnt|not) (?:work|working|fixed|right|what i)\w*)"
    r"|(\bthat'?s (?:not|wrong)\b)|(\byou (?:didn'?t|did not|broke|forgot|ignored|missed)\b)"
    r"|(\bstill (?:broken|failing|wrong|not)\b)|(\bwrong\b)|(\bbuggy\b)|(\bregress\w*)|(\bstop (?:doing|that)\b)|(^\s*no[,.! ])|(\bwtf\b)|(\bfuck\w*)",
    re.I | re.M)  # identical to oss-factory telemetry common._CORRECTION
CRED = re.compile(r"\b(api[ _-]?keys?|tokens?|passwords?|passcode|2fa|otp|verification code|log(?:ged)? ?in|sign(?:ed)? ?in|"
                  r"authenticat\w*|authori[sz]\w*|credentials?|secrets?|bws|vault)\b", re.I)
PHYS = re.compile(r"\b(plugged|unplugged|plug(?:ged)? (?:it )?in|reconnected|rebooted|power(?:ed)? (?:on|off|cycled)|"
                  r"turned (?:it )?(?:on|off)|on my phone|my phone|unlocked|usb|cable|charger|i tapped|i clicked|i pressed|"
                  r"scanned|i installed|i opened|i'?m (?:at|home|back|away|out)|in the (?:garden|room|car|kitchen))\b", re.I)
APPROVE = re.compile(r"^\W*(y|ya|yes|yep|yup|yeah|ok|okay|k|kk|sure|go|go ahead|go for it|do it|do that|do both|both|"
                     r"proceed|continue|keep going|approved?|lgtm|ship it|merge it|sounds good|perfect|great|nice|cool|"
                     r"thanks?|ty|please do|yes please|all of (?:it|them)|option \w|[a-d1-4])\b", re.I)
TASTE = re.compile(r"\b(looks?|looking|ugly|pretty|prettier|beautiful|gorgeous|styles?|styling|vibes?|feels?|aesthetic\w*|"
                   r"colou?rs?|fonts?|spacing|too (?:big|small|dark|bright|busy|much|slow)|i (?:like|love|hate|prefer)|"
                   r"prefer|design|cleaner|cluttered|readable|taste)\b", re.I)
QUESTION = re.compile(r"(\?\s*$)|(^\s*(what|why|how|where|when|which|who|is|are|does|do|can|could|should|did)\b)", re.I)
GOAL_VERB = re.compile(r"\b(build|make|add|implement|create|research|find|fix|write|ship|set up|setup|install|refactor|"
                       r"investigate|design|plan|deploy|run|test|migrate|clean|organize|want|need|let'?s|lets)\b", re.I)

ASK_PERMISSION = re.compile(r"\b(should i|shall i|do you want(?: me)?|want me to|would you like(?: me)?|ok(?:ay)? to|"
                            r"can i|may i|go ahead|proceed\?|confirm(?: that)?|let me know if|which (?:one|option|do you)|"
                            r"or should|prefer i)\b", re.I)
ASK_RISK = re.compile(r"\b(delete|remove|rm -rf|force[- ]push|push to main|merge|production|prod\b|payment|purchase|buy|"
                      r"send (?:the )?(?:email|message)|post (?:it|this)|publish|public|drop (?:table|database)|reset --hard|"
                      r"irreversible|destructive|spend|billing)\b", re.I)
ASK_CRED = CRED
ASK_PHYS = re.compile(r"\b(plug|unplug|reconnect|reboot|your phone|on the phone|tap |unlock|usb|cable|physically|"
                      r"scan the qr|press the|in person|power (?:on|off|cycle))\b", re.I)
ASK_TASTE = re.compile(r"\b(prefer|look(?:s)? (?:right|good|better)|which (?:style|look|design|version)|like (?:this|it)|"
                       r"taste|feel|aesthetic)\b", re.I)


def owner_text(t: str | None) -> str | None:
    if not t:
        return None
    t = t.strip()
    if t.startswith("[Replying to:"):
        end = t.find("]")
        t = t[end + 1:].strip() if end > 0 else ""
    elif t.startswith("[OUT-OF-BAND USER MESSAGE"):
        t = t.split("]", 1)[-1].strip()
    if not t or t.startswith(("<", "#", "[", "{", "kickoff:", "You are ", "SYSTEM", "Review the conversation")):
        return None
    return t


def classify_owner(t: str) -> str:
    words = len(t.split())
    if len(t) > 3000:
        return "context_paste"
    if t.startswith("/"):
        return "slash_command"
    if CRED.search(t[:600]) and words <= 60:
        return "credential_or_auth"
    if PHYS.search(t[:600]) and words <= 80:
        return "physical_action_report"
    if CORRECTION.search(t[:1500]):
        return "correction"
    if words <= 8 and APPROVE.search(t):
        return "approval_or_ack"
    if TASTE.search(t[:1500]):
        return "taste_or_feedback"
    if QUESTION.search(t) and words <= 40:
        return "question_to_agent"
    if words >= 6 and GOAL_VERB.search(t[:1500]):
        return "goal_or_direction"
    if words >= 6:
        return "other_direction"
    return "other_short"


def classify_ask(a: str | None) -> str | None:
    if not a:
        return None
    tail = a.strip()[-600:]
    asked = tail.rstrip().endswith("?") or ASK_PERMISSION.search(tail)
    if not asked:
        return None
    if ASK_CRED.search(tail):
        return "needs_credential"
    if ASK_PHYS.search(tail):
        return "needs_physical_action"
    if ASK_TASTE.search(tail):
        return "taste_choice"
    if ASK_PERMISSION.search(tail):
        return "risk_gated_permission" if ASK_RISK.search(tail) else "reversible_permission"
    return "clarifying_question"


def human_column(dbs: list[Path]) -> dict:
    seen: dict[str, tuple[int, Counter, Counter, Counter, str]] = {}
    for db in dbs:
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            sess = con.execute(
                "select id, source from sessions where source in (%s)" % ",".join("?" * len(INTERACTIVE)),
                sorted(INTERACTIVE)).fetchall()
        except sqlite3.Error:
            continue
        for sid, source in sess:
            msgs = con.execute("select role, content from messages where session_id=? and role in ('user','assistant') "
                               "order by timestamp, id", (sid,)).fetchall()
            owner, asks, pairs = Counter(), Counter(), Counter()
            last_assistant = None
            n_owner = 0
            for role, content in msgs:
                if role == "assistant":
                    if content and content.strip():
                        last_assistant = content
                    continue
                t = owner_text(content)
                if t is None:
                    continue
                n_owner += 1
                cls = classify_owner(t)
                owner[cls] += 1
                ask = classify_ask(last_assistant)
                if ask:
                    asks[ask] += 1
                    pairs[f"{ask}->{cls}"] += 1
                last_assistant = None
            prev = seen.get(sid)
            if prev is None or n_owner > prev[0]:
                seen[sid] = (n_owner, owner, asks, pairs, source)
        con.close()
    owner_tot, ask_tot, pair_tot, by_source = Counter(), Counter(), Counter(), Counter()
    sessions_with_owner = 0
    for n_owner, owner, asks, pairs, source in seen.values():
        if n_owner:
            sessions_with_owner += 1
            by_source[source] += 1
        owner_tot.update(owner)
        ask_tot.update(asks)
        pair_tot.update(pairs)
    total_owner = sum(owner_tot.values())
    total_asks = sum(ask_tot.values())
    decidable = sum(v for k, v in pair_tot.items()
                    if k.startswith("reversible_permission->") and k.endswith(("approval_or_ack",)))
    decidable += sum(v for k, v in pair_tot.items()
                     if k.startswith("clarifying_question->") and k.endswith("approval_or_ack"))
    return {
        "interactive_sessions": len(seen),
        "sessions_with_owner_messages": sessions_with_owner,
        "sessions_by_source": dict(by_source.most_common()),
        "owner_messages": total_owner,
        "owner_message_classes": {k: [v, rnd(v / total_owner)] for k, v in owner_tot.most_common()},
        "agent_asks_answered": total_asks,
        "agent_ask_classes": {k: [v, rnd(v / max(1, total_asks))] for k, v in ask_tot.most_common()},
        "ask_reply_pairs_top": [[k, v] for k, v in pair_tot.most_common(25)],
        "asks_agent_could_have_decided": decidable,
        "asks_agent_could_have_decided_share": rnd(decidable / max(1, total_asks)),
        "method": "fixed-vocabulary regex classifier over owner text in memory; first match wins in the order "
                  "context_paste, slash_command, credential_or_auth, physical_action_report, correction, "
                  "approval_or_ack, taste_or_feedback, question_to_agent, goal_or_direction, other. "
                  "'could have decided' = an agent ask classed reversible_permission or clarifying_question that the "
                  "owner answered with a bare approval (<= 8 words). Heuristic, not hand-labelled.",
    }


# ----------------------------------------------------------------------------- SLM / Jev / shadow

def jev_routing(paths: list[Path]) -> dict:
    tiers, spec, routed, lat, kinds, modes = Counter(), Counter(), Counter(), [], Counter(), Counter()
    costly = Counter()
    n = 0
    for p in paths:
        if not p.exists():
            continue
        for line in p.open():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            n += 1
            tiers[r.get("tier") or "none"] += 1
            spec[r.get("specialty") or "none"] += 1
            routed[str(bool(r.get("routed")))] += 1
            modes[r.get("mode") or "?"] += 1
            kinds[r.get("kind") or "?"] += 1
            costly[str(r.get("costly_mistake"))] += 1
            if isinstance(r.get("latency_ms"), (int, float)):
                lat.append(r["latency_ms"])
    return {"decisions": n, "tier": dict(tiers.most_common()), "specialty": dict(spec.most_common()),
            "routed": dict(routed), "mode": dict(modes), "kind": dict(kinds), "costly_mistake": dict(costly),
            "latency_ms_p50": q(lat, 0.5), "latency_ms_p90": q(lat, 0.9)}


def shadow(dirp: Path) -> dict:
    out = {}
    for name in ("baseline_coverage.json", "coverage_eval.json", "champion_confirm.json", "baseline_confirm.json"):
        p = dirp / name
        if not p.exists():
            continue
        j = json.loads(p.read_text())
        keep = {k: j[k] for k in ("schema", "n_confirm", "coverage", "local_precision", "escalate_rate",
                                  "champion_confirm_acc", "majority", "by_family", "by_local_family", "policy") if k in j}
        out[name.removesuffix(".json")] = keep
    return out


def lane_priors(p: Path) -> dict:
    if not p.exists():
        return {}
    j = json.loads(p.read_text())
    return {"schema": j.get("schema"), "generated_at": j.get("generated_at"),
            "ranked_lanes_by_task_kind": j.get("ranked_lanes_by_task_kind")}


# ----------------------------------------------------------------------------- main

def main() -> None:
    home = Path(os.path.expanduser("~"))
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True, type=Path)
    ap.add_argument("--hermes-db", action="append", type=Path, default=[])
    ap.add_argument("--jev-log", action="append", type=Path, default=[])
    ap.add_argument("--shadow-dir", type=Path, default=home / ".z0int/shadow")
    ap.add_argument("--lane-priors", type=Path,
                    default=Path("/mnt/zer0models/workspace/zer0/data/operations/agent-outcomes/lane-priors.json"))
    ap.add_argument("--out", type=Path, default=HERE.parent / "data")
    ap.add_argument("--recent-days", type=int, default=14)
    ap.add_argument("--skip-human", action="store_true")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    def dump(name: str, obj) -> None:
        (a.out / name).write_text(json.dumps(obj, indent=1, sort_keys=False) + "\n")

    allt = build_cells(a.ledger, None)
    recent = build_cells(a.ledger, time.time() - a.recent_days * 86400)
    dump("role-cells.json", {"schema": "z0evals.role_ledger.cells.v1", "min_cell_n": MIN_N,
                             "verifiable_kinds": sorted(VERIFIABLE_KINDS), "all_time": allt,
                             f"recent_{a.recent_days}d": recent})
    if not a.skip_human:
        dump("human-column.json", {"schema": "z0evals.role_ledger.human.v1", **human_column(a.hermes_db)})
    dump("slm-and-routing.json", {"schema": "z0evals.role_ledger.slm.v1",
                                  "jev_routing_decisions": jev_routing(a.jev_log),
                                  "next_action_shadow": shadow(a.shadow_dir),
                                  "dispatcher_lane_priors": lane_priors(a.lane_priors)})
    print("ok", allt["runs"], "runs all-time;", recent["runs"], "recent")


if __name__ == "__main__":
    main()
