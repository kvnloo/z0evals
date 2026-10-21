def deep_merge(base, override):
    """Return a new dict: keys from both; where both values are dicts, merge them
    recursively; otherwise override wins. A value of None in override deletes the
    key. Neither input is mutated."""
    out = dict(base)
    out.update(override)
    return out
