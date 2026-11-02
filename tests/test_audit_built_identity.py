"""Tests for the identity surfaces in the built-output audit."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
_ORIGINAL_SYS_PATH = sys.path[:]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    SPEC = importlib.util.spec_from_file_location(
        "audit_built_identity", ROOT / "scripts" / "audit_built_identity.py"
    )
    assert SPEC and SPEC.loader
    M = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(M)  # type: ignore[union-attr]
finally:
    sys.path[:] = _ORIGINAL_SYS_PATH


class AuditBuiltIdentityTest(unittest.TestCase):
    def setUp(self):
        self.path = M.REPO / "web" / "out" / "index.html"
        self.prefix = "web/out/index.html: "

    def test_clean_surface(self):
        raw = (
            '<div data-arm-id="compiler+jev" data-model-id="nanojev_06b">'
            "nanojev 0.6b<title>nanojev 0.6b · compiler-first</title></div>"
        )

        problems, stats = M.surface_problems(self.path, raw)

        self.assertEqual(problems, [])
        self.assertEqual(stats["data-arm-id elements"], 1)
        self.assertEqual(stats["<title> elements"], 1)
        self.assertIs(stats["carries identity surfaces"], True)

    def test_missing_model_id_and_bare_label(self):
        problems, _ = M.surface_problems(
            self.path, '<div data-arm-id="compiler+jev">jev</div>'
        )

        self.assertEqual(
            problems,
            [
                self.prefix + "compiler+jev carries no data-model-id",
                self.prefix + "arm compiler+jev renders bare 'jev' as its label: 'jev'",
                self.prefix
                + "renders arm identities but no <title> carries the long nanojev name",
            ],
        )

    def test_wrong_model_id(self):
        raw = (
            '<div data-arm-id="compiler+jev" data-model-id="other">'
            "nanojev<title>nanojev</title></div>"
        )

        problems, _ = M.surface_problems(self.path, raw)

        self.assertEqual(
            problems,
            [
                self.prefix
                + "compiler+jev declares data-model-id='other', resolver says 'nanojev_06b'"
            ],
        )

    def test_model_board_name(self):
        problems, _ = M.surface_problems(
            self.path, '<td class="modelName">Jev</td>'
        )

        self.assertEqual(
            problems,
            [self.prefix + "model-board identity renders bare 'jev': 'Jev'"],
        )

    def test_lane_without_title(self):
        raw = (
            '<text class="corpusLabel" data-arm-id="compiler" '
            'data-model-id="">compiler</text>'
        )

        problems, _ = M.surface_problems(self.path, raw)

        self.assertIn(
            self.prefix + "lane compiler has no <title> with the long name", problems
        )

    def test_ladder_rungs(self):
        raw = (
            '<svg aria-label="escalation ladder"><text>compiler</text>'
            "<text>qwen</text></svg>"
        )
        problems, _ = M.surface_problems(self.path, raw)
        self.assertEqual(
            problems,
            [
                self.prefix
                + "no ladder rung names nanojev (rungs=['compiler', 'qwen'])"
            ],
        )

        with_nanojev = raw.replace("<text>qwen</text>", "<text>nanojev 0.6b</text>")
        problems, _ = M.surface_problems(self.path, with_nanojev)
        self.assertEqual(problems, [])

    def test_no_identity_surfaces_and_word_boundaries(self):
        problems, stats = M.surface_problems(
            self.path, "<p>nojev jev-like jev_x</p>"
        )

        self.assertEqual(problems, [])
        self.assertIs(stats["carries identity surfaces"], False)

    def test_attr_elements(self):
        self.assertEqual(
            M.attr_elements('<a x="1">in</a><b x="2">', "x"),
            [("1", ' x="1"', "in"), ("2", ' x="2"', "")],
        )

    def test_main_on_empty_outdirs(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(M, "OUT_DIRS", [Path(directory)]):
                with contextlib.redirect_stderr(io.StringIO()):
                    result = M.main()

        self.assertEqual(result, 2)


if __name__ == "__main__":
    unittest.main()
