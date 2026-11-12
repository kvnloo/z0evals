#!/usr/bin/env python3
"""Freeze allowlisted historical measurements and check their arithmetic offline."""
import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path

RUNS = ["033902", "040146", "041047"]
LATENCY_KEYS = "mode rep ttft_s total_s correct profile at".split()
REQUEST_KEYS = "id lane model ok completion_tokens visible_tokens prompt_tokens s attempt t".split()
PROBE_KEYS = "provider model kind rep at status ttft_s total_s completion_tokens decode_tok_s prompt_tokens".split()
SUMMARY_KEYS = "units ok failed not_run wall_s completion_tokens aggregate_tok_s".split()


def load(path):
    return json.loads(Path(path).read_text())


def sha(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def project(row, keys):
    return {k: row[k] for k in keys if k in row}


def freeze(source, output):
    source = Path(source)
    sources = []

    def add(name, keys, summary=False):
        raw = (source / name).read_bytes()
        value = project(json.loads(raw), keys) if summary else [
            project(json.loads(line), keys) for line in raw.splitlines() if line.strip()
        ]
        sources.append(dict(name=name, original_sha256=sha(raw),
                            projection_sha256=sha(canonical(value)), data=value))

    add("lat-final.jsonl", LATENCY_KEYS)
    add("speed.jsonl", PROBE_KEYS)
    for run in RUNS:
        prefix = f"swarm-bench/bench-20261105T{run}"
        add(prefix + ".jsonl", REQUEST_KEYS)
        add(prefix + ".summary.json", SUMMARY_KEYS, summary=True)
    methods = []
    for name in ["hermes_latency.py", "probe_all.py"]:
        raw = (source / name).read_bytes()
        methods.append(dict(name=name, original_sha256=sha(raw)))
    data = dict(status="private-draft", source_root=str(source.resolve()),
                token_count_provenance="unverified", sources=sources, methods=methods)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(data, indent=2) + "\n")


def latency(rows):
    measured = [r for r in rows if r["rep"] >= 0]
    times = [r["ttft_s"] for r in measured if r["ttft_s"] is not None]
    if any(not math.isfinite(t) or t < 0 for t in times):
        raise ValueError("invalid latency")
    return dict(n=len(measured), timed=len(times), correct=sum(r["correct"] for r in measured),
                median_s=statistics.median(times) if times else None,
                max_s=max(times) if times else None)


def parallel(rows, summary):
    completed = [r for r in rows if r["ok"]]
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("duplicate final unit ids")
    tokens = sum(r["completion_tokens"] for r in completed)
    if (len(completed) != summary["ok"] or len(rows) - len(completed) != summary["failed"]
            or tokens != summary["completion_tokens"]
            or summary["units"] != len(rows) + summary["not_run"]):
        raise ValueError("raw rows disagree with summary")
    if summary["wall_s"] <= 0:
        raise ValueError("invalid wall time")
    rate = tokens / summary["wall_s"]
    if abs(rate - summary["aggregate_tok_s"]) > 0.15:
        raise ValueError("recorded rate disagrees with token total and wall time")
    return dict(ok=len(completed), failed=summary["failed"], not_run=summary["not_run"],
                wall_s=summary["wall_s"], recorded_completion_tokens=tokens,
                recorded_tok_s=round(rate, 1), token_count_provenance="unverified")


def verify_data(data):
    sources = {}
    for source in data["sources"]:
        if sha(canonical(source["data"])) != source["projection_sha256"]:
            raise ValueError(f"projection hash mismatch: {source['name']}")
        if source["name"] in sources:
            raise ValueError("duplicate source")
        sources[source["name"]] = source["data"]
    output = dict(latency=latency(sources["lat-final.jsonl"]), parallel={})
    for run in RUNS:
        prefix = f"swarm-bench/bench-20261105T{run}"
        output["parallel"][run] = parallel(sources[prefix + ".jsonl"], sources[prefix + ".summary.json"])
    probes = sources["speed.jsonl"]
    statuses = {}
    for row in probes:
        key = str(row["status"])
        statuses[key] = statuses.get(key, 0) + 1
    output["probe"] = dict(rows=len(probes), statuses=statuses,
                           exact_token_rates_publishable=False,
                           reason="producer permits characters // 4 fallback; rows do not identify its use")
    return output


def verify(path):
    return verify_data(load(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("freeze")
    capture.add_argument("source")
    capture.add_argument("output")
    check = commands.add_parser("verify")
    check.add_argument("path")
    args = parser.parse_args()
    if args.command == "freeze":
        freeze(args.source, args.output)
        print(f"wrote allowlisted projection: {args.output}")
    else:
        print(json.dumps(verify(args.path), indent=2))


if __name__ == "__main__":
    main()
