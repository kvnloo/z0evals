#!/usr/bin/env bash
# Run each local shadow arm in its own process, one at a time, under the host heavy lock.
# Usage: harness/run_local_arms.sh RUN_ID arm1 arm2 ...
# Env per arm is set here only (never exported globally). PYTHONPATH from the host agent is
# scrubbed because it injects a different interpreter's site-packages.
set -u
cd "$(dirname "$0")/.."
RUN=$1; shift
LOCK=${HEAVY_LOCK:-/home/kvn/.hermes/profiles/clean/cache/scratch/heavy.lock}
Z0SRC=${Z0INT_SRC:-/mnt/zer0models/z0-wt/z0intelligence/src}
for arm in "$@"; do
  case "$arm" in
    z0int:laya_421m) PY=/mnt/zer0models/z0-wt/venv-stack-z0/bin/python ;;
    *) PY=/mnt/zer0models/z0-wt/venv-claude-code/bin/python ;;
  esac
  out="data/shadow/$(echo "$arm" | tr ':|/' '---' | tr -s '-').jsonl"
  echo "== $arm -> $out ($(date +%T))"
  env -u PYTHONPATH -u PYTHONHOME Z0INT_SRC="$Z0SRC" \
    timeout 1800 flock "$LOCK" nice -n 10 "$PY" harness/shadow_eval.py --arm "$arm" --reps 3 --run-id "$RUN" --out "$out" 2>&1 | tail -3
done
