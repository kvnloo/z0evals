#!/usr/bin/env bash
# Thin entrypoint only. Task preparation, execution, retries and scoring stay upstream.
set -euo pipefail
: "${HERMES_RLM_SOURCE:?Set the pinned plugin checkout}"
mode="${1:?Use prepare, smoke, or matrix}"
shift
case "$mode" in
  prepare)
    exec python3 "$HERMES_RLM_SOURCE/bench/paper_tasks.py" "$@"
    ;;
  smoke|matrix)
    : "${TASK_MANIFEST:?Set the evaluator-only task manifest}"
    : "${RAW_OUT:?Set the private JSONL output file}"
    : "${OPS_DIR:?Set the private run directory}"
    : "${HOME_TEMPLATE:?Set the throwaway home template}"
    : "${RELEASED_SOURCE:?Set the released Hermes checkout}"
    : "${RELEASED_PYTHON:?Set its environment Python}"
    : "${FORK_SOURCE:?Set the fork checkout}"
    : "${FORK_PYTHON:?Set its environment Python}"
    : "${NANO_SOURCE:?Set the nano checkout}"
    repeats=3
    selection=()
    if [[ "$mode" == smoke ]]; then
      repeats=1
      selection=(--smallest-sniah)
    fi
    exec nice -n 10 python3 "$HERMES_RLM_SOURCE/bench/paper_matrix.py" \
      "$TASK_MANIFEST" "$RAW_OUT" --ops-dir "$OPS_DIR" \
      --home-template "$HOME_TEMPLATE" \
      --released-source "$RELEASED_SOURCE" --released-python "$RELEASED_PYTHON" \
      --fork-source "$FORK_SOURCE" --fork-python "$FORK_PYTHON" \
      --nano-source "$NANO_SOURCE" --repeats "$repeats" "${selection[@]}" \
      --hermes-ingress library --disable-thinking --base-context-chars 240000 --timeout 100 --cell-timeout 70 \
      --max-turns 10 --max-tokens 3072 --sub-max-tokens 1536 --max-subcalls 12 \
      --provider-cap 2700 "$@"
    ;;
  *) printf 'Use prepare, smoke, or matrix\n' >&2; exit 2 ;;
esac
