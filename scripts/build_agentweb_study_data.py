#!/usr/bin/env python3
"""Build the AgentWeb/Emma/z0 study status document for the static site."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "agentweb-emma-z0-v0"
OUT = ROOT / "web" / "data" / "agentweb-study.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    scenarios = [
        json.loads(line)
        for line in (STUDY / "scenarios.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    context = read_json(STUDY / "results" / "context-e2e-20260930.json")
    reliability = read_json(STUDY / "results" / "reliability-e2e-20260930.json")
    blocker = read_json(STUDY / "results" / "model-smoke-blocked-20260930.json")
    ladder = read_json(STUDY / "promotion-ladder.json")

    families = Counter(row["family"] for row in scenarios)
    frozen_heads = context["source_heads"]
    assert reliability["source_heads"] == frozen_heads

    doc = {
        "schema": "z0evals.site.agentweb-study.v1",
        "title": "agentweb + emma + z0",
        "subtitle": "first-class integration, still shadow-first",
        "date": "september 30, 2026",
        "scenarioCount": len(scenarios),
        "families": dict(sorted(families.items())),
        "frozenHeads": frozen_heads,
        "context": {
            "stage": ladder["capabilities"]["context_packet_v1"]["current_stage"],
            "assistEnabled": ladder["capabilities"]["context_packet_v1"]["assist_enabled"],
            "rows": context["summary"]["n_rows"],
            "requiredTermFailures": len(context["summary"]["required_term_failures"]),
            "privacyLeaks": len(context["summary"]["privacy_leaks"]),
            "budgetViolations": len(context["summary"]["budget_violations"]),
            "modelCallViolations": len(context["summary"]["model_call_violations"]),
            "largeContextRatios": context["summary"]["fixture_large_context_ratios"],
            "eligibleForAssistReview": context["summary"]["eligible_for_assist_review"],
            "workflowRunId": context["workflow_run_id"],
            "artifactSha256": context["artifact_sha256"],
        },
        "reliability": {
            "stage": ladder["capabilities"]["reliability_observation_v1"]["current_stage"],
            "qualityAuthoritative": ladder["capabilities"]["reliability_observation_v1"]["quality_authoritative"],
            "rows": reliability["summary"]["n_results"],
            "durableRows": reliability["summary"]["n_observed_receipts"],
            "privacyLeaks": len(reliability["summary"]["privacy_leaks"]),
            "qualityViolations": len(reliability["summary"]["quality_violations"]),
            "passed": reliability["summary"]["passed"],
            "workflowRunId": reliability["workflow_run_id"],
            "artifactSha256": reliability["artifact_sha256"],
        },
        "modelCampaign": {
            "reportStage": ladder["capabilities"]["report_type_v1"]["current_stage"],
            "stopStage": ladder["capabilities"]["stop_request_v1"]["current_stage"],
            "credentialsAvailable": blocker["credentials_available"],
            "missing": blocker["missing"],
            "executed": blocker["executed"],
            "workflowRunId": blocker["workflow_run_id"],
            "artifactSha256": blocker["artifact_sha256"],
            "requiredReportLivePairs": ladder["capabilities"]["report_type_v1"]["required_live_pairs"],
            "requiredStopLivePairs": ladder["capabilities"]["stop_request_v1"]["required_live_pairs"],
            "requiredExplicitStops": ladder["capabilities"]["stop_request_v1"]["required_explicit_stops"],
        },
        "global": ladder["global"],
        "evidenceClasses": ladder["evidence_classes"],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
