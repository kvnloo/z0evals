import unittest
from pager import paginate
class H(unittest.TestCase):
    def test_past_end(self): self.assertEqual(paginate([1, 2], 3, 2), [])
    def test_bad_page(self):
        with self.assertRaises(ValueError): paginate([1], 0, 2)
    def test_bad_per_page(self):
        with self.assertRaises(ValueError): paginate([1], 1, 0)
    def test_middle(self): self.assertEqual(paginate(list("abcdefg"), 2, 3), ["d", "e", "f"])
