import io, unittest
from wc import main
class H(unittest.TestCase):
    def test_min_and_top(self): self.assertEqual(main(["--min-count", "2", "--top", "1"], io.StringIO("x y y z z z")), "z 3")
    def test_min_none(self): self.assertEqual(main(["--min-count", "5"], io.StringIO("x y")), "")
    def test_default(self): self.assertEqual(main([], io.StringIO("q q r")), "q 2\nr 1")
