"""Tests for the legacy static-site builder."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
sys.path.insert(0, SCRIPTS)
SPEC = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build_site.py")
assert SPEC and SPEC.loader
build_site = importlib.util.module_from_spec(SPEC)
try:
    SPEC.loader.exec_module(build_site)  # type: ignore[union-attr]
finally:
    sys.path.remove(SCRIPTS)


class BuildSiteTest(unittest.TestCase):
    def setUp(self):
        self.original_root = build_site.ROOT
        self.original_out = build_site.OUT

    def tearDown(self):
        build_site.ROOT = self.original_root
        build_site.OUT = self.original_out

    def configure_temp_root(self, root: Path) -> None:
        (root / "posts").mkdir()
        (root / "studies").mkdir()
        (root / "research-ui.js").write_text("// test fixture\n", encoding="utf-8")
        build_site.ROOT = root
        build_site.OUT = root / "site"

    def test_split_frontmatter(self):
        self.assertEqual(build_site.split_frontmatter("no fm"), ({}, "no fm"))
        source = "---\ntitle: T\ntoc:\n - {id: a, label: A}\n---\n\nBody"
        self.assertEqual(
            build_site.split_frontmatter(source),
            ({"title": "T", "toc": [{"id": "a", "label": "A"}]}, "Body"),
        )
        self.assertEqual(build_site.split_frontmatter("---\n---\nB"), ({}, "B"))

    def test_page_escapes_and_toc(self):
        rendered = build_site.page(
            "A<b>",
            "<p>x</p>",
            fm={
                "toc": [{"id": "s1", "label": "One & Two"}],
                "author": "Ann",
                "date": "2026-01-02",
            },
        )
        self.assertIn("<title>A&lt;b&gt; · z0evals</title>", rendered)
        self.assertIn("<h1>A&lt;b&gt;</h1>", rendered)
        self.assertIn('<p class="meta">Ann·2026-01-02</p>', rendered)
        self.assertIn(
            '<ul class="toc"><li><a href="#s1">One &amp; Two</a></li></ul>',
            rendered,
        )
        self.assertIn("<article><p>x</p></article>", rendered)

    def test_page_defaults(self):
        rendered = build_site.page("T", "b")
        self.assertNotIn('class="toc"', rendered)
        self.assertIn("Zer0 Research", rendered)
        with_metadata = build_site.page(
            "T", "b", subtitle="Sub <b> &", meta="META <i> &"
        )
        self.assertIn('<p class="subtitle">Sub &lt;b&gt; &amp;</p>', with_metadata)
        self.assertIn('<p class="meta">META &lt;i&gt; &amp;</p>', with_metadata)
        self.assertNotIn("<b>", with_metadata)
        self.assertNotIn("<i>", with_metadata)

    def test_main_builds_into_temp_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.configure_temp_root(root)
            (root / "posts" / "a.md").write_text(
                "---\ntitle: Alpha\nsubtitle: Sub\nstudy: s1\nstatus: draft\n---\n\nBody\n",
                encoding="utf-8",
            )
            study = root / "studies" / "s1"
            (study / "data").mkdir(parents=True)
            (study / "manifest.yaml").write_text(
                "status: frozen\nupdated: '2026-02-02'\n", encoding="utf-8"
            )
            (study / "data" / "d.json").write_text('{"value": 1}\n', encoding="utf-8")

            build_site.main()

            post = (root / "site" / "posts" / "a.html").read_text(encoding="utf-8")
            self.assertIn("<h1>Alpha</h1>", post)
            self.assertIn('<p class="subtitle">Sub</p>', post)
            self.assertIn(
                '<p class="meta">study=s1 · status=frozen · updated=2026-02-02</p>', post
            )
            index = (root / "site" / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="posts/a.html"', index)
            self.assertIn("Alpha", index)
            self.assertIn("Sub", index)
            self.assertIn('<span class="badge">s1</span>', index)
            self.assertTrue((root / "site" / "data" / "s1" / "d.json").is_file())
            self.assertTrue((root / "site" / "research-ui.js").is_file())

    def test_main_rebuild_removes_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.configure_temp_root(root)
            (root / "site").mkdir()
            stale = root / "site" / "stale.html"
            stale.write_text("stale", encoding="utf-8")

            build_site.main()

            self.assertFalse(stale.exists())

    def test_main_no_posts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.configure_temp_root(root)

            build_site.main()

            index = (root / "site" / "index.html").read_text(encoding="utf-8")
            self.assertIn("No reports yet.", index)


if __name__ == "__main__":
    unittest.main()
