from collections import Counter


def count(words, ignore_case=False):
    """Count word occurrences, optionally case-insensitively."""
    if ignore_case:
        words = (w.lower() for w in words)
    return Counter(words)


def top(words, n=10, ignore_case=False):
    """Return the n most common words as (word, count) pairs.

    Ties in count are ordered alphabetically.
    """
    if n <= 0:
        return []
    counts = count(words, ignore_case)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:n]
