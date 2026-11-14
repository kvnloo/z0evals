import unittest
from decimal import Decimal
from money import Money
from money.errors import CurrencyMismatch
from money.invoice import total


class H(unittest.TestCase):
    def test_parse_more(self):
        self.assertEqual(Money.parse("-1.005"), Money(-101))
        self.assertEqual(Money.parse("2"), Money(200))
        self.assertEqual(Money.parse("0.285", "EUR"), Money(29, "EUR"))
        self.assertTrue(issubclass(CurrencyMismatch, ValueError))

    def test_allocate_more(self):
        self.assertEqual(Money(5, "EUR").allocate([3, 7]), [Money(2, "EUR"), Money(3, "EUR")])
        self.assertEqual(Money(10).allocate([1, 0, 1]), [Money(5), Money(0), Money(5)])
        parts = Money(1001).allocate([1, 2, 3, 4])
        self.assertEqual(sum(p.cents for p in parts), 1001)

    def test_invoice_more(self):
        self.assertEqual(total([], "0.1"), Money(0, "USD"))
        self.assertEqual(total([(Money(199, "EUR"), 3)], Decimal("0.0825")), Money(646, "EUR"))
        with self.assertRaises(CurrencyMismatch):
            total([(Money(1, "USD"), 1), (Money(1, "EUR"), 1)], "0")
