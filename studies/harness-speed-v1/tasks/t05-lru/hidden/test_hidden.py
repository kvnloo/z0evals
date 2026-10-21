import unittest
from lru import LRUCache
class H(unittest.TestCase):
    def test_update_refreshes(self):
        c = LRUCache(2); c.put(1, 1); c.put(2, 2); c.put(1, 10); c.put(3, 3)
        self.assertEqual(c.get(2), -1); self.assertEqual(c.get(1), 10); self.assertEqual(len(c), 2)
    def test_bad(self):
        with self.assertRaises(ValueError): LRUCache(0)
    def test_one(self):
        c = LRUCache(1); c.put("a", 1); c.put("b", 2); self.assertEqual(c.get("a"), -1); self.assertEqual(c.get("b"), 2)
