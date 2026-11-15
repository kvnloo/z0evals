import unittest
from scripts.audit_web_export import PageAudit


class TocScopeTests(unittest.TestCase):
    def test_void_elements_do_not_extend_toc_scope(self) -> None:
        from scripts.audit_web_export import check_toc_order
        audit = PageAudit()
        audit.feed('<h2 id="first">First</h2><h2 id="second">Second</h2>'
                   '<nav class="toc toc-sidebar"><a href="#second">Second<br>line</a></nav>'
                   '<a href="#first">Back to first</a>')
        self.assertEqual(audit.desktop_toc_hrefs, ["second"])
        errors = []
        check_toc_order("page", audit, errors)
        self.assertEqual(errors, [])

    def test_self_closing_void_elements_do_not_end_toc_early(self) -> None:
        from scripts.audit_web_export import check_toc_order
        for void in ('<br/>', '<img src="icon.png"/>', '<hr/>'):
            with self.subTest(void=void):
                audit = PageAudit()
                audit.feed('<h2 id="first"></h2><h2 id="second"></h2>'
                           '<nav class="toc toc-sidebar">' + void +
                           '<a href="#second">Second</a><a href="#first">First</a></nav>'
                           '<a href="#outside">Outside</a>')
                self.assertEqual(audit.desktop_toc_hrefs, ["second", "first"])
                errors = []
                check_toc_order("page", audit, errors)
                self.assertEqual(errors, [
                    "page: desktop TOC order does not match document order: second -> first"
                ])

