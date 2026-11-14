import re

_PATTERN = re.compile(r"(?:([0-9]+)h)?(?:([0-9]+)m)?(?:([0-9]+)s)?")


def parse_duration(text):
    """Parse '1h30m', '45s', '2h', '1h2m3s' (units h, m, s in that order, each at most
    once, at least one present) into total seconds as an int. Whitespace around the
    string is ignored. Anything else raises ValueError."""
    if not isinstance(text, str):
        raise ValueError("duration must be a string")
    match = _PATTERN.fullmatch(text.strip())
    if match is None:
        raise ValueError(f"invalid duration: {text!r}")
    hours, minutes, seconds = match.groups()
    if hours is None and minutes is None and seconds is None:
        raise ValueError(f"invalid duration: {text!r}")
    return (
        int(hours or 0) * 3600
        + int(minutes or 0) * 60
        + int(seconds or 0)
    )
