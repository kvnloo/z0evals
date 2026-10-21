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
