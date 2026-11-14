from collections import OrderedDict


class LRUCache:
    """Fixed-capacity least-recently-used cache.
    get(key) returns the value or -1 and marks the key as most recently used.
    put(key, value) inserts or updates and marks it most recently used; when the
    cache is over capacity it evicts the least recently used key.
    capacity < 1 raises ValueError. len(cache) is the number of stored keys."""

    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self._data = OrderedDict()

    def get(self, key):
        try:
            value = self._data[key]
        except KeyError:
            return -1
        self._data.move_to_end(key)
        return value

    def put(self, key, value):
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)

    def __len__(self):
        return len(self._data)
