#!/usr/bin/env python3
"""Offline frozen-s3 completeness and fixture-validity checks; no model calls."""
import collections
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch

from bench import pin_profile_cwd
from verify import verify

STUDY = Path(__file__).resolve().parents[1]


def check_rows():
    hashes = json.loads((STUDY / "analysis/retrieval-sha256.json").read_text())
    for relative, digest in hashes.items():
        assert hashlib.sha256((STUDY / relative).read_bytes()).hexdigest() == digest, relative
    print("retrieval hashes:", len(hashes), "match MBP snapshot")
    rows = [json.loads(line) for path in (STUDY / "data/s3").glob("*.jsonl")
            for line in path.read_text().splitlines() if line.strip()]
    cold = {"fx-base", "fx-cli", "hermes-base", "hermes-default-ft", "hermes-speed",
            "hermes-speed-guided", "omp-base", "pi-base"}
    warm = {"fx-base", "hermes-speed", "omp-base", "pi-base"}
    task_arms = cold - {"hermes-default-ft", "omp-base"}
    expected = set()
    for mode, arms, blocks in (("cold", cold, 32), ("warm", warm, 30)):
        for arm in arms:
            for block in range(-1, blocks):
                expected.add(("latency", "s3", mode, arm, block))
    for session, prefix in (("s3", "t"), ("s3h", "h")):
        for task in (STUDY / "tasks").glob(prefix + "*"):
            for arm in task_arms:
                for rep in range(2):
                    expected.add(("task", session, task.name, arm, rep))
    keys = []
    for row in rows:
        if row["kind"] == "latency":
            keys.append(("latency", row["session"], row["mode"], row["arm"], row["block"]))
            assert row["correct"], keys[-1]
            assert row["phase"] == ("warmup" if row["block"] == -1 else "run")
        else:
            keys.append(("task", row["session"], row["task"], row["arm"], row["rep"]))
            assert row["verified"]["pass"] and not row["verified"]["tests_modified"], keys[-1]
        assert row.get("exit", 0) == 0 and not row.get("timed_out") and not row.get("errors"), keys[-1]
    assert len(keys) == len(set(keys)), "duplicate cells"
    assert set(keys) == expected, ("missing", expected - set(keys), "extra", set(keys) - expected)
    aborted = [json.loads(line) for line in
               (STUDY / "data/s3/aborted-tasks/tasks.jsonl").read_text().splitlines()]
    assert len(aborted) == 19
    print("s3 cells:", len(keys), "complete, unique; aborted rows retained:", len(aborted))
    print("groups:", dict(collections.Counter((r["kind"], r["session"]) for r in rows)))


def check_fixtures():
    count = 0
    for task in sorted((STUDY / "tasks").iterdir()):
        if not task.is_dir():
            continue
        with tempfile.TemporaryDirectory(prefix="hsb-verify-") as scratch:
            work = Path(scratch) / "repo"
            shutil.copytree(task / "repo", work)
            assert not verify(str(task), str(work))["pass"], f"original passes: {task.name}"
            shutil.copytree(task / "reference", work, dirs_exist_ok=True)
            assert verify(str(task), str(work))["pass"], f"reference fails: {task.name}"
        count += 1
    assert count == 14
    print("fixtures: 14 originals fail, 14 references pass")


def check_profile_scope():
    with patch("bench.subprocess.run") as run:
        pin_profile_cwd("speed", str(STUDY))
        assert run.call_args.args[0] == ["hermes", "-p", "speed", "config", "set", "terminal.cwd", str(STUDY)]
        run.assert_called_once()
    for profile in ("clean", "default", "owner", "../speed"):
        with patch("bench.subprocess.run") as run:
            try:
                pin_profile_cwd(profile, str(STUDY))
            except ValueError:
                pass
            else:
                raise AssertionError(f"unowned profile accepted: {profile}")
            run.assert_not_called()
    print("profile pinning: scoped CLI setter; unowned profiles refused")


if __name__ == "__main__":
    check_rows()
    check_fixtures()
    check_profile_scope()
