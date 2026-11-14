from decimal import Decimal

from .errors import CurrencyMismatch
from .money import Money
from ._rounding import round_ratio


def _as_rate(tax_rate):
    if isinstance(tax_rate, Decimal):
        return tax_rate
    return Decimal(str(tax_rate))


def total(lines, tax_rate):
    lines = list(lines)
    if not lines:
        return Money(0, "USD")

    rate_numerator, rate_denominator = _as_rate(tax_rate).as_integer_ratio()
    currency = lines[0][0].currency
    subtotal_cents = 0
    tax_cents = 0

    for price, qty in lines:
        if price.currency != currency:
            raise CurrencyMismatch(
                f"invoice mixes {currency} and {price.currency}"
            )
        line_cents = price.cents * qty
        subtotal_cents += line_cents
        tax_cents += round_ratio(line_cents * rate_numerator, rate_denominator)

    return Money(subtotal_cents + tax_cents, currency)
