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
