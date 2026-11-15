#!/usr/bin/env python3
"""Recompute recorded measurements, without inference calls or estimated token counts."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"


def read_rows(name):
    return [json.loads(line) for line in (DATA / name).read_text().splitlines()]


def analyze():
    warm = read_rows("warm.jsonl")
    measured = [r for r in warm if r["rep"] >= 0]
    wire = read_rows("wire.jsonl")
    runs = [r for r in read_rows("runs.jsonl") if r["rep"] >= 0 and r["kind"] == "decode"]
    lanes = {"local": "local", "nim": "nim", "kilo": "kilo-free", "cohere": "cohere", "groq": "groq"}
    groups = defaultdict(list)
    for run in runs:
        for row in wire:
            if (row["lane"] == lanes[run["model"].split("-")[0]]
                    and row["path"].endswith("/chat/completions")
                    and row.get("total_s") is not None
                    and run["at"] <= row["at"] - row["total_s"] <= run["at"] + run["total_s"]
                    and row["status"] == 200 and row.get("stream") is True
                    and row["usage"].get("completion_tokens", 0) > 250
                    and row.get("decode_tok_s") is not None):
                groups[(run["model"], run["arm"])].append(row["decode_tok_s"])
    parallel = read_rows("parallel.jsonl")
    receipt = json.loads((DATA / "parallel-run.json").read_text())
    # t is elapsed completion time and s is call duration, both rounded by the source.
    events = sorted((point, delta) for row in parallel for point, delta in [(row["t"] - row["s"], 1), (row["t"], -1)])
    active = peak = 0
    for _, delta in events:
        active += delta
        peak = max(peak, active)
    return {
        "classification": "source-reported measurements; offline analysis reproduced",
        "warm": {
            "count": len(measured),
            "correct": sum(r["correct"] for r in measured),
            "warmup_excluded": len(warm) - len(measured),
            "median_ttft_s": round(median(r["ttft_s"] for r in measured), 4),
        },
        "wire_decode": [
            {"model": model, "arm": arm, "count": len(values), "median_tok_s": round(median(values), 1)}
            for (model, arm), values in sorted(groups.items())
        ],
        "wire_status_counts": dict(sorted(Counter(str(r["status"]) for r in wire).items())),
        "parallel": {
            "completed": sum(r["ok"] for r in parallel),
            "failed_units": receipt["failed"],
            "not_run": receipt["not_run"],
            "planned_units": receipt["units"],
            "wall_s": receipt["wall_s"],
            "completed_units_per_s": round(sum(r["ok"] for r in parallel) / receipt["wall_s"], 4),
            "max_interval_overlap": peak,
            "lanes": dict(sorted(Counter(r["lane"] for r in parallel).items())),
            "rate_limit_attempts": sum(r["429"] for r in receipt["lanes"].values()),
            "independently_verified_quality": False,
            "aggregate_token_rate": None,
            "token_rate_exclusion": "original runner and token-count method not independently established",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare with the committed summary")
    args = parser.parse_args()
    result = analyze()
    if args.check:
        assert result == json.loads((HERE / "summary.json").read_text()), "summary differs from measurements"
        print("ok: recorded measurements exactly reproduce summary.json")
    else:
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
