import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CuaStatusTests(unittest.TestCase):
    def test_offline_uses_snapshot_and_says_so(self):
        status = load("build_cua_status")
        text = status.build(offline=True)
        self.assertIn("upstream prs merged into trycua/cua | 7", text)
        self.assertIn("show the 2026-10-26 snapshot", text)
        self.assertEqual(sum("5338" in line for line in text.splitlines()), 1)  # credited once, never counted as ours

    def test_live_failure_falls_back_per_item(self):
        status = load("build_cua_status")
        with patch.object(status, "fetch_state", return_value=None):
            text = status.build()
        self.assertIn("snapshot", text)

    def test_post_splices_generated_block_or_keeps_snapshot(self):
        posts = load("build_posts")
        body = "a\n<!-- generated:demo -->\nold\n<!-- /generated:demo -->\nb\n"
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(posts, "GENERATED", Path(temp)):
                self.assertIn("old", posts.splice_generated(body))
                (Path(temp) / "demo.md").write_text("fresh\n")
                spliced = posts.splice_generated(body)
        self.assertIn("fresh", spliced)
        self.assertNotIn("old", spliced)


if __name__ == "__main__":
    unittest.main()
