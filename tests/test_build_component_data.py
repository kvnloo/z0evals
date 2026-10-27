"""Regression tests for deterministic component-figure helper functions."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

SPEC = importlib.util.spec_from_file_location(
    "build_component_data", SCRIPTS / "build_component_data.py"
)
assert SPEC and SPEC.loader
build_component_data = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_component_data)

SITE_SPEC = importlib.util.spec_from_file_location(
    "build_site_data", SCRIPTS / "build_site_data.py"
)
assert SITE_SPEC and SITE_SPEC.loader
build_site_data = importlib.util.module_from_spec(SITE_SPEC)
SITE_SPEC.loader.exec_module(build_site_data)


class BuildComponentDataTest(unittest.TestCase):
    def test_wilson_values(self):
        self.assertEqual(build_component_data._wilson(0, 0), (0.0, 0.0))
        cases = (
            (5, 10, (0.2365895936154873, 0.7634104063845127)),
            (10, 10, (0.7224598312333834, 1.0)),
            (0, 10, (0.0, 0.2775401687666165)),
        )
        for k, n, expected in cases:
            with self.subTest(k=k, n=n):
                actual = build_component_data._wilson(k, n)
                self.assertEqual(len(actual), 2)
                for value, expected_value in zip(actual, expected):
                    self.assertAlmostEqual(value, expected_value, places=9)

        for k in range(21):
            with self.subTest(k=k, n=20):
                lower, upper = build_component_data._wilson(k, 20)
                self.assertLessEqual(lower, upper)
                for bound in (lower, upper):
                    self.assertGreaterEqual(bound, 0.0)
                    self.assertLessEqual(bound, 1.0)

    def test_wilson_matches_build_site_data(self):
        for k, n in ((3, 7), (28, 28), (1, 84)):
            with self.subTest(k=k, n=n):
                actual = build_component_data._wilson(k, n)
                expected = build_site_data.wilson(k, n)
                for value, reference_value in zip(actual, expected):
                    self.assertAlmostEqual(value, reference_value, places=9)

    def test_jitter_deterministic(self):
        jitter = build_component_data._jitter
        self.assertAlmostEqual(
            jitter("r", "s", "a", 1), -0.1274588259153822, places=9
        )
        self.assertEqual(jitter("r", "s", "a", 1), jitter("r", "s", "a", 1.0))
        self.assertAlmostEqual(
            jitter("r", "s", "a", 2), 0.17410813397181302, places=9
        )
        self.assertEqual(jitter("r", "s", "a", 1, spread=0.0), 0.0)

    def test_jitter_range(self):
        for i in range(500):
            run_id = f"run-{i // 100}"
            state_id = f"state-{i % 100}"
            arm = f"arm-{i % 17}"
            rep = i % 5
            with self.subTest(i=i):
                self.assertLessEqual(
                    abs(build_component_data._jitter(run_id, state_id, arm, rep)),
                    0.34,
                )
                self.assertLessEqual(
                    abs(
                        build_component_data._jitter(
                            run_id, state_id, arm, rep, spread=1.0
                        )
                    ),
                    1.0,
                )

    def test_label_delegates(self):
        # _label imports arm_identity lazily; make scripts importable only
        # during this test, then restore sys.path and the module cache.
        with (
            mock.patch.object(sys, "path", [str(SCRIPTS), *sys.path]),
            mock.patch.dict(sys.modules),
        ):
            import arm_identity

            actual = build_component_data._label("compiler+jev")
            self.assertEqual(actual, "nanojev 0.6b · compiler-first")
            self.assertEqual(actual, arm_identity.long("compiler+jev"))

    def test_load_skips_blank_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "observations.jsonl"
            path.write_text('{"a":1}\n\n  \n{"a":2}\n', encoding="utf-8")
            self.assertEqual(
                build_component_data._load(path), [{"a": 1}, {"a": 2}]
            )

    def test_constants(self):
        self.assertEqual(build_component_data.BUDGET_MS, 4000.0)
        self.assertEqual(build_component_data.FROZEN_UTILITY, -1.0)


if __name__ == "__main__":
    unittest.main()
