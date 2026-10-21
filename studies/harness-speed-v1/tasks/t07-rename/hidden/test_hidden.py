import unittest, pathlib
import shapes.geometry as g
class H(unittest.TestCase):
    def test_old_name_gone(self): self.assertFalse(hasattr(g, "calc_area"))
    def test_no_old_refs(self):
        for p in pathlib.Path("shapes").glob("*.py"):
            self.assertNotIn("calc_area", p.read_text(), str(p))
    def test_circle(self): self.assertAlmostEqual(g.area("circle", 1), 3.14159, places=4)
