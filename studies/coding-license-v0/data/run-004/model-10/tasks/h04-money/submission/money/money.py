from decimal import Decimal

from .errors import CurrencyMismatch
from ._rounding import round_ratio


class Money:
    def __init__(self, cents, currency="USD"):
        self.cents = int(cents)
        self.currency = currency

    def __add__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise CurrencyMismatch(
                f"cannot add {self.currency} to {other.currency}"
            )
        return Money(self.cents + other.cents, self.currency)

    def __eq__(self, other):
        return isinstance(other, Money) and (self.cents, self.currency) == (other.cents, other.currency)

    def __repr__(self):
        return f"Money({self.cents}, {self.currency!r})"

    @classmethod
    def parse(cls, text, currency="USD"):
        numerator, denominator = Decimal(text).as_integer_ratio()
        return cls(round_ratio(numerator * 100, denominator), currency)

    def allocate(self, ratios):
        ratios = list(ratios)
        for ratio in ratios:
            if not isinstance(ratio, int) or isinstance(ratio, bool) or ratio < 0:
                raise ValueError("ratios must be non-negative integers")

        total_ratio = sum(ratios)
        if total_ratio == 0:
            if self.cents == 0:
                return [Money(0, self.currency) for _ in ratios]
            raise ValueError("ratios must not all be zero")

        shares = [(self.cents * ratio) // total_ratio for ratio in ratios]
        leftover = self.cents - sum(shares)
        for i in range(leftover):
            shares[i % len(shares)] += 1
        return [Money(share, self.currency) for share in shares]
