import unittest
from duration import parse_duration
class T(unittest.TestCase):
    def test_hm(self): self.assertEqual(parse_duration("1h30m"), 5400)
if __name__ == "__main__": unittest.main()
