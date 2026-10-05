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


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def _read_jsonl(path: Path, value_key: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    with path.open(encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, 1):
            if not raw.strip():
                continue
            row = json.loads(raw)
            item_id = str(row.get("id") or "")
            if not item_id or value_key not in row:
                raise ProtectedEvalError(f"{path.name}:{line_no} requires id and {value_key}")
            if item_id in result:
                raise ProtectedEvalError(f"duplicate item id in {path.name}")
            result[item_id] = row[value_key]
    if not result:
        raise ProtectedEvalError(f"{path.name} is empty")
    return result


def score_predictions(
    manifest: dict[str, Any],
    *,
    cohort_name: str,
    predictions_path: Path,
    candidate_id: str,
    candidate_revision: str,
    state_dir: Path,
) -> dict[str, Any]:
    if not PIN_RE.fullmatch(candidate_revision):
        raise ProtectedEvalError("candidate_revision must be a full 40-character git SHA")
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

        truth_path = _resolve_truth_ref(str(cohort["truth_ref"]))
        truth = _read_jsonl(truth_path, "expected")
        predictions = _read_jsonl(predictions_path, "prediction")
        if predictions.keys() != truth.keys():
            raise ProtectedEvalError("prediction IDs must exactly match the protected cohort IDs")

        correct = sum(predictions[item_id] == expected for item_id, expected in truth.items())
        score = correct / len(truth)
        verdict = "KEEP" if score >= float(manifest["scoring"]["pass_threshold"]) else "DISCARD"
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
            "predictions_sha256": _sha256_file(predictions_path),
            "result_sha256": public_core["result_sha256"],
            "score": score,
            "verdict": verdict,
        }
        _append_audit(state_dir, audit)
        state["query_count"] = query_index
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
