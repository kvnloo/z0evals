import unittest
from slug import slugify
class H(unittest.TestCase):
    def test_accents(self): self.assertEqual(slugify("Crème Brûlée"), "creme-brulee")
    def test_runs(self): self.assertEqual(slugify("  a -- b__c  "), "a-b-c")
    def test_digits(self): self.assertEqual(slugify("Top 10 Tips"), "top-10-tips")
    def test_empty(self): self.assertEqual(slugify("!!!"), "n-a")
