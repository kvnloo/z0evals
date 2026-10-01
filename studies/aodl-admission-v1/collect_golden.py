#!/usr/bin/env python3
"""Collect one governed root trace from canonical z0 receipts without inventing success."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = path.read_bytes()
    rows = []
    for line in data.splitlines(keepends=True):
        if not line.strip() or not line.endswith(b"\n"):
            continue
        rows.append(json.loads(line))
    return rows


def latest_by_trace(rows):
    latest = {}
    for row in rows:
        trace = row.get("trace_id")
        if isinstance(trace, str):
            latest[trace] = row
    return latest


def find_one(rows, predicate):
    matches = [row for row in rows if predicate(row)]
    return matches[-1] if matches else None


def verified_outcome(outcomes, trace_ids):
    hits = []
    for row in outcomes:
        if row.get("trace_id") not in trace_ids:
            continue
        outcome = row.get("outcome") or {}
        if row.get("outcome_tier") == "gold" and (
            outcome.get("verified_success") is not None
            or outcome.get("verified") is not None
            or outcome.get("test_pass") is not None
            or outcome.get("verifier_ok") is not None
            or outcome.get("pr_merged") is not None
            or outcome.get("task_done") is not None
        ):
            hits.append(row)
    return hits[-1] if hits else None


def collect(receipts, outcomes, tokenomics, root_trace_id):
    latest = latest_by_trace(receipts)

    preparation = find_one(
        receipts,
        lambda r: r.get("capability_id") == "aodl.governed_request"
        and (r.get("extra") or {}).get("caller_trace_id") == root_trace_id,
    )
    admission = find_one(
        receipts,
        lambda r: r.get("capability_id") == "aodl.structural_admission"
        and (r.get("extra") or {}).get("caller_trace_id") == root_trace_id,
    )
    dispatch = find_one(
        receipts,
        lambda r: r.get("capability_id") == "intelligence.dispatch"
        and (r.get("extra") or {}).get("caller_trace_id") == root_trace_id,
    )

    dispatch_id = dispatch.get("trace_id") if dispatch else None
    admission_id = admission.get("trace_id") if admission else None

    provider_admission = find_one(
        receipts,
        lambda r: r.get("capability_id") == "intelligence.provider_admission"
        and (r.get("extra") or {}).get("permit_dispatch_id") == dispatch_id,
    ) if dispatch_id else None

    physical = find_one(
        receipts,
        lambda r: (r.get("extra") or {}).get("authority_dispatch_id") == dispatch_id
        and r.get("execution") == "live",
    ) if dispatch_id else None

    gate_latency = find_one(
        tokenomics,
        lambda r: r.get("schema") == "z0int.aodl_gate_latency.v1"
        and r.get("trace_id") == admission_id,
    ) if admission_id else None

    result = (dispatch.get("extra") or {}).get("result") if dispatch else None
    physical_trace = physical.get("trace_id") if physical else None
    verified = verified_outcome(outcomes, {x for x in (root_trace_id, dispatch_id, physical_trace) if x})

    admission_payload = (admission.get("extra") or {}).get("aodl_admission") if admission else None
    usage_known = bool(
        physical
        and isinstance(physical.get("input_tokens"), int)
        and isinstance(physical.get("output_tokens"), int)
    )

    checks = {
        "preparation_present": preparation is not None,
        "admission_present": admission is not None,
        "admission_allowed": bool(admission_payload and admission_payload.get("allowed") is True),
        "dispatch_present": dispatch is not None,
        "dispatch_links_admission": bool(
            dispatch and (dispatch.get("extra") or {}).get("aodl_admission_receipt_id") == admission_id
        ),
        "provider_admission_present": provider_admission is not None,
        "provider_admission_links_dispatch": bool(
            provider_admission and (provider_admission.get("extra") or {}).get("permit_dispatch_id") == dispatch_id
        ),
        "physical_receipt_present": physical is not None,
        "physical_links_dispatch": bool(
            physical and (physical.get("extra") or {}).get("authority_dispatch_id") == dispatch_id
        ),
        "usage_known": usage_known,
        "gate_latency_present": gate_latency is not None,
        "result_root_trace_matches": bool(result and result.get("trace_id") == root_trace_id),
        "verified_outcome_present": verified is not None,
    }

    structural_required = (
        "preparation_present",
        "admission_present",
        "admission_allowed",
        "dispatch_present",
        "dispatch_links_admission",
        "provider_admission_present",
        "provider_admission_links_dispatch",
        "physical_receipt_present",
        "physical_links_dispatch",
        "usage_known",
        "gate_latency_present",
        "result_root_trace_matches",
    )

    return {
        "schema": "z0eval.aodl_golden_trace.v1",
        "root_trace_id": root_trace_id,
        "structural_execution_complete": all(checks[name] for name in structural_required),
        "verified_outcome_complete": checks["verified_outcome_present"],
        "checks": checks,
        "stages": {
            "governed_preparation": {
                "receipt_id": preparation.get("trace_id") if preparation else None,
                "present": preparation is not None,
            },
            "aodl_admission": {
                "receipt_id": admission_id,
                "present": admission is not None,
                "allowed": admission_payload.get("allowed") if isinstance(admission_payload, dict) else None,
                "codes": admission_payload.get("codes") if isinstance(admission_payload, dict) else None,
                "semantic_fingerprint": admission_payload.get("aodl_semantic_fingerprint") if isinstance(admission_payload, dict) else None,
                "intent_source_hash": admission_payload.get("aodl_intent_source_hash") if isinstance(admission_payload, dict) else None,
            },
            "dispatch": {
                "receipt_id": dispatch_id,
                "present": dispatch is not None,
                "status": (dispatch.get("extra") or {}).get("status") if dispatch else None,
            },
            "provider_admission": {
                "receipt_id": provider_admission.get("trace_id") if provider_admission else None,
                "present": provider_admission is not None,
                "status": (provider_admission.get("extra") or {}).get("status") if provider_admission else None,
                "provider": provider_admission.get("provider") if provider_admission else None,
            },
            "physical_execution": {
                "receipt_id": physical_trace,
                "present": physical is not None,
                "status": (physical.get("extra") or {}).get("status") if physical else None,
                "provider": physical.get("provider") if physical else None,
                "model": physical.get("model") if physical else None,
                "input_tokens": physical.get("input_tokens") if physical else None,
                "output_tokens": physical.get("output_tokens") if physical else None,
            },
            "gate_latency": {
                "present": gate_latency is not None,
                "latency_ms": gate_latency.get("latency_ms") if gate_latency else None,
            },
            "verified_outcome": {
                "present": verified is not None,
                "trace_id": verified.get("trace_id") if verified else None,
                "outcome_tier": verified.get("outcome_tier") if verified else None,
                "outcome": verified.get("outcome") if verified else None,
            },
        },
        "limitations": (
            []
            if verified is not None
            else ["No gold verified outcome is joined; execution completion is not task success."]
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--tokenomics", type=Path, required=True)
    parser.add_argument("--trace-id", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-verified", action="store_true")
    args = parser.parse_args()

    proof = collect(
        read_jsonl(args.receipts),
        read_jsonl(args.outcomes),
        read_jsonl(args.tokenomics),
        args.trace_id,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    passed = proof["structural_execution_complete"] and (
        proof["verified_outcome_complete"] or not args.require_verified
    )
    print(json.dumps({
        "structural_execution_complete": proof["structural_execution_complete"],
        "verified_outcome_complete": proof["verified_outcome_complete"],
        "require_verified": args.require_verified,
        "passed": passed,
        "out": str(args.out),
    }))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
