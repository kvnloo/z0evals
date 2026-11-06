"""Offline evidence contract for the measured-speed post."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies/speed-measurements-v0"


class SpeedMeasurementsTest(unittest.TestCase):
    def test_measurements_recompute_and_render(self):
        self.assertTrue((STUDY / "summary.json").is_file(), "measured-speed summary is missing")
        spec = importlib.util.spec_from_file_location("speed_analysis", STUDY / "analyze.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        summary = json.loads((STUDY / "summary.json").read_text())
        self.assertEqual(module.analyze(), summary)
        self.assertEqual(summary["warm"]["count"], 12)
        self.assertEqual(summary["warm"]["warmup_excluded"], 1)
        self.assertEqual(summary["parallel"]["completed"], 401)
        self.assertEqual(summary["parallel"]["not_run"], 4599)
        self.assertGreater(summary["parallel"]["max_interval_overlap"], 1)
        self.assertNotIn("aggregate_tok_s", summary["parallel"])
        self.assertTrue(summary["wire_decode"])
        for row in summary["wire_decode"]:
            self.assertGreater(row["count"], 0)
            self.assertGreater(row["median_tok_s"], 0)
        for name in ("warm.jsonl", "wire.jsonl", "parallel.jsonl"):
            for line in (STUDY / "data" / name).read_text().splitlines():
                row = json.loads(line)
                self.assertTrue(set(row).isdisjoint({"text", "err", "stderr_tail", "rl", "system", "messages"}))
        spec = importlib.util.spec_from_file_location("build_posts", ROOT / "scripts/build_posts.py")
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        page = build.build_post(ROOT / "posts/speed-measurements-v0.md")
        self.assertIn("401", page["html"])
        self.assertIn("not independently", page["html"])
        for item in page["toc"]:
            self.assertIn(f'id="{item["id"]}"', page["html"])


if __name__ == "__main__":
    unittest.main()
