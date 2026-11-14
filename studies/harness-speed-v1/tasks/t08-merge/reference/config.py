def deep_merge(base, override):
    out = {k: (deep_merge(v, {}) if isinstance(v, dict) else v) for k, v in base.items()}
    for k, v in override.items():
        if v is None: out.pop(k, None)
        elif isinstance(v, dict) and isinstance(out.get(k), dict): out[k] = deep_merge(out[k], v)
        elif isinstance(v, dict): out[k] = deep_merge(v, {})
        else: out[k] = v
    return out
