from collections import Counter


def top(words, n):
    return sorted(Counter(words).items(), key=lambda kv: (-kv[1], kv[0]))[:n]
