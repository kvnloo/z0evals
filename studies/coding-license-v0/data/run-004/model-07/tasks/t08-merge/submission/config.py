def deep_merge(base, override):
    """Return a new dict: keys from both; where both values are dicts, merge them
    recursively; otherwise override wins. A value of None in override deletes the
    key. Neither input is mutated."""
    out = dict(base)
    for key, value in override.items():
        if value is None:
            out.pop(key, None)
        elif key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out
