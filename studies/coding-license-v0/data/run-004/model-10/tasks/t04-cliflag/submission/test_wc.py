import io, unittest
from wc import main
class T(unittest.TestCase):
    def test_top(self): self.assertEqual(main(["--top", "2"], io.StringIO("b a a c c c")), "c 3\na 2")
    def test_min(self): self.assertEqual(main(["--min-count", "2"], io.StringIO("b a a c c c")), "c 3\na 2")
if __name__ == "__main__": unittest.main()
