import re

def parse_duration(text):
    """Parse '1h30m', '45s', '2h', '1h2m3s' (units h, m, s in that order, each at most
    once, at least one present) into total seconds as an int. Whitespace around the
    string is ignored. Anything else raises ValueError."""
    if not isinstance(text, str):
        raise ValueError("duration must be a string")
    match = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", text.strip())
    if match is None or not any(match.groups()):
        raise ValueError("invalid duration")

    hours, minutes, seconds = (int(value or 0) for value in match.groups())
    return hours * 3600 + minutes * 60 + seconds
