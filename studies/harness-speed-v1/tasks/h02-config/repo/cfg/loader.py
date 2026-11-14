import os
from .errors import ConfigError


def load_string(text, base_dir="."):
    data = {}
    section = None
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
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
        data[section][key.strip()] = value.strip()
    return data


def load_file(path):
    with open(path) as f:
        return load_string(f.read(), base_dir=os.path.dirname(os.path.abspath(path)))
