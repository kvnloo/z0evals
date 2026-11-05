"""Offline regression tests for the legacy static-site builder."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build_site.py")
assert SPEC and SPEC.loader
build_site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_site)  # type: ignore[union-attr]


class BuildSiteTest(unittest.TestCase):
    def _temp_root(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "posts").mkdir()
        (root / "studies").mkdir()
        (root / "research-ui.js").write_text("// offline fixture\n", encoding="utf-8")
        return root

    def _build(self, root: Path) -> Path:
        out = root / "site"
        with patch.object(build_site, "ROOT", root), patch.object(build_site, "OUT", out):
            build_site.main()
        return out

    def test_split_frontmatter(self):
        self.assertEqual(build_site.split_frontmatter("no fm"), ({}, "no fm"))
        self.assertEqual(
            build_site.split_frontmatter(
                "---\ntitle: T\ntoc:\n - {id: a, label: A}\n---\n\nBody"
            ),
            ({"title": "T", "toc": [{"id": "a", "label": "A"}]}, "Body"),
        )
        self.assertEqual(build_site.split_frontmatter("---\n---\nB"), ({}, "B"))

    def test_page_escapes_and_toc(self):
        markup = build_site.page(
            "A<b>",
            "<p>x</p>",
            fm={
                "toc": [{"id": "s1", "label": "One & Two"}],
                "author": "Ann",
                "date": "2026-01-02",
            },
        )
        self.assertIn("<title>A&lt;b&gt; · z0evals</title>", markup)
        self.assertIn("<h1>A&lt;b&gt;</h1>", markup)
        self.assertIn('<p class="meta">Ann·2026-01-02</p>', markup)
        self.assertIn(
            '<ul class="toc"><li><a href="#s1">One &amp; Two</a></li></ul>',
            markup,
        )
        self.assertIn("<article><p>x</p></article>", markup)

    def test_page_defaults(self):
        markup = build_site.page("T", "b")
        self.assertNotIn('class="toc"', markup)
        self.assertIn("Zer0 Research", markup)
        # Legacy page() accepts subtitle/meta arguments but does not render them.
        markup = build_site.page("T", "b", subtitle="SUBTITLE", meta="META")
        self.assertNotIn("SUBTITLE", markup)
        self.assertNotIn("META", markup)

    def test_main_builds_into_temp_root(self):
        root = self._temp_root()
        (root / "posts" / "a.md").write_text(
            "---\ntitle: Alpha\nsubtitle: Sub\nstudy: s1\nstatus: draft\n---\n\n"
            "Body **bold**.\n",
            encoding="utf-8",
        )
        study = root / "studies" / "s1"
        (study / "data").mkdir(parents=True)
        (study / "manifest.yaml").write_text(
            "status: frozen\nupdated: '2026-02-02'\n", encoding="utf-8"
        )
        data = '{"sample": 1}\n'
        (study / "data" / "d.json").write_text(data, encoding="utf-8")
        ui = "// fixture research UI\n"
        (root / "research-ui.js").write_text(ui, encoding="utf-8")

        out = self._build(root)
        self.assertTrue((out / "posts" / "a.html").is_file())
        post = (out / "posts" / "a.html").read_text(encoding="utf-8")
        index = (out / "index.html").read_text(encoding="utf-8")
        self.assertIn("<h1>Alpha</h1>", post)
        self.assertIn('href="posts/a.html"', index)
        self.assertIn(">Alpha</a>", index)
        self.assertIn("<p>Sub</p>", index)
        self.assertIn('<span class="badge">s1</span>', index)
        self.assertTrue((out / "data" / "s1" / "d.json").is_file())
        self.assertEqual(
            (out / "data" / "s1" / "d.json").read_text(encoding="utf-8"), data
        )
        self.assertTrue((out / "research-ui.js").is_file())
        self.assertEqual((out / "research-ui.js").read_text(encoding="utf-8"), ui)

    def test_main_rebuild_removes_stale(self):
        root = self._temp_root()
        stale = root / "site" / "stale.html"
        stale.parent.mkdir()
        stale.write_text("obsolete", encoding="utf-8")
        out = self._build(root)
        self.assertFalse(stale.exists())
        self.assertTrue((out / "index.html").is_file())

    def test_main_no_posts(self):
        root = self._temp_root()
        out = self._build(root)
        index = (out / "index.html").read_text(encoding="utf-8")
        self.assertIn("No reports yet.", index)


if __name__ == "__main__":
    unittest.main()
