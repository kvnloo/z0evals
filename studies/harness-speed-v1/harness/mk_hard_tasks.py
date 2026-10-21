#!/usr/bin/env python3
"""Write the six harder harness-speed tasks (h01-h06) into <tasks_dir>. Each task: repo/ (agent-visible,
visible tests fail on the original), hidden/test_hidden.py, reference/ (overlay of changed files), prompt.txt."""
import os
import sys
import textwrap

OUT = sys.argv[1]
T = {}


def task(name, prompt, repo, reference, hidden):
    T[name] = dict(prompt=prompt, repo=repo, reference=reference, hidden=hidden)


def d(s):
    return textwrap.dedent(s).lstrip("\n")


# ---------------------------------------------------------------- h01 inventory reservations
task("h01-reserve",
     "Add stock reservations to the inv package. Inventory.reserve(sku, qty) holds qty units, Inventory.release(sku, qty) "
     "returns held units, and Inventory.available(sku) is on_hand minus reserved. Reserving more than is available, "
     "releasing more than is reserved, and remove() calls that would leave on_hand below the reserved quantity must raise "
     "a new exception InsufficientStock, defined in inv/errors.py as a subclass of InventoryError. Unknown SKUs raise "
     "UnknownSku in every method. inv.report.summary must output the header `sku,on_hand,reserved,available` and one row "
     "per SKU in sorted order. Make `python3 -m unittest` pass. Do not modify the tests.",
     repo={
         "inv/__init__.py": "",
         "inv/errors.py": d('''
            class InventoryError(Exception):
                pass


            class UnknownSku(InventoryError):
                pass
            '''),
         "inv/store.py": d('''
            from .errors import UnknownSku


            class Inventory:
                def __init__(self):
                    self._on_hand = {}

                def add(self, sku, qty):
                    if qty <= 0:
                        raise ValueError("qty must be positive")
                    self._on_hand[sku] = self._on_hand.get(sku, 0) + qty

                def remove(self, sku, qty):
                    if sku not in self._on_hand:
                        raise UnknownSku(sku)
                    if qty > self._on_hand[sku]:
                        raise ValueError("not enough stock")
                    self._on_hand[sku] -= qty

                def on_hand(self, sku):
                    if sku not in self._on_hand:
                        raise UnknownSku(sku)
                    return self._on_hand[sku]

                def skus(self):
                    return sorted(self._on_hand)
            '''),
         "inv/report.py": d('''
            def summary(inv):
                lines = ["sku,on_hand"]
                for sku in inv.skus():
                    lines.append(f"{sku},{inv.on_hand(sku)}")
                return "\\n".join(lines)
            '''),
         "test_inv.py": d('''
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
                    self.assertEqual(summary(i), "sku,on_hand,reserved,available\\na,2,0,2\\nb,4,1,3")
            '''),
     },
     reference={
         "inv/errors.py": d('''
            class InventoryError(Exception):
                pass


            class UnknownSku(InventoryError):
                pass


            class InsufficientStock(InventoryError):
                pass
            '''),
         "inv/store.py": d('''
            from .errors import InsufficientStock, UnknownSku


            class Inventory:
                def __init__(self):
                    self._on_hand = {}
                    self._reserved = {}

                def _check(self, sku):
                    if sku not in self._on_hand:
                        raise UnknownSku(sku)

                def add(self, sku, qty):
                    if qty <= 0:
                        raise ValueError("qty must be positive")
                    self._on_hand[sku] = self._on_hand.get(sku, 0) + qty
                    self._reserved.setdefault(sku, 0)

                def remove(self, sku, qty):
                    self._check(sku)
                    if self._on_hand[sku] - qty < self._reserved[sku]:
                        raise InsufficientStock(sku)
                    self._on_hand[sku] -= qty

                def reserve(self, sku, qty):
                    self._check(sku)
                    if qty > self.available(sku):
                        raise InsufficientStock(sku)
                    self._reserved[sku] += qty

                def release(self, sku, qty):
                    self._check(sku)
                    if qty > self._reserved[sku]:
                        raise InsufficientStock(sku)
                    self._reserved[sku] -= qty

                def on_hand(self, sku):
                    self._check(sku)
                    return self._on_hand[sku]

                def reserved(self, sku):
                    self._check(sku)
                    return self._reserved[sku]

                def available(self, sku):
                    self._check(sku)
                    return self._on_hand[sku] - self._reserved[sku]

                def skus(self):
                    return sorted(self._on_hand)
            '''),
         "inv/report.py": d('''
            def summary(inv):
                lines = ["sku,on_hand,reserved,available"]
                for sku in inv.skus():
                    lines.append(f"{sku},{inv.on_hand(sku)},{inv.on_hand(sku) - inv.available(sku)},{inv.available(sku)}")
                return "\\n".join(lines)
            '''),
     },
     hidden=d('''
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
        '''))

