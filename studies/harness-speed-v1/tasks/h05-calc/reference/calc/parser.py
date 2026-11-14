from .errors import CalcError
from .tokenizer import tokenize


class _P:
    def __init__(self, toks, env):
        self.toks, self.i, self.env = toks, 0, env

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def take(self):
        t = self.peek(); self.i += 1; return t

    def expr(self):
        v = self.term()
        while self.peek() in (("op", "+"), ("op", "-")):
            op = self.take()[1]
            r = self.term()
            v = v + r if op == "+" else v - r
        return v

    def term(self):
        v = self.unary()
        while self.peek() in (("op", "*"), ("op", "/")):
            op = self.take()[1]
            r = self.unary()
            if op == "/" and r == 0:
                raise CalcError("division by zero")
            v = v * r if op == "*" else v / r
        return v

    def unary(self):
        if self.peek() == ("op", "-"):
            self.take(); return -self.unary()
        if self.peek() == ("op", "+"):
            self.take(); return self.unary()
        return self.power()

    def power(self):
        base = self.atom()
        if self.peek() == ("op", "^"):
            self.take()
            return base ** self.unary()
        return base

    def atom(self):
        kind, val = self.take()
        if kind == "num":
            return val
        if kind == "name":
            if val not in self.env:
                raise CalcError(f"unknown variable {val}")
            return self.env[val]
        if (kind, val) == ("op", "("):
            v = self.expr()
            if self.take() != ("op", ")"):
                raise CalcError("missing )")
            return v
        raise CalcError(f"unexpected {val!r}")


def evaluate(expr, env=None):
    p = _P(tokenize(expr), env or {})
    v = p.expr()
    if p.i != len(p.toks):
        raise CalcError("unexpected trailing input")
    return v
