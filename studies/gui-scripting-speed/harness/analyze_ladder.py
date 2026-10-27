#!/usr/bin/env python3
"""Per-model capability profile from the difficulty ladder (+ L4 from the shadow eval).

    python harness/analyze_ladder.py   # writes analysis/capability-profiles.{json,md}
L2 is asked in both orders: 'both' = right in both orders (order-robust), 'one' = right in
exactly one order (position-driven), chance = 50%. L3 chance = 25%. L1 chance depends on the
base rate of 'done' cases (reported).
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


def main():
    shadow = json.loads((STUDY / "analysis/shadow-summary.json").read_text())["arms"]
    prof = {}
    for f in sorted(glob.glob(str(STUDY / "data/ladder/*.jsonl"))):
        rows = [json.loads(l) for l in open(f)]
        rows = [r for r in rows if not r["schema"].endswith(".header")]
        if not rows:
            continue
        arm = rows[0]["arm"]
        p = {}
        for lvl in ("L1", "L2", "L3"):
            rs = [r for r in rows if r["level"] == lvl]
            if not rs:
                continue
            lat = [r["latency_ms"] for r in rs if not r["error"]]
            p[lvl] = {"n": len(rs), "correct": sum(r["correct"] for r in rs), "acc": round(sum(r["correct"] for r in rs) / len(rs), 3),
                      "errors": sum(bool(r["error"]) for r in rs), "p50_ms": round(pct(lat, .5), 1) if lat else None}
            if lvl == "L1":
                p[lvl]["base_rate_done"] = round(sum(bool(r["gold"]) for r in rs) / len(rs), 3)
                p[lvl]["always_no_acc"] = round(1 - p[lvl]["base_rate_done"], 3)
            if lvl == "L2":
                byc = collections.defaultdict(list)
                for r in rs:
                    byc[r["case"]].append(r["correct"])
                p[lvl]["both_orders"] = sum(all(v) and len(v) == 2 for v in byc.values())
                p[lvl]["one_order"] = sum(sum(v) == 1 for v in byc.values())
                p[lvl]["pairs"] = len(byc)
                # order-debiased pair: average p(gold) over both orders (the BT building block)
                pg = collections.defaultdict(list)
                for r in rs:
                    if isinstance(r.get("confidence"), (int, float)) and r["pick"] is not None:
                        pg[r["case"]].append(r["confidence"] if r["correct"] else 1 - r["confidence"])
                both = [sum(v) / 2 for v in pg.values() if len(v) == 2]
                p[lvl]["debiased_acc"] = round(sum(x > 0.5 for x in both) / len(both), 3) if both else None
        s = shadow.get(arm)
        if s:
            p["L4"] = {"n": s["decisions"], "acc": s["raw_accuracy"], "p50_ms": s["latency_ms_p50"]}
        prof[arm] = p
    (STUDY / "analysis/capability-profiles.json").write_text(json.dumps(prof, indent=1) + "\n")
    lines = ["| model | L1 done? acc (always-no) | L2 pair acc | L2 right in both orders / one order | L2 order-debiased | L3 4-way acc | L4 full table acc | p50 ms (L2 / L4) |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for arm, p in sorted(prof.items()):
        l1, l2, l3, l4 = (p.get(k, {}) for k in ("L1", "L2", "L3", "L4"))
        lines.append(f"| {arm} | {l1.get('acc')} ({l1.get('always_no_acc')}) | {l2.get('acc')} | "
                     f"{l2.get('both_orders')}/{l2.get('pairs')} , {l2.get('one_order')}/{l2.get('pairs')} | {l2.get('debiased_acc')} | {l3.get('acc')} | {l4.get('acc')} | "
                     f"{l2.get('p50_ms')} / {l4.get('p50_ms')} |")
    (STUDY / "analysis/capability-profiles.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