# ---------------------------------------------------------------- h02 config interpolation + include
task("h02-config",
     "Extend the cfg package. (1) Values may reference environment variables as ${NAME} or ${NAME:-default}; `$$` is a "
     "literal `$`; a missing variable without a default raises ConfigError. Put the expansion in a new module "
     "cfg/interp.py exposing expand(value, env) -> str. load_string(text, base_dir='.', env=None) and "
     "load_file(path, env=None) take an env mapping that defaults to os.environ. (2) A line `@include <path>` (at top "
     "level or inside a section) loads another file, resolved relative to the directory of the including file "
     "(base_dir for load_string), and merges its sections into the result at that point: later keys override earlier "
     "ones, and the current section is unchanged after the include. Include cycles raise ConfigError. Make "
     "`python3 -m unittest` pass. Do not modify the tests.",
     repo={
         "cfg/__init__.py": "from .loader import load_file, load_string\n",
         "cfg/errors.py": "class ConfigError(Exception):\n    pass\n",
         "cfg/loader.py": d('''
            import os
            from .errors import ConfigError


            def load_string(text, base_dir="."):
                data = {}
                section = None
                for n, raw in enumerate(text.splitlines(), 1):
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("[") and line.endswith("]"):
                        section = line[1:-1].strip()
                        data.setdefault(section, {})
                        continue
                    if "=" not in line:
                        raise ConfigError(f"line {n}: expected key=value")
                    if section is None:
                        raise ConfigError(f"line {n}: key outside section")
                    key, value = line.split("=", 1)
                    data[section][key.strip()] = value.strip()
                return data


            def load_file(path):
                with open(path) as f:
                    return load_string(f.read(), base_dir=os.path.dirname(os.path.abspath(path)))
            '''),
         "test_cfg.py": d('''
            import os
            import tempfile
            import unittest
            from cfg import load_file, load_string
            from cfg.errors import ConfigError


            class T(unittest.TestCase):
                def test_env(self):
                    d = load_string("[s]\\na=${HOME_X}/x\\nb=${NOPE:-dflt}", env={"HOME_X": "/h"})
                    self.assertEqual(d, {"s": {"a": "/h/x", "b": "dflt"}})

                def test_missing(self):
                    with self.assertRaises(ConfigError):
                        load_string("[s]\\na=${NOPE}", env={})

                def test_include(self):
                    with tempfile.TemporaryDirectory() as t:
                        open(os.path.join(t, "base.cfg"), "w").write("[db]\\nhost=localhost\\nport=1\\n")
                        open(os.path.join(t, "main.cfg"), "w").write("@include base.cfg\\n[db]\\nport=2\\n")
                        self.assertEqual(load_file(os.path.join(t, "main.cfg"), env={}),
                                         {"db": {"host": "localhost", "port": "2"}})
            '''),
     },
     reference={
         "cfg/interp.py": d('''
            import re
            from .errors import ConfigError

            _PAT = re.compile(r"\\$\\$|\\$\\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\\}")


            def expand(value, env):
                def sub(m):
                    if m.group(0) == "$$":
                        return "$"
                    name, default = m.group(1), m.group(2)
                    if name in env:
                        return env[name]
                    if default is not None:
                        return default
                    raise ConfigError(f"undefined variable {name}")
                return _PAT.sub(sub, value)
            '''),
         "cfg/loader.py": d('''
            import os
            from .errors import ConfigError
            from .interp import expand


            def _load(text, base_dir, env, data, stack):
                section = None
                for n, raw in enumerate(text.splitlines(), 1):
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("@include"):
                        path = os.path.abspath(os.path.join(base_dir, line[len("@include"):].strip()))
                        if path in stack:
                            raise ConfigError(f"include cycle at {path}")
                        with open(path) as f:
                            _load(f.read(), os.path.dirname(path), env, data, stack + [path])
                        continue
                    if line.startswith("[") and line.endswith("]"):
                        section = line[1:-1].strip()
                        data.setdefault(section, {})
                        continue
                    if "=" not in line:
                        raise ConfigError(f"line {n}: expected key=value")
                    if section is None:
                        raise ConfigError(f"line {n}: key outside section")
                    key, value = line.split("=", 1)
                    data.setdefault(section, {})[key.strip()] = expand(value.strip(), env)
                return data


            def load_string(text, base_dir=".", env=None, _stack=None):
                env = os.environ if env is None else env
                return _load(text, base_dir, env, {}, _stack or [])


            def load_file(path, env=None):
                path = os.path.abspath(path)
                env = os.environ if env is None else env
                with open(path) as f:
                    return _load(f.read(), os.path.dirname(path), env, {}, [path])
            '''),
     },
     hidden=d('''
        import os
        import tempfile
        import unittest
        from cfg import load_file, load_string
        from cfg.errors import ConfigError
        from cfg.interp import expand


        class H(unittest.TestCase):
            def test_expand(self):
                self.assertEqual(expand("a$$b ${X}", {"X": "1"}), "a$b 1")
                self.assertEqual(expand("${Y:-}", {}), "")

            def test_default_env_is_os_environ(self):
                os.environ["HSB_CFG_T"] = "zz"
                self.assertEqual(load_string("[s]\\na=${HSB_CFG_T}"), {"s": {"a": "zz"}})

            def test_cycle(self):
                with tempfile.TemporaryDirectory() as t:
                    open(os.path.join(t, "a.cfg"), "w").write("@include b.cfg\\n")
                    open(os.path.join(t, "b.cfg"), "w").write("@include a.cfg\\n")
                    with self.assertRaises(ConfigError):
                        load_file(os.path.join(t, "a.cfg"), env={})

            def test_nested_relative_and_order(self):
                with tempfile.TemporaryDirectory() as t:
                    os.makedirs(os.path.join(t, "sub"))
                    open(os.path.join(t, "sub", "inner.cfg"), "w").write("[x]\\nk=inner\\nj=${J:-dj}\\n")
                    open(os.path.join(t, "sub", "mid.cfg"), "w").write("@include inner.cfg\\n[y]\\nm=1\\n")
                    open(os.path.join(t, "top.cfg"), "w").write("[x]\\nk=top\\n@include sub/mid.cfg\\nl=after\\n")
                    got = load_file(os.path.join(t, "top.cfg"), env={})
                    self.assertEqual(got, {"x": {"k": "inner", "j": "dj", "l": "after"}, "y": {"m": "1"}})

            def test_include_from_string_base_dir(self):
                with tempfile.TemporaryDirectory() as t:
                    open(os.path.join(t, "b.cfg"), "w").write("[q]\\nv=1\\n")
                    self.assertEqual(load_string("@include b.cfg", base_dir=t, env={}), {"q": {"v": "1"}})
        '''))

