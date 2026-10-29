"""Hermetic regression coverage for the shipped HTML export audit."""
from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_web_export", ROOT / "scripts" / "audit_web_export.py"
)
assert SPEC is not None and SPEC.loader is not None
audit_web_export = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_web_export)


def parse_html(html: str) -> audit_web_export.PageAudit:
    audit = audit_web_export.PageAudit()
    audit.feed(html)
    audit.close()
    return audit


class WebExportAuditTests(unittest.TestCase):
    def test_page_audit_collects(self) -> None:
        audit = parse_html(
            '<nav class="toc toc-sidebar">'
            '<a href="#b">B</a><a href="#a">A</a>'
            '</nav><h2 id="a"></h2><h2 id="b"></h2>'
            '<button aria-controls="menu x"></button>'
            '<a href="#zz">z</a><a href="/abs">r</a>'
            '<a href="https://e.x">e</a>'
        )

        self.assertEqual(audit.ids, ["a", "b"])
        self.assertEqual(audit.fragment_hrefs, ["b", "a", "zz"])
        self.assertEqual(audit.desktop_toc_hrefs, ["b", "a"])
        self.assertEqual(audit.aria_controls, ["menu", "x"])
        self.assertEqual(
            audit.hrefs, ["#b", "#a", "#zz", "/abs", "https://e.x"]
        )

    def test_check_ids_and_aria(self) -> None:
        duplicate = parse_html(
            '<h2 id="a"></h2><h2 id="b"></h2><span id="a"></span>'
            '<button aria-controls="menu x"></button>'
        )
        errors: list[str] = []
        audit_web_export.check_ids_and_aria("p", duplicate, errors)
        self.assertEqual(
            errors,
            [
                "p: duplicate ids: a",
                "p: aria-controls without targets: menu, x",
            ],
        )

        clean = parse_html(
            '<main id="a"><button aria-controls="menu x"></button>'
            '<div id="menu"></div><div id="x"></div></main>'
        )
        errors = []
        audit_web_export.check_ids_and_aria("p", clean, errors)
        self.assertEqual(errors, [])

    def test_check_fragments(self) -> None:
        audit = parse_html('<h2 id="a"></h2><a href="#zz">missing</a>')
        errors: list[str] = []
        audit_web_export.check_fragments("p", audit, errors)
        self.assertEqual(errors, ["p: fragment links without targets: zz"])

        errors = []
        audit_web_export.check_fragments(
            "p", parse_html('<h2 id="a"></h2><a href="#a">present</a>'), errors
        )
        self.assertEqual(errors, [])

    def test_check_toc_order(self) -> None:
        reversed_toc = parse_html(
            '<nav class="toc toc-sidebar">'
            '<a href="#b">B</a><a href="#a">A</a></nav>'
            '<h2 id="a"></h2><h2 id="b"></h2>'
        )
        errors: list[str] = []
        audit_web_export.check_toc_order("p", reversed_toc, errors)
        self.assertEqual(
            errors,
            ["p: desktop TOC order does not match document order: b -> a"],
        )

        ordered_toc = parse_html(
            '<nav class="toc toc-sidebar">'
            '<a href="#a">A</a><a href="#b">B</a></nav>'
            '<h2 id="a"></h2><h2 id="b"></h2>'
        )
        errors = []
        audit_web_export.check_toc_order("p", ordered_toc, errors)
        self.assertEqual(errors, [])

        errors = []
        audit_web_export.check_toc_order(
            "p", parse_html('<h2 id="a"></h2><h2 id="b"></h2>'), errors
        )
        self.assertEqual(errors, [])

    def test_check_story_page(self) -> None:
        missing_prose = parse_html(
            '<article class="article-body"></article><div class="prose"></div>'
            '<a href="/abs">internal</a><a href="//cdn.x/a">cdn</a>'
        )
        errors: list[str] = []
        audit_web_export.check_story_page("p", missing_prose, errors)
        self.assertEqual(
            errors,
            [
                "p: StoryShell article is missing the prose styling class",
                "p: root-absolute internal anchors escape the project Pages site: /abs",
            ],
        )

        clean = parse_html(
            '<article class="article-body prose">'
            '<a href="//cdn.x/a">cdn</a></article>'
        )
        errors = []
        audit_web_export.check_story_page("p", clean, errors)
        self.assertEqual(errors, [])

    def test_check_relative_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "export"
            (root / "sub").mkdir(parents=True)
            page = root / "index.html"
            page.write_text("<h1>Index</h1>", encoding="utf-8")
            (root / "sub" / "index.html").write_text(
                "<h1>Sub</h1>", encoding="utf-8"
            )

            valid_hrefs = (
                "sub/",
                "sub",
                "sub/index.html?x#y",
                "#frag",
                "mailto:a@b",
                "https://e.x",
                "/abs",
            )
            valid = parse_html(
                "".join(f'<a href="{href}">link</a>' for href in valid_hrefs)
            )
            errors: list[str] = []
            audit_web_export.check_relative_links("p", page, root, valid, errors)
            self.assertEqual(errors, [])

            missing = parse_html('<a href="missing.html">missing</a>')
            errors = []
            audit_web_export.check_relative_links("p", page, root, missing, errors)
            self.assertEqual(
                errors, ["p: internal href has no exported target: missing.html"]
            )

    def test_relative_link_escaping_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "export"
            root.mkdir()
            page = root / "index.html"
            page.write_text("<h1>Index</h1>", encoding="utf-8")

            escaping = parse_html('<a href="../out.html">escape</a>')
            errors: list[str] = []
            audit_web_export.check_relative_links("p", page, root, escaping, errors)
            self.assertEqual(
                errors, ["p: internal href escapes export root: ../out.html"]
            )

    def test_main_missing_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = io.StringIO()
            with patch.object(sys, "argv", ["x", "--root", temp]):
                with redirect_stdout(output):
                    result = audit_web_export.main()

        self.assertEqual(result, 1)
        self.assertIn("phase1b: missing exported page", output.getvalue())


if __name__ == "__main__":
    unittest.main()
