import unittest
from calc import evaluate
from calc.errors import CalcError


class T(unittest.TestCase):
    def test_unary(self):
        self.assertEqual(evaluate("-3 + 5"), 2)

    def test_power(self):
        self.assertEqual(evaluate("-2^2"), -4)
        self.assertEqual(evaluate("2*3^2"), 18)

    def test_vars(self):
        self.assertEqual(evaluate("x * (y + 1)", {"x": 2, "y": 4}), 10)

    def test_errors(self):
        with self.assertRaises(CalcError):
            evaluate("1 / 0")
