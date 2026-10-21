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
