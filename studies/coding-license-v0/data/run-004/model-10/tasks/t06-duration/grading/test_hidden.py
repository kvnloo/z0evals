import unittest
from duration import parse_duration
class H(unittest.TestCase):
    def test_all(self): self.assertEqual(parse_duration(" 1h2m3s "), 3723)
    def test_s(self): self.assertEqual(parse_duration("45s"), 45)
    def test_bad_order(self):
        with self.assertRaises(ValueError): parse_duration("3s1h")
    def test_bad_empty(self):
        with self.assertRaises(ValueError): parse_duration("")
    def test_bad_junk(self):
        with self.assertRaises(ValueError): parse_duration("1x")
    def test_bad_repeat(self):
        with self.assertRaises(ValueError): parse_duration("1h1h")
