import re
from .errors import CalcError

TOKEN = re.compile(r"\s*(?:(\d+\.?\d*)|(.))")


def tokenize(s):
    out = []
    for num, op in TOKEN.findall(s.strip()):
        if num:
            out.append(("num", float(num)))
        elif op in "+-*/()":
            out.append(("op", op))
        elif op.strip():
            raise CalcError(f"bad character {op!r}")
    return out
