"""Independent D2 behavior oracle; run outside the native agent's write scope."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.fixture
def candidate():
    raw = os.environ.get("Z0_QUALIFICATION_CANDIDATE")
    if not raw:
        pytest.skip("requires an explicitly frozen isolated candidate")
    return Path(raw).resolve(strict=True)


def invoke(candidate, path):
    return subprocess.run(
        [sys.executable, str(candidate / "tools/probe_exact_path.py"), path],
        cwd=candidate, env=dict(os.environ), text=True, capture_output=True,
    )


def assert_exact_evidence(candidate, path):
    from z0int.context_resolve import _fetch_exact_path
    result = invoke(candidate, path)
    assert result.returncode == 0, result.stderr
    actual = json.loads(result.stdout)
    ref = _fetch_exact_path(path, candidate)
    assert ref is not None
    assert actual == {key: getattr(ref, key) for key in ("source_id", "locator", "source_version", "excerpt")}
    assert len(actual["excerpt"]) <= 800  # production bounds 400 characters before newline escaping
    return actual


def test_same_size_same_second_replacement(candidate):
    target = candidate / "tests/qualification_value.txt"
    try:
        identities = []
        for content in ("value = 1\n", "value = 2\n"):
            target.write_text(content)
            os.utime(target, (1700000000, 1700000000))
            identities.append(assert_exact_evidence(candidate, str(target.relative_to(candidate)))["source_version"])
        assert identities[0] != identities[1]
    finally:
        target.unlink(missing_ok=True)


def test_valid_empty_file_is_complete_evidence(candidate):
    target = candidate / "tests/qualification_empty.txt"
    try:
        target.write_bytes(b"")
        assert assert_exact_evidence(candidate, str(target.relative_to(candidate)))["excerpt"] == ""
    finally:
        target.unlink(missing_ok=True)


def test_missing_file_is_failure(candidate):
    assert invoke(candidate, "tools/qualification_missing.py").returncode != 0


def test_absolute_and_parent_component_rejected(candidate):
    for path in ("/etc/hosts", "../candidate/zer0.repo.yaml"):
        result = invoke(candidate, path)
        assert result.returncode != 0
        assert "repository-relative path required" in result.stderr
