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
    assert len(rows) == 32, len(rows)
    assert len(ids) == len(set(ids)), "duplicate scenario id"
    assert {row["mode"] for row in rows} == {"off", "shadow", "active"}

    families = {row["family"] for row in rows}
    assert {
        "mode", "routing", "identity", "failure", "privacy", "policy",
        "receipt", "quality", "agentweb-guard", "context", "performance",
    } <= families

    for row in rows:
        if row["mode"] == "shadow":
            assert row["endpoint"] == "/v1/plan", row["id"]
            assert row["expected_max_physical_calls"] == 0, row["id"]

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
    }
    assert hard <= set(ids), sorted(hard - set(ids))

    schema = json.loads((STUDY / "receipt.schema.json").read_text())
    required = set(schema["required"])
    assert {"agentweb_sha", "z0intelligence_sha", "scenario_id", "passed", "evidence"} <= required
    assert schema["properties"]["agentweb_sha"]["pattern"] == "^[0-9a-f]{40}$"
    assert schema["properties"]["z0intelligence_sha"]["pattern"] == "^[0-9a-f]{40}$"
    print("ok: agentweb-emma-z0-v0 contract (32 scenarios)")


if __name__ == "__main__":
    main()
