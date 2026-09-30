#!/usr/bin/env python3
"""Score AgentWeb -> z0 bounded context packet experiment rows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median


def score(rows: list[dict]) -> dict:
    fixture = [r for r in rows if r.get("sample_source") == "fixture"]
    live = [r for r in rows if r.get("sample_source") == "live"]

    successful = [r for r in rows if r.get("ok") is True]
    budget_violations = [
        r.get("id") for r in successful
        if isinstance(r.get("packet_bytes"), int)
        and isinstance(r.get("max_packet_bytes"), int)
        and r["packet_bytes"] > r["max_packet_bytes"]
    ]
    required_term_failures = [
        r.get("id") for r in fixture
        if r.get("required_terms_preserved") is not True
    ]
    privacy_leaks = [r.get("id") for r in rows if r.get("source_label_leak") is True]
    applied = [r.get("id") for r in rows if r.get("applied") is True]
    persistence = [
        r.get("id") for r in successful
        if r.get("private_text_persisted") is not False
    ]
    model_calls = [
        r.get("id") for r in successful
        if r.get("network_model_calls") != 0
    ]
    diversity_failures = [
        r.get("id") for r in fixture
        if isinstance(r.get("source_diversity_target"), int)
        and (r.get("retained_source_count") or 0) < r["source_diversity_target"]
        and r.get("source_diversity_degraded_for_budget") is not True
    ]
    diversity_budget_degradations = [
        r.get("id") for r in fixture
        if r.get("source_diversity_degraded_for_budget") is True
    ]
    gap_mismatches = [
        r.get("id") for r in fixture
        if bool(r.get("expect_gap")) != bool((r.get("unresolved_gap_count") or 0) > 0)
    ]
    truncation_failures = [
        r.get("id") for r in fixture
        if r.get("expect_compress") is True
        and (r.get("truncated_excerpts") or 0) <= 0
    ]
    # ContextPacket has fixed structural/provenance overhead. Total-byte
    # compression is meaningful only after the source payload is large enough
    # to amortize that envelope; use the same >=8KB threshold as the live gate.
    large_fixture_rows = [
        r for r in fixture
        if r.get("expect_compress") is True
        and isinstance(r.get("input_content_bytes"), (int, float))
        and r["input_content_bytes"] >= 8000
        and isinstance(r.get("compression_ratio"), (int, float))
    ]
    weak_compression = [
        r.get("id") for r in large_fixture_rows
        if float(r["compression_ratio"]) >= 0.80
    ]
    live_ratios = [
        float(r["compression_ratio"])
        for r in live
        if isinstance(r.get("compression_ratio"), (int, float))
        and (r.get("input_content_bytes") or 0) >= 8000
    ]

    gates = {
        "fixture_required_terms_preserved": not required_term_failures,
        "packet_budget_respected": not budget_violations,
        "source_labels_private": not privacy_leaks,
        "shadow_never_applied": not applied,
        "private_text_not_persisted": not persistence,
        "zero_model_calls": not model_calls,
        "source_diversity_or_explicit_budget_degradation": not diversity_failures,
        "gap_semantics_match": not gap_mismatches,
        "fixture_expected_excerpts_truncated": not truncation_failures,
        "fixture_large_context_sample_present": len(large_fixture_rows) >= 3,
        "fixture_large_context_compression_under_80pct": (
            len(large_fixture_rows) >= 3 and not weak_compression
        ),
        "minimum_live_sample": len(live) >= 500,
        "live_large_context_median_compression_under_70pct": (
            len(live_ratios) >= 100 and median(live_ratios) <= 0.70
        ),
    }
    return {
        "schema": "z0eval.agentweb_context_packet_summary.v1",
        "n_rows": len(rows),
        "n_fixture": len(fixture),
        "n_live": len(live),
        "budget_violations": budget_violations,
        "required_term_failures": required_term_failures,
        "privacy_leaks": privacy_leaks,
        "applied_violations": applied,
        "persistence_violations": persistence,
        "model_call_violations": model_calls,
        "source_diversity_failures": diversity_failures,
        "source_diversity_budget_degradations": diversity_budget_degradations,
        "gap_mismatches": gap_mismatches,
        "truncation_failures": truncation_failures,
        "fixture_large_context_n": len(large_fixture_rows),
        "fixture_large_context_ratios": {
            str(r.get("id")): float(r["compression_ratio"])
            for r in large_fixture_rows
        },
        "weak_compression": weak_compression,
        "live_large_context_n": len(live_ratios),
        "live_large_context_median_compression": (
            median(live_ratios) if live_ratios else None
        ),
        "gates": gates,
        "eligible_for_assist_review": all(gates.values()),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("results")
    p.add_argument("--output")
    args = p.parse_args()
    rows = [
        json.loads(line)
        for line in Path(args.results).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    summary = score(rows)
    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
