import argparse
from .stats import top
from .words import read_stopwords, words


def main(argv):
    ap = argparse.ArgumentParser(prog="ts")
    ap.add_argument("file")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--ignore-case", action="store_true")
    ap.add_argument("--stopwords")
    ap.add_argument("--min-length", type=int, default=1)
    a = ap.parse_args(argv)
    stop = read_stopwords(a.stopwords) if a.stopwords else ()
    with open(a.file) as f:
        ws = words(f.read(), ignore_case=a.ignore_case, min_length=a.min_length, stopwords=stop)
    return "\n".join(f"{w}\t{c}" for w, c in top(ws, a.top))
