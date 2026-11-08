"""Unit tests for the deterministic component-data helpers."""
from __future__ import annotations

import importlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _load_script(name: str):
    """Load a scripts module while leaving the process import path unchanged."""
    original_path = sys.path[:]
    try:
        sys.path.insert(0, str(SCRIPTS))
        # build_component_data imports this lazily, so make it available after
        # the scripts directory has been removed from sys.path again.
        importlib.import_module("arm_identity")
        spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = original_path


build_component_data = _load_script("build_component_data")
build_site_data = _load_script("build_site_data")
arm_identity = sys.modules["arm_identity"]


class BuildComponentDataTest(unittest.TestCase):
    def test_wilson_values(self):
        expected = {
            (0, 0): (0.0, 0.0),
            (5, 10): (0.2365895936154873, 0.7634104063845127),
            (10, 10): (0.7224598312333834, 1.0),
            (0, 10): (0.0, 0.2775401687666165),
        }
        for args, interval in expected.items():
            with self.subTest(k=args[0], n=args[1]):
                actual = build_component_data._wilson(*args)
                self.assertAlmostEqual(actual[0], interval[0], places=9)
                self.assertAlmostEqual(actual[1], interval[1], places=9)

        for k in range(21):
            with self.subTest(k=k, n=20):
                low, high = build_component_data._wilson(k, 20)
                self.assertGreaterEqual(low, 0.0)
                self.assertLessEqual(low, 1.0)
                self.assertGreaterEqual(high, 0.0)
                self.assertLessEqual(high, 1.0)

    def test_wilson_matches_build_site_data(self):
        for k, n in ((3, 7), (28, 28), (1, 84)):
            with self.subTest(k=k, n=n):
                component = build_component_data._wilson(k, n)
                site = build_site_data.wilson(k, n)
                self.assertAlmostEqual(component[0], site[0], places=15)
                self.assertAlmostEqual(component[1], site[1], places=15)

    def test_jitter_deterministic(self):
        first = build_component_data._jitter("r", "s", "a", 1)
        self.assertAlmostEqual(first, -0.1274588259153822)
        self.assertEqual(first, build_component_data._jitter("r", "s", "a", 1.0))
        self.assertAlmostEqual(
            build_component_data._jitter("r", "s", "a", 2),
            0.17410813397181302,
        )
        self.assertEqual(build_component_data._jitter("r", "s", "a", 1, spread=0.0), 0.0)

    def test_jitter_range(self):
        default_offsets = [
            build_component_data._jitter(f"run-{i}", f"state-{i % 28}", f"arm-{i % 11}", i % 3)
            for i in range(500)
        ]
        unit_offsets = [
            build_component_data._jitter(
                f"run-{i}", f"state-{i % 28}", f"arm-{i % 11}", i % 3, spread=1.0
            )
            for i in range(500)
        ]
        self.assertLessEqual(max(map(abs, default_offsets)), 0.34)
        self.assertLessEqual(max(map(abs, unit_offsets)), 1.0)
        self.assertEqual(len(default_offsets), 500)

    def test_label_delegates(self):
        expected = "nanojev 0.6b · compiler-first"
        self.assertEqual(build_component_data._label("compiler+jev"), expected)
        self.assertEqual(build_component_data._label("compiler+jev"), arm_identity.long("compiler+jev"))

    def test_load_skips_blank_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observations.jsonl"
            path.write_text('{"a":1}\n\n  \n{"a":2}\n', encoding="utf-8")
            self.assertEqual(build_component_data._load(path), [{"a": 1}, {"a": 2}])

    def test_constants(self):
        self.assertEqual(build_component_data.BUDGET_MS, 4000.0)
        self.assertEqual(build_component_data.FROZEN_UTILITY, -1.0)


if __name__ == "__main__":
    unittest.main()
