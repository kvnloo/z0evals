#!/usr/bin/env python3
"""Adapt the Phase 1B run into the site's data document.

Source of truth, in order of preference:
  1. the raw per-call observations (results/phase1b/<run>/observations.jsonl)
     when the local-only source is present;
  2. the committed transcription (studies/slm-router-v0/data/phase1b-summary.json).

Every value the site renders is derived from one of those. Nothing is invented:
if a dimension was not measured it is emitted as null and the component omits it.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "studies" / "slm-router-v0" / "data" / "phase1b-summary.json"
MATRIX_OUT = ROOT / "studies" / "slm-router-v0" / "data" / "phase1b-matrix.json"
SITE_OUT = ROOT / "web" / "data" / "study.json"
RUN = "p1b-20260921T1430Z"

ARM_LABEL = {
    "compiler+functiongemma_270m": "FnGemma 270M",
    "compiler+hammer2.1_3b": "Hammer 3B",
    "compiler+hammer2.1_7b": "Hammer 7B",
    "compiler+jev": "NanoJev 0.6B",
    "compiler+nemotron_orchestrator_8b": "Nemotron 8B",
    "compiler+qwen3.5_4b": "Qwen 4B",
    "compiler+qwen3.5_9b": "Qwen 9B",
    "unfiltered+hammer2.1_3b": "Unfiltered · Hammer 3B",
    "unfiltered+nemotron_orchestrator_8b": "Unfiltered · Nemotron",
    "unfiltered+qwen3.5_4b": "Unfiltered · Qwen 4B",
    "unfiltered+qwen3.5_9b": "Unfiltered · Qwen 9B",
}
ARM_ORDER = [
    "compiler+hammer2.1_3b", "compiler+qwen3.5_4b", "compiler+qwen3.5_9b",
    "compiler+hammer2.1_7b", "compiler+nemotron_orchestrator_8b",
    "compiler+functiongemma_270m", "compiler+jev",
    "unfiltered+hammer2.1_3b", "unfiltered+qwen3.5_4b",
    "unfiltered+qwen3.5_9b", "unfiltered+nemotron_orchestrator_8b",
]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval — the honest band for a bounded-count success rate."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


def find_raw() -> Path | None:
    for base in (Path("/home/kvn/tmp/openjev"), Path.home() / "tmp" / "openjev"):
        p = base / "results" / "phase1b" / RUN / "observations.jsonl"
        if p.is_file():
            return p
    return None


def build_matrix(raw: Path) -> dict:
    rows = [json.loads(l) for l in raw.read_text(encoding="utf-8").splitlines() if l.strip()]
    bc = [r for r in rows if r.get("arm_kind") in ("bounded", "unfiltered")]

    states: dict[str, dict] = {}
    for r in bc:
        s = states.setdefault(r["state_id"], {
            "id": r["state_id"], "family": r["state_family"],
            "legalCount": len(r.get("legal_actions") or []),
            "deterministicSolution": r.get("deterministic_solution"),
            "arms": {},
        })
        a = s["arms"].setdefault(r["arm"], {"runs": []})
        a["runs"].append({
            "correct": bool(r.get("correct")),
            "abstained": bool(r.get("abstained")),
            "invalid": bool(r.get("invalid_call")),
            "dangerous": bool(r.get("dangerous_selected")),
            "decisionMs": r.get("decision_ms"),
            "confidence": r.get("confidence"),
            "entropy": r.get("entropy"),
            "margin": r.get("margin"),
            "selected": r.get("selected_action"),
            "goldAction": (r.get("verification") or {}).get("gold_action"),
            "expectAbstain": (r.get("verification") or {}).get("expect_abstain"),
            "repetition": r.get("repetition"),
            "coldOrWarm": r.get("cold_or_warm"),
            "tokensIn": r.get("tokens_in"),
            "tokensOut": r.get("tokens_out"),
            "costUsd": r.get("cost_usd"),
        })

    state_list = sorted(states.values(), key=lambda s: s["id"])
    for s in state_list:
        for a in s["arms"].values():
            runs = a["runs"]
            a["n"] = len(runs)
            a["successRate"] = sum(1 for x in runs if x["correct"]) / len(runs) if runs else None
            ms = sorted(x["decisionMs"] for x in runs if x["decisionMs"] is not None)
            a["p50Ms"] = ms[len(ms) // 2] if ms else None
            a["unanimous"] = len({x["correct"] for x in runs}) == 1

    # per-arm aggregates over the whole matrix
    agg: dict[str, dict] = {}
    for s in state_list:
        for arm, a in s["arms"].items():
            g = agg.setdefault(arm, {"runs": [], "states": 0, "repDisagree": 0})
            g["runs"].extend(a["runs"])
            g["states"] += 1
            if not a["unanimous"]:
                g["repDisagree"] += 1

    arms = []
    for arm in ARM_ORDER + [a for a in agg if a not in ARM_ORDER]:
        if arm not in agg:
            continue
        g = agg[arm]
        runs = g["runs"]
        n = len(runs)
        k = sum(1 for x in runs if x["correct"])
        warm = sorted(x["decisionMs"] for x in runs if x["decisionMs"] is not None)
        arms.append({
            "id": arm,
            "label": ARM_LABEL.get(arm, arm),
            "unfiltered": arm.startswith("unfiltered"),
            "n": n,
            "states": g["states"],
            "success": k,
            "successRate": k / n,
            "wilson95": [round(v, 4) for v in wilson(k, n)],
            "warmP50Ms": warm[len(warm) // 2] if warm else None,
            "warmP95Ms": warm[min(len(warm) - 1, int(len(warm) * 0.95))] if warm else None,
            "dangerous": sum(1 for x in runs if x["dangerous"]),
            "abstained": sum(1 for x in runs if x["abstained"]),
            "invalid": sum(1 for x in runs if x["invalid"]),
            "repDisagreeStates": g["repDisagree"],
            "meanConfidence": (sum(x["confidence"] for x in runs if x["confidence"] is not None)
                               / max(1, sum(1 for x in runs if x["confidence"] is not None))),
        })

    families = []
    for fam in sorted({s["family"] for s in state_list}):
        fam_states = [s for s in state_list if s["family"] == fam]
        runs = [x for s in fam_states for a in s["arms"].values() for x in a["runs"]]
        families.append({
            "name": fam,
            "states": len(fam_states),
            "runs": len(runs),
            "correct": sum(1 for x in runs if x["correct"]),
            "abstained": sum(1 for x in runs if x["abstained"]),
            "invalid": sum(1 for x in runs if x["invalid"]),
            "dangerous": sum(1 for x in runs if x["dangerous"]),
        })
    families.sort(key=lambda f: -f["runs"])

    return {
        "runId": RUN,
        "arms": arms,
        "states": state_list,
        "families": families,
        "armOrder": [a["id"] for a in arms],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", help="path to observations.jsonl")
    args = ap.parse_args()

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    raw = Path(args.raw) if args.raw else find_raw()

    if raw and raw.is_file():
        matrix = build_matrix(raw)
        MATRIX_OUT.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
        origin = f"raw observations ({raw})"
    elif MATRIX_OUT.is_file():
        matrix = json.loads(MATRIX_OUT.read_text(encoding="utf-8"))
        origin = "committed transcription (studies/slm-router-v0/data/phase1b-matrix.json)"
    else:
        matrix = None
        origin = "summary only"

    doc = {
        "schema": "z0evals.site.study.v1",
        "study": {
            "id": summary["study_id"], "runId": summary["run_id"],
            "title": "Small Models Calling the Shots",
            "subtitle": "Phase 1B: what actually routes best on a local RTX 3080 Ti?",
            "author": "Kevin Rajan", "date": "September 21, 2026",
            "evidenceStatus": summary["evidence_status"],
            "hardware": summary["hardware"],
            "externalSpendUsd": summary["external_inference_spend_usd"],
        },
        "provenance": summary["provenance"],
        "sources": summary["sources"],
        "density": summary["density"],
        "residency": {
            "classes": [
                {"label": "cold load", "p50Ms": summary["residency"]["cold_load_p50_ms"]},
                {"label": "model swap", "p50Ms": summary["residency"]["model_swap_p50_ms"]},
                {"label": "warm invocation", "p50Ms": summary["residency"]["warm_invocation_p50_ms"]},
            ],
            "coldExamples": summary["residency"]["cold_total_examples_ms"],
        },
        "composition": {
            "statesTotal": summary["composition"]["states_total"],
            "artifactConsumedStates": summary["composition"]["artifact_delivered_consumed_states"],
            "base": "qwen4b",
            "baseCorrect": summary["composition"]["qwen4b_alone_correct"],
            "variants": [
                {"id": "qwen4b+hammer3b", "label": "Qwen 4B + Hammer 3B",
                 "correct": summary["composition"]["qwen4b_plus_hammer3b_correct"],
                 "helped": summary["composition"]["qwen4b_plus_hammer3b_helped_states"],
                 "hurt": summary["composition"]["qwen4b_plus_hammer3b_hurt_states"]},
                {"id": "qwen4b+jev", "label": "Qwen 4B + NanoJev",
                 "correct": summary["composition"]["qwen4b_plus_jev_correct"],
                 "helped": summary["composition"]["qwen4b_plus_jev_helped_states"],
                 "hurt": summary["composition"]["qwen4b_plus_jev_hurt_states"]},
            ],
        },
        "orchestration": {"expanded": {"total": 40, **summary["orchestration"]["expanded_40"]},
                          "frozen": {"total": 12, **summary["orchestration"]["frozen_12_scenario_reproduction"]}},
        "compilerContract": summary["compiler_contract"],
        "features": summary["features"],
        "gate": summary["gate"],
        "tests": summary["tests"],
        "matrix": matrix,
        "matrixOrigin": origin,
    }
    SITE_OUT.parent.mkdir(parents=True, exist_ok=True)
    SITE_OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {SITE_OUT.relative_to(ROOT)}   (matrix from {origin})")
    if matrix:
        print(f"  arms={len(matrix['arms'])} states={len(matrix['states'])} families={len(matrix['families'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
