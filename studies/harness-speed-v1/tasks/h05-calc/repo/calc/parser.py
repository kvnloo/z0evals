from .errors import CalcError
from .tokenizer import tokenize


class _P:
    def __init__(self, toks):
        self.toks, self.i = toks, 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def take(self):
        t = self.peek(); self.i += 1; return t

    def expr(self):
        v = self.term()
        while self.peek() in (("op", "+"), ("op", "-")):
            op = self.take()[1]
            v = v + self.term() if op == "+" else v - self.term()
        return v

    def term(self):
        v = self.atom()
        while self.peek() in (("op", "*"), ("op", "/")):
            op = self.take()[1]
            v = v * self.atom() if op == "*" else v / self.atom()
        return v

    def atom(self):
        kind, val = self.take()
        if kind == "num":
            return val
        if (kind, val) == ("op", "("):
            v = self.expr()
            self.take()
            return v
        raise CalcError(f"unexpected {val!r}")


def evaluate(expr):
    return _P(tokenize(expr)).expr()
