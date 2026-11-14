import argparse

from .stats import top
from .words import load_stopwords, words


def main(argv):
    ap = argparse.ArgumentParser(prog="ts")
    ap.add_argument("file")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--ignore-case", action="store_true")
    ap.add_argument("--stopwords")
    ap.add_argument("--min-length", type=int, default=1)
    a = ap.parse_args(argv)
    with open(a.file) as f:
        ws = words(f.read())
    if a.ignore_case:
        ws = [w.lower() for w in ws]
    if a.stopwords:
        stop = load_stopwords(a.stopwords)
        if a.ignore_case:
            stop = {w.lower() for w in stop}
        ws = [w for w in ws if w not in stop]
    if a.min_length > 1:
        ws = [w for w in ws if len(w) >= a.min_length]
    return "\n".join(f"{w}\t{c}" for w, c in top(ws, a.top))
