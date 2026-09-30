#!/usr/bin/env python3
"""Score automatic AgentWeb -> z0 route-plan shadow observations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_jsonl(path: str) -> list[dict]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def score(rows: list[dict]) -> dict:
    executed = [r["id"] for r in rows if r.get("executed") is True]
    wrong_route = [
        r["id"] for r in rows
        if r.get("route_kind") != r.get("expected_route")
    ]
    reconcile = [r["id"] for r in rows if r.get("reconcile_required") is True]
    raw_identity = [r["id"] for r in rows if r.get("raw_session_leak") is True]
    failures = [r["id"] for r in rows if r.get("ok") is not True]
    gates = {
        "zero_execution": not executed,
        "expected_abstention": not wrong_route,
        "no_reconciliation_required": not reconcile,
        "no_raw_session_leak": not raw_identity,
        "all_observations_returned": not failures,
    }
    return {
        "schema": "z0eval.agentweb_route_shadow_summary.v1",
        "n": len(rows),
        "executed_violations": executed,
        "route_mismatches": wrong_route,
        "reconcile_violations": reconcile,
        "privacy_violations": raw_identity,
        "observation_failures": failures,
        "gates": gates,
        "passed": all(gates.values()),
        "interpretation": (
            "This corpus establishes the current native_turn abstention baseline. "
            "It is not routing-quality evidence and cannot authorize active routing."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("results")
    p.add_argument("--output")
    args = p.parse_args()
    summary = score(read_jsonl(args.results))
    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
