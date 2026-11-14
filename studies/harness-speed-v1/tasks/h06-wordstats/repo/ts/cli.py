import argparse
from .stats import top
from .words import words


def main(argv):
    ap = argparse.ArgumentParser(prog="ts")
    ap.add_argument("file")
    a = ap.parse_args(argv)
    with open(a.file) as f:
        ws = words(f.read())
    return "\n".join(f"{w}\t{c}" for w, c in top(ws, 10))