# ---------------------------------------------------------------- h03 event bus
task("h03-bus",
     "Extend bus.Bus. (1) subscribe(topic, handler, priority=0) returns a Subscription object with a cancel() method "
     "(calling it twice is harmless); handlers run in descending priority, ties in subscription order. (2) A subscription "
     "topic may use `*` to match exactly one dot-separated segment and `#`, only as the last segment, to match one or "
     "more segments: `orders.*` matches `orders.new` but not `orders.new.eu`; `orders.#` matches both but not `orders`. "
     "Put the matching in a new module bus/match.py with matches(pattern, topic) -> bool. (3) publish(topic, payload) "
     "calls every matching handler even if some raise; if any raised, after all handlers ran it raises "
     "bus.errors.PublishError (new module) whose .errors attribute lists the raised exceptions in call order. publish "
     "returns the number of handlers called. Make `python3 -m unittest` pass. Do not modify the tests.",
     repo={
         "bus/__init__.py": "from .bus import Bus\n",
         "bus/bus.py": d('''
            class Bus:
                def __init__(self):
                    self._subs = {}

                def subscribe(self, topic, handler):
                    self._subs.setdefault(topic, []).append(handler)

                def publish(self, topic, payload=None):
                    for h in self._subs.get(topic, []):
                        h(topic, payload)
            '''),
         "test_bus.py": d('''
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
            '''),
     },
     reference={
         "bus/errors.py": d('''
            class PublishError(Exception):
                def __init__(self, errors):
                    super().__init__(f"{len(errors)} handler(s) failed")
                    self.errors = list(errors)
            '''),
         "bus/match.py": d('''
            def matches(pattern, topic):
                p, t = pattern.split("."), topic.split(".")
                if p and p[-1] == "#":
                    head = p[:-1]
                    if len(t) <= len(head):
                        return False
                    t = t[:len(head)]
                    p = head
                if len(p) != len(t):
                    return False
                return all(a == "*" or a == b for a, b in zip(p, t))
            '''),
         "bus/bus.py": d('''
            import itertools
            from .errors import PublishError
            from .match import matches


            class Subscription:
                def __init__(self, bus, key):
                    self._bus, self._key = bus, key

                def cancel(self):
                    self._bus._subs.pop(self._key, None)


            class Bus:
                def __init__(self):
                    self._subs = {}
                    self._seq = itertools.count()

                def subscribe(self, topic, handler, priority=0):
                    key = next(self._seq)
                    self._subs[key] = (topic, handler, priority)
                    return Subscription(self, key)

                def publish(self, topic, payload=None):
                    hits = [(k, h, pr) for k, (pat, h, pr) in self._subs.items() if matches(pat, topic)]
                    hits.sort(key=lambda x: (-x[2], x[0]))
                    errors = []
                    for _k, h, _pr in hits:
                        try:
                            h(topic, payload)
                        except Exception as e:
                            errors.append(e)
                    if errors:
                        raise PublishError(errors)
                    return len(hits)
            '''),
     },
     hidden=d('''
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
        '''))

