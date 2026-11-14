import unittest
from lru import LRUCache
class T(unittest.TestCase):
    def test_evict(self):
        c = LRUCache(2); c.put(1, "a"); c.put(2, "b"); c.get(1); c.put(3, "c")
        self.assertEqual(c.get(2), -1); self.assertEqual(c.get(1), "a")
if __name__ == "__main__": unittest.main()
