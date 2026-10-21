import unittest
from pager import paginate
class T(unittest.TestCase):
    def test_first(self): self.assertEqual(paginate(list(range(10)), 1, 3), [0, 1, 2])
    def test_last(self): self.assertEqual(paginate(list(range(10)), 4, 3), [9])
if __name__ == "__main__": unittest.main()
