#!/usr/bin/env python3
"""Validate z0eval study manifests and frozen artifact hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    schema = json.loads((ROOT / "schemas/study-manifest.schema.json").read_text())
    validator = Draft202012Validator(schema)
    errors = 0

    manifests = sorted((ROOT / "studies").glob("*/manifest.yaml"))
    if not manifests:
        raise SystemExit("no study manifests found")

    for path in manifests:
        data = yaml.safe_load(path.read_text())
        problems = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        if problems:
            errors += len(problems)
            for e in problems:
                print(f"{path}: schema error at {list(e.path)}: {e.message}")

        study_dir = path.parent
        for artifact in data.get("artifacts", []):
            target = study_dir / artifact["path"]
            if not target.exists():
                print(f"{path}: missing artifact {artifact['path']}")
                errors += 1
                continue
            expected = artifact.get("sha256")
            if expected and digest(target) != expected:
                print(f"{path}: hash mismatch {artifact['path']}")
                errors += 1

        if data.get("status") in {"frozen", "published"}:
            for src in data.get("sources", []):
                if len(src.get("commit", "")) != 40:
                    print(f"{path}: frozen source is not a full commit SHA: {src}")
                    errors += 1

    if errors:
        raise SystemExit(f"{errors} validation error(s)")
    print(f"ok: {len(manifests)} study manifest(s)")


if __name__ == "__main__":
    main()
