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

    def _build(self, src: str) -> dict:
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "x.md"
            f.write_text(src)
            return build_posts.build_post(f)

    def test_tldr_front_matter_is_rendered_and_optional(self):
        p = self._build("---\ntitle: t\ntldr: |\n  the view was **smaller**.\n---\n\nbody\n")
        self.assertEqual(p["tldr"], "<p>the view was <strong>smaller</strong>.</p>")
        self.assertNotIn("smaller", p["html"])
        self.assertEqual(self._build("---\ntitle: t\n---\n\nbody\n")["tldr"], "")

    def test_setup_block_folds_onto_the_next_table(self):
        p = self._build(
            "---\ntitle: t\n---\n\nbefore\n\n```setup\neight **synthetic** docs.\n```\n"
            "| x | y |\n|---|---|\n| 1 | 2 |\n\nafter\n"
        )
        html = p["html"]
        self.assertIn('<figure class="es-fig es-wide has-setup"><details class="es-setup"><summary>setup</summary>', html)
        self.assertIn('<div class="es-setup-body"><p>eight <strong>synthetic</strong> docs.</p></div></details>', html)
        self.assertIn('</details><div class="table-wrap"><table>', html)
        self.assertIn("</table></div></figure>", html)
        self.assertLess(html.index("before"), html.index("<figure"))
        self.assertLess(html.index("</figure>"), html.index("after"))
        self.assertNotIn("<code>", html)
        self.assertNotIn("es-setup-slot", html)

    def test_setup_block_takes_a_whole_code_fence_or_figure(self):
        fence = self._build("---\ntitle: t\n---\n\n```setup\nhow\n```\n\n```text\na\n\nb\n```\n\nafter\n")["html"]
        self.assertIn("<pre><code class=\"language-text\">a\n\nb\n</code></pre></figure>", fence)
        fig = self._build("---\ntitle: t\n---\n\n```setup\nhow\n```\n<figure>\n<img src=\"a.png\">\n\n<figcaption>c</figcaption>\n</figure>\n\nafter\n")["html"]
        self.assertIn("<figcaption>c</figcaption>\n</figure></figure>", fig)

    def test_setup_block_without_a_figure_is_an_error(self):
        with self.assertRaises(ValueError):
            self._build("---\ntitle: t\n---\n\n```setup\nhow\n```\n")

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
