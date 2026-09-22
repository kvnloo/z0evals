#!/usr/bin/env python3
"""Validate z0eval study manifests and frozen artifact hashes.

Also enforces supersession. A study must be able to say "the measurement is
unchanged, the interpretation is superseded" WITHOUT mutating history. Before
this there was only a `status: superseded` value and a prose audit trail, so the
distinction the whole evidence taxonomy rests on lived in free text.

The guarantee is not a promise, it is the artifact hashes: a `measurement_unchanged:
true` claim requires at least one hashed artifact and those hashes must still
verify. Rewriting a frozen number to change what it is taken to mean therefore
fails validation, which is the point.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_root(root: Path) -> tuple[list[str], int]:
    """Return (problems, manifest_count). Pure with respect to `root`."""
    schema = json.loads((root / "schemas/study-manifest.schema.json").read_text())
    validator = Draft202012Validator(schema)
    problems: list[str] = []

    manifests = sorted((root / "studies").glob("*/manifest.yaml"))
    if not manifests:
        raise SystemExit("no study manifests found")

    loaded: dict[str, dict[str, Any]] = {}
    for path in manifests:
        data = yaml.safe_load(path.read_text()) or {}
        if isinstance(data.get("id"), str):
            loaded[data["id"]] = data

    for path in manifests:
        data = yaml.safe_load(path.read_text()) or {}
        study_id = data.get("id", path.parent.name)
        for e in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
            problems.append(f"{path}: schema error at {list(e.path)}: {e.message}")

        study_dir = path.parent
        hashed_artifacts = 0
        for artifact in data.get("artifacts") or []:
            target = study_dir / artifact["path"]
            if not target.exists():
                problems.append(f"{path}: missing artifact {artifact['path']}")
                continue
            expected = artifact.get("sha256")
            if expected:
                if digest(target) != expected:
                    problems.append(f"{path}: hash mismatch {artifact['path']}")
                else:
                    hashed_artifacts += 1

        if data.get("status") in {"frozen", "published"}:
            for src in data.get("sources") or []:
                if len(src.get("commit", "")) != 40:
                    problems.append(
                        f"{path}: frozen source is not a full commit SHA: {src}"
                    )

        problems.extend(
            _supersession_problems(path, study_id, data, loaded, hashed_artifacts)
        )

    return problems, len(manifests)


def _supersession_problems(
    path: Path,
    study_id: str,
    data: dict[str, Any],
    loaded: dict[str, dict[str, Any]],
    hashed_artifacts: int,
) -> list[str]:
    """Rules that keep a supersession honest and history immutable."""
    out: list[str] = []
    block = data.get("supersession")

    if data.get("status") == "superseded" and not block:
        out.append(
            f"{path}: status is 'superseded' but no supersession block records "
            "what was superseded. The status alone asserts history that is not written down."
        )
    if block and data.get("status") != "superseded":
        out.append(
            f"{path}: has a supersession block but status is "
            f"{data.get('status')!r}, not 'superseded'."
        )
    if not block:
        return out

    target = block.get("superseded_by")
    if target:
        if target not in loaded:
            out.append(f"{path}: superseded_by {target!r} names no study manifest")
        elif target == study_id:
            out.append(f"{path}: superseded_by cannot name the study itself")
        elif (loaded[target].get("supersession") or {}).get("superseded_by") == study_id:
            out.append(f"{path}: supersession cycle with {target!r}")

    unchanged = block.get("measurement_unchanged")
    changed = block.get("interpretation_changed")
    if unchanged and not changed:
        out.append(
            f"{path}: measurement_unchanged=true with interpretation_changed=false "
            "records no change at all."
        )
    if unchanged and hashed_artifacts == 0:
        out.append(
            f"{path}: measurement_unchanged=true but no artifact hash verifies, "
            "so the claim cannot be checked. Hash the frozen artifacts."
        )
    return out


def main() -> None:
    problems, count = validate_root(ROOT)
    for problem in problems:
        print(problem)
    if problems:
        raise SystemExit(f"{len(problems)} validation error(s)")
    print(f"ok: {count} study manifest(s)")


if __name__ == "__main__":
    main()
