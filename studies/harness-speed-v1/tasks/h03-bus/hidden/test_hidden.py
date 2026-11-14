import unittest
from bus import Bus
from bus.errors import PublishError
from bus.match import matches


class H(unittest.TestCase):
    def test_matches(self):
        self.assertTrue(matches("a.#", "a.b"))
        self.assertTrue(matches("a.#", "a.b.c"))
        self.assertFalse(matches("a.#", "a"))
        self.assertTrue(matches("*.b", "x.b"))
        self.assertFalse(matches("a.*", "a"))
        self.assertTrue(matches("a.b", "a.b"))
        self.assertFalse(matches("a.b", "a.c"))

    def test_ties_and_cancel(self):
        b, seen = Bus(), []
        s1 = b.subscribe("x.#", lambda t, p: seen.append(1))
        b.subscribe("x.y", lambda t, p: seen.append(2))
        b.subscribe("x.*", lambda t, p: seen.append(3), priority=-1)
        self.assertEqual(b.publish("x.y", None), 3)
        self.assertEqual(seen, [1, 2, 3])
        s1.cancel(); s1.cancel()
        self.assertEqual(b.publish("x.y"), 2)

    def test_payload_and_zero(self):
        b, got = Bus(), []
        b.subscribe("p", lambda t, p: got.append((t, p)))
        b.publish("p", {"k": 1})
        self.assertEqual(got, [("p", {"k": 1})])
        self.assertEqual(b.publish("nobody"), 0)

    def test_error_order(self):
        b = Bus()
        def e1(t, p): raise ValueError("1")
        def e2(t, p): raise TypeError("2")
        b.subscribe("a", e2)
        b.subscribe("a", e1, priority=3)
        with self.assertRaises(PublishError) as cm:
            b.publish("a")
        self.assertEqual([type(e) for e in cm.exception.errors], [ValueError, TypeError])
