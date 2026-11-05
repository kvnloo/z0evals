"""Regression tests for the semantic identity checks in built HTML.

These tests use synthetic markup only; no built site or user configuration is
required. Run with python -m unittest discover -s tests -p
'test_audit_built_identity.py' -v.
"""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

# The audited script imports arm_identity. Keep its import-time sys.path
# mutation local to this load so other tests see their original path.
_PATH_BEFORE_IMPORT = sys.path[:]
try:
    sys.path.insert(0, str(SCRIPTS))
    SPEC = importlib.util.spec_from_file_location(
        "audit_built_identity", ROOT / "scripts" / "audit_built_identity.py"
    )
    if SPEC is None or SPEC.loader is None:
        raise ImportError("could not load scripts/audit_built_identity.py")
    M = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(M)
finally:
    sys.path[:] = _PATH_BEFORE_IMPORT

p = M.REPO / "web" / "out" / "index.html"
PREFIX = "web/out/index.html: "


class AuditBuiltIdentityTests(unittest.TestCase):
    def test_clean_surface(self):
        raw = (
            '<div data-arm-id="compiler+jev" data-model-id="nanojev_06b">'
            'nanojev 0.6b<title>nanojev 0.6b · compiler-first</title></div>'
        )
        problems, stats = M.surface_problems(p, raw)
        self.assertEqual(problems, [])
        self.assertEqual(stats, {
            "data-arm-id elements": 1,
            "model-board name cells": 0,
            "identity-bearing chart lanes": 0,
            "ladder rung labels": 0,
            "<title> elements": 1,
            "carries identity surfaces": True,
        })

    def test_missing_model_id_and_bare_label(self):
        problems, stats = M.surface_problems(
            p, '<div data-arm-id="compiler+jev">jev</div>'
        )
        self.assertEqual(problems, [
            PREFIX + "compiler+jev carries no data-model-id",
            PREFIX + "arm compiler+jev renders bare 'jev' as its label: 'jev'",
            PREFIX + "renders arm identities but no <title> carries the long nanojev name",
        ])
        self.assertEqual(stats["data-arm-id elements"], 1)
        self.assertEqual(stats["<title> elements"], 0)

    def test_wrong_model_id(self):
        raw = (
            '<div data-arm-id="compiler+jev" data-model-id="other">'
            'nanojev 0.6b<title>nanojev 0.6b · compiler-first</title></div>'
        )
        problems, stats = M.surface_problems(p, raw)
        self.assertEqual(problems, [
            PREFIX + "compiler+jev declares data-model-id='other', resolver says 'nanojev_06b'",
        ])
        self.assertEqual(stats["data-arm-id elements"], 1)

    def test_model_board_name(self):
        problems, stats = M.surface_problems(
            p, '<td class="modelName">Jev</td>'
        )
        self.assertEqual(problems, [
            PREFIX + "model-board identity renders bare 'jev': 'Jev'",
        ])
        self.assertEqual(stats["model-board name cells"], 1)

    def test_lane_without_title(self):
        raw = (
            '<text class="corpusLabel" data-arm-id="compiler" '
            'data-model-id="">compiler</text>'
        )
        problems, stats = M.surface_problems(p, raw)
        self.assertEqual(problems, [
            PREFIX + "lane compiler has no <title> with the long name",
            PREFIX + "renders arm identities but no <title> carries the long nanojev name",
        ])
        self.assertEqual(stats["identity-bearing chart lanes"], 1)
        self.assertEqual(stats["carries identity surfaces"], True)

    def test_ladder_rungs(self):
        without_nanojev = (
            '<svg aria-label="escalation ladder">'
            '<text>compiler</text><text>qwen</text></svg>'
        )
        problems, stats = M.surface_problems(p, without_nanojev)
        self.assertEqual(problems, [
            PREFIX + "no ladder rung names nanojev (rungs=['compiler', 'qwen'])",
        ])
        self.assertEqual(stats["ladder rung labels"], 2)

        with_nanojev = (
            '<svg aria-label="escalation ladder">'
            '<text>compiler</text><text>nanojev 0.6b</text></svg>'
        )
        problems, stats = M.surface_problems(p, with_nanojev)
        self.assertEqual(problems, [])
        self.assertEqual(stats["ladder rung labels"], 2)

    def test_no_identity_surfaces_and_word_boundaries(self):
        raw = "<p>nojev jev-like jev_x</p>"
        problems, stats = M.surface_problems(p, raw)
        self.assertEqual(problems, [])
        self.assertEqual(stats, {
            "data-arm-id elements": 0,
            "model-board name cells": 0,
            "identity-bearing chart lanes": 0,
            "ladder rung labels": 0,
            "<title> elements": 0,
            "carries identity surfaces": False,
        })
        self.assertIsNone(M.BARE_JEVE.search("nojev jev-like jev_x"))
        self.assertEqual(M.BARE_JEVE.findall("jev"), ["jev"])

    def test_attr_elements(self):
        self.assertEqual(
            M.attr_elements('<a x="1">in</a><b x="2">', "x"),
            [("1", ' x="1"', "in"), ("2", ' x="2"', "")],
        )

    def test_main_on_empty_outdirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with mock.patch.object(M, "OUT_DIRS", [Path(tmp)]):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    result = M.main()

        self.assertIsInstance(result, int)
        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(
            stderr.getvalue(),
            "no built output found; run the Next build first\n",
        )


if __name__ == "__main__":
    unittest.main()
