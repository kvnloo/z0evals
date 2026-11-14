from decimal import Decimal, ROUND_HALF_UP, localcontext

from .errors import CurrencyMismatch
from .money import Money


def _as_rate(tax_rate):
    if isinstance(tax_rate, Decimal):
        return tax_rate
    return Decimal(str(tax_rate))


def _round_cents(value):
    with localcontext() as ctx:
        ctx.prec = max(28, len(value.as_tuple().digits) + 10)
        return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def total(lines, tax_rate):
    lines = list(lines)
    if not lines:
        return Money(0, "USD")

    rate = _as_rate(tax_rate)
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
        tax_cents += _round_cents(Decimal(line_cents) * rate)

    return Money(subtotal_cents + tax_cents, currency)
