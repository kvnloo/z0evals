import argparse, sys

def count_words(text):
    counts = {}
    for word in text.split():
        counts[word.lower()] = counts.get(word.lower(), 0) + 1
    return counts

def main(argv=None, stdin=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=3)
    parser.add_argument("--min-count", type=int, default=1)
    args = parser.parse_args(argv)
    text = (stdin or sys.stdin).read()
    counts = count_words(text)
    items = sorted((kv for kv in counts.items() if kv[1] >= args.min_count), key=lambda kv: (-kv[1], kv[0]))[: args.top]
    return "\n".join(f"{w} {c}" for w, c in items)

if __name__ == "__main__":
    print(main())
