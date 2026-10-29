"""Unit coverage for scripts/validate.py manifest and artifact integrity gates."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate", ROOT / "scripts" / "validate.py")
assert SPEC and SPEC.loader
validate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate)  # type: ignore[union-attr]


class ValidateManifestsTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

        (self.root / "schemas").mkdir()
        shutil.copyfile(
            ROOT / "schemas" / "study-manifest.schema.json",
            self.root / "schemas" / "study-manifest.schema.json",
        )
        (self.root / "studies").mkdir()

        root_patch = patch.object(validate, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)

    @staticmethod
    def _write_manifest(path, data):
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    def _make_manifest(self, study_id="demo"):
        study_dir = self.root / "studies" / study_id
        study_dir.mkdir(parents=True)
        artifact_path = study_dir / "data" / "x.json"
        artifact_path.parent.mkdir()
        payload = b'{"value": 1}\n'
        artifact_path.write_bytes(payload)

        data = {
            "schema_version": "z0eval.study.v1",
            "id": study_id,
            "title": "Demo",
            "status": "draft",
            "created": "2026-01-01",
            "sources": [{"repo": "kvnloo/x", "commit": "abc1234"}],
            "questions": ["q"],
            "artifacts": [
                {
                    "path": "data/x.json",
                    "kind": "result",
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            ],
        }
        manifest_path = study_dir / "manifest.yaml"
        self._write_manifest(manifest_path, data)
        return manifest_path, artifact_path, data

    def _run_ok(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = validate.main()
        self.assertIsNone(result)
        return stdout.getvalue()

    def _run_error(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as raised:
                validate.main()
        return raised.exception.code, stdout.getvalue()

    def test_digest_matches_hashlib(self):
        large = bytes(range(256)) * 10_240
        self.assertEqual(len(large), 2_621_440)  # 2.5 MiB, three read chunks
        for name, payload in (
            ("empty", b""),
            ("abc", b"abc"),
            ("multi_chunk", large),
        ):
            with self.subTest(case=name):
                path = self.root / "payload.bin"
                path.write_bytes(payload)
                actual = validate.digest(path)
                self.assertEqual(actual, hashlib.sha256(payload).hexdigest())
                if name == "abc":
                    self.assertEqual(
                        actual,
                        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
                    )

    def test_valid_manifest_prints_ok(self):
        self._make_manifest()
        self.assertEqual(self._run_ok(), "ok: 1 study manifest(s)\n")

    def test_no_manifests(self):
        code, stdout = self._run_error()
        self.assertEqual(code, "no study manifests found")
        self.assertEqual(stdout, "")

    def test_missing_artifact(self):
        _, artifact_path, _ = self._make_manifest()
        artifact_path.unlink()
        code, stdout = self._run_error()
        self.assertEqual(code, "1 validation error(s)")
        self.assertIn("missing artifact data/x.json", stdout)

    def test_hash_mismatch(self):
        manifest_path, _, data = self._make_manifest()
        data["artifacts"][0]["sha256"] = "0" * 64
        self._write_manifest(manifest_path, data)
        code, stdout = self._run_error()
        self.assertEqual(code, "1 validation error(s)")
        self.assertIn("hash mismatch data/x.json", stdout)

        del data["artifacts"][0]["sha256"]
        self._write_manifest(manifest_path, data)
        self.assertEqual(self._run_ok(), "ok: 1 study manifest(s)\n")

    def test_frozen_requires_full_sha(self):
        manifest_path, _, data = self._make_manifest()
        data["status"] = "frozen"
        self._write_manifest(manifest_path, data)
        code, stdout = self._run_error()
        self.assertEqual(code, "1 validation error(s)")
        self.assertIn("frozen source is not a full commit SHA", stdout)

        data["sources"][0]["commit"] = "a" * 40
        self._write_manifest(manifest_path, data)
        self.assertEqual(self._run_ok(), "ok: 1 study manifest(s)\n")

        data["status"] = "draft"
        data["sources"][0]["commit"] = "abc1234"
        self._write_manifest(manifest_path, data)
        self.assertEqual(self._run_ok(), "ok: 1 study manifest(s)\n")

    def test_schema_error_reported(self):
        manifest_path, _, data = self._make_manifest()
        data["status"] = "bogus"
        self._write_manifest(manifest_path, data)
        code, stdout = self._run_error()
        self.assertEqual(code, "1 validation error(s)")
        self.assertIn("schema error at ['status']", stdout)

    def test_errors_accumulate(self):
        _, first_artifact, _ = self._make_manifest("first")
        first_artifact.unlink()

        second_manifest, _, second_data = self._make_manifest("second")
        second_data["artifacts"][0]["sha256"] = "0" * 64
        self._write_manifest(second_manifest, second_data)

        code, stdout = self._run_error()
        self.assertEqual(code, "2 validation error(s)")
        self.assertIn("missing artifact data/x.json", stdout)
        self.assertIn("hash mismatch data/x.json", stdout)

    def test_repo_manifests_still_validate(self):
        with patch.object(validate, "ROOT", ROOT):
            stdout = self._run_ok()
        self.assertRegex(stdout, r"^ok: [1-9][0-9]* study manifest\(s\)\n$")


if __name__ == "__main__":
    unittest.main()
