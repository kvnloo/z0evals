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
    assert len(rows) == 62, len(rows)
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
        if row["endpoint"] in {"/v1/experimental/choice", "/v1/experimental/noul"}:
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
        "stop-shadow-gemini-authoritative",
        "stop-remote-opt-in",
        "stop-noul-replay",
        "stop-noul-mutation-conflict",
        "stop-user-control-live-sample-gate",
        "context-boundary-opt-in",
        "context-source-pseudonymization",
        "context-final-byte-budget",
        "context-source-diversity",
        "context-lexical-focus",
        "context-incomplete-scan-gap",
        "context-zero-persistence-model",
        "context-agentweb-result-unchanged",
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

    stop_rows = [
        json.loads(line)
        for line in (STUDY / "stop-request-fixtures.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert len(stop_rows) == 40
    assert sum(row["expected_stop"] is True for row in stop_rows) == 20
    assert sum(row["expected_stop"] is False for row in stop_rows) == 20
    assert all(row["difficulty"] in {"clear", "edge"} for row in stop_rows)

    from score_agentweb_stop_request import score as score_stop
    synthetic_stop = []
    for index, row in enumerate(stop_rows):
        synthetic_stop.append({
            "id": row["id"],
            "expected_stop": row["expected_stop"],
            "incumbent_stop": row["expected_stop"],
            "p_stop": 0.99 if row["expected_stop"] else 0.01,
            "incumbent_latency_ms": 100 + index,
            "z0_latency_ms": 50 + index,
            "applied": False,
            "dispatch_receipt_id": "fixture-" + row["id"],
        })
    stop_summary = score_stop(synthetic_stop)
    assert stop_summary["n_paired"] == 40
    assert stop_summary["explicit_stop_misrouted_to_continue"] == 0
    assert stop_summary["high_stop_precision"] == 1.0
    assert stop_summary["gates"]["minimum_live_sample"] is False
    assert stop_summary["gates"]["minimum_explicit_stop_sample"] is False
    assert stop_summary["eligible_for_review"] is False

    context_rows = [
        json.loads(line)
        for line in (STUDY / "context-packet-fixtures.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert len(context_rows) == 18
    assert any(row["has_more"] is True for row in context_rows if "has_more" in row)
    assert any(row["scan_incomplete"] is True for row in context_rows if "scan_incomplete" in row)
    assert any(len(row["results"]) >= 10 for row in context_rows)
    assert any(len(row["required_terms"]) >= 3 for row in context_rows)

    from score_agentweb_context_packet import score as score_context
    synthetic_context = []
    for row in context_rows:
        synthetic_context.append({
            "sample_source": "fixture",
            "id": row["id"],
            "ok": True,
            "applied": False,
            "expect_gap": row["expect_gap"],
            "expect_compress": row["expect_compress"],
            "required_terms_preserved": True,
            "source_label_leak": False,
            "input_source_count": len(row["results"]),
            "retained_source_count": min(3, len(row["results"])) if row["results"] else 0,
            "source_diversity_target": min(3, len(row["results"])),
            "source_diversity_degraded_for_budget": False,
            "unresolved_gap_count": 1 if row["expect_gap"] else 0,
            "input_content_bytes": 10000 if row["expect_compress"] else 100,
            "packet_bytes": 5000 if row["expect_compress"] else 900,
            "max_packet_bytes": row["max_packet_bytes"],
            "compression_ratio": 0.5 if row["expect_compress"] else 9.0,
            "truncated_excerpts": 1 if row["expect_compress"] else 0,
            "network_model_calls": 0,
            "private_text_persisted": False,
        })
    context_summary = score_context(synthetic_context)
    assert context_summary["required_term_failures"] == []
    assert context_summary["privacy_leaks"] == []
    assert context_summary["gates"]["minimum_live_sample"] is False
    assert context_summary["eligible_for_assist_review"] is False

    reliability_rows = [
        json.loads(line)
        for line in (STUDY / "reliability-observation-fixtures.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert len(reliability_rows) == 7
    assert {row["outcome"] for row in reliability_rows} == {
        "success", "error", "timeout", "blocked", "skipped",
        "pending_confirmation", "user_refused",
    }

    from score_agentweb_reliability import score as score_reliability
    synthetic_results = []
    synthetic_receipts = []
    for index, row in enumerate(reliability_rows):
        trace = "agentweb-observe-" + format(index + 1, "064x")
        expected = {
            key.removeprefix("expected_"): value
            for key, value in row.items()
            if key.startswith("expected_")
        }
        synthetic_results.append({
            "id": row["id"],
            "trace_id": trace,
            "first_exported": True,
            "second_exported": True,
            "second_replayed": True,
            "projection_privacy_ok": True,
            "expected": expected,
        })
        outcome = {"source": "agentweb_reliability_event", **expected}
        synthetic_receipts.append({
            "schema": "z0int.decision_receipt.v1",
            "trace_id": trace,
            "capability_id": "agentweb.tool." + row["tool"],
            "provider": "agentweb",
            "route": "shadow",
            "execution": "log_only",
            "action_taken": row["outcome"],
            "latency_ms": row["latency_ms"],
            "measurement_state": "partial",
            "state_reason": "observational_agentweb_tool_outcome_not_quality_verification",
            "outcome": outcome,
            "extra": {
                "observational": True,
                "tool": row["tool"],
                "reliability_outcome": row["outcome"],
                "status": "observed",
                "quality_authoritative": False,
            },
        })
    reliability_summary = score_reliability(synthetic_results, synthetic_receipts)
    assert reliability_summary["passed"] is True

    ladder = json.loads((STUDY / "promotion-ladder.json").read_text())
    assert ladder["global"] == {
        "active_routing_enabled": False,
        "upstream_promotion_allowed": False,
        "aggregate_override_allowed": False,
    }
    assert ladder["evidence_classes"]["contract"]["can_inform_quality"] is False
    assert ladder["evidence_classes"]["deterministic_e2e"]["can_inform_quality"] is False
    assert ladder["evidence_classes"]["model_backed_paired"]["can_inform_quality"] is True
    assert ladder["capabilities"]["context_packet_v1"]["assist_enabled"] is False
    assert ladder["capabilities"]["reliability_observation_v1"]["quality_authoritative"] is False
    assert ladder["capabilities"]["report_type_v1"]["required_live_pairs"] == 1000
    assert ladder["capabilities"]["stop_request_v1"]["required_live_pairs"] == 1000

    frozen_context = json.loads(
        (STUDY / "results" / "context-e2e-20260930.json").read_text()
    )
    frozen_reliability = json.loads(
        (STUDY / "results" / "reliability-e2e-20260930.json").read_text()
    )
    expected_heads = {
        "agentweb": "361e962bf652e3475f49bb8e5e21c68793c57669",
        "z0intelligence": "7aa6be0ab0df25b1c7cb4c85709ca4cb01f392ce",
        "z0evals": "97d54f85fa85e604c4563510e41eb3a0bff05828",
    }
    assert frozen_context["source_heads"] == expected_heads
    assert frozen_reliability["source_heads"] == expected_heads
    assert frozen_context["summary"]["eligible_for_assist_review"] is False
    assert frozen_context["summary"]["gates"]["packet_budget_respected"] is True
    assert frozen_context["summary"]["gates"]["fixture_required_terms_preserved"] is True
    assert frozen_reliability["summary"]["passed"] is True
    assert frozen_reliability["summary"]["gates"]["never_mints_quality_gold"] is True

    schema = json.loads((STUDY / "receipt.schema.json").read_text())
    required = set(schema["required"])
    assert {"agentweb_sha", "z0intelligence_sha", "scenario_id", "passed", "evidence"} <= required
    assert schema["properties"]["agentweb_sha"]["pattern"] == "^[0-9a-f]{40}$"
    assert schema["properties"]["z0intelligence_sha"]["pattern"] == "^[0-9a-f]{40}$"
    print("ok: agentweb-emma-z0-v0 contract (62 scenarios)")


if __name__ == "__main__":
    main()
