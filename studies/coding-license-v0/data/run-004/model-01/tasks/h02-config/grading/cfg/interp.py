"""Environment-variable interpolation for configuration values."""

from .errors import ConfigError


def expand(value, env):
    """Expand ``${NAME}`` and ``${NAME:-default}`` references in *value*.

    ``$$`` is an escaped literal ``$``. A reference to a variable that is
    not present in *env* raises :class:`ConfigError` unless a default was
    supplied. Defaults are themselves expanded.
    """
    result = []
    i = 0
    length = len(value)

    while i < length:
        ch = value[i]

        if ch != "$":
            result.append(ch)
            i += 1
            continue

        # "$$" is an escaped dollar sign.
        if i + 1 < length and value[i + 1] == "$":
            result.append("$")
            i += 2
            continue

        if i + 1 >= length or value[i + 1] != "{":
            # A lone dollar sign that is not part of a reference.
            result.append(ch)
            i += 1
            continue

        # Find the matching closing brace, allowing nested references in the
        # default portion of the expression.
        j = i + 2
        depth = 1
        while j < length:
            if value[j] == "{":
                depth += 1
            elif value[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1

        if j >= length:
            raise ConfigError(
                "unterminated environment variable reference: "
                + value[i:]
            )

        expression = value[i + 2:j]
        name, separator, default = expression.partition(":-")
        if not name:
            raise ConfigError("empty environment variable name")

        if name in env:
            replacement = env[name]
        elif separator:
            replacement = expand(default, env)
        else:
            raise ConfigError(
                "missing environment variable: " + name
            )

        result.append(str(replacement))
        i = j + 1

    return "".join(result)