import re
def parse_duration(text):
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", text.strip())
    if not m or not any(m.groups()): raise ValueError(text)
    h, mi, s = (int(g or 0) for g in m.groups())
    return h * 3600 + mi * 60 + s
