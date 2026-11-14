from .errors import CalcError
from .tokenizer import tokenize


class _P:
    def __init__(self, toks, env):
        self.toks, self.i = toks, 0
        self.env = env

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
        v = self.unary()
        while self.peek() in (("op", "*"), ("op", "/")):
            op = self.take()[1]
            rhs = self.unary()
            if op == "*":
                v = v * rhs
            else:
                if rhs == 0:
                    raise CalcError("division by zero")
                v = v / rhs
        return v

    def unary(self):
        if self.peek() == ("op", "+"):
            self.take()
            return self.unary()
        if self.peek() == ("op", "-"):
            self.take()
            return -self.unary()
        return self.power()

    def power(self):
        v = self.atom()
        if self.peek() == ("op", "^"):
            self.take()
            # Right-associative, and the exponent may itself be unary:
            # 2^3^2 == 2^(3^2), 2^-3 == 2^(-3).
            return v ** self.unary()
        return v

    def atom(self):
        kind, val = self.take()
        if kind == "num":
            return val
        if kind == "ident":
            if not self.env or val not in self.env:
                raise CalcError(f"unknown variable {val!r}")
            return self.env[val]
        if (kind, val) == ("op", "("):
            v = self.expr()
            if self.take() != ("op", ")"):
                raise CalcError("unbalanced parentheses")
            return v
        raise CalcError(f"unexpected {val!r}")


def evaluate(expr, env=None):
    p = _P(tokenize(expr), env)
    v = p.expr()
    if p.peek() != (None, None):
        raise CalcError(f"unexpected token {p.peek()[1]!r}")
    return v
