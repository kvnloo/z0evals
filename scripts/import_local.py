#!/usr/bin/env python3
"""Import explicitly allowlisted artifacts from pinned local git commits."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/import_local.py imports/<study>.local.yaml")

    spec_path = Path(sys.argv[1]).resolve()
    spec = yaml.safe_load(spec_path.read_text())
    study_id = spec["study"]
    study_dir = ROOT / "studies" / study_id
    manifest_path = study_dir / "manifest.yaml"
    if not manifest_path.exists():
        raise SystemExit(f"study does not exist: {study_id}")

    manifest = yaml.safe_load(manifest_path.read_text())
    imported = []
    source_rows = []

    for src in spec.get("sources", []):
        local_root = Path(src["root"]).expanduser().resolve()
        requested = str(src["commit"]).strip()
        actual = git(local_root, "rev-parse", requested)
        if not actual.startswith(requested) and not requested.startswith(actual):
            raise SystemExit(f"{src['name']}: requested commit did not resolve as expected")
        if len(actual) != 40:
            raise SystemExit(f"{src['name']}: commit must resolve to full SHA")

        # Require every copied file to exist in the pinned commit, not merely
        # as an uncommitted local artifact.
        for item in src.get("files", []):
            rel = item["from"]
            subprocess.check_call(
                ["git", "-C", str(local_root), "cat-file", "-e", f"{actual}:{rel}"]
            )
            out = study_dir / item["to"]
            out.parent.mkdir(parents=True, exist_ok=True)
            data = subprocess.check_output(
                ["git", "-C", str(local_root), "show", f"{actual}:{rel}"]
            )
            out.write_bytes(data)
            imported.append(
                {"path": str(out.relative_to(study_dir)), "kind": item["kind"], "sha256": sha256(out)}
            )

        source_rows.append(
            {
                "repo": src["repo"],
                "commit": actual,
                "branch": git(local_root, "branch", "--show-current") or "detached",
                "role": src.get("role", src["name"]),
            }
        )

    manifest["sources"] = source_rows
    manifest["artifacts"] = imported
    manifest["updated"] = __import__("datetime").date.today().isoformat()
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    print(f"imported {len(imported)} artifacts into {study_id}")
    for row in imported:
        print(f"  {row['kind']:8} {row['path']}  {row['sha256'][:12]}")


if __name__ == "__main__":
    main()
