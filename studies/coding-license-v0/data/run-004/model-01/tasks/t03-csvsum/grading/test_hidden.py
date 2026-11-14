import unittest
from report import total_by_category
class H(unittest.TestCase):
    def test_plain(self): self.assertEqual(total_by_category("category,amount\na,1\nb,2\na,3"), {"a": 4.0, "b": 2.0})
    def test_escaped_quote(self):
        self.assertEqual(total_by_category('category,amount\n"say ""hi""",4\n'), {'say "hi"': 4.0})
    def test_header_only(self): self.assertEqual(total_by_category("category,amount\n"), {})
