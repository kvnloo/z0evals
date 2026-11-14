import unittest
from calc import evaluate
from calc.errors import CalcError


class H(unittest.TestCase):
    def test_assoc(self):
        self.assertEqual(evaluate("2^3^2"), 512)
        self.assertEqual(evaluate("2^-1"), 0.5)
        self.assertEqual(evaluate("-(1+2)^2"), -9)
        self.assertEqual(evaluate("2*-3"), -6)
        self.assertEqual(evaluate("--4"), 4)
        self.assertEqual(evaluate("+4 - -1"), 5)

    def test_names(self):
        self.assertEqual(evaluate("rate_2 ^ 2", {"rate_2": 3}), 9)
        with self.assertRaises(CalcError):
            evaluate("nope + 1", {})

    def test_bad(self):
        for e in ("1 2", "(1 + 2", "1 +", ")"):
            with self.assertRaises(CalcError, msg=e):
                evaluate(e)
