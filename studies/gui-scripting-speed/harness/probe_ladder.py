#!/usr/bin/env python3
"""Difficulty-ladder probe: what can each shadow SLM already win? (curriculum start point)

Levels derived deterministically (seeded) from the frozen 46-case fixture:
  L1  boolean   "is the goal's answer visible on this screen now?"  (gold: 'done' in gold)
  L2  2-way     gold action vs one non-gold distractor, asked in BOTH orders (position bias)
  L3  4-way     gold + 3 non-gold distractors
  L4  full      the whole legal table (from shadow_eval.py; not re-run here)
Passive predictions on a fixture; nothing is executed.

    python harness/probe_ladder.py --arm z0int:openjev_06b --out data/ladder/openjev.jsonl
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from shadow_eval import CASES, INSTRUCTIONS, make_arm, state_for  # noqa: E402

DONE_Q = "Is the answer to the goal already visible on this screen right now?"


def gold_id(c):
    for g in c["gold"]:
        if g not in ("reobserve", "abstain"):
            return g
    return c["gold"][0]


def derived(cases, seed=20261020):
    rng = random.Random(seed)
    out = []
    for c in cases:
        g = gold_id(c)
        gold_opt = next(o for o in c["candidates"] if o["id"] == g)
        others = [o for o in c["candidates"] if o["id"] not in c["gold"]]
        out.append({"level": "L1", "case": c, "type": "boolean", "gold": "done" in c["gold"]})
        if others:
            d = rng.choice(others)
            out.append({"level": "L2", "case": c, "type": "choice", "options": [gold_opt, d], "gold": g, "order": "gold_first"})
            out.append({"level": "L2", "case": c, "type": "choice", "options": [d, gold_opt], "gold": g, "order": "gold_second"})
        if len(others) >= 3:
            opts = rng.sample(others, 3) + [gold_opt]
            rng.shuffle(opts)
            out.append({"level": "L3", "case": c, "type": "choice", "options": opts, "gold": g})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cases = json.loads(CASES.read_text())
    arm = make_arm(a.arm)
    cold = arm.load()
    items = derived(cases)
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a") as f:
        f.write(json.dumps({"schema": "z0evals.gui_scripting_speed.ladder.v1.header", "arm": a.arm,
                            "cold_load_ms": cold, "items": len(items), "ts": time.time()}) + "\n")
    for it in items:
        c = it["case"]
        t0 = time.perf_counter()
        err = None
        try:
            if a.arm.startswith("z0int:"):
                if it["type"] == "boolean":
                    q = {"id": "done", "type": "boolean", "instructions": DONE_Q}
                else:
                    q = {"id": "next", "type": "choice", "instructions": INSTRUCTIONS,
                         "options": [{"id": o["id"], "description": o["description"]} for o in it["options"]]}
                res = arm.backend.evaluate(arm.req({"state": state_for(c), "request_id": c["case"], "questions": [q]}))
                ans = res.answers[0]
                pick, conf = ans.value, ans.confidence
            else:
                # Jev's contract requires reobserve + abstain rows; they are added and scored as wrong.
                extra = [{"id": "reobserve", "description": "Look at the screen again without changing anything."},
                         {"id": "abstain", "description": "Do not act; stop and ask the person for help."}]
                if it["type"] == "boolean":
                    sub = dict(c, candidates=[{"id": "done", "description": "Stop: the answer is visible on screen now."},
                                              {"id": "continue", "description": "Not yet: keep navigating."}] + extra)
                    r = arm.choose(sub, 0)
                    pick, conf = r["raw_argmax"] == "done", r["confidence"]
                else:
                    opts = [o for o in it["options"] if o["id"] not in ("reobserve", "abstain")]
                    r = arm.choose(dict(c, candidates=opts + extra), 0)
                    pick, conf = r["raw_argmax"], r["confidence"]
        except Exception as e:  # noqa: BLE001
            pick, conf, err = None, None, f"{type(e).__name__}: {str(e)[:160]}"
        ms = (time.perf_counter() - t0) * 1000
        if it["type"] == "boolean" and isinstance(pick, str):
            pick = pick.lower() in ("true", "yes", "1")
        row = {"schema": "z0evals.gui_scripting_speed.ladder.v1", "arm": a.arm, "level": it["level"],
               "case": c["case"], "kind": c["kind"], "order": it.get("order"), "gold": it["gold"], "pick": pick,
               "confidence": conf, "correct": pick == it["gold"], "latency_ms": round(ms, 2), "error": err,
               "evidence_class": "passive_shadow_prediction_on_frozen_fixture"}
        with out.open("a") as f:
            f.write(json.dumps(row) + "\n")
    print(a.arm, "done", len(items))


if __name__ == "__main__":
    main()
