#!/usr/bin/env python3
"""Freeze an explicit analysis/summary.json result into a validated receipt."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def finding_view(result: dict) -> dict:
    finding = {key: copy.deepcopy(result[key]) for key in (
        "arm", "metric", "evidence_class", "scope_note", "ts"
    )}
    finding["subject"] = {"family": result["family"], "job": result["job"]}
    for key in ("baseline", "expires_at"):
        if key in result:
            finding[key] = copy.deepcopy(result[key])
    return finding


def require_finite(value: object) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("result contains a non-finite number")
    if isinstance(value, dict):
        for child in value.values():
            require_finite(child)
    elif isinstance(value, list):
        for child in value:
            require_finite(child)


def validate_result(result: dict) -> None:
    schema = json.loads((ROOT / "schemas/z0eval.result.v1.json").read_text())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(result)
    require_finite(result)
    metric = result["metric"]
    if metric["ci_low"] > metric["ci_high"]:
        raise ValueError("ci_low must not exceed ci_high")
    if result["findings"] != [finding_view(result)]:
        raise ValueError("findings must match the top-level certified result")
    if result["verdict"] == "KEEP" and any(gate != "pass" for gate in result["gates"].values()):
        raise ValueError("KEEP requires every gate to pass")


def evidence_path(study: Path, ref: dict) -> Path:
    path = Path(ref["path"])
    target = (study / path).resolve()
    if path.is_absolute() or not target.is_relative_to(study):
        raise ValueError(f"evidence must remain inside the study: {ref['path']}")
    if target == study / "result.json":
        raise ValueError("result.json cannot be its own evidence")
    if not target.is_file():
        raise ValueError(f"evidence is not a file: {ref['path']}")
    return target


def emit_result(study_dir: Path) -> Path:
    study = study_dir.resolve()
    manifest_path = study / "manifest.yaml"
    summary_path = study / "analysis/summary.json"
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest_schema = json.loads((ROOT / "schemas/study-manifest.schema.json").read_text())
    Draft202012Validator(manifest_schema, format_checker=FormatChecker()).validate(manifest)
    if manifest["id"] != study.name:
        raise ValueError("manifest id must match the study directory")
    summary = json.loads(summary_path.read_text())
    if not isinstance(summary, dict) or not isinstance(summary.get("result"), dict):
        raise ValueError("analysis/summary.json must contain an explicit result object")
    result = copy.deepcopy(summary["result"])
    if "findings" in result:
        raise ValueError("result.findings is derived by the emitter, not supplied by analysis")
    for key, expected in (("schema", "z0eval.result.v1"), ("suite_id", manifest["id"])):
        if key in result and result[key] != expected:
            raise ValueError(f"result.{key} does not match the study")
        result[key] = expected
    # Do not infer an arm, verdict, metric, revision, or evidence class from prose.
    try:
        result["findings"] = [finding_view(result)]
    except KeyError as exc:
        raise ValueError(f"result lacks required field: {exc.args[0]}") from exc
    validate_result(result)
    for refs in result["evidence"].values():
        for ref in refs:
            if digest(evidence_path(study, ref)) != ref["sha256"]:
                raise ValueError(f"evidence hash mismatch: {ref['path']}")
    # Bind the analysis and the manifest without a self-referential summary hash.
    source_refs = result["evidence"]["source_artifacts"]
    for path in (manifest_path, summary_path):
        relative = path.relative_to(study).as_posix()
        if not any(ref["path"] == relative for refs in result["evidence"].values() for ref in refs):
            source_refs.append({"path": relative, "sha256": digest(path)})
    validate_result(result)
    output = study / "result.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path, help="study directory with manifest.yaml and analysis/summary.json")
    args = parser.parse_args()
    try:
        output = emit_result(args.study)
    except (OSError, ValueError, yaml.YAMLError, ValidationError) as exc:
        parser.exit(1, f"emit_result: {exc}\n")
    print(output)


if __name__ == "__main__":
    main()
