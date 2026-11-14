import re

def parse_duration(text):
    """Parse '1h30m', '45s', '2h', '1h2m3s' (units h, m, s in that order, each at most
    once, at least one present) into total seconds as an int. Whitespace around the
    string is ignored. Anything else raises ValueError."""
    if not isinstance(text, str):
        raise ValueError("duration must be a string")
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", text.strip())
    if not m or not any(m.groups()): raise ValueError
    h, mi, s = (int(g or 0) for g in m.groups())
    return h * 3600 + mi * 60 + s
