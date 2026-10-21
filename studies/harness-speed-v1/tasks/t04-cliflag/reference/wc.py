import argparse, sys
def count_words(text):
    counts = {}
    for word in text.split():
        counts[word.lower()] = counts.get(word.lower(), 0) + 1
    return counts
def main(argv=None, stdin=None):
    p = argparse.ArgumentParser(); p.add_argument("--top", type=int, default=3); p.add_argument("--min-count", type=int, default=1)
    a = p.parse_args(argv)
    text = (stdin or sys.stdin).read()
    items = [kv for kv in count_words(text).items() if kv[1] >= a.min_count]
    items = sorted(items, key=lambda kv: (-kv[1], kv[0]))[: a.top]
    return "\n".join(f"{w} {c}" for w, c in items)
