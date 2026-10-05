#!/usr/bin/env python3
"""Wrap pinned z0live evidence into a z0eval.result.v1 receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_IDENTITY = {
    "actor_id",
    "provider",
    "model",
    "model_revision",
    "runtime_backend",
    "quantization",
    "host_fingerprint",
    "hardware_class",
    "harness",
    "harness_revision",
    "adapter_revision",
}


def load_json(path: str | Path) -> dict[str, Any]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected JSON object")
    return raw


def certify(
    replay: dict[str, Any],
    identity: dict[str, Any],
    *,
    metrics: dict[str, Any] | None = None,
    speculation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    missing = sorted(REQUIRED_IDENTITY - set(identity))
    if missing:
        raise ValueError(f"identity missing required keys: {', '.join(missing)}")

    if replay.get("schema") != "z0live.replay_result.v1":
        raise ValueError("replay must be z0live.replay_result.v1")
    cases = list(replay.get("cases") or [])
    passed_n = sum(1 for case in cases if case.get("passed") is True)
    replay_passed = bool(replay.get("passed")) and passed_n == len(cases) and bool(cases)

    limitations: list[str] = []
    if not replay_passed:
        decision = "DISCARD"
        limitations.append("Frozen deterministic contract replay failed.")
    elif metrics is None:
        decision = "PARTIAL"
        limitations.append(
            "Contract replay passed, but target-host actor latency/naturalness/resource metrics were not supplied."
        )
    else:
        # Preserve measured dimensions; do not invent a universal blended threshold.
        decision = "PARTIAL"
        limitations.append(
            "Measured actor dimensions are attached, but KEEP requires an explicitly frozen baseline/challenger decision rule."
        )

    if speculation is not None:
        mutations = int(speculation.get("speculative_mutations") or 0)
        p50 = speculation.get("p50_useful_gain_ms")
        if mutations != 0:
            decision = "DISCARD"
            limitations.append("Speculative execution mutated state before final authority.")
        elif p50 is not None and float(p50) < 50.0:
            limitations.append("Speculative prewarm did not meet the pre-registered 50 ms p50 useful-gain gate.")

    return {
        "schema": "z0eval.result.v1",
        "study": "z0live-v0",
        "decision": decision,
        "identity": identity,
        "fixture": {
            "revision": replay.get("revision"),
            "sha256": replay.get("fixture_sha256"),
        },
        "contract_replay": {
            "passed": replay_passed,
            "cases_total": len(cases),
            "cases_passed": passed_n,
        },
        "metrics": metrics,
        "speculation": speculation,
        "limitations": limitations,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--replay", required=True)
    p.add_argument("--identity", required=True)
    p.add_argument("--metrics")
    p.add_argument("--speculation")
    p.add_argument("--output")
    args = p.parse_args(argv)

    result = certify(
        load_json(args.replay),
        load_json(args.identity),
        metrics=load_json(args.metrics) if args.metrics else None,
        speculation=load_json(args.speculation) if args.speculation else None,
    )
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if result["decision"] != "DISCARD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
