#!/usr/bin/env python3
"""Score the AgentWeb -> z0 reliability observation cross-repo campaign."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


FORBIDDEN_OUTCOME_KEYS = {"verified_success", "verified", "verification_source", "test_pass", "verifier_ok", "task_done", "pr_merged"}


def _read_jsonl(path: str) -> list[dict]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def score(results: list[dict], receipts: list[dict]) -> dict:
    observed = [
        row for row in receipts
        if str(row.get("trace_id", "")).startswith("agentweb-observe-")
    ]
    by_trace = {row.get("trace_id"): row for row in observed}

    export_failures = [r.get("id") for r in results if r.get("first_exported") is not True]
    replay_failures = [
        r.get("id") for r in results
        if r.get("second_exported") is not True or r.get("second_replayed") is not True
    ]
    privacy_leaks = [r.get("id") for r in results if r.get("projection_privacy_ok") is not True]
    missing_receipts = [r.get("id") for r in results if r.get("trace_id") not in by_trace]

    semantic_failures: list[str] = []
    quality_violations: list[str] = []
    for result in results:
        row = by_trace.get(result.get("trace_id"))
        if not row:
            continue
        outcome = row.get("outcome") or {}
        expected = result.get("expected") or {}
        for key in ("execution_completed", "tool_ok", "success", "user_refused"):
            if key in expected and outcome.get(key) is not expected[key]:
                semantic_failures.append(f"{result.get('id')}:{key}")
        if any(key in outcome for key in FORBIDDEN_OUTCOME_KEYS):
            quality_violations.append(result.get("id"))
        if row.get("execution") != "log_only" or row.get("measurement_state") != "partial":
            quality_violations.append(result.get("id"))
        extra = row.get("extra") or {}
        if extra.get("quality_authoritative") is not False or extra.get("status") != "observed":
            quality_violations.append(result.get("id"))

    duplicate_rows = len(observed) != len({r.get("trace_id") for r in observed})
    gates = {
        "all_first_exports_stored": not export_failures,
        "all_second_exports_replayed": not replay_failures,
        "projection_privacy_preserved": not privacy_leaks,
        "one_durable_row_per_observation": not duplicate_rows and len(observed) == len(results),
        "receipt_semantics_match": not semantic_failures,
        "never_mints_quality_gold": not quality_violations,
    }
    return {
        "schema": "z0eval.agentweb_reliability_summary.v1",
        "n_results": len(results),
        "n_observed_receipts": len(observed),
        "export_failures": export_failures,
        "replay_failures": replay_failures,
        "privacy_leaks": privacy_leaks,
        "missing_receipts": missing_receipts,
        "semantic_failures": semantic_failures,
        "quality_violations": sorted(set(quality_violations)),
        "gates": gates,
        "passed": all(gates.values()) and not missing_receipts,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("results")
    p.add_argument("receipts")
    p.add_argument("--output")
    args = p.parse_args()
    summary = score(_read_jsonl(args.results), _read_jsonl(args.receipts))
    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
