#!/usr/bin/env python3
"""Import a completed governed AODL golden canary into frozen z0evals results.

Only sanitized summary artifacts are copied. Raw z0int state/receipts stay
outside the repository and are referenced only by the local bundle path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

import jsonschema


HERE = Path(__file__).resolve().parent
REQUIRED_FILES = (
    "bundle.json",
    "golden-trace.json",
    "summary.json",
    "health.json",
    "omp-governed.json",
)
SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "access_token",
    "refresh_token",
    "secret",
    "password",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def walk_sensitive(value, where="$"):
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                yield f"{where}.{key}"
            yield from walk_sensitive(item, f"{where}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_sensitive(item, f"{where}[{index}]")


def pinned_z0int_revision() -> str:
    text = (HERE / "golden-trace-manifest.yaml").read_text(encoding="utf-8")
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "- repo: kvnloo/z0intelligence":
            for next_line in lines[index + 1:index + 5]:
                stripped = next_line.strip()
                if stripped.startswith("commit: "):
                    value = stripped.removeprefix("commit: ").strip()
                    if len(value) == 40 and all(c in "0123456789abcdef" for c in value):
                        return value
    raise ValueError("golden-trace manifest has no exact z0intelligence revision")


def validate_bundle(bundle_dir: Path) -> tuple[dict, dict, dict[str, str]]:
    missing = [name for name in REQUIRED_FILES if not (bundle_dir / name).is_file()]
    if missing:
        raise ValueError("missing sanitized bundle files: " + ", ".join(missing))
    if (bundle_dir / "raw").exists():
        # Raw state is allowed to exist locally, but import is intentionally
        # constrained to REQUIRED_FILES and never traverses/copies raw/.
        pass

    bundle = load_json(bundle_dir / "bundle.json")
    golden = load_json(bundle_dir / "golden-trace.json")
    jsonschema.validate(bundle, load_json(HERE / "golden-canary-bundle.schema.json"))
    jsonschema.validate(golden, load_json(HERE / "golden-trace.schema.json"))

    pinned = pinned_z0int_revision()
    if bundle["z0int_revision"] != pinned or bundle["study_pinned_z0int_revision"] != pinned:
        raise ValueError("bundle revision does not match frozen study revision")
    if bundle["root_trace_id"] != golden["root_trace_id"]:
        raise ValueError("bundle and golden trace root identities do not match")
    if (
        bundle["structural_execution_complete"] != golden["structural_execution_complete"]
        or bundle["verified_outcome_complete"] != golden["verified_outcome_complete"]
    ):
        raise ValueError("bundle completion flags do not match the golden trace")
    if not golden["structural_execution_complete"] or not golden["verified_outcome_complete"]:
        raise ValueError("golden trace is incomplete")

    hashes: dict[str, str] = {}
    live_secret = os.environ.get("OPENROUTER_API_KEY")
    for name in REQUIRED_FILES:
        path = bundle_dir / name
        parsed = load_json(path)
        sensitive = list(walk_sensitive(parsed))
        if sensitive:
            raise ValueError(f"{name} contains sensitive credential-shaped keys: {sensitive}")
        raw = path.read_text(encoding="utf-8")
        if live_secret and live_secret in raw:
            raise ValueError(f"{name} contains the live OpenRouter credential")
        hashes[name] = sha256(path)

    return bundle, golden, hashes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument(
        "--results-root",
        type=Path,
        default=HERE / "results" / "golden",
    )
    args = parser.parse_args()

    bundle, golden, hashes = validate_bundle(args.bundle_dir)
    revision = bundle["z0int_revision"]
    destination = args.results_root / revision[:12]
    if destination.exists():
        parser.error(f"destination already exists: {destination}")
    destination.mkdir(parents=True)

    for name in REQUIRED_FILES:
        shutil.copy2(args.bundle_dir / name, destination / name)

    index = {
        "schema": "z0eval.aodl_golden_import.v1",
        "z0int_revision": revision,
        "z0evals_revision_at_run": bundle["z0evals_revision"],
        "root_trace_id": bundle["root_trace_id"],
        "structural_execution_complete": golden["structural_execution_complete"],
        "verified_outcome_complete": golden["verified_outcome_complete"],
        "verification_scope": bundle["verification_scope"],
        "files": hashes,
        "raw_state_imported": False,
    }
    (destination / "index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "destination": str(destination), "files": len(REQUIRED_FILES)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
