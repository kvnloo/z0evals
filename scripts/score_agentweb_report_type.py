#!/usr/bin/env python3
"""Score paired incumbent vs z0 report_type_v1 experiment receipts."""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

LABELS = ("creative", "performance", "research")


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return xs[lo]
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def _accuracy(rows: list[dict], key: str) -> float | None:
    usable = [r for r in rows if r.get(key) in LABELS and r.get("expected") in LABELS]
    if not usable:
        return None
    return sum(r[key] == r["expected"] for r in usable) / len(usable)


def _per_class(rows: list[dict], key: str) -> dict[str, float | None]:
    out = {}
    for label in LABELS:
        subset = [r for r in rows if r.get("expected") == label]
        out[label] = _accuracy(subset, key)
    return out


def _margin(row: dict) -> float | None:
    probs = row.get("z0_probabilities")
    if not isinstance(probs, dict):
        return None
    vals = sorted(
        [float(v) for v in probs.values() if isinstance(v, (int, float)) and math.isfinite(float(v))],
        reverse=True,
    )
    return vals[0] - vals[1] if len(vals) >= 2 else None


def score(rows: list[dict]) -> dict:
    paired = [
        r for r in rows
        if r.get("expected") in LABELS
        and r.get("incumbent_label") in LABELS
        and r.get("z0_label") in LABELS
    ]
    high_conf = [
        r for r in paired
        if isinstance(r.get("z0_confidence"), (int, float))
        and float(r["z0_confidence"]) >= 0.90
        and (_margin(r) is not None and _margin(r) >= 0.25)
    ]
    incumbent_lat = [float(r["incumbent_latency_ms"]) for r in paired if isinstance(r.get("incumbent_latency_ms"), (int, float))]
    z0_lat = [float(r["z0_latency_ms"]) for r in paired if isinstance(r.get("z0_latency_ms"), (int, float))]
    applied_violations = [r.get("id") for r in rows if r.get("applied") is True]
    missing_receipts = [r.get("id") for r in rows if not r.get("dispatch_receipt_id")]

    incumbent_accuracy = _accuracy(paired, "incumbent_label")
    z0_accuracy = _accuracy(paired, "z0_label")
    covered_accuracy = _accuracy(high_conf, "z0_label")
    agreement = (
        sum(r["incumbent_label"] == r["z0_label"] for r in paired) / len(paired)
        if paired else None
    )
    coverage = len(high_conf) / len(paired) if paired else None

    per_incumbent = _per_class(paired, "incumbent_label")
    per_z0 = _per_class(paired, "z0_label")
    class_regression = any(
        per_incumbent[label] is not None
        and per_z0[label] is not None
        and per_z0[label] < per_incumbent[label] - 0.01
        for label in LABELS
    )

    gates = {
        "shadow_never_applied": not applied_violations,
        "receipt_complete": not missing_receipts,
        "minimum_live_sample": len(paired) >= 1000,
        "high_conf_coverage_at_least_50pct": coverage is not None and coverage >= 0.50,
        "high_conf_accuracy_at_least_98pct": covered_accuracy is not None and covered_accuracy >= 0.98,
        "no_per_class_regression_gt_1pp": not class_regression,
        "z0_p95_not_slower_than_incumbent": (
            _percentile(z0_lat, 0.95) is not None
            and _percentile(incumbent_lat, 0.95) is not None
            and _percentile(z0_lat, 0.95) <= _percentile(incumbent_lat, 0.95)
        ),
    }
    return {
        "schema": "z0eval.agentweb_report_type_summary.v1",
        "n_rows": len(rows),
        "n_paired": len(paired),
        "label_counts": dict(Counter(r.get("expected") for r in paired)),
        "incumbent_accuracy": incumbent_accuracy,
        "z0_accuracy": z0_accuracy,
        "agreement": agreement,
        "high_conf_n": len(high_conf),
        "high_conf_coverage": coverage,
        "high_conf_accuracy": covered_accuracy,
        "per_class_incumbent_accuracy": per_incumbent,
        "per_class_z0_accuracy": per_z0,
        "incumbent_latency_ms": {
            "p50": median(incumbent_lat) if incumbent_lat else None,
            "p95": _percentile(incumbent_lat, 0.95),
        },
        "z0_latency_ms": {
            "p50": median(z0_lat) if z0_lat else None,
            "p95": _percentile(z0_lat, 0.95),
        },
        "applied_violations": applied_violations,
        "missing_receipts": missing_receipts,
        "gates": gates,
        "eligible_for_review": all(gates.values()),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("results", help="paired result JSONL")
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
