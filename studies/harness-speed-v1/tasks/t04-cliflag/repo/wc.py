import argparse, sys

def count_words(text):
    counts = {}
    for word in text.split():
        counts[word.lower()] = counts.get(word.lower(), 0) + 1
    return counts

def main(argv=None, stdin=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=3)
    args = parser.parse_args(argv)
    text = (stdin or sys.stdin).read()
    items = sorted(count_words(text).items(), key=lambda kv: (-kv[1], kv[0]))[: args.top]
    return "\n".join(f"{w} {c}" for w, c in items)

if __name__ == "__main__":
    print(main())
