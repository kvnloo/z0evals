import unittest
from inv.store import Inventory
from inv.errors import InsufficientStock
from inv.report import summary


class T(unittest.TestCase):
    def test_reserve_reduces_available(self):
        i = Inventory(); i.add("a", 5); i.reserve("a", 2)
        self.assertEqual(i.available("a"), 3)
        self.assertEqual(i.on_hand("a"), 5)

    def test_over_reserve(self):
        i = Inventory(); i.add("a", 1)
        with self.assertRaises(InsufficientStock):
            i.reserve("a", 2)

    def test_report(self):
        i = Inventory(); i.add("b", 4); i.add("a", 2); i.reserve("b", 1)
        self.assertEqual(summary(i), "sku,on_hand,reserved,available\na,2,0,2\nb,4,1,3")
