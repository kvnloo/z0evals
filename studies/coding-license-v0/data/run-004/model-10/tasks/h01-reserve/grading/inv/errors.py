class InventoryError(Exception):
    pass


class InsufficientStock(InventoryError):
    pass


class UnknownSku(InventoryError):
    pass
