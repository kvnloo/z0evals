"""Harbor `hermes` agent with the version probe current hermes-agent understands.

Harbor 0.25.0's built-in `hermes` agent finishes install with `hermes version`
and uses the same string as its version command. hermes-agent v2026.9.24 and
main (2026-11-03) only accept `hermes --version`; the subcommand form exits 2
("'version' is not a `hermes` command"), so every trial dies in agent setup
before the model is called (observed on TerminalBench 4 music-harmony,
2026-11-03). With `--version` alone the fresh /tmp/hermes data root then fails
with "no dependency environment is committed for this install; run `hermes pm
repair`", so install runs that first. This subclass changes only the probe. Install source, config,
run command, provider routing and trajectory export are Harbor's own.

Use: harbor run ... -a hermes_harbor_agent:HermesCurrentCli  (with this file's
directory on PYTHONPATH). Not upstreamed from here; it is a local adapter.
"""
from __future__ import annotations

from harbor.agents.installed.hermes import Hermes

_PROBE = 'export PATH="$HOME/.local/bin:$PATH"; hermes --version'


class HermesCurrentCli(Hermes):
    def get_version_command(self) -> str | None:
        return _PROBE

    async def install(self, environment) -> None:
        await self.ensure_system_dependencies(environment, ("curl", "git", "ripgrep", "xz"))
        branch_flag = f" --branch {self._version}" if self._version else ""
        await self.exec_as_agent(
            environment,
            command=(
                "set -euo pipefail; "
                "curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh"
                f" | bash -s -- --skip-setup{branch_flag} && "
                'export PATH="$HOME/.local/bin:$PATH" && '
                'export HERMES_HOME="${HERMES_HOME:-/tmp/hermes}" && '
                'mkdir -p "$HERMES_HOME" "$HERMES_HOME/sessions" "$HERMES_HOME/skills" "$HERMES_HOME/memories" && '
                # A fresh data root (HERMES_HOME=/tmp/hermes) has no committed dependency
                # environment; `hermes --version` then exits 1 and asks for `hermes pm repair`.
                "hermes pm repair && hermes --version"
            ),
        )
