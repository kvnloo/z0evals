from copy import deepcopy


def deep_merge(base, override):
    """Return a new dict: keys from both; where both values are dicts, merge them
    recursively; otherwise override wins. A value of None in override deletes the
    key. Neither input is mutated."""
    out = deepcopy(base)
    for k, v in override.items():
        if v is None:
            out.pop(k, None)
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = deepcopy(v)
    return out
