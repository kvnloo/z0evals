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
