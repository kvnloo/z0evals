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
            "---\ntitle: t\ndate: october 5, 2026\narea: memory\ntoc:\n  - id: a\n    label: A\n---\n\n"
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

    def _build(self, front: str, body: str = "## a {#a}\n\ntext\n"):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "x.md"
            f.write_text(f"---\n{front}\n---\n\n{body}")
            return build_posts.build_post(f)

    def test_catalog_fields_and_iso_fallback(self):
        p = self._build('title: t\ndate: "updated October 5, 2026"\narea: memory\nseries: memory\nlog: [x]')
        self.assertEqual(p["published"], "2026-10-05")
        self.assertEqual(p["area"], "memory")
        self.assertEqual(p["kind"], "post")
        self.assertEqual(p["series"], "memory")
        self.assertEqual(p["log"], ["x"])
        p = self._build("title: t\ndate: whenever\npublished: 2026-09-21\narea: research\nkind: study")
        self.assertEqual((p["published"], p["kind"]), ("2026-09-21", "study"))

    def test_invalid_metadata_fails(self):
        with self.assertRaises(build_posts.PostError):
            self._build("title: t\ndate: october 5, 2026\narea: vibes")
        with self.assertRaises(build_posts.PostError):
            self._build("title: t\ndate: not a date\narea: memory")
        with self.assertRaises(build_posts.PostError):
            self._build('title: t\ndate: october 5, 2026\narea: memory\ndek: "' + "x" * 141 + '"')

    def test_long_posts_are_sectioned_at_top_level_h2(self):
        p = self._build("title: t\ndate: october 5, 2026\narea: memory", "intro\n\n## a {#a}\n\none\n\n## b {#b}\n\ntwo\n")
        self.assertEqual(p["html"].count('<section class="post-sec">'), 2)
        self.assertTrue(p["html"].startswith("<p>intro</p>"))

    def test_every_post_is_catalogued(self):
        index = []
        for path in sorted((ROOT / "posts").glob("*.md")):
            with self.subTest(post=path.name):
                p = build_posts.build_post(path)
                self.assertIn(p["area"], build_posts.AREAS)
                self.assertTrue(p["dek"] and len(p["dek"]) <= 140)
                index.append(p)
        self.assertLessEqual(sum(1 for p in index if p["featured"]), 1)

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
