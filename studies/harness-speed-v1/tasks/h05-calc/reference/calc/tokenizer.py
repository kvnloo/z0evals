import re
from .errors import CalcError

TOKEN = re.compile(r"\s*(?:(\d+\.?\d*)|([A-Za-z_][A-Za-z0-9_]*)|(.))")


def tokenize(s):
    out = []
    for num, name, op in TOKEN.findall(s.strip()):
        if num:
            out.append(("num", float(num)))
        elif name:
            out.append(("name", name))
        elif op in "+-*/^()":
            out.append(("op", op))
        elif op.strip():
            raise CalcError(f"bad character {op!r}")
    return out
