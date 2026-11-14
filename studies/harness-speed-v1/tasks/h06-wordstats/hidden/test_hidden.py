import os
import tempfile
import unittest
from ts.cli import main
from ts.words import words


def write(d, name, text):
    p = os.path.join(d, name)
    open(p, "w").write(text)
    return p


class H(unittest.TestCase):
    def test_apostrophes(self):
        self.assertEqual(words("'tis don't 'quoted' ''"), ["tis", "don't", "quoted"])

    def test_case_sensitive_stopwords(self):
        with tempfile.TemporaryDirectory() as d:
            f = write(d, "a.txt", "The the x")
            s = write(d, "s.txt", "the\n")
            self.assertEqual(main([f, "--stopwords", s]), "The\t1\nx\t1")

    def test_min_length_default_top(self):
        with tempfile.TemporaryDirectory() as d:
            f = write(d, "a.txt", " ".join(f"w{chr(97 + i)}" for i in range(12)) + " a bb bb")
            out = main([f, "--min-length", "2"]).splitlines()
            self.assertEqual(len(out), 10)
            self.assertEqual(out[0], "bb\t2")
            self.assertNotIn("a\t1", out)
