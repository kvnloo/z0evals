class LRUCache:
    """Fixed-capacity least-recently-used cache.
    get(key) returns the value or -1 and marks the key as most recently used.
    put(key, value) inserts or updates and marks it most recently used; when the
    cache is over capacity it evicts the least recently used key.
    capacity < 1 raises ValueError. len(cache) is the number of stored keys."""
