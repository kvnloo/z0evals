from pathlib import Path
import hashlib
import tempfile
import unittest

from omp_qualification_paths import canonical_output_target, verify_reviewed_write


class QualificationScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "candidate"
        self.root.mkdir()
        self.content = "print('bounded fixture')\n"
        self.binding = {
            "task_id": "work-one", "session_id": "native-one", "candidate_ref": "a" * 40,
            "policy_revision": "v0", "launcher_sha256": "b" * 64,
            "candidate_root": str(self.root),
        }

    def test_relative_and_absolute_target_are_equivalent(self):
        relative = canonical_output_target(self.root, "tools/probe_exact_path.py", self.root)
        absolute = canonical_output_target(self.root, str(relative), self.root.parent)
        self.assertEqual(relative, absolute)

    def test_escape_and_other_file_are_denied(self):
        paths = ("../outside.py", "tools/other.py", str(self.root.parent / "candidate-sibling/tools/probe_exact_path.py"))
        for path in paths:
            with self.subTest(path=path), self.assertRaises(ValueError):
                canonical_output_target(self.root, path, self.root)

    def test_symlink_escape_is_denied(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        (self.root / "tools").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            canonical_output_target(self.root, "tools/probe_exact_path.py", self.root)

    def test_missing_parent_does_not_broaden_scope(self):
        target = canonical_output_target(self.root, "tools/probe_exact_path.py", self.root)
        self.assertEqual(target, self.root / "tools/probe_exact_path.py")
        with self.assertRaises(ValueError):
            canonical_output_target(self.root, "tools/probe_exact_path.py/other", self.root)

    def test_write_stays_bound_to_reviewed_target_and_content(self):
        digest = hashlib.sha256(self.content.encode()).hexdigest()
        target = verify_reviewed_write(self.root, "tools/probe_exact_path.py", self.root,
                                       self.content, digest, self.binding, self.binding)
        self.assertEqual(target, self.root / "tools/probe_exact_path.py")
        for path, content in (("tools/other.py", self.content), ("tools/probe_exact_path.py", "changed")):
            with self.subTest(path=path, content=content), self.assertRaises(ValueError):
                verify_reviewed_write(self.root, path, self.root, content, digest, self.binding, self.binding)

    def test_old_review_cannot_follow_changed_source_policy_or_run(self):
        digest = hashlib.sha256(self.content.encode()).hexdigest()
        for key in ("candidate_ref", "policy_revision", "task_id", "session_id", "launcher_sha256", "candidate_root"):
            changed = {**self.binding, key: "changed"}
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_reviewed_write(self.root, "tools/probe_exact_path.py", self.root,
                                      self.content, digest, self.binding, changed)


if __name__ == "__main__":
    unittest.main()
