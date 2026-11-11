import tempfile
import unittest
from pathlib import Path

from scripts.audit_web_export import PageAudit, check_relative_links


class RelativeLinkAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name) / "out"
        self.page = self.root / "nested" / "index.html"
        self.page.parent.mkdir(parents=True)
        self.page.touch()

    def errors_for(self, href: str, base: str = "") -> list[str]:
        audit = PageAudit()
        audit.hrefs.append(href)
        errors: list[str] = []
        check_relative_links("page", self.page, self.root, audit, errors, base)
        return errors

    def assert_escape_flagged(self, href: str) -> None:
        self.assertEqual(
            self.errors_for(href),
            [f"page: internal href escapes export root: {href}"],
        )

    def test_plain_parent_path_is_flagged(self) -> None:
        self.page = self.root / "index.html"
        self.page.touch()
        self.assert_escape_flagged("../outside.html")

    def test_nested_parent_path_is_flagged(self) -> None:
        self.page = self.root / "index.html"
        self.page.touch()
        self.assert_escape_flagged("a/../../outside.html")

    def test_absolute_path_is_flagged(self) -> None:
        self.assert_escape_flagged("/outside.html")

    def test_url_encoded_parent_path_is_flagged(self) -> None:
        self.page = self.root / "index.html"
        self.page.touch()
        self.assert_escape_flagged("%2e%2e/outside.html")

    def test_backslash_parent_path_is_flagged(self) -> None:
        self.page = self.root / "index.html"
        self.page.touch()
        self.assert_escape_flagged(r"..\outside.html")

    def test_directory_index_symlink_outside_root_is_flagged(self) -> None:
        outside = self.root.parent / "outside.html"
        outside.write_text("outside")
        article = self.root / "article"
        article.mkdir()
        (article / "index.html").symlink_to(outside)
        for href in ("../article/", "../article"):
            with self.subTest(href=href):
                self.assert_escape_flagged(href)

    def test_directory_index_symlink_inside_root_is_allowed(self) -> None:
        target = self.root / "target.html"
        target.write_text("inside")
        article = self.root / "article"
        article.mkdir()
        (article / "index.html").symlink_to(target)
        self.assertEqual(self.errors_for("../article/"), [])

    def test_basepath_routes_are_allowed(self) -> None:
        article = self.root / "article"
        article.mkdir()
        (article / "index.html").touch()
        for base in ("/z0evals", "/z0evals/next"):
            for suffix in ("/article/", "/article", "/%61rticle/?query=1#section"):
                with self.subTest(base=base, suffix=suffix):
                    self.assertEqual(self.errors_for(base + suffix, base), [])

    def test_basepath_escapes_are_rejected(self) -> None:
        for href in ("/z0evals-other/article/", "/outside.html",
                     "/z0evals/%2e%2e/outside.html",
                     r"/z0evals/..\outside.html"):
            with self.subTest(href=href):
                self.assertEqual(self.errors_for(href, "/z0evals"),
                                 [f"page: internal href escapes export root: {href}"])

    def test_basepath_symlinks_stay_contained(self) -> None:
        outside = self.root.parent / "outside.html"
        outside.touch()
        (self.root / "escape.html").symlink_to(outside)
        article = self.root / "article"
        article.mkdir()
        (article / "index.html").symlink_to(outside)
        for href in ("/z0evals/escape.html", "/z0evals/article/",
                     "/z0evals/article"):
            with self.subTest(href=href):
                self.assertEqual(self.errors_for(href, "/z0evals"),
                                 [f"page: internal href escapes export root: {href}"])

    def test_in_root_path_is_not_flagged(self) -> None:
        target = self.root / "article" / "index.html"
        target.parent.mkdir()
        target.touch()

        self.assertEqual(self.errors_for("../article/"), [])


if __name__ == "__main__":
    unittest.main()
