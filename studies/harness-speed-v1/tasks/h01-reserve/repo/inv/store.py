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
