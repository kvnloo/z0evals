#!/usr/bin/env python3
"""Score-only protected evaluator boundary for adaptive optimizers.

Protected truth stays behind a trusted runner. Optimizers submit complete
prediction files and receive only aggregate score/verdict metadata. The audit
log stores hashes, not protected rows or prediction contents.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
STATE_SCHEMA = "z0eval.protected.state.v1"
RESULT_SCHEMA = "z0eval.result.v1"
PIN_RE = re.compile(r"^[0-9a-f]{40}$")
ENV_REF_RE = re.compile(r"^env://([A-Z_][A-Z0-9_]*)(?:/(.*))?$")


class ProtectedEvalError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_evaluator_manifest(data: dict[str, Any]) -> None:
    schema = json.loads((ROOT / "schemas" / "protected-evaluator.schema.json").read_text(encoding="utf-8"))
    problems = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    if problems:
        first = problems[0]
        raise ProtectedEvalError(f"manifest schema error at {list(first.path)}: {first.message}")

    label_id = str(data["label_generator"]["id"])
    verifier = data["verifier"]
    if verifier["id"] == label_id:
        raise ProtectedEvalError("label generator cannot also be the verifier")
    if label_id not in verifier["independent_of"]:
        raise ProtectedEvalError("verifier must explicitly declare independence from label generator")

    protected_roles = {"confirm", "ood", "future"}
    roles = {str(v["role"]) for v in data["cohorts"].values()}
    if "future" not in roles:
        raise ProtectedEvalError("a future cohort is required and must remain separate")
    for name, cohort in data["cohorts"].items():
        role = str(cohort["role"])
        if role in protected_roles and cohort["training_allowed"]:
            raise ProtectedEvalError(f"protected cohort {name!r} cannot be training_allowed")
        if role == "future" and cohort["optimizer_queryable"]:
            raise ProtectedEvalError("future cohort cannot be optimizer_queryable")


def load_manifest(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ProtectedEvalError("evaluator manifest must be a mapping")
    validate_evaluator_manifest(data)
    return data


def _state_path(state_dir: Path) -> Path:
    return state_dir / "state.json"


@contextmanager
def _locked_state(state_dir: Path):
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / "state.lock"
    with lock_path.open("a+", encoding="utf-8") as lock:
        lock_path.chmod(0o600)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _audit_path(state_dir: Path) -> Path:
    return state_dir / "queries.jsonl"


def _default_state(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": STATE_SCHEMA,
        "suite_id": manifest["id"],
        "suite_version": manifest["version"],
        "manifest_sha256": _sha256_bytes(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()),
        "cohort_revisions": None,
        "status": "active",
        "query_count": 0,
        "contamination": None,
        "superseded_by": None,
        "updated_at": _now(),
    }


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def load_state(state_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    path = _state_path(state_dir)
    if not path.exists():
        state = _default_state(manifest)
        _atomic_json(path, state)
        return state
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("suite_id") != manifest["id"] or state.get("suite_version") != manifest["version"]:
        raise ProtectedEvalError("state belongs to a different suite/version")
    if not state.get("manifest_sha256"):
        raise ProtectedEvalError("historical evaluator state is unbound; use explicit suite rotation")
    current_manifest = _sha256_bytes(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())
    if state["manifest_sha256"] != current_manifest:
        raise ProtectedEvalError("evaluator manifest changed under the same suite/version")
    return state


def _append_audit(state_dir: Path, entry: dict[str, Any]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    path = _audit_path(state_dir)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    path.chmod(0o600)


def _resolve_truth_ref(ref: str) -> Path:
    match = ENV_REF_RE.fullmatch(ref)
    if not match:
        raise ProtectedEvalError("truth_ref must use env://VAR/relative-path")
    var, relative = match.group(1), match.group(2) or ""
    root_value = os.environ.get(var)
    if not root_value:
        raise ProtectedEvalError(f"protected truth root environment variable {var} is not set")
    root = Path(root_value).resolve()
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ProtectedEvalError("protected truth relative path escapes its root")
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ProtectedEvalError("protected truth path escapes its root") from exc
    if not target.is_file():
        raise ProtectedEvalError("protected truth is unavailable to the evaluator")
    return target


def _read_jsonl_rows(path: Path, value_key: str) -> tuple[dict[str, dict[str, Any]], str]:
    result: dict[str, Any] = {}
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for line_no, raw in enumerate(fh, 1):
            digest.update(raw)
            if not raw.strip():
                continue
            row = json.loads(raw)
            item_id = str(row.get("id") or "")
            if not item_id or value_key not in row:
                raise ProtectedEvalError(f"{path.name}:{line_no} requires id and {value_key}")
            if item_id in result:
                raise ProtectedEvalError(f"duplicate item id in {path.name}")
            result[item_id] = row
    if not result:
        raise ProtectedEvalError(f"{path.name} is empty")
    return result, digest.hexdigest()


def _truth_cohorts(manifest: dict[str, Any]) -> tuple[dict[str, dict[str, dict[str, Any]]], dict[str, str]]:
    """Validate trusted work-item groups before any cohort can earn sealed credit."""
    cohorts = {}
    revisions = {}
    owners: dict[str, str] = {}
    for name, cohort in manifest["cohorts"].items():
        rows, revisions[name] = _read_jsonl_rows(_resolve_truth_ref(str(cohort["truth_ref"])), "expected")
        for row in rows.values():
            group = row.get("group")
            if not isinstance(group, str) or not group or group != group.strip():
                raise ProtectedEvalError("truth rows require normalized nonempty work-item lineage groups")
            if group in owners and owners[group] != name:
                raise ProtectedEvalError("work-item lineage overlaps across evaluator cohorts")
            owners[group] = name
        cohorts[name] = rows
    return cohorts, revisions


def _score_exact_match(truth_rows: dict[str, dict[str, Any]], predictions: dict[str, Any], metric: str) -> float:
    if metric == "group_macro_exact_match":
        groups: dict[str, list[bool]] = {}
        for item_id, row in truth_rows.items():
            groups.setdefault(row["group"], []).append(predictions[item_id] == row["expected"])
        return sum(sum(matches) / len(matches) for matches in groups.values()) / len(groups)
    if metric == "exact_match":
        return sum(predictions[item_id] == row["expected"] for item_id, row in truth_rows.items()) / len(truth_rows)
    raise ProtectedEvalError("unsupported protected scoring metric")


def score_predictions(
    manifest: dict[str, Any],
    *,
    cohort_name: str,
    predictions_path: Path,
    candidate_id: str,
    candidate_revision: str,
    state_dir: Path,
    baseline_predictions_path: Path | None = None,
    baseline_revision: str | None = None,
) -> dict[str, Any]:
    if not PIN_RE.fullmatch(candidate_revision):
        raise ProtectedEvalError("candidate_revision must be a full 40-character git SHA")
    if (baseline_predictions_path is None) != (baseline_revision is None):
        raise ProtectedEvalError("paired scoring requires baseline predictions and revision together")
    if baseline_revision is not None and not PIN_RE.fullmatch(baseline_revision):
        raise ProtectedEvalError("baseline_revision must be a full 40-character git SHA")
    cohort = (manifest.get("cohorts") or {}).get(cohort_name)
    if not cohort:
        raise ProtectedEvalError(f"unknown cohort {cohort_name!r}")
    if not cohort["optimizer_queryable"]:
        raise ProtectedEvalError(f"cohort {cohort_name!r} is not optimizer-queryable")
    if cohort["training_allowed"]:
        raise ProtectedEvalError("protected scoring cohort cannot be training_allowed")

    with _locked_state(state_dir):
        state = load_state(state_dir, manifest)
        if state["status"] != "active":
            raise ProtectedEvalError(f"suite cannot mint sealed credit while status={state['status']}")
        max_queries = int(manifest["scoring"]["max_queries"])
        if int(state["query_count"]) >= max_queries:
            raise ProtectedEvalError("protected evaluator query budget exhausted")

        cohorts, revisions = _truth_cohorts(manifest)
        if state["cohort_revisions"] is None:
            if state["query_count"]:
                raise ProtectedEvalError("queried evaluator state has unbound cohort revisions")
        elif state["cohort_revisions"] != revisions:
            raise ProtectedEvalError("protected cohort revision changed; use explicit suite rotation")
        truth_rows = cohorts[cohort_name]
        truth = {item_id: row["expected"] for item_id, row in truth_rows.items()}
        prediction_rows, predictions_sha256 = _read_jsonl_rows(predictions_path, "prediction")
        predictions = {item_id: row["prediction"] for item_id, row in prediction_rows.items()}
        if predictions.keys() != truth.keys():
            raise ProtectedEvalError("prediction IDs must exactly match the protected cohort IDs")

        metric = manifest["scoring"]["metric"]
        score = _score_exact_match(truth_rows, predictions, metric)
        verdict = "KEEP" if score >= float(manifest["scoring"]["pass_threshold"]) else "DISCARD"
        baseline = None
        if baseline_predictions_path is not None:
            baseline_rows, baseline_digest = _read_jsonl_rows(baseline_predictions_path, "prediction")
            if baseline_rows.keys() != truth.keys():
                raise ProtectedEvalError("baseline IDs must exactly match the protected cohort IDs")
            baseline_score = _score_exact_match(
                truth_rows, {item_id: row["prediction"] for item_id, row in baseline_rows.items()}, metric,
            )
            baseline = {"revision": baseline_revision, "score": baseline_score,
                        "score_delta": score - baseline_score, "predictions_sha256": baseline_digest}
            if score <= baseline_score:
                verdict = "DISCARD"
        query_index = int(state["query_count"]) + 1

        public_core = {
            "schema": RESULT_SCHEMA,
            "suite_id": manifest["id"],
            "suite_version": manifest["version"],
            "cohort": cohort_name,
            "candidate_id": candidate_id,
            "candidate_revision": candidate_revision,
            "metric": manifest["scoring"]["metric"],
            "score": score,
            "verdict": verdict,
            "query_index": query_index,
            "sealed_credit": True,
        }
        if baseline is not None:
            public_core["baseline"] = baseline
        public_core["result_sha256"] = _sha256_bytes(
            json.dumps(public_core, sort_keys=True, separators=(",", ":")).encode()
        )

        audit = {
            "at": _now(),
            "suite_id": manifest["id"],
            "suite_version": manifest["version"],
            "cohort": cohort_name,
            "candidate_id": candidate_id,
            "candidate_revision": candidate_revision,
            "query_index": query_index,
            "predictions_sha256": predictions_sha256,
            "result_sha256": public_core["result_sha256"],
            "score": score,
            "verdict": verdict,
        }
        if baseline is not None:
            audit["baseline"] = baseline
        _append_audit(state_dir, audit)
        state["query_count"] = query_index
        state["cohort_revisions"] = revisions
        state["updated_at"] = audit["at"]
        _atomic_json(_state_path(state_dir), state)
        return public_core


def mark_contaminated(
    manifest: dict[str, Any], state_dir: Path, *, reason: str, replacement_suite: str | None = None
) -> dict[str, Any]:
    with _locked_state(state_dir):
        state = load_state(state_dir, manifest)
        state["status"] = "contaminated"
        state["contamination"] = {
            "at": _now(),
            "reason_sha256": _sha256_bytes(reason.encode()),
        }
        if replacement_suite:
            state["superseded_by"] = replacement_suite
        state["updated_at"] = state["contamination"]["at"]
        _atomic_json(_state_path(state_dir), state)
        return public_status(state)


def supersede(
    manifest: dict[str, Any], state_dir: Path, *, replacement_suite: str
) -> dict[str, Any]:
    if not replacement_suite:
        raise ProtectedEvalError("replacement_suite is required")
    with _locked_state(state_dir):
        state = load_state(state_dir, manifest)
        state["status"] = "superseded"
        state["superseded_by"] = replacement_suite
        state["updated_at"] = _now()
        _atomic_json(_state_path(state_dir), state)
        return public_status(state)


def public_status(state: dict[str, Any]) -> dict[str, Any]:
    contamination = state.get("contamination")
    return {
        "schema": STATE_SCHEMA,
        "suite_id": state["suite_id"],
        "suite_version": state["suite_version"],
        "status": state["status"],
        "query_count": int(state["query_count"]),
        "contaminated": contamination is not None,
        "superseded_by": state.get("superseded_by"),
        "updated_at": state.get("updated_at"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Protected score-only evaluator")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    score = sub.add_parser("score")
    score.add_argument("--cohort", required=True)
    score.add_argument("--predictions", type=Path, required=True)
    score.add_argument("--candidate-id", required=True)
    score.add_argument("--candidate-revision", required=True)
    score.add_argument("--baseline-predictions", type=Path)
    score.add_argument("--baseline-revision")

    contaminate = sub.add_parser("contaminate")
    contaminate.add_argument("--reason", required=True)
    contaminate.add_argument("--replacement-suite")

    rotate = sub.add_parser("supersede")
    rotate.add_argument("--replacement-suite", required=True)
    sub.add_parser("status")

    args = parser.parse_args(argv)
    manifest = load_manifest(args.manifest)
    try:
        if args.command == "score":
            output = score_predictions(
                manifest, cohort_name=args.cohort, predictions_path=args.predictions,
                candidate_id=args.candidate_id, candidate_revision=args.candidate_revision,
                state_dir=args.state_dir,
                baseline_predictions_path=args.baseline_predictions, baseline_revision=args.baseline_revision,
            )
        elif args.command == "contaminate":
            output = mark_contaminated(
                manifest, args.state_dir, reason=args.reason, replacement_suite=args.replacement_suite
            )
        elif args.command == "supersede":
            output = supersede(manifest, args.state_dir, replacement_suite=args.replacement_suite)
        else:
            output = public_status(load_state(args.state_dir, manifest))
    except ProtectedEvalError as exc:
        raise SystemExit(f"protected evaluator refused: {exc}") from exc
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