# ---------------------------------------------------------------- h04 money
task("h04-money",
     "Fix and extend the money package. (1) Adding Money values with different currencies must raise CurrencyMismatch, "
     "defined in a new module money/errors.py as a subclass of ValueError. (2) Money.parse(text, currency='USD') must "
     "parse the decimal string exactly (no float) and round to cents half away from zero: '1.005' -> 101 cents, "
     "'-1.005' -> -101, '2' -> 200. (3) Add Money.allocate(ratios): split the amount into len(ratios) Money values in "
     "proportion to the non-negative integer ratios, flooring each share, then give the leftover cents one at a time to "
     "the first shares, so the parts always sum to the original. (4) money.invoice.total(lines, tax_rate) takes lines "
     "of (unit_price: Money, qty: int) and a tax rate given as a string or Decimal; it must compute tax per line "
     "(line cents * rate, rounded half away from zero to a cent) and sum lines plus taxes. All lines must share one "
     "currency (otherwise CurrencyMismatch); the result is in that currency; an empty invoice returns Money(0, 'USD'). "
     "Make `python3 -m unittest` pass. Do not modify the tests.",
     repo={
         "money/__init__.py": "from .money import Money\n",
         "money/money.py": d('''
            class Money:
                def __init__(self, cents, currency="USD"):
                    self.cents = int(cents)
                    self.currency = currency

                def __add__(self, other):
                    return Money(self.cents + other.cents, self.currency)

                def __eq__(self, other):
                    return isinstance(other, Money) and (self.cents, self.currency) == (other.cents, other.currency)

                def __repr__(self):
                    return f"Money({self.cents}, {self.currency!r})"

                @classmethod
                def parse(cls, text, currency="USD"):
                    return cls(round(float(text) * 100), currency)
            '''),
         "money/invoice.py": d('''
            from .money import Money


            def total(lines, tax_rate):
                subtotal = Money(0)
                for price, qty in lines:
                    subtotal = subtotal + Money(price.cents * qty, price.currency)
                tax = Money(int(subtotal.cents * float(tax_rate)), subtotal.currency)
                return subtotal + tax
            '''),
         "test_money.py": d('''
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
            '''),
     },
     reference={
         "money/errors.py": "class CurrencyMismatch(ValueError):\n    pass\n",
         "money/money.py": d('''
            from decimal import Decimal, ROUND_HALF_UP
            from .errors import CurrencyMismatch


            def round_cents(value):
                return int(Decimal(value).quantize(Decimal(1), rounding=ROUND_HALF_UP))


            class Money:
                def __init__(self, cents, currency="USD"):
                    self.cents = int(cents)
                    self.currency = currency

                def __add__(self, other):
                    if other.currency != self.currency:
                        raise CurrencyMismatch(f"{self.currency} != {other.currency}")
                    return Money(self.cents + other.cents, self.currency)

                def __eq__(self, other):
                    return isinstance(other, Money) and (self.cents, self.currency) == (other.cents, other.currency)

                def __repr__(self):
                    return f"Money({self.cents}, {self.currency!r})"

                @classmethod
                def parse(cls, text, currency="USD"):
                    return cls(round_cents(Decimal(text.strip()) * 100), currency)

                def allocate(self, ratios):
                    total = sum(ratios)
                    shares = [self.cents * r // total for r in ratios]
                    left = self.cents - sum(shares)
                    for i in range(left):
                        shares[i % len(shares)] += 1
                    return [Money(s, self.currency) for s in shares]
            '''),
         "money/invoice.py": d('''
            from decimal import Decimal
            from .errors import CurrencyMismatch
            from .money import Money, round_cents


            def total(lines, tax_rate):
                if not lines:
                    return Money(0, "USD")
                rate = Decimal(str(tax_rate))
                currency = lines[0][0].currency
                cents = 0
                for price, qty in lines:
                    if price.currency != currency:
                        raise CurrencyMismatch(f"{currency} != {price.currency}")
                    line = price.cents * qty
                    cents += line + round_cents(Decimal(line) * rate)
                return Money(cents, currency)
            '''),
     },
     hidden=d('''
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
        '''))

