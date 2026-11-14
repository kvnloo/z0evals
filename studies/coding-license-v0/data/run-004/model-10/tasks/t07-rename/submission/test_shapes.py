import unittest
from shapes.geometry import area
from shapes.report import describe
from shapes.batch import total
class T(unittest.TestCase):
    def test_area(self): self.assertEqual(area("square", 3), 9)
    def test_describe(self): self.assertEqual(describe("square", 2), "square area 4.00")
    def test_total(self): self.assertEqual(total([("square", 1), ("square", 2)]), 5)
if __name__ == "__main__": unittest.main()
