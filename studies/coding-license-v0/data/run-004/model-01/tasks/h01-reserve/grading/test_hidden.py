import unittest
from inv.store import Inventory
from inv.errors import InsufficientStock, InventoryError, UnknownSku


class H(unittest.TestCase):
    def setUp(self):
        self.i = Inventory(); self.i.add("a", 5)

    def test_subclass(self):
        self.assertTrue(issubclass(InsufficientStock, InventoryError))

    def test_accumulate_and_release(self):
        self.i.reserve("a", 2); self.i.reserve("a", 1)
        self.assertEqual(self.i.available("a"), 2)
        self.i.release("a", 3)
        self.assertEqual(self.i.available("a"), 5)

    def test_over_release(self):
        self.i.reserve("a", 1)
        with self.assertRaises(InsufficientStock):
            self.i.release("a", 2)

    def test_remove_respects_reserved(self):
        self.i.reserve("a", 3)
        self.i.remove("a", 2)
        self.assertEqual(self.i.on_hand("a"), 3)
        with self.assertRaises(InsufficientStock):
            self.i.remove("a", 1)

    def test_remove_below_zero(self):
        with self.assertRaises(InsufficientStock):
            self.i.remove("a", 6)

    def test_unknown(self):
        for call in (lambda: self.i.reserve("z", 1), lambda: self.i.release("z", 1),
                     lambda: self.i.available("z")):
            with self.assertRaises(UnknownSku):
                call()
