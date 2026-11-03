#!/usr/bin/env bash
# Trigger the free-taskfit workflow and download its rows + receipt.
#   scripts/dispatch_taskfit.sh [--ref BRANCH] [-f lanes=...] [-f repeats=2] [-f force=true]
# Artifacts land in studies/free-taskfit-v0/data/runs/<artifact-name>/.
set -euo pipefail
REPO=kvnloo/z0evals
REF=main
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --ref) REF="$2"; shift 2 ;;
    -f) ARGS+=(-f "$2"); shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
since=$(date -u +%Y-%m-%dT%H:%M:%SZ)
gh workflow run free-taskfit.yml -R "$REPO" --ref "$REF" "${ARGS[@]}"
run=""
for _ in $(seq 30); do
  run=$(gh run list -R "$REPO" -w free-taskfit.yml -e workflow_dispatch -b "$REF" --json databaseId,createdAt \
        -q "[.[] | select(.createdAt >= \"$since\")][0].databaseId")
  [[ -n "$run" ]] && break
  sleep 5
done
[[ -n "$run" ]] || { echo "dispatched, but no run found yet" >&2; exit 1; }
echo "run https://github.com/$REPO/actions/runs/$run"
gh run watch "$run" -R "$REPO" --exit-status || echo "run failed; downloading artifacts anyway" >&2
dest="$(git rev-parse --show-toplevel)/studies/free-taskfit-v0/data/runs"
gh run download "$run" -R "$REPO" -D "$dest"
ls -R "$dest" | tail -n 20
