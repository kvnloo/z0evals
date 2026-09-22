"""A study must be able to say "measurement unchanged / interpretation
superseded" without mutating history.

Before this, supersession was only a `status: superseded` value plus prose in
`docs/audit-trail.md`. The distinction the whole evidence taxonomy rests on —
that a FROZEN MEASUREMENT can stand while what it is taken to MEAN is replaced —
lived in free text, so nothing could check it and nothing stopped a frozen
number being quietly rewritten to mean something else.

The guarantee is the artifact hashes, not a promise: a `measurement_unchanged:
true` claim requires a hashed artifact and that hash must still verify. Case 6
below is the one that matters — tampering with the frozen artifact fails the
claim that says it was not tampered with.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import validate as validate_mod  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(study_id: str, **over) -> dict:
    data = {
        "schema_version": "z0eval.study.v1",
        "id": study_id,
        "title": f"Study {study_id}",
        "status": "frozen",
        "created": "2026-09-21",
        # shapes must satisfy the real schema: questions are strings, sources
        # are non-empty and need a full commit SHA for a frozen status.
        "sources": [{"repo": "kvnloo/z0evals", "commit": "0" * 40}],
        "questions": ["What happened?"],
        "artifacts": [],
    }
    data.update(over)
    return data


class SupersessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "schemas").mkdir()
        shutil.copy(REPO / "schemas/study-manifest.schema.json",
                    self.root / "schemas/study-manifest.schema.json")
        (self.root / "studies").mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write(self, study_id: str, data: dict, artifact: bytes | None = None) -> None:
        d = self.root / "studies" / study_id
        d.mkdir(parents=True, exist_ok=True)
        if artifact is not None:
            target = d / "result.json"
            target.write_bytes(artifact)
            data.setdefault("artifacts", []).append(
                {"path": "result.json", "kind": "result", "sha256": _sha256(target)}
            )
        (d / "manifest.yaml").write_text(yaml.safe_dump(data, sort_keys=False))

    def _problems(self) -> list[str]:
        problems, _ = validate_mod.validate_root(self.root)
        return problems

    def _supersession(self, **over) -> dict:
        block = {
            "superseded_by": "study-b",
            "measurement_unchanged": True,
            "interpretation_changed": True,
            "what_changed": "the 0.941 figure was read as a capability; it is a rate over covered rows",
            "recorded": "2026-09-22",
        }
        block.update(over)
        return block

    # 1 -----------------------------------------------------------------
    def test_valid_supersession_is_clean(self) -> None:
        self._write("study-b", _manifest("study-b"))
        self._write("study-a", _manifest("study-a", status="superseded",
                                        supersession=self._supersession()),
                    artifact=b'{"accuracy": 0.941}')
        self.assertEqual(self._problems(), [])

    # 2 -----------------------------------------------------------------
    def test_status_superseded_requires_a_record(self) -> None:
        self._write("study-a", _manifest("study-a", status="superseded"))
        problems = self._problems()
        self.assertTrue(any("no supersession block" in p for p in problems), problems)

    # 3 -----------------------------------------------------------------
    def test_a_block_without_the_status_is_rejected(self) -> None:
        self._write("study-b", _manifest("study-b"))
        self._write("study-a", _manifest("study-a", status="frozen",
                                        supersession=self._supersession()),
                    artifact=b"{}")
        problems = self._problems()
        self.assertTrue(any("not 'superseded'" in p for p in problems), problems)

    # 4 -----------------------------------------------------------------
    def test_measurement_unchanged_with_nothing_changed_is_rejected(self) -> None:
        self._write("study-b", _manifest("study-b"))
        self._write("study-a", _manifest("study-a", status="superseded",
                                        supersession=self._supersession(
                                            interpretation_changed=False)),
                    artifact=b"{}")
        problems = self._problems()
        self.assertTrue(any("no change at all" in p for p in problems), problems)

    # 5 -----------------------------------------------------------------
    def test_measurement_unchanged_needs_a_verifiable_hash(self) -> None:
        self._write("study-b", _manifest("study-b"))
        # artifact present but NO sha256 -> the claim is unverifiable
        self._write("study-a", _manifest("study-a", status="superseded",
                                        supersession=self._supersession(),
                                        artifacts=[{"path": "result.json", "kind": "result"}]))
        (self.root / "studies/study-a/result.json").write_bytes(b"{}")
        problems = self._problems()
        self.assertTrue(any("cannot be checked" in p for p in problems), problems)

    # 6 -- THE ONE THAT MATTERS -----------------------------------------
    def test_tampering_with_a_frozen_artifact_fails_the_unchanged_claim(self) -> None:
        self._write("study-b", _manifest("study-b"))
        self._write("study-a", _manifest("study-a", status="superseded",
                                        supersession=self._supersession()),
                    artifact=b'{"accuracy": 0.941}')
        # Someone rewrites the frozen number instead of recording an erratum.
        (self.root / "studies/study-a/result.json").write_bytes(b'{"accuracy": 0.999}')
        problems = self._problems()
        self.assertTrue(any("hash mismatch" in p for p in problems), problems)

    # 7 -----------------------------------------------------------------
    def test_superseded_by_must_name_a_real_study(self) -> None:
        self._write("study-a", _manifest("study-a", status="superseded",
                                        supersession=self._supersession(
                                            superseded_by="does-not-exist")),
                    artifact=b"{}")
        problems = self._problems()
        self.assertTrue(any("names no study manifest" in p for p in problems), problems)

    # 8 -----------------------------------------------------------------
    def test_supersession_cycle_is_rejected(self) -> None:
        self._write("study-b", _manifest("study-b", status="superseded",
                                        supersession=self._supersession(
                                            superseded_by="study-a")),
                    artifact=b"{}")
        self._write("study-a", _manifest("study-a", status="superseded",
                                        supersession=self._supersession(
                                            superseded_by="study-b")),
                    artifact=b"{}")
        problems = self._problems()
        self.assertTrue(any("cycle" in p for p in problems), problems)

    # 9 -----------------------------------------------------------------
    def test_self_supersession_is_rejected(self) -> None:
        self._write("study-a", _manifest("study-a", status="superseded",
                                        supersession=self._supersession(
                                            superseded_by="study-a")),
                    artifact=b"{}")
        problems = self._problems()
        self.assertTrue(any("cannot name the study itself" in p for p in problems), problems)

    # 10 ----------------------------------------------------------------
    def test_schema_rejects_an_unknown_supersession_key(self) -> None:
        self._write("study-b", _manifest("study-b"))
        self._write("study-a", _manifest("study-a", status="superseded",
                                        supersession=self._supersession(bogus="x")),
                    artifact=b"{}")
        problems = self._problems()
        self.assertTrue(any("schema error" in p for p in problems), problems)

    # 11 ----------------------------------------------------------------
    def test_the_real_repo_still_validates(self) -> None:
        """The change must not disturb the existing study tree."""
        problems, count = validate_mod.validate_root(REPO)
        self.assertEqual(problems, [])
        self.assertGreaterEqual(count, 1)

    # 12 ----------------------------------------------------------------
    def test_the_new_field_is_declared_in_the_repo_schema(self) -> None:
        schema = json.loads((REPO / "schemas/study-manifest.schema.json").read_text())
        self.assertIn("supersession", schema["properties"])
        self.assertIn("measurement_unchanged",
                      schema["properties"]["supersession"]["properties"])


if __name__ == "__main__":
    unittest.main()
