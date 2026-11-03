#!/usr/bin/env bash
# Bounded Hermes-harness pilot on the PUBLIC Hermes Index suites (TerminalBench 4,
# TerminalBench Science, SkillsBench via Harbor), FREE OpenRouter models only.
#
# This reproduces the harness, not the Index: Hermes Bench (the fourth suite) is not
# public, so a full Hermes Index can't be recomputed. A pilot answers "does our
# Hermes-in-Harbor path run and grade end to end on a free lane?", not "what is
# model X's score?" (one task, one attempt, capped turns => no score claim).
#
# Guards (fail closed):
#   * model must be openrouter/<id>:free; any other route is refused
#   * the OpenRouter key must report a 0 USD credit limit (so a non-free auxiliary
#     call can't bill); checked live before any trial
#   * turn cap and agent-timeout multiplier always set
#
# Usage (key never on argv; run via dsh-env-exec or `read -r OPENROUTER_API_KEY`):
#   OPENROUTER_API_KEY=... harbor_pilot.sh <dataset@version> <task-name> <openrouter/model:free> <out-dir> [max_turns] [timeout_mult]
# Example:
#   harbor_pilot.sh terminal-bench/terminal-bench@4.0.0 music-harmony \
#     openrouter/nvidia/nemotron-3.5-super-vl:free ~/harbor-pilot/jobs 40 0.0625
set -euo pipefail
dataset=${1:?dataset@version}; task=${2:?task name}; model=${3:?openrouter/<id>:free}; out=${4:?jobs dir}
max_turns=${5:-40}; tmult=${6:-0.0625}

case "$model" in
  openrouter/*:free) ;;
  *) echo "refused: $model is not an openrouter/...:free model" >&2; exit 2 ;;
esac
: "${OPENROUTER_API_KEY:?OPENROUTER_API_KEY must be in the environment (never argv)}"

limit=$(python3 - <<'PY'
import json, os, urllib.request
req = urllib.request.Request("https://openrouter.ai/api/v1/key",
      headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "User-Agent": "Mozilla/5.0"})
d = json.load(urllib.request.urlopen(req, timeout=30))["data"]
print(d.get("limit"))
PY
)
if [ "$limit" != "0" ]; then
  echo "refused: OpenRouter key credit limit is '$limit', not 0; a non-free call could bill" >&2; exit 3
fi

command -v harbor >/dev/null || { echo "harbor not installed: uv tool install harbor" >&2; exit 4; }
mkdir -p "$out"
# Harbor 0.25.0's built-in hermes agent probes `hermes version`, which current hermes-agent
# rejects; hermes_harbor_agent.py fixes only that probe (see its docstring).
here=$(cd "$(dirname "$0")" && pwd)
export PYTHONPATH="$here${PYTHONPATH:+:$PYTHONPATH}"
exec harbor run -d "$dataset" -i "$task" -a hermes_harbor_agent:HermesCurrentCli -m "$model" \
  --ak max_turns="$max_turns" --ak toolsets=terminal,file,todo \
  --agent-timeout-multiplier "$tmult" -k 1 -n 1 -e docker -o "$out" -y
