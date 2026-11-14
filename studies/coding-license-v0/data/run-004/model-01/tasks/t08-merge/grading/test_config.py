import unittest
from config import deep_merge
class T(unittest.TestCase):
    def test_nested(self):
        self.assertEqual(deep_merge({"a": {"x": 1, "y": 2}}, {"a": {"y": 3}}), {"a": {"x": 1, "y": 3}})
if __name__ == "__main__": unittest.main()
