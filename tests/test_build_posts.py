"""Every posts/*.md must prerender into the page data the site serves."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_posts", ROOT / "scripts" / "build_posts.py")
assert SPEC and SPEC.loader
build_posts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_posts)  # type: ignore[union-attr]


class BuildPostsTest(unittest.TestCase):
    def test_every_post_has_title_toc_and_body(self):
        posts = sorted((ROOT / "posts").glob("*.md"))
        self.assertGreater(len(posts), 0)
        for path in posts:
            with self.subTest(post=path.name):
                p = build_posts.build_post(path)
                self.assertTrue(p["title"] and p["title"] != path.stem, "frontmatter title missing")
                self.assertTrue(p["html"].strip())
                for item in p["toc"]:
                    self.assertIn(f'id="{item["id"]}"', p["html"], f"toc anchor {item['id']} has no heading")

    def test_heading_ids_lede_and_wide_tables(self):
        src = (
            "---\ntitle: t\ntoc:\n  - id: a\n    label: A\n---\n\n"
            '<div class="lede">\nthe **lede**\n</div>\n\n## first *thing* {#a}\n\n| x | y |\n|---|---|\n| 1 | 2 |\n'
        )
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "x.md"
            f.write_text(src)
            p = build_posts.build_post(f)
        self.assertEqual(p["lede"], "the lede")
        self.assertIn('<h2 id="a">first <em>thing</em></h2>', p["html"])
        self.assertIn('<div class="table-wrap"><table>', p["html"])
        self.assertNotIn('class="lede"', p["html"])
        self.assertEqual(p["toc"], [{"id": "a", "label": "A"}])

    def test_research_log_entries_are_complete(self):
        doc = json.loads((ROOT / "web" / "data" / "research-log.json").read_text())
        posts = {p.stem for p in (ROOT / "posts").glob("*.md")}
        ids = [e["id"] for e in doc["entries"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate entry ids")
        for e in doc["entries"]:
            with self.subTest(entry=e["id"]):
                for k in ("title", "area", "question", "status", "date", "finding", "caveat", "links"):
                    self.assertIn(k, e)
                if e.get("post"):
                    self.assertIn(e["post"], posts, "entry links a post that does not exist")
                for link in e["links"]:
                    self.assertTrue(link["url"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()
