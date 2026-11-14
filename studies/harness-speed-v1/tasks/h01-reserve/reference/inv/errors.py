class InventoryError(Exception):
    pass


class UnknownSku(InventoryError):
    pass


class InsufficientStock(InventoryError):
    pass
