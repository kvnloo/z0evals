#!/usr/bin/env bash
# Promote a channel downstream, without losing unpushed work.
#
# Written after losing four commits: a hand-run loop did
#   git checkout main && git reset --hard origin/main && git merge ... && git push
# while main held a new commit that had not been pushed yet. The reset discarded
# it, and the merge then promoted the *old* main. The commits survived only in the
# reflog.
#
# The rule this enforces: never reset a branch that has unpushed commits, and
# push each channel before moving to the next.
set -euo pipefail

usage() { echo "usage: $0 <source> <target> [<target> ...]" >&2; exit 2; }
[ $# -ge 2 ] || usage
SRC="$1"; shift

git rev-parse --verify -q "origin/$SRC" >/dev/null || { echo "no such channel: $SRC" >&2; exit 2; }

for TGT in "$@"; do
  git rev-parse --verify -q "origin/$TGT" >/dev/null || { echo "no such channel: $TGT" >&2; exit 2; }
done

# Refuse if any channel has unpushed commits — that is the exact condition that
# caused the loss.
for B in "$SRC" "$@"; do
  if git rev-parse --verify -q "$B" >/dev/null; then
    AHEAD=$(git rev-list --count "origin/$B..$B" 2>/dev/null || echo 0)
    if [ "$AHEAD" != "0" ]; then
      echo "refusing: '$B' has $AHEAD unpushed commit(s). push it first." >&2
      exit 1
    fi
  fi
done

git fetch -q origin
for TGT in "$@"; do
  echo "==> $SRC -> $TGT"
  git checkout -q "$TGT"
  git reset -q --hard "origin/$TGT"
  if git merge-base --is-ancestor "origin/$SRC" HEAD; then
    echo "    already contains $SRC; nothing to do"
    continue
  fi
  git merge --no-ff "origin/$SRC" -m "Promote $SRC into $TGT"
  # push immediately, so the next iteration cannot reset over this merge
  git push origin "$TGT"
  printf '    %s = %s\n' "$TGT" "$(git rev-parse --short HEAD)"
done
git checkout -q "$SRC"
echo "done"
