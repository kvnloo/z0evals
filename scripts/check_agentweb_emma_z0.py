#!/usr/bin/env python3
"""Contract checks for the downstream AgentWeb + Emma + z0 v0 study."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "agentweb-emma-z0-v0"


def load_scenarios() -> list[dict]:
    return [
        json.loads(line)
        for line in (STUDY / "scenarios.jsonl").read_text().splitlines()
        if line.strip()
    ]


def main() -> None:
    rows = load_scenarios()
    ids = [row["id"] for row in rows]
    assert len(rows) == 40, len(rows)
    assert len(ids) == len(set(ids)), "duplicate scenario id"
    assert {row["mode"] for row in rows} == {"off", "shadow", "active"}

    families = {row["family"] for row in rows}
    assert {
        "mode", "routing", "identity", "failure", "privacy", "policy",
        "receipt", "quality", "agentweb-guard", "context", "performance",
    } <= families

    for row in rows:
        if row["endpoint"] == "/v1/plan":
            assert row["mode"] == "shadow", row["id"]
            assert row["expected_max_physical_calls"] == 0, row["id"]
        if row["endpoint"] == "/v1/experimental/choice":
            assert row["mode"] == "shadow", row["id"]
            assert row["expected_max_physical_calls"] in (0, 1), row["id"]

    hard = {
        "mode-off-no-call",
        "active-timeout-unknown",
        "trace-conflict-rejected",
        "restart-uncertain-no-reexecute",
        "user-id-redaction",
        "session-id-pseudonym",
        "remote-default-deny",
        "free-only-paid-block",
        "reliability-success-not-gold",
        "evaluation-workspace-guard",
        "scheduled-publish-consent",
        "report-type-z0-shadow-incumbent-authority",
        "report-type-z0-remote-opt-in",
        "report-type-z0-replay",
        "report-type-z0-mutation-conflict",
        "report-type-receipt-non-authoritative",
    }
    assert hard <= set(ids), sorted(hard - set(ids))

    report_rows = [
        json.loads(line)
        for line in (STUDY / "report-type-fixtures.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert len(report_rows) == 30
    counts = {}
    for row in report_rows:
        counts[row["label"]] = counts.get(row["label"], 0) + 1
        assert row["difficulty"] in {"clear", "edge"}
        assert row["filename"] and row["excerpt"]
    assert counts == {"creative": 10, "performance": 10, "research": 10}

    from score_agentweb_report_type import score
    synthetic = []
    for index, row in enumerate(report_rows):
        synthetic.append({
            "id": row["id"],
            "expected": row["label"],
            "incumbent_label": row["label"],
            "z0_label": row["label"],
            "z0_confidence": 0.99,
            "z0_probabilities": {
                label: (0.98 if label == row["label"] else 0.01)
                for label in ("creative", "performance", "research")
            },
            "incumbent_latency_ms": 100 + index,
            "z0_latency_ms": 50 + index,
            "applied": False,
            "dispatch_receipt_id": "fixture-" + row["id"],
        })
    summary = score(synthetic)
    assert summary["n_paired"] == 30
    assert summary["high_conf_accuracy"] == 1.0
    assert summary["gates"]["minimum_live_sample"] is False
    assert summary["eligible_for_review"] is False

    schema = json.loads((STUDY / "receipt.schema.json").read_text())
    required = set(schema["required"])
    assert {"agentweb_sha", "z0intelligence_sha", "scenario_id", "passed", "evidence"} <= required
    assert schema["properties"]["agentweb_sha"]["pattern"] == "^[0-9a-f]{40}$"
    assert schema["properties"]["z0intelligence_sha"]["pattern"] == "^[0-9a-f]{40}$"
    print("ok: agentweb-emma-z0-v0 contract (32 scenarios)")


if __name__ == "__main__":
    main()
