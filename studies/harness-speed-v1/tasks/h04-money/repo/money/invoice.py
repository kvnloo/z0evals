from .money import Money


def total(lines, tax_rate):
    subtotal = Money(0)
    for price, qty in lines:
        subtotal = subtotal + Money(price.cents * qty, price.currency)
    tax = Money(int(subtotal.cents * float(tax_rate)), subtotal.currency)
    return subtotal + tax
