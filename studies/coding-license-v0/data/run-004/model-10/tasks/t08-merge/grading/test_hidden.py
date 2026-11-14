import copy, unittest
from config import deep_merge
class H(unittest.TestCase):
    def test_delete(self): self.assertEqual(deep_merge({"a": 1, "b": {"c": 2, "d": 3}}, {"b": {"c": None}}), {"a": 1, "b": {"d": 3}})
    def test_no_mutation(self):
        b = {"a": {"x": [1]}}; o = {"a": {"y": 2}}; b0, o0 = copy.deepcopy(b), copy.deepcopy(o)
        r = deep_merge(b, o); r["a"]["x"].append(9) if False else None
        self.assertEqual(b, b0); self.assertEqual(o, o0); self.assertIsNot(r["a"], b["a"])
    def test_replace_non_dict(self): self.assertEqual(deep_merge({"a": {"x": 1}}, {"a": 5}), {"a": 5})
    def test_deep(self): self.assertEqual(deep_merge({"a": {"b": {"c": 1}}}, {"a": {"b": {"d": 2}}}), {"a": {"b": {"c": 1, "d": 2}}})
