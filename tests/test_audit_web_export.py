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

    def errors_for(self, href: str) -> list[str]:
        audit = PageAudit()
        audit.hrefs.append(href)
        errors: list[str] = []
        check_relative_links("page", self.page, self.root, audit, errors)
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

    def test_in_root_path_is_not_flagged(self) -> None:
        target = self.root / "article" / "index.html"
        target.parent.mkdir()
        target.touch()

        self.assertEqual(self.errors_for("../article/"), [])


if __name__ == "__main__":
    unittest.main()
