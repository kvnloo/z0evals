"""Hermetic tests for pinned-commit, allowlisted local artifact imports."""
from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("import_local", ROOT / "scripts" / "import_local.py")
assert SPEC and SPEC.loader
import_local = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(import_local)


@unittest.skipUnless(shutil.which("git"), "git is required for local import tests")
class ImportLocalTest(unittest.TestCase):
    COMMITTED_BYTES = b'{"a": 1}'
    BRANCH = "fixture-branch"

    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)

        # Do not read or write the developer's Git config, home, or XDG files.
        home = self.base / "home"
        home.mkdir()
        xdg = self.base / "xdg"
        xdg.mkdir()
        git_env = mock.patch.dict(
            os.environ,
            {
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(xdg),
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_COUNT": "0",
                "GIT_TERMINAL_PROMPT": "0",
            },
        )
        git_env.start()
        self.addCleanup(git_env.stop)

        self.source_repo = self.base / "source"
        self.source_repo.mkdir()
        self._git("init", "-q")
        self._git("config", "--local", "user.email", "fixture@example.invalid")
        self._git("config", "--local", "user.name", "Fixture Author")
        self._git("checkout", "-q", "-b", self.BRANCH)

        self.source_file = self.source_repo / "results" / "r.json"
        self.source_file.parent.mkdir()
        self.source_file.write_bytes(self.COMMITTED_BYTES)
        self._git("add", "results/r.json")
        self._git("commit", "-q", "-m", "Add test result")
        self.full_sha = self._git("rev-parse", "HEAD")

        self.output_root = self.base / "z0evals"
        self.study_dir = self.output_root / "studies" / "demo"
        self.study_dir.mkdir(parents=True)
        (self.study_dir / "manifest.yaml").write_text(
            "id: demo\nstatus: draft\n", encoding="utf-8"
        )

        self.spec_path = self.base / "import.yaml"
        self.spec = {
            "study": "demo",
            "sources": [
                {
                    "name": "src",
                    "repo": "kvnloo/src",
                    "root": str(self.source_repo),
                    "commit": self.full_sha,
                    "files": [
                        {
                            "from": "results/r.json",
                            "to": "data/r.json",
                            "kind": "result",
                        }
                    ],
                }
            ],
        }

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.source_repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def _run_import(self, argv: list[str] | None = None) -> None:
        if argv is None:
            self.spec_path.write_text(
                yaml.safe_dump(self.spec, sort_keys=False), encoding="utf-8"
            )
            argv = ["import_local.py", str(self.spec_path)]
        with (
            mock.patch.object(import_local, "ROOT", self.output_root),
            mock.patch.object(sys, "argv", argv),
        ):
            import_local.main()

    def _manifest(self) -> dict:
        return yaml.safe_load(
            (self.study_dir / "manifest.yaml").read_text(encoding="utf-8")
        )

    def test_imports_file_from_commit(self) -> None:
        self._run_import()
        self.assertEqual(
            (self.study_dir / "data" / "r.json").read_bytes(), self.COMMITTED_BYTES
        )
        manifest = self._manifest()
        self.assertEqual(
            manifest["artifacts"],
            [
                {
                    "path": "data/r.json",
                    "kind": "result",
                    "sha256": hashlib.sha256(self.COMMITTED_BYTES).hexdigest(),
                }
            ],
        )
        self.assertEqual(manifest["id"], "demo")
        self.assertEqual(manifest["status"], "draft")
        self.assertEqual(manifest["updated"], date.today().isoformat())
        self.assertEqual(
            manifest["sources"],
            [
                {
                    "repo": "kvnloo/src",
                    "commit": self.full_sha,
                    "branch": self.BRANCH,
                    "role": "src",
                }
            ],
        )
        self.assertEqual(len(manifest["sources"][0]["commit"]), 40)

    def test_abbreviated_commit_resolves_to_full_sha(self) -> None:
        self.spec["sources"][0]["commit"] = self.full_sha[:12]
        self._run_import()
        recorded = self._manifest()["sources"][0]["commit"]
        self.assertEqual(recorded, self.full_sha)
        self.assertEqual(len(recorded), 40)

    def test_symbolic_ref_rejected(self) -> None:
        self.spec["sources"][0]["commit"] = "HEAD"
        with self.assertRaises(SystemExit) as caught:
            self._run_import()
        self.assertEqual(
            str(caught.exception), "src: requested commit did not resolve as expected"
        )
        self.assertFalse((self.study_dir / "data" / "r.json").exists())

    def test_uncommitted_file_rejected(self) -> None:
        (self.source_repo / "results" / "new.json").write_bytes(b'{"new": true}')
        self.spec["sources"][0]["files"] = [
            {"from": "results/new.json", "to": "data/new.json", "kind": "result"}
        ]
        with self.assertRaises(subprocess.CalledProcessError):
            self._run_import()
        self.assertFalse((self.study_dir / "data" / "new.json").exists())
        self.assertEqual(self._manifest(), {"id": "demo", "status": "draft"})

    def test_committed_bytes_not_worktree(self) -> None:
        self.source_file.write_bytes(b'{"a": 999}')
        self._run_import()
        imported = (self.study_dir / "data" / "r.json").read_bytes()
        self.assertEqual(imported, self.COMMITTED_BYTES)
        self.assertNotEqual(imported, self.source_file.read_bytes())

    def test_branch_name_and_detached(self) -> None:
        self.spec["sources"][0]["role"] = "baseline"
        self._run_import()
        named = self._manifest()["sources"][0]
        self.assertEqual(named["branch"], self.BRANCH)
        self.assertEqual(named["role"], "baseline")

        self._git("checkout", "-q", "--detach", self.full_sha)
        self._run_import()
        detached = self._manifest()["sources"][0]
        self.assertEqual(detached["branch"], "detached")
        self.assertEqual(detached["role"], "baseline")
        self.assertEqual(detached["commit"], self.full_sha)

    def test_missing_study(self) -> None:
        self.spec["study"] = "nope"
        with self.assertRaises(SystemExit) as caught:
            self._run_import()
        self.assertEqual(str(caught.exception), "study does not exist: nope")
        self.assertFalse((self.output_root / "studies" / "nope").exists())

    def test_usage(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            self._run_import(["import_local.py"])
        self.assertTrue(str(caught.exception).startswith("usage:"))


if __name__ == "__main__":
    unittest.main()
