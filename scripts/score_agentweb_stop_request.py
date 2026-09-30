#!/usr/bin/env python3
"""Score paired incumbent vs z0 stop_request_v1 shadow results."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import median


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return xs[lo]
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def _accuracy(rows: list[dict], prediction) -> float | None:
    if not rows:
        return None
    return sum(bool(prediction(r)) == bool(r["expected_stop"]) for r in rows) / len(rows)


def score(rows: list[dict]) -> dict:
    paired = [
        r for r in rows
        if isinstance(r.get("expected_stop"), bool)
        and isinstance(r.get("incumbent_stop"), bool)
        and isinstance(r.get("p_stop"), (int, float))
        and 0 <= float(r["p_stop"]) <= 1
    ]
    high_stop = [r for r in paired if float(r["p_stop"]) >= 0.90]
    high_continue = [r for r in paired if float(r["p_stop"]) <= 0.10]
    ambiguous = [
        r for r in paired
        if 0.10 < float(r["p_stop"]) < 0.90
    ]
    confident = high_stop + high_continue

    high_stop_precision = (
        sum(r["expected_stop"] is True for r in high_stop) / len(high_stop)
        if high_stop else None
    )
    low_band_stop_leakage = (
        sum(r["expected_stop"] is True for r in high_continue) / len(high_continue)
        if high_continue else None
    )
    explicit_stop_count = sum(r["expected_stop"] is True for r in paired)
    explicit_stop_misrouted_to_continue = sum(
        r["expected_stop"] is True for r in high_continue
    )
    incumbent_accuracy = _accuracy(paired, lambda r: r["incumbent_stop"])
    confident_accuracy = _accuracy(
        confident,
        lambda r: float(r["p_stop"]) >= 0.90,
    )
    agreement = (
        sum(
            (float(r["p_stop"]) >= 0.5) == r["incumbent_stop"]
            for r in paired
        ) / len(paired)
        if paired else None
    )
    coverage = len(confident) / len(paired) if paired else None

    inc_lat = [
        float(r["incumbent_latency_ms"])
        for r in paired if isinstance(r.get("incumbent_latency_ms"), (int, float))
    ]
    z0_lat = [
        float(r["z0_latency_ms"])
        for r in paired if isinstance(r.get("z0_latency_ms"), (int, float))
    ]
    applied = [r.get("id") for r in rows if r.get("applied") is True]
    missing_receipts = [r.get("id") for r in rows if not r.get("dispatch_receipt_id")]

    gates = {
        "shadow_never_applied": not applied,
        "receipt_complete": not missing_receipts,
        "minimum_live_sample": len(paired) >= 1000,
        "minimum_explicit_stop_sample": explicit_stop_count >= 200,
        "confident_coverage_at_least_50pct": coverage is not None and coverage >= 0.50,
        "high_stop_precision_at_least_99_5pct": (
            high_stop_precision is not None and high_stop_precision >= 0.995
        ),
        "zero_explicit_stops_in_high_continue_band": explicit_stop_misrouted_to_continue == 0,
        "confident_accuracy_at_least_99pct": (
            confident_accuracy is not None and confident_accuracy >= 0.99
        ),
        "z0_p95_not_slower_than_incumbent": (
            _percentile(z0_lat, 0.95) is not None
            and _percentile(inc_lat, 0.95) is not None
            and _percentile(z0_lat, 0.95) <= _percentile(inc_lat, 0.95)
        ),
    }

    return {
        "schema": "z0eval.agentweb_stop_request_summary.v1",
        "n_rows": len(rows),
        "n_paired": len(paired),
        "explicit_stop_count": explicit_stop_count,
        "incumbent_accuracy": incumbent_accuracy,
        "incumbent_z0_midpoint_agreement": agreement,
        "high_stop_n": len(high_stop),
        "high_continue_n": len(high_continue),
        "ambiguous_n": len(ambiguous),
        "confident_coverage": coverage,
        "high_stop_precision": high_stop_precision,
        "high_continue_stop_leakage": low_band_stop_leakage,
        "explicit_stop_misrouted_to_continue": explicit_stop_misrouted_to_continue,
        "confident_accuracy": confident_accuracy,
        "incumbent_latency_ms": {
            "p50": median(inc_lat) if inc_lat else None,
            "p95": _percentile(inc_lat, 0.95),
        },
        "z0_latency_ms": {
            "p50": median(z0_lat) if z0_lat else None,
            "p95": _percentile(z0_lat, 0.95),
        },
        "applied_violations": applied,
        "missing_receipts": missing_receipts,
        "gates": gates,
        "eligible_for_review": all(gates.values()),
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
