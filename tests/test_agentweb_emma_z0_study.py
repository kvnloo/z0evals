import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "agentweb-emma-z0-v0"


def scenarios():
    return [
        json.loads(line)
        for line in (STUDY / "scenarios.jsonl").read_text().splitlines()
        if line.strip()
    ]


def test_agentweb_emma_z0_scenario_matrix_is_unique_and_broad():
    rows = scenarios()
    ids = [row["id"] for row in rows]
    assert len(rows) == 40
    assert len(ids) == len(set(ids))
    assert {row["mode"] for row in rows} == {"off", "shadow", "active"}
    assert {
        "mode",
        "routing",
        "identity",
        "failure",
        "privacy",
        "policy",
        "receipt",
        "quality",
        "agentweb-guard",
        "context",
        "performance",
    } <= {row["family"] for row in rows}


def test_shadow_scenarios_never_expect_physical_calls():
    for row in scenarios():
        if row["endpoint"] == "/v1/plan":
            assert row["mode"] == "shadow"
            assert row["expected_max_physical_calls"] == 0


def test_hard_safety_scenarios_are_present():
    ids = {row["id"] for row in scenarios()}
    assert {
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
    } <= ids


def test_receipt_schema_requires_exact_source_revisions():
    schema = json.loads((STUDY / "receipt.schema.json").read_text())
    required = set(schema["required"])
    assert {"agentweb_sha", "z0intelligence_sha", "scenario_id", "passed", "evidence"} <= required
    assert schema["properties"]["agentweb_sha"]["pattern"] == "^[0-9a-f]{40}$"
    assert schema["properties"]["z0intelligence_sha"]["pattern"] == "^[0-9a-f]{40}$"
