#!/usr/bin/env bash
# Exp-8-style weight editing on Qwen3.5-0.8B (thinking on): one matrix process per editor, all on Modal (sandbox + GPU).
# usage: launch-exp8.sh <run-id> <passes> <editor>...
set -u
run=$1 passes=$2; shift 2
W=/mnt/zer0models/z0-wt/z0int-weight-space
S=~/.z0int/state/weight-space/slm/$run
mkdir -p "$S"
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus WSP_BACKEND=modal WSP_MODAL_GPU=L4 WSP_ADMIT_MB=1200 PYTHONUNBUFFERED=1
for ed in "$@"; do
  systemd-run --user --unit="wsp-$run-$ed" --slice=agent.slice -p MemoryMax=2G --working-directory="$W" \
    -E DBUS_SESSION_BUS_ADDRESS -E WSP_BACKEND -E WSP_MODAL_GPU -E WSP_ADMIT_MB -E PYTHONUNBUFFERED -E HOME \
    -E PATH="$HOME/.local/bin:$HOME/.hermes/profiles/clean/bin:/usr/local/bin:/usr/bin:/bin" \
    bash -c "bws-env-exec --scope hermes -- $HOME/.hermes/profiles/clean/cache/scratch/wsp-pre/with-deepseek.sh \
      .venv-wsp/bin/python benchmarks/weight_space/slm/matrix.py --run-id $run --targets qwen35-0.8b \
      --editors $ed --passes $passes >> $S/matrix-$ed.log 2>&1"
  echo "started wsp-$run-$ed"
done
