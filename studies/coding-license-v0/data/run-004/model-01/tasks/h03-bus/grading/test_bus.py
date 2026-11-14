import unittest
from bus import Bus
from bus.errors import PublishError


class T(unittest.TestCase):
    def test_priority(self):
        b, seen = Bus(), []
        b.subscribe("a", lambda t, p: seen.append("low"))
        b.subscribe("a", lambda t, p: seen.append("high"), priority=5)
        self.assertEqual(b.publish("a"), 2)
        self.assertEqual(seen, ["high", "low"])

    def test_star(self):
        b, seen = Bus(), []
        b.subscribe("orders.*", lambda t, p: seen.append(t))
        b.publish("orders.new"); b.publish("orders.new.eu")
        self.assertEqual(seen, ["orders.new"])

    def test_errors_collected(self):
        b, seen = Bus(), []
        def bad(t, p): raise KeyError("x")
        b.subscribe("a", bad, priority=1)
        b.subscribe("a", lambda t, p: seen.append(1))
        with self.assertRaises(PublishError) as cm:
            b.publish("a")
        self.assertEqual(seen, [1])
        self.assertEqual(len(cm.exception.errors), 1)
