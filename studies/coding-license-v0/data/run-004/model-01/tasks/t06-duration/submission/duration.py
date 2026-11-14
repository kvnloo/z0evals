def parse_duration(text):
    """Parse '1h30m', '45s', '2h', '1h2m3s' (units h, m, s in that order, each at most
    once, at least one present) into total seconds as an int. Whitespace around the
    string is ignored. Anything else raises ValueError."""
    raise NotImplementedError
