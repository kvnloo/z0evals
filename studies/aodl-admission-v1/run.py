#!/usr/bin/env python3
"""Frozen runner for z0evals#78 AODL admission conformance."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
Z0INT_REVISION = "ba43be05c450035929804cf4f8e1f4588c871777"
AODL_REVISION = "68231658f0ec0338464c0916a2329b9587444312"


def base_document(overrides):
    dynamic_allowed = overrides.get("dynamic_allowed", True)
    max_children = overrides.get("max_children", 4)
    max_depth = overrides.get("max_depth", 2)
    dim = overrides.get("budget_dim", "tokens")
    limit = 10 ** 1000 if overrides.get("huge_budget") else overrides.get("budget_limit", 1000)
    ceiling = overrides.get("ceiling", ["execute", "verify"])
    node_kind = ["task"] if overrides.get("invalid_kind") else "task"
    return {
        "specVersion": "0.2",
        "graphId": "admission-study",
        "revision": 3,
        "intentGraph": {
            "nodes": [{
                "id": "parent",
                "kind": node_kind,
                "ports": [{"id": "out", "direction": "out", "schema": "Task"}],
                "capabilities": ["execute"],
                "authorityCeiling": ceiling,
                "lifecycle": "declared",
            }],
            "edges": [],
        },
        "policies": {
            "kinds": ["sequence"],
            "fanIn": "all",
            "dynamic": {
                "allowed": dynamic_allowed,
                "maxChildren": max_children,
                "maxDepth": max_depth,
            },
        },
        "constraints": {
            "budgets": {dim: limit},
            "termination": {"on": "done"},
        },
        "provenance": {"source": "z0evals#78", "sourceHash": "0" * 64},
    }


def make_request(cls, overrides):
    dim = overrides.get("budget_dim", "tokens")
    observed = [] if overrides.get("malformed_observed") else {dim: overrides.get("observed_value", 400)}
    proposed = {dim: overrides.get("proposed_value", 100)}
    return cls(
        request_revision=overrides.get("request_revision", 3),
        parent_node_id=overrides.get("parent_node_id", "parent"),
        live_children=overrides.get("live_children", 1),
        parent_depth=overrides.get("parent_depth", 0),
        observed=observed,
        proposed=proposed,
        requested=tuple(overrides.get("requested", ["execute"])),
    )


def semantic_tuple(decision):
    return (
        decision.allowed,
        decision.codes,
        decision.numeric_codes,
        decision.semantic_fingerprint,
        decision.contract_revision,
        decision.request_revision,
        decision.parent_node_id,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--z0int-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.z0int_root / "src"))
    from z0int.aodl_admission import SpawnRequest, decide_spawn
    import aodl_contract

    class FutureCanon:
        CANON_VERSION = "aodl-canon-2"
        validate = staticmethod(aodl_contract.validate)
        semantic_fingerprint = staticmethod(aodl_contract.semantic_fingerprint)

    rows = []
    failed = 0
    for case in CASES["cases"]:
        doc = base_document(case.get("document") or {})
        req = make_request(SpawnRequest, case.get("request") or {})
        api = FutureCanon if case.get("api_mode") == "future-canon" else None
        first = decide_spawn(doc, req, contract_api=api)
        second = decide_spawn(doc, req, contract_api=api)
        replay_stable = semantic_tuple(first) == semantic_tuple(second)

        expected_allow = case["expected_allow"]
        expected_numeric = tuple(case.get("expected_codes") or ())
        expected_labels = tuple(case.get("expected_labels") or ())
        ok = first.allowed is expected_allow and replay_stable
        if expected_numeric:
            ok = ok and first.numeric_codes == expected_numeric
        if expected_labels:
            ok = ok and first.codes == expected_labels
        if not ok:
            failed += 1

        row = first.receipt()
        row["schema"] = "z0eval.aodl_admission_receipt.v1"
        row["case_id"] = case["id"]
        row["replay_stable"] = replay_stable
        row["z0int_revision"] = Z0INT_REVISION
        row["aodl_revision"] = AODL_REVISION
        rows.append(row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(json.dumps({"cases": len(rows), "failed": failed, "out": str(args.out)}))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
