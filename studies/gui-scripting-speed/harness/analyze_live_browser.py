#!/usr/bin/env python3
"""Summaries for the live S22+ runs and the browser CDP mechanics bench.

    python harness/analyze_live_browser.py   # writes analysis/live-summary.{json,md}, analysis/browser-summary.{json,md}
"""
from __future__ import annotations

import collections
import glob
import json
import statistics as st
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))] if xs else None


def rows(pattern):
    out = []
    for f in sorted(glob.glob(str(STUDY / pattern))):
        out += [json.loads(l) for l in open(f) if '"schema"' in l and not json.loads(l)["schema"].endswith(".header")]
    return out


def live():
    rs = rows("data/live/*.jsonl")
    g = collections.defaultdict(list)
    for r in rs:
        g[(r["goal_id"], r["arm"])].append(r)
    summary, lines = {}, ["| goal | arm | verified/runs | wall ms p50 | range | model calls (median) | phone actions (median) | errors |",
                          "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for (goal, arm), v in sorted(g.items()):
        ok = [x for x in v if x.get("status") not in ("error", "no_json")]
        w = [x["wall_ms"] for x in ok]
        s = {"runs": len(v), "verified": sum(bool(x["verified"]) for x in v),
             "wall_ms_p50": round(st.median(w), 0) if w else None, "wall_ms_min": round(min(w)) if w else None,
             "wall_ms_max": round(max(w)) if w else None,
             "model_calls_median": st.median([x.get("model_calls") or 0 for x in ok]) if ok else None,
             "phone_actions_median": st.median([x.get("phone_actions") or 0 for x in ok]) if ok else None,
             "errors": [x.get("error") or x.get("status") for x in v if x.get("status") in ("error", "no_json")],
             "unverified_statuses": [x.get("status") for x in v if not x["verified"]]}
        summary[f"{goal}|{arm}"] = s
        lines.append(f"| {goal} | {arm} | {s['verified']}/{s['runs']} | {s['wall_ms_p50']} | {s['wall_ms_min']}-{s['wall_ms_max']} | "
                     f"{s['model_calls_median']} | {s['phone_actions_median']} | {len(s['errors'])} |")
    by_arm = collections.defaultdict(list)
    for r in rs:
        by_arm[r["arm"]].append(r)
    lines += ["", "| arm (all goals) | verified/runs | wall ms p50 | p95 |", "| --- | --- | --- | --- |"]
    for arm, v in sorted(by_arm.items()):
        w = [x["wall_ms"] for x in v if x.get("wall_ms") and x.get("status") not in ("error", "no_json")]
        lines.append(f"| {arm} | {sum(bool(x['verified']) for x in v)}/{len(v)} | {round(st.median(w))} | {round(pct(w, .95))} |")
        summary[f"ALL|{arm}"] = {"runs": len(v), "verified": sum(bool(x["verified"]) for x in v),
                                 "wall_ms_p50": round(st.median(w)), "wall_ms_p95": round(pct(w, .95))}
    (STUDY / "analysis/live-summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    (STUDY / "analysis/live-summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def browser():
    rs = rows("data/browser/*.jsonl")
    g = collections.defaultdict(list)
    for r in rs:
        g[(r["task"], r["arm"])].append(r)
    summary, lines = {}, ["| task | arm | verified/runs | total ms p50 | range | observe ms p50 | settle ms p50 | observation bytes p50 | observations |",
                          "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for (task, arm), v in sorted(g.items()):
        t = [x["total_ms"] for x in v]
        s = {"runs": len(v), "verified": sum(x["verified"] for x in v), "total_ms_p50": round(st.median(t), 1),
             "total_ms_min": round(min(t), 1), "total_ms_max": round(max(t), 1),
             "observe_ms_p50": round(st.median(x["observe_ms_sum"] for x in v), 1),
             "settle_ms_p50": round(st.median(x["settle_ms_sum"] for x in v), 1),
             "obs_bytes_p50": int(st.median(x["obs_bytes_sum"] for x in v)),
             "observations": int(st.median(x["observations"] for x in v))}
        summary[f"{task}|{arm}"] = s
        lines.append(f"| {task} | {arm} | {s['verified']}/{s['runs']} | {s['total_ms_p50']} | {s['total_ms_min']}-{s['total_ms_max']} | "
                     f"{s['observe_ms_p50']} | {s['settle_ms_p50']} | {s['obs_bytes_p50']} | {s['observations']} |")
    (STUDY / "analysis/browser-summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    (STUDY / "analysis/browser-summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    live()
    print()
    browser()
