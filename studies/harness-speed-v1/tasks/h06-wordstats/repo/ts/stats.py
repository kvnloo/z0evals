from collections import Counter


def top(words, n):
    return Counter(words).most_common(n)
