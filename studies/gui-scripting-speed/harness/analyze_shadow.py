#!/usr/bin/env python3
"""Score shadow receipts against the frozen gold labels and simulate credited offload.

    python harness/analyze_shadow.py            # writes analysis/shadow-summary.json + .md

Scoring rules (fixed before looking at local-model results):
  correct     selected id in the case's gold set
  uncertain   selected 'reobserve' and reobserve is not gold (declined; the loop would look again)
  wrong       anything else; 'false_autonomy' = a wrong pick whose row is marked Consequential
  raw_*       the same on the arm's raw argmax (before any confidence floor)
Agreement with Jev is reported for information only; it is never scored as correctness.

Offload simulation (passive replay, NOT an executed outcome): a local candidate answers
first; if its confidence >= tau it 'acts', else the step defers to the incumbent (Jev flat,
same case and rep). tau is fit on a DEV split and reported on a disjoint HOLDOUT split.
Splits are lineage-safe: every case from one recorded screen (or one synthetic case) stays
in one split. Latency = candidate latency + incumbent latency when deferred (sequential).
"""
from __future__ import annotations

import collections
import glob
import hashlib
import json
import statistics as st
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
CASES = {c["case"]: c for c in json.loads((STUDY / "tasks/android-chooser-cases.v1.json").read_text())}
CONSEQ = {cid: {o["id"] for o in c["candidates"] if "Consequential" in o["description"]} for cid, c in CASES.items()}
KINDS = ["clear", "split", "multi", "trap"]
INCUMBENT = "jev:flat"


def load():
    rows, headers = [], {}
    for f in sorted(glob.glob(str(STUDY / "data/shadow/*.jsonl"))):
        for line in open(f):
            r = json.loads(line)
            if r["schema"].endswith(".header"):
                headers[r["arm"]] = r
            else:
                rows.append(r)
    return rows, headers


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))] if xs else None


def group_of(case):
    c = CASES[case]
    return f"screen:{c.get('screen')}" if c["source"] == "recorded-s22" and c.get("screen") else f"case:{case}"


def split_of(case):
    h = int(hashlib.sha256(group_of(case).encode()).hexdigest(), 16)
    return "dev" if h % 2 == 0 else "holdout"


def verdict(pid, case):
    gold = CASES[case]["gold"]
    if pid in gold:
        return "correct"
    if pid is None:
        return "error"
    if pid == "reobserve":
        return "uncertain"
    return "wrong"


def summarize_arm(rs, inc_by_key):
    n = len(rs)
    v = collections.Counter(r["verdict"] for r in rs)
    rv = collections.Counter(verdict(r.get("raw_argmax"), r["case"]) for r in rs)
    fa = sum(1 for r in rs if r["verdict"] == "wrong" and r["selected_action"] in CONSEQ[r["case"]])
    lat = [r["latency_ms"] for r in rs if r.get("error") is None]
    by_kind = {}
    for k in KINDS:
        kr = [r for r in rs if r["kind"] == k]
        if kr:
            by_kind[k] = {"n": len(kr), "correct": sum(r["verdict"] == "correct" for r in kr),
                          "raw_correct": sum(verdict(r.get("raw_argmax"), r["case"]) == "correct" for r in kr)}
    agree = [r["selected_action"] == inc_by_key.get((r["case"], r["rep"])) for r in rs
             if (r["case"], r["rep"]) in inc_by_key]
    confs = [r["confidence"] for r in rs if isinstance(r.get("confidence"), (int, float))]
    return {"decisions": n, "correct": v["correct"], "uncertain": v["uncertain"], "wrong": v["wrong"],
            "error": v["error"], "false_autonomy": fa, "accuracy": round(v["correct"] / n, 3) if n else None,
            "raw_correct": rv["correct"], "raw_accuracy": round(rv["correct"] / n, 3) if n else None,
            "latency_ms_p50": round(pct(lat, .5), 1) if lat else None,
            "latency_ms_p95": round(pct(lat, .95), 1) if lat else None,
            "model_calls_mean": round(st.mean(r.get("model_calls") or 0 for r in rs), 2),
            "by_kind": by_kind, "agreement_with_incumbent_info_only": round(sum(agree) / len(agree), 3) if agree else None,
            "has_confidence": bool(confs)}


def cascade(cand, inc, tau, split):
    """Candidate acts at conf>=tau (raw argmax), else incumbent's gated choice."""
    out = []
    for key, r in cand.items():
        if split_of(key[0]) != split or key not in inc:
            continue
        i = inc[key]
        c = r.get("confidence")
        offload = isinstance(c, (int, float)) and c >= tau and r.get("raw_argmax") not in (None, "reobserve")
        pick = r["raw_argmax"] if offload else i["selected_action"]
        lat = r["latency_ms"] + (0 if offload else i["latency_ms"])
        out.append((verdict(pick, key[0]), offload, lat, pick in CONSEQ[key[0]] and verdict(pick, key[0]) == "wrong"))
    if not out:
        return None
    n = len(out)
    return {"n": n, "accuracy": round(sum(o[0] == "correct" for o in out) / n, 3),
            "wrong": sum(o[0] == "wrong" for o in out), "false_autonomy": sum(o[3] for o in out),
            "offload_rate": round(sum(o[1] for o in out) / n, 3),
            "latency_ms_p50": round(pct([o[2] for o in out], .5), 1),
            "latency_ms_mean": round(st.mean(o[2] for o in out), 1),
            "latency_ms_p95": round(pct([o[2] for o in out], .95), 1)}