# ---------------------------------------------------------------- h05 calculator
task("h05-calc",
     "Extend the calc expression evaluator (calc/tokenizer.py, calc/parser.py). Add unary minus and plus; add `^` "
     "exponentiation, right-associative and binding tighter than unary minus (so -2^2 == -4 and 2^3^2 == 512); add "
     "variables: identifiers [A-Za-z_][A-Za-z0-9_]* looked up in evaluate(expr, env=None), where env is a dict. An "
     "unknown variable, division by zero, unbalanced parentheses and leftover tokens (e.g. '1 2') must raise CalcError "
     "from calc/errors.py. Make `python3 -m unittest` pass. Do not modify the tests.",
     repo={
         "calc/__init__.py": "from .parser import evaluate\n",
         "calc/errors.py": "class CalcError(Exception):\n    pass\n",
         "calc/tokenizer.py": d('''
            import re
            from .errors import CalcError

            TOKEN = re.compile(r"\\s*(?:(\\d+\\.?\\d*)|(.))")


            def tokenize(s):
                out = []
                for num, op in TOKEN.findall(s.strip()):
                    if num:
                        out.append(("num", float(num)))
                    elif op in "+-*/()":
                        out.append(("op", op))
                    elif op.strip():
                        raise CalcError(f"bad character {op!r}")
                return out
            '''),
         "calc/parser.py": d('''
            from .errors import CalcError
            from .tokenizer import tokenize


            class _P:
                def __init__(self, toks):
                    self.toks, self.i = toks, 0

                def peek(self):
                    return self.toks[self.i] if self.i < len(self.toks) else (None, None)

                def take(self):
                    t = self.peek(); self.i += 1; return t

                def expr(self):
                    v = self.term()
                    while self.peek() in (("op", "+"), ("op", "-")):
                        op = self.take()[1]
                        v = v + self.term() if op == "+" else v - self.term()
                    return v

                def term(self):
                    v = self.atom()
                    while self.peek() in (("op", "*"), ("op", "/")):
                        op = self.take()[1]
                        v = v * self.atom() if op == "*" else v / self.atom()
                    return v

                def atom(self):
                    kind, val = self.take()
                    if kind == "num":
                        return val
                    if (kind, val) == ("op", "("):
                        v = self.expr()
                        self.take()
                        return v
                    raise CalcError(f"unexpected {val!r}")


            def evaluate(expr):
                return _P(tokenize(expr)).expr()
            '''),
         "test_calc.py": d('''
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
            '''),
     },
     reference={
         "calc/tokenizer.py": d('''
            import re
            from .errors import CalcError

            TOKEN = re.compile(r"\\s*(?:(\\d+\\.?\\d*)|([A-Za-z_][A-Za-z0-9_]*)|(.))")


            def tokenize(s):
                out = []
                for num, name, op in TOKEN.findall(s.strip()):
                    if num:
                        out.append(("num", float(num)))
                    elif name:
                        out.append(("name", name))
                    elif op in "+-*/^()":
                        out.append(("op", op))
                    elif op.strip():
                        raise CalcError(f"bad character {op!r}")
                return out
            '''),
         "calc/parser.py": d('''
            from .errors import CalcError
            from .tokenizer import tokenize


            class _P:
                def __init__(self, toks, env):
                    self.toks, self.i, self.env = toks, 0, env

                def peek(self):
                    return self.toks[self.i] if self.i < len(self.toks) else (None, None)

                def take(self):
                    t = self.peek(); self.i += 1; return t

                def expr(self):
                    v = self.term()
                    while self.peek() in (("op", "+"), ("op", "-")):
                        op = self.take()[1]
                        r = self.term()
                        v = v + r if op == "+" else v - r
                    return v

                def term(self):
                    v = self.unary()
                    while self.peek() in (("op", "*"), ("op", "/")):
                        op = self.take()[1]
                        r = self.unary()
                        if op == "/" and r == 0:
                            raise CalcError("division by zero")
                        v = v * r if op == "*" else v / r
                    return v

                def unary(self):
                    if self.peek() == ("op", "-"):
                        self.take(); return -self.unary()
                    if self.peek() == ("op", "+"):
                        self.take(); return self.unary()
                    return self.power()

                def power(self):
                    base = self.atom()
                    if self.peek() == ("op", "^"):
                        self.take()
                        return base ** self.unary()
                    return base

                def atom(self):
                    kind, val = self.take()
                    if kind == "num":
                        return val
                    if kind == "name":
                        if val not in self.env:
                            raise CalcError(f"unknown variable {val}")
                        return self.env[val]
                    if (kind, val) == ("op", "("):
                        v = self.expr()
                        if self.take() != ("op", ")"):
                            raise CalcError("missing )")
                        return v
                    raise CalcError(f"unexpected {val!r}")


            def evaluate(expr, env=None):
                p = _P(tokenize(expr), env or {})
                v = p.expr()
                if p.i != len(p.toks):
                    raise CalcError("unexpected trailing input")
                return v
            '''),
     },
     hidden=d('''
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
        '''))

