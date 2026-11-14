"""Topic pattern matching for :mod:`bus`.

A pattern is a dot-separated list of segments.  ``*`` matches exactly one
segment and ``#`` matches one or more segments.  ``#`` is only valid as the
final segment; an invalid pattern never matches.
"""


def matches(pattern, topic):
    """Return ``True`` if ``topic`` matches ``pattern``."""
    if not isinstance(pattern, str) or not isinstance(topic, str):
        return False
    pattern_parts = pattern.split(".")
    topic_parts = topic.split(".")
    last = len(pattern_parts) - 1
    for index, part in enumerate(pattern_parts):
        if part == "#":
            if index != last:
                return False
            # ``#`` matches one or more segments, so at least one must remain.
            return len(topic_parts) > index
        if index >= len(topic_parts):
            return False
        if part != "*" and part != topic_parts[index]:
            return False
    return len(topic_parts) == len(pattern_parts)