import os

from .errors import ConfigError
from .interp import expand


def load_string(text, base_dir=".", env=None):
    if env is None:
        env = os.environ
    return _load_string(text, base_dir=base_dir, env=env, stack=())


def _load_string(text, base_dir, env, stack):
    data = {}
    section = None
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split(None, 1)
        if parts[0] == "@include":
            if len(parts) == 1:
                raise ConfigError(f"line {n}: @include requires a path")
            path = parts[1].strip()
            include_path = path
            if not os.path.isabs(include_path):
                include_path = os.path.join(base_dir, include_path)
            included = _load_file(include_path, env=env, stack=stack)
            for included_section, values in included.items():
                target = data.setdefault(included_section, {})
                target.update(values)
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
        data[section][key.strip()] = expand(value.strip(), env)
    return data


def _load_file(path, env, stack):
    real_path = os.path.realpath(path)
    if real_path in stack:
        raise ConfigError(f"include cycle detected: {path}")
    with open(path) as f:
        text = f.read()
    return _load_string(
        text,
        base_dir=os.path.dirname(os.path.abspath(path)),
        env=env,
        stack=stack + (real_path,),
    )


def load_file(path, env=None):
    if env is None:
        env = os.environ
    return _load_file(path, env=env, stack=())
