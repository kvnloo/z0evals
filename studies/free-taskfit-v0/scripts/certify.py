#!/usr/bin/env python3
"""Certify free task-fit rows into a z0eval.result.v1 receipt for z0intelligence.

z0evals is the frozen evaluator: this script re-grades every row that carries
its full answer text with the frozen graders in ../frozen/tasks.py, refuses
rows produced against a different task set, and only then counts acceptances.
z0intelligence consumes the receipt through its existing ingest path
(`z0int policy ingest`, source kind `z0eval_result`) and its model-routing
catalog generator, which turns these findings into
`models[].task_classes[<task class>].p_accept` for O14.

Finding shape (what the #222 catalog generator accepts as a measured prior):
  subject  {family: model.routing.acceptance, task: taskfit.<family>, job: ShadowEvals}
  arm      {kind: frontier, provider, model}
  metric   {name: acceptance_rate, value=accepted/n, n, accepted, wilson95 ci,
            acceptance_kind: rubric_draft_quality, promotion_eligible: false}
  evidence_kind proxy
A deterministic auto-graded battery is a proxy for product success, never a
product outcome, so these rows are benchmark-grade priors and cannot promote.

Latency findings (family model.routing.performance: ttft_p50_ms and decode
tokens_per_second) ride in the same receipt for the O14 latency term.

Limits: rows the runner planned out (`not_eligible:<reason>`) and rows that
hit a daily quota are not trials of the model, so they leave the p_accept
denominator and are reported under evidence.not_eligible / quota_stopped. A run
that contains a 413/request-too-large row, or any sent row that
frozen/limits.json rules out (plan_taskfit.replay), fails certification: that
is a self-inflicted transport failure, never a model measurement.

Usage:
  certify.py ROWS.jsonl [ROWS.jsonl ...] --run-id ID --out result.json [--now ISO]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent / "frozen" / "tasks.py"
FROZEN_SHA256 = "119209b5c61d07c8ebf109aeb995b778e58fc0cd49ec6f04fa90df4b90ed987b"
STUDY = "free-taskfit-v0"
TASK_CLASS_PREFIX = "taskfit."
# Provider ids as z0intelligence's model-routing catalog spells them.
CATALOG_PROVIDER = {"groq": "groq", "openrouter": "openrouter", "nvidia": "nvidia", "cerebras": "cerebras"}
EXPIRY_DAYS = 14  # free routes rot; matches z0int ingest's default finding lifetime


sys.path.insert(0, str(HERE))
import plan_taskfit as planner  # noqa: E402


class CertifyError(ValueError):
    pass


def wilson(correct: int, n: int) -> tuple[float, float]:
    """Same formula and z as z0int.policy.ingest.wilson (the consumer re-checks it)."""
    z = 1.959963984540054
    p = correct / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def iso(ts: float | datetime) -> str:
    value = ts if isinstance(ts, datetime) else datetime.fromtimestamp(ts, timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_tasks():
    actual = hashlib.sha256(FROZEN.read_bytes()).hexdigest()
    if actual != FROZEN_SHA256:
        raise CertifyError(f"frozen task set changed: {actual} != {FROZEN_SHA256}")
    sys.path.insert(0, str(FROZEN.parent))
    from tasks import TASKS  # noqa: PLC0415
    return {t["id"]: t for t in TASKS}


def regrade(rows: list[dict], tasks: dict, limits: dict | None = None) -> tuple[list[dict], dict]:
    """Return graded rows plus an audit of what was re-graded vs trusted.

    Raises CertifyError when a row was sent although the frozen limits rule it out.
    """
    limits = limits or planner.load_limits()
    audit = {"rows": len(rows), "regraded": 0, "runner_disagreed": 0, "failed_calls": 0, "rejected": [],
             "not_eligible": 0, "quota_stopped": 0, "superseded": 0}
    latest: dict[tuple, dict] = {}
    for row in rows:  # a resumed run appends; the last row per (lane, task, rep) is the trial
        key = (row.get("model"), row.get("task"), row.get("rep"))
        if key in latest:
            audit["superseded"] += 1
        latest[key] = row
    rows = list(latest.values())
    too_large = [r for r in rows if not str(r.get("status", "")).startswith(planner.NOT_ELIGIBLE)
                 and planner.too_large_error(r.get("error") or "", r.get("http_status"))]
    ruled_out = planner.replay(rows, tasks, limits)
    if too_large or ruled_out:
        names = sorted({f"{r['model']}/{r['task']}#{r.get('rep')}" for r in too_large + ruled_out})
        raise CertifyError(
            f"{len(names)} row(s) were sent although {planner.LIMITS.relative_to(HERE.parent)} rules them out "
            f"({len(too_large)} came back 413/request-too-large): {', '.join(names[:8])}"
            f"{' ...' if len(names) > 8 else ''}. Re-run with run_taskfit.py, which plans these out as "
            "not_eligible; never count them as model failures.")
    graded = []
    for row in rows:
        if row.get("task_set_sha256") not in (None, FROZEN_SHA256):
            raise CertifyError(f"row {row.get('model')}/{row.get('task')} ran a different task set")
        status = str(row.get("status", ""))
        if status.startswith(planner.NOT_ELIGIBLE):
            audit["not_eligible"] += 1
            graded.append({**row, "graded_by": "not_eligible"})
            continue
        if status == planner.QUOTA_EXHAUSTED:
            audit["quota_stopped"] += 1
            graded.append({**row, "graded_by": "quota_stopped"})
            continue
        task = tasks.get(row.get("task"))
        if task is None or task["family"] != row.get("family"):
            audit["rejected"].append({"model": row.get("model"), "task": row.get("task"), "reason": "unknown task/family"})
            continue
        if not row.get("ok"):
            audit["failed_calls"] += 1
            graded.append({**row, "correct": False, "graded_by": "failed_call"})
            continue
        if "text" not in row:
            # Truncated `sample` rows cannot be re-graded; refuse rather than trust the runner.
            audit["rejected"].append({"model": row["model"], "task": row["task"], "reason": "no full text to re-grade"})
            continue
        try:
            correct = bool(task["grade"](row["text"]))
        except Exception:
            correct = False
        audit["regraded"] += 1
        if "correct" in row and bool(row["correct"]) != correct:
            audit["runner_disagreed"] += 1
        graded.append({**row, "correct": correct, "graded_by": "z0evals_frozen_grader"})
    return graded, audit


EXCLUDED = ("not_eligible", "quota_stopped")


def excluded_report(graded: list[dict]) -> list[dict]:
    """Per (lane, family): rows kept out of p_accept, with their reasons."""
    out: dict[tuple, dict] = {}
    for row in graded:
        if row["graded_by"] in EXCLUDED:
            rec = out.setdefault((row["model"], row["family"]), {"model": row["model"], "family": row["family"],
                                                                 "n": 0, "reasons": {}})
            rec["n"] += 1
            reason = row.get("status", row["graded_by"])
            rec["reasons"][reason] = rec["reasons"].get(reason, 0) + 1
    return [out[k] for k in sorted(out)]


def _arm(spec: str) -> dict:
    provider, model = spec.split("/", 1)
    return {"kind": "frontier", "provider": CATALOG_PROVIDER.get(provider, provider), "model": model,
            "transport": provider}


def findings(graded: list[dict], ts: str, expires_at: str) -> list[dict]:
    by_class = defaultdict(list); by_model = defaultdict(list)
    for row in graded:
        if row["graded_by"] in EXCLUDED:  # not a trial of the model: outside every denominator
            continue
        by_class[(row["model"], row["family"])].append(row)
        by_model[row["model"]].append(row)
    out = []
    scope = ("Only this frozen 20-task deterministic non-code battery (free-taskfit-v0, task set sha256 "
             f"{FROZEN_SHA256[:12]}), this exact provider/model route, temperature 0, streaming. A failed call "
             "counts as not accepted. Proxy for draft quality, not product success; no generalization to code, "
             "tools or other prompts.")
    for (spec, family), rows in sorted(by_class.items()):
        n = len(rows); accepted = sum(1 for r in rows if r["correct"])
        low, high = wilson(accepted, n)
        out.append({
            "ts": ts, "expires_at": expires_at, "evidence_class": "measured", "evidence_kind": "proxy",
            "subject": {"family": "model.routing.acceptance", "task": TASK_CLASS_PREFIX + family,
                        "job": "ShadowEvals", "study": STUDY},
            "arm": _arm(spec),
            "metric": {"name": "acceptance_rate", "value": accepted / n, "n": n, "accepted": accepted,
                       "ci_low": low, "ci_high": high, "ci_method": "wilson95", "higher_is_better": True,
                       "acceptance_kind": "rubric_draft_quality", "promotion_eligible": False,
                       "failed_calls": sum(1 for r in rows if not r.get("ok"))},
            "scope_note": scope,
        })
    for spec, rows in sorted(by_model.items()):
        ok = [r for r in rows if r.get("ok") and r.get("ttft_s") is not None]
        if ok:
            ttft = sorted(r["ttft_s"] * 1000 for r in ok)
            out.append({
                "ts": ts, "expires_at": expires_at, "evidence_class": "measured", "evidence_kind": "proxy",
                "subject": {"family": "model.routing.performance", "task": "taskfit.all", "job": "ShadowEvals",
                            "study": STUDY},
                "arm": _arm(spec),
                "metric": {"name": "ttft_p50_ms", "value": statistics.median(ttft), "n": len(ttft),
                           "ci_low": ttft[0], "ci_high": ttft[-1], "ci_method": "none", "higher_is_better": False,
                           "basis": "streamed first content-or-reasoning delta; min/max carried in ci_low/ci_high"},
                "scope_note": "Client-side TTFT from groot over the public internet for this battery; includes network RTT.",
            })
        decode = []
        for r in ok:
            usage = r.get("usage") or {}
            tokens = usage.get("completion_tokens")
            span = (r.get("total_s") or 0) - (r.get("ttft_s") or 0)
            if isinstance(tokens, int) and tokens > 0 and span > 0.05:
                decode.append(tokens / span)
        if decode:
            decode.sort()
            out.append({
                "ts": ts, "expires_at": expires_at, "evidence_class": "measured", "evidence_kind": "proxy",
                "subject": {"family": "model.routing.performance", "task": "taskfit.all", "job": "ShadowEvals",
                            "study": STUDY},
                "arm": _arm(spec),
                "metric": {"name": "tokens_per_second", "value": statistics.median(decode), "n": len(decode),
                           "ci_low": decode[0], "ci_high": decode[-1], "ci_method": "none", "higher_is_better": True,
                           "basis": "provider-reported completion_tokens / (total - ttft); includes reasoning tokens"},
                "scope_note": "Median decode rate on this battery's answers; short answers understate sustained tok/s.",
            })
    return out


def certify(paths: list[Path], run_id: str, now: datetime | None = None) -> dict:
    tasks = load_tasks()
    rows = []
    for path in paths:
        rows.extend(json.loads(line) for line in path.read_text().splitlines() if line.strip())
    if not rows:
        raise CertifyError("no rows")
    limits = planner.load_limits()
    graded, audit = regrade(rows, tasks, limits)
    if not graded:
        raise CertifyError("no gradable rows")
    if not any(r["graded_by"] not in EXCLUDED for r in graded):
        raise CertifyError("no rows were trials of a model (all not_eligible or quota-stopped)")
    observed = max(r["at"] for r in graded if isinstance(r.get("at"), (int, float)))
    ts = iso(observed)
    expires = iso(datetime.fromtimestamp(observed, timezone.utc) + timedelta(days=EXPIRY_DAYS))
    if now is not None and now < datetime.fromtimestamp(observed, timezone.utc):
        raise CertifyError("rows are from the future relative to --now")
    contract = "pass" if not audit["rejected"] else "fail"
    return {
        "schema": "z0eval.result.v1",
        "suite_id": STUDY,
        "suite_revision": FROZEN_SHA256,
        "run_id": run_id,
        "ts": ts,
        # Not a champion/challenger promotion: a measured capability prior. PARTIAL keeps
        # promotion_eligible false all the way through z0int ingest.
        "verdict": "PARTIAL",
        "gates": {"contract": contract, "authority": "not_applicable", "quality_noninferiority": "not_applicable",
                  "latency_tail": "not_applicable"},
        "source": {"adapter": "free_taskfit", "task_set_sha256": FROZEN_SHA256,
                   "task_set_origin": "kvnloo/z0intelligence@f12b926e:deploy/vllm-sr/profiles/tasks.py"},
        "evidence": {"row_files": [{"path": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
                     "grading_audit": audit, "limits_sha256": limits["_sha256"],
                     "not_eligible": excluded_report(graded)},
        "limitations": [
            "20 tasks; classify has 1 task, so per-family n is tasks x repeats and one task moves a family score a lot.",
            "Free routes are shared capacity; reliability is a point-in-time measurement.",
            "Deterministic graders measure exact-format answers, not open-ended usefulness.",
        ],
        "findings": findings(graded, ts, expires),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rows", nargs="+", type=Path)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    try:
        result = certify(a.rows, a.run_id, datetime.now(timezone.utc))
    except CertifyError as e:
        print(f"certification FAILED: {e}", file=sys.stderr)
        return 2
    a.out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    acc = [f for f in result["findings"] if f["metric"]["name"] == "acceptance_rate"]
    print(f"{len(acc)} acceptance findings, audit {result['evidence']['grading_audit']}")
    return 0 if result["gates"]["contract"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
