import os
import tempfile
import unittest
from ts.cli import main


def write(d, name, text):
    p = os.path.join(d, name)
    open(p, "w").write(text)
    return p


class T(unittest.TestCase):
    def test_top_and_ties(self):
        with tempfile.TemporaryDirectory() as d:
            f = write(d, "a.txt", "b a c b a d")
            self.assertEqual(main([f, "--top", "3"]), "a\t2\nb\t2\nc\t1")

    def test_ignore_case_and_stopwords(self):
        with tempfile.TemporaryDirectory() as d:
            f = write(d, "a.txt", "The cat the CAT a")
            s = write(d, "stop.txt", "# common\nthe\n\na\n")
            self.assertEqual(main([f, "--ignore-case", "--stopwords", s]), "cat\t2")
