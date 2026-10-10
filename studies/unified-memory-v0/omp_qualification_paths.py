"""Evidence-only target checks for the existing OMP qualification launcher.

These checks do not grant execution permission or replace native approvals.
The caller must obtain the expected bindings from its separately held manifest.
"""

from pathlib import Path
from types import SimpleNamespace
import hashlib
import re

from z0int.bridge.reuse import _mutation_scope

OUTPUT_REL = "tools/probe_exact_path.py"
REVIEW_FIELDS = ("task_id", "session_id", "candidate_ref", "policy_revision", "launcher_sha256", "candidate_root")


def canonical_output_target(candidate_root: Path, raw_path: str, execution_cwd: Path) -> Path:
    root = candidate_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("recorded candidate root is not a directory")
    cwd = execution_cwd.resolve(strict=True)
    # Use the production boundary check, including symlink and .git handling.
    _mutation_scope(SimpleNamespace(root=root), {
        "target_cwd": str(cwd), "target_paths": [raw_path], "tool_name": "write",
    })
    target = (cwd / raw_path).resolve()
    if target != root / OUTPUT_REL:
        raise ValueError("mutation proposal escaped the one-file scope")
    return target


def verify_reviewed_write(candidate_root: Path, raw_path: str, execution_cwd: Path,
                          content: str, content_sha256: str, reviewed: dict, current: dict) -> Path:
    for key in REVIEW_FIELDS:
        if not isinstance(reviewed.get(key), str) or not reviewed[key] or current.get(key) != reviewed[key]:
            raise ValueError(f"review binding changed or unavailable: {key}")
    if Path(reviewed["candidate_root"]).resolve(strict=True) != candidate_root.resolve(strict=True):
        raise ValueError("review belongs to a different candidate root")
    if not isinstance(content, str) or not isinstance(content_sha256, str) or re.fullmatch(r"[0-9a-f]{64}", content_sha256) is None:
        raise ValueError("reviewed write content is unavailable")
    if hashlib.sha256(content.encode("utf-8")).hexdigest() != content_sha256:
        raise ValueError("write content changed after review")
    return canonical_output_target(candidate_root, raw_path, execution_cwd)