# ---------------------------------------------------------------- h06 word stats cli
task("h06-wordstats",
     "Extend the ts word-statistics package. ts.cli.main(argv) returns the report text. Add options: `--top N` "
     "(default 10), `--ignore-case` (count case-insensitively and report lowercase words), `--stopwords FILE` (one word "
     "per line; blank lines and lines starting with '#' are ignored; matched case-insensitively when --ignore-case is "
     "given, exactly otherwise), and `--min-length K` (default 1; drop shorter words). Words are runs of letters and "
     "apostrophes with leading and trailing apostrophes stripped and empty results dropped. Ties in count are ordered "
     "alphabetically. Each output line is `word<TAB>count`. Keep word splitting in ts/words.py and counting in "
     "ts/stats.py. Make `python3 -m unittest` pass. Do not modify the tests.",
     repo={
         "ts/__init__.py": "",
         "ts/words.py": d('''
            import re


            def words(text):
                return re.findall(r"[A-Za-z']+", text)
            '''),
         "ts/stats.py": d('''
            from collections import Counter


            def top(words, n):
                return Counter(words).most_common(n)
            '''),
         "ts/cli.py": d('''
            import argparse
            from .stats import top
            from .words import words


            def main(argv):
                ap = argparse.ArgumentParser(prog="ts")
                ap.add_argument("file")
                a = ap.parse_args(argv)
                with open(a.file) as f:
                    ws = words(f.read())
                return "\\n".join(f"{w}\\t{c}" for w, c in top(ws, 10))
            '''),
         "test_ts.py": d('''
            import os
            import tempfile
            import unittest
            from ts.cli import main


            def write(d, name, text):
                p = os.path.join(d, name)
                open(p, "w").write(text)
                return p


            class T(unittest.TestCase):
                def test_top_and_ties(self):
                    with tempfile.TemporaryDirectory() as d:
                        f = write(d, "a.txt", "b a c b a d")
                        self.assertEqual(main([f, "--top", "3"]), "a\\t2\\nb\\t2\\nc\\t1")

                def test_ignore_case_and_stopwords(self):
                    with tempfile.TemporaryDirectory() as d:
                        f = write(d, "a.txt", "The cat the CAT a")
                        s = write(d, "stop.txt", "# common\\nthe\\n\\na\\n")
                        self.assertEqual(main([f, "--ignore-case", "--stopwords", s]), "cat\\t2")
            '''),
     },
     reference={
         "ts/words.py": d('''
            import re


            def words(text, ignore_case=False, min_length=1, stopwords=()):
                out = []
                stop = {s.lower() for s in stopwords} if ignore_case else set(stopwords)
                for raw in re.findall(r"[A-Za-z']+", text):
                    w = raw.strip("'")
                    if not w:
                        continue
                    if ignore_case:
                        w = w.lower()
                    if len(w) < min_length or w in stop:
                        continue
                    out.append(w)
                return out


            def read_stopwords(path):
                with open(path) as f:
                    return [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
            '''),
         "ts/stats.py": d('''
            from collections import Counter


            def top(words, n):
                return sorted(Counter(words).items(), key=lambda kv: (-kv[1], kv[0]))[:n]
            '''),
         "ts/cli.py": d('''
            import argparse
            from .stats import top
            from .words import read_stopwords, words


            def main(argv):
                ap = argparse.ArgumentParser(prog="ts")
                ap.add_argument("file")
                ap.add_argument("--top", type=int, default=10)
                ap.add_argument("--ignore-case", action="store_true")
                ap.add_argument("--stopwords")
                ap.add_argument("--min-length", type=int, default=1)
                a = ap.parse_args(argv)
                stop = read_stopwords(a.stopwords) if a.stopwords else ()
                with open(a.file) as f:
                    ws = words(f.read(), ignore_case=a.ignore_case, min_length=a.min_length, stopwords=stop)
                return "\\n".join(f"{w}\\t{c}" for w, c in top(ws, a.top))
            '''),
     },
     hidden=d('''
        import os
        import tempfile
        import unittest
        from ts.cli import main
        from ts.words import words


        def write(d, name, text):
            p = os.path.join(d, name)
            open(p, "w").write(text)
            return p


        class H(unittest.TestCase):
            def test_apostrophes(self):
                self.assertEqual(words("'tis don't 'quoted' ''"), ["tis", "don't", "quoted"])

            def test_case_sensitive_stopwords(self):
                with tempfile.TemporaryDirectory() as d:
                    f = write(d, "a.txt", "The the x")
                    s = write(d, "s.txt", "the\\n")
                    self.assertEqual(main([f, "--stopwords", s]), "The\\t1\\nx\\t1")

            def test_min_length_default_top(self):
                with tempfile.TemporaryDirectory() as d:
                    f = write(d, "a.txt", " ".join(f"w{chr(97 + i)}" for i in range(12)) + " a bb bb")
                    out = main([f, "--min-length", "2"]).splitlines()
                    self.assertEqual(len(out), 10)
                    self.assertEqual(out[0], "bb\\t2")
                    self.assertNotIn("a\\t1", out)
        '''))


for name, t in T.items():
    base = os.path.join(OUT, name)
    for sub, files in (("repo", t["repo"]), ("reference", t["reference"])):
        for rel, text in files.items():
            p = os.path.join(base, sub, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w").write(text)
    os.makedirs(os.path.join(base, "hidden"), exist_ok=True)
    open(os.path.join(base, "hidden", "test_hidden.py"), "w").write(t["hidden"])
    open(os.path.join(base, "prompt.txt"), "w").write(t["prompt"] + "\n")
print("wrote", sorted(T))
