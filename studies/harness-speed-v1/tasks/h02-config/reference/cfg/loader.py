import os
from .errors import ConfigError
from .interp import expand


def _load(text, base_dir, env, data, stack):
    section = None
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("@include"):
            path = os.path.abspath(os.path.join(base_dir, line[len("@include"):].strip()))
            if path in stack:
                raise ConfigError(f"include cycle at {path}")
            with open(path) as f:
                _load(f.read(), os.path.dirname(path), env, data, stack + [path])
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            data.setdefault(section, {})
            continue
        if "=" not in line:
            raise ConfigError(f"line {n}: expected key=value")
        if section is None:
            raise ConfigError(f"line {n}: key outside section")
        key, value = line.split("=", 1)
        data.setdefault(section, {})[key.strip()] = expand(value.strip(), env)
    return data


def load_string(text, base_dir=".", env=None, _stack=None):
    env = os.environ if env is None else env
    return _load(text, base_dir, env, {}, _stack or [])


def load_file(path, env=None):
    path = os.path.abspath(path)
    env = os.environ if env is None else env
    with open(path) as f:
        return _load(f.read(), os.path.dirname(path), env, {}, [path])
