import unittest
from money import Money
from money.errors import CurrencyMismatch
from money.invoice import total


class T(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(Money.parse("1.005"), Money(101))

    def test_mismatch(self):
        with self.assertRaises(CurrencyMismatch):
            Money(1, "USD") + Money(1, "EUR")

    def test_allocate(self):
        self.assertEqual(Money(100).allocate([1, 1, 1]), [Money(34), Money(33), Money(33)])

    def test_invoice_per_line(self):
        self.assertEqual(total([(Money(333), 1), (Money(333), 1)], "0.5"), Money(1000))
