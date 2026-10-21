#!/usr/bin/env python3
"""Offline synthetic HCL receipt conformance; never certifies human benefit."""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_FIELDS = {
    "schema_version", "data_kind", "claim", "source_revision",
    "evaluator_revision", "registered_at", "as_of", "rows",
}
ROW_FIELDS = {
    "id", "group", "split", "arm", "assignment_probability", "exposure_at",
    "outcome_due", "choice", "status", "measurement", "assistance",
    "value", "observed_at",
}
ENUMS = {
    "split": {"search", "evaluation"},
    "arm": {"control", "candidate"},
    "choice": {"YES", "NO", "SKIP", "UNKNOWN"},
    "status": {"OBSERVED", "MISSING", "SKIPPED", "NOT_DUE"},
    "measurement": {"self_report", "objective_task", "physiological_proxy", "simulation"},
    "assistance": {"none", "assisted", "unknown"},
}


class Invalid(ValueError):
    """A stable error code, not an echo of potentially sensitive input."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise Invalid(code)


def exact_fields(value: Any, fields: set[str], code: str) -> None:
    require(isinstance(value, dict) and set(value) == fields, code)


def finite(value: Any) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def instant(value: Any) -> datetime:
    require(isinstance(value, str) and len(value) <= 48, "TIMESTAMP")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(parsed.tzinfo is not None, "TIMESTAMP_ZONE")
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError) as exc:
        if isinstance(exc, Invalid):
            raise
        raise Invalid("TIMESTAMP") from exc


def revision(value: Any) -> None:
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None,
            "REVISION_SHAPE")
    require(value != "0" * 40, "REVISION_PLACEHOLDER")


def validate(document: Any) -> dict[str, Any]:
    """Check declared synthetic semantics. No network, source verification or promotion."""
    exact_fields(document, ROOT_FIELDS, "DOCUMENT_FIELDS")
    require(document["schema_version"] == "hcl-conformance-v0", "SCHEMA_VERSION")
    require(document["data_kind"] == "synthetic", "SYNTHETIC_ONLY")
    require(document["claim"] == "contract_only", "CLAIM_BOUNDARY")
    revision(document["source_revision"])
    revision(document["evaluator_revision"])
    locked, as_of = instant(document["registered_at"]), instant(document["as_of"])
    require(locked <= as_of, "ANALYSIS_BEFORE_LOCK")
    rows = document["rows"]
    require(isinstance(rows, list) and 0 < len(rows) <= 10000, "ROW_COUNT")
    identities: set[str] = set()
    group_splits: dict[str, str] = {}
    counts: Counter[tuple[str, str]] = Counter()
    choices: Counter[str] = Counter()
    measurements: Counter[str] = Counter()
    for row in rows:
        exact_fields(row, ROW_FIELDS, "ROW_FIELDS")
        for key in ("id", "group"):
            require(isinstance(row[key], str) and
                    re.fullmatch(r"[A-Za-z0-9_.-]{1,96}", row[key]) is not None, "IDENTITY")
        require(row["id"] not in identities, "DUPLICATE_ID")
        identities.add(row["id"])
        for key, options in ENUMS.items():
            require(isinstance(row[key], str) and row[key] in options, "ENUM_" + key.upper())
        group = row["group"]
        require(group not in group_splits or group_splits[group] == row["split"], "GROUP_LEAKAGE")
        group_splits[group] = row["split"]
        probability = row["assignment_probability"]
        require(finite(probability) and 0 < probability <= 1, "ASSIGNMENT_PROBABILITY")
        exposure, due = instant(row["exposure_at"]), instant(row["outcome_due"])
        require(locked < exposure <= due, "PROSPECTIVE_ORDER")
        require(exposure <= as_of, "FUTURE_EXPOSURE")
        status = row["status"]
        if status == "OBSERVED":
            require(finite(row["value"]), "OBSERVED_VALUE")
            observed = instant(row["observed_at"])
            require(due <= observed <= as_of, "OBSERVATION_WINDOW")
        else:
            require(row["value"] is None and row["observed_at"] is None, "ABSENT_NOT_ZERO")
            if status == "NOT_DUE":
                require(due > as_of, "ALREADY_DUE")
            elif status == "MISSING":
                require(due <= as_of, "NOT_YET_MISSING")
        counts[(row["arm"], status)] += 1
        choices[row["choice"]] += 1
        measurements[row["measurement"]] += 1
    # Choice, observation and measurement classes stay separate; no effect/score is computed.
    return {
        "status": "CONTRACT_ONLY", "data_kind": "synthetic", "rows": len(rows),
        "human_benefit": "NOT_EVALUATED", "can_promote": False,
        "by_arm": {arm: {state: counts[(arm, state)] for state in sorted(ENUMS["status"])}
                   for arm in sorted(ENUMS["arm"])},
        "choices": {key: choices[key] for key in sorted(ENUMS["choice"])},
        "measurement_classes": {key: measurements[key] for key in sorted(ENUMS["measurement"])},
        "limitations": ["declared timestamps are not durable preregistration proof",
                        "revision shape is not remote source verification",
                        "synthetic declaration is not a privacy or authenticity check",
                        "no effect estimate, clinical conclusion or runtime authority"],
    }


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    try:
        with args.fixture.open("rb") as handle:
            payload = handle.read(1_000_001)
        require(len(payload) <= 1_000_000, "INPUT_TOO_LARGE")
        document = json.loads(payload.decode("utf-8"), object_pairs_hook=unique_object)
        result = validate(document)
    except Invalid as exc:
        print(json.dumps({"status": "INVALID", "code": str(exc)}, sort_keys=True))
        return 2
    except (OSError, UnicodeError, ValueError, OverflowError, RecursionError):
        print(json.dumps({"status": "INVALID", "code": "INPUT_ERROR"}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