def main():
    rows, headers = load()
    by_arm = collections.defaultdict(list)
    for r in rows:
        by_arm[r["arm"]].append(r)
    inc = {(r["case"], r["rep"]): r for r in by_arm.get(INCUMBENT, [])}
    inc_sel = {k: r["selected_action"] for k, r in inc.items()}
    arms = {a: summarize_arm(rs, inc_sel) for a, rs in sorted(by_arm.items())}
    for a, h in headers.items():
        if a in arms:
            arms[a].update(cold_load_ms=round(h["cold_load_ms"], 1) if h.get("cold_load_ms") else None,
                           engine=h.get("engine"), max_options=h.get("max_options"))
    inc_dev = [inc[k] for k in inc if split_of(k[0]) == "dev"]
    inc_hold = [inc[k] for k in inc if split_of(k[0]) == "holdout"]
    base = {s: {"accuracy": round(sum(r["verdict"] == "correct" for r in rs) / len(rs), 3),
                "latency_ms_p50": round(pct([r["latency_ms"] for r in rs], .5), 1),
                "latency_ms_mean": round(st.mean(r["latency_ms"] for r in rs), 1), "n": len(rs)}
            for s, rs in (("dev", inc_dev), ("holdout", inc_hold)) if rs}
    offload = {}
    for a, rs in by_arm.items():
        if a.startswith("jev:") or not any(isinstance(r.get("confidence"), (int, float)) for r in rs):
            continue
        cand = {(r["case"], r["rep"]): r for r in rs}
        grid = [round(0.5 + 0.05 * i, 2) for i in range(10)] + [0.97, 0.99]
        best = None
        for tau in grid:
            d = cascade(cand, inc, tau, "dev")
            if d is None:
                continue
            # credited-offload rule: no accuracy loss vs incumbent on dev, no false autonomy, max offload
            if d["accuracy"] >= base["dev"]["accuracy"] and d["false_autonomy"] == 0:
                if best is None or d["offload_rate"] > best[1]["offload_rate"]:
                    best = (tau, d)
        offload[a] = {"tau_dev": best[0] if best else None, "dev": best[1] if best else None,
                      "holdout": cascade(cand, inc, best[0], "holdout") if best else None}
    splits = collections.Counter(split_of(c) for c in CASES)
    out = {"schema": "z0evals.gui_scripting_speed.shadow_summary.v1", "incumbent": INCUMBENT,
           "cases": len(CASES), "split_cases": dict(splits), "arms": arms, "incumbent_by_split": base,
           "offload_simulation": offload,
           "notes": ["passive shadow predictions on a frozen fixture; not executed outcomes",
                     "agreement_with_incumbent is information only"]}
    (STUDY / "analysis").mkdir(exist_ok=True)
    (STUDY / "analysis/shadow-summary.json").write_text(json.dumps(out, indent=1) + "\n")
    lines = ["| arm | engine | decisions | correct (gated) | raw argmax correct | uncertain | wrong | false autonomy | p50 ms | p95 ms | calls/decision | cold load s |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for a, s in sorted(arms.items(), key=lambda kv: -(kv[1]["raw_accuracy"] or 0)):
        lines.append(f"| {a} | {s.get('engine')} | {s['decisions']} | {s['correct']} ({s['accuracy']:.0%}) | "
                     f"{s['raw_correct']} ({s['raw_accuracy']:.0%}) | {s['uncertain']} | {s['wrong']} | {s['false_autonomy']} | "
                     f"{s['latency_ms_p50']} | {s['latency_ms_p95']} | {s['model_calls_mean']} | "
                     f"{(s.get('cold_load_ms') or 0) / 1000:.1f} |")
    lines += ["", "Capability profile (raw-argmax correct / decisions by case kind):", "",
              "| arm | " + " | ".join(KINDS) + " |", "| --- |" + " --- |" * len(KINDS)]
    for a, s in sorted(arms.items()):
        cells = [f"{s['by_kind'][k]['raw_correct']}/{s['by_kind'][k]['n']}" if k in s["by_kind"] else "-" for k in KINDS]
        lines.append(f"| {a} | " + " | ".join(cells) + " |")
    lines += ["", f"Offload simulation (incumbent {INCUMBENT}; dev/holdout split by screen lineage; {dict(splits)} cases):", "",
              "| candidate | tau (dev) | dev offload | dev acc | holdout offload | holdout acc | holdout false autonomy | holdout mean ms | incumbent holdout acc / mean ms |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for a, o in sorted(offload.items()):
        if not o["dev"]:
            lines.append(f"| {a} | none credited | - | - | - | - | - | - | {base['holdout']['accuracy']} / {base['holdout']['latency_ms_mean']} |")
            continue
        h = o["holdout"]
        lines.append(f"| {a} | {o['tau_dev']} | {o['dev']['offload_rate']:.0%} | {o['dev']['accuracy']} | {h['offload_rate']:.0%} | "
                     f"{h['accuracy']} | {h['false_autonomy']} | {h['latency_ms_mean']} | {base['holdout']['accuracy']} / {base['holdout']['latency_ms_mean']} |")
    (STUDY / "analysis/shadow-summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
