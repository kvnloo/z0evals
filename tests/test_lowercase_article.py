"""Regression tests for the lowercase article JSX scanner and folding pipeline."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SPEC = importlib.util.spec_from_file_location(
    "lowercase_article", SCRIPTS / "lowercase_article.py"
)
assert SPEC and SPEC.loader

# Keep sibling imports (such as arm_identity) available while loading the script,
# without leaking a changed import path into other unittest modules.
_original_sys_path = sys.path[:]
try:
    sys.path.insert(0, str(SCRIPTS))
    lowercase_article = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(lowercase_article)
finally:
    sys.path[:] = _original_sys_path


class LowercaseArticleTest(unittest.TestCase):
    def test_fold_protects_tokens(self):
        self.assertEqual(
            lowercase_article.fold("Run P1B-20260921T1430Z on Qwen3.5-4B"),
            "run p1b-20260921T1430Z on qwen3.5-4b",
        )
        self.assertEqual(lowercase_article.fold("Hello WORLD"), "hello world")

    def test_transform_folds_jsx_text_across_closing_tags(self):
        self.assertEqual(
            lowercase_article.transform("<p>Hello <strong>DEF</strong>. Without IT</p>"),
            "<p>hello <strong>def</strong>. without it</p>",
        )

    def test_transform_leaves_generics_and_code(self):
        self.assertEqual(
            lowercase_article.transform(
                "const x: Record<string, never> = {}; <p>Hi</p>"
            ),
            "const x: Record<string, never> = {}; <p>hi</p>",
        )
        self.assertEqual(lowercase_article.transform("a<br/>B"), "a<br/>B")

    def test_transform_folds_text_attrs_only(self):
        self.assertEqual(
            lowercase_article.transform(
                '<p title="Big Title" className="Foo">X</p>'
            ),
            '<p title="big title" className="Foo">x</p>',
        )

    def test_expression_verbatim_and_comments(self):
        self.assertEqual(
            lowercase_article.transform("<p>A {Foo.Bar} B</p>"),
            "<p>a {Foo.Bar} b</p>",
        )
        self.assertEqual(
            lowercase_article.transform("// Comment HERE\n<p>A</p>"),
            "// Comment HERE\n<p>a</p>",
        )
        self.assertEqual(
            lowercase_article.transform("Text <b>X</b> More", start_in_text=True),
            "text <b>x</b> more",
        )

    def test_pre_diagram_template_is_folded(self):
        self.assertEqual(
            lowercase_article.transform("<div><pre>{`DIAGRAM A`}</pre></div>"),
            "<div><pre>{`diagram a`}</pre></div>",
        )
        self.assertEqual(
            lowercase_article.transform(
                "<div><pre>{`X`}</pre><p>{`KEEP`}</p></div>"
            ),
            "<div><pre>{`x`}</pre><p>{`KEEP`}</p></div>",
        )

    def test_fold_jsx_fragments_nested(self):
        self.assertEqual(
            lowercase_article.fold_jsx_fragments("x = <>Outer <>INNER</> TAIL</>; Y"),
            "x = <>outer <>inner</> tail</>; Y",
        )
        self.assertEqual(
            lowercase_article.fold_jsx_fragments("<>Unclosed"),
            "<>Unclosed",
        )

    def test_fold_literal_sites(self):
        self.assertEqual(
            lowercase_article.fold_literal_sites(
                '{ label: "Big", other: "Keep", unit: "MS" }'
            ),
            '{ label: "big", other: "Keep", unit: "ms" }',
        )

    def test_scan_tag(self):
        self.assertEqual(lowercase_article._scan_tag('<a href="x>y">', 0), 14)
        self.assertEqual(lowercase_article._scan_tag("<a b={c>d}>", 0), 11)
        self.assertEqual(lowercase_article._scan_tag("<a", 0), 2)

    def test_pipeline_is_idempotent_on_repo_sources(self):
        def pipeline(src: str) -> str:
            return lowercase_article.fold_literal_sites(
                lowercase_article.fold_jsx_fragments(
                    lowercase_article.transform(src)
                )
            )

        paths = lowercase_article.targets()
        self.assertIn(ROOT / "web" / "app" / "page.tsx", paths)
        for path in paths:
            with self.subTest(path=str(path.relative_to(ROOT))):
                source = path.read_text(encoding="utf-8")
                once = pipeline(source)
                self.assertEqual(pipeline(once), once)


if __name__ == "__main__":
    unittest.main()
