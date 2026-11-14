import re
from .errors import ConfigError

_PAT = re.compile(r"\$\$|\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def expand(value, env):
    def sub(m):
        if m.group(0) == "$$":
            return "$"
        name, default = m.group(1), m.group(2)
        if name in env:
            return env[name]
        if default is not None:
            return default
        raise ConfigError(f"undefined variable {name}")
    return _PAT.sub(sub, value)
