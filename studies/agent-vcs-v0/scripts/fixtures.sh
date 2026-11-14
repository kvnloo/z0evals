#!/usr/bin/env bash
# Clone the two fixture repos at pinned SHAs. Shallow by date: E1 replays the
# last turns, E3 samples commit pairs and merges inside the same window.
set -euo pipefail
FX=${FX:-$PWD/fixtures}
mkdir -p "$FX"
T3_SHA=${T3_SHA:-cefb544af3c98224874419198c0359b652ca3c94}
HERMES_SHA=${HERMES_SHA:-c314285f077e91937c995d419b9fa40af9eb4981}
SINCE=${SINCE:-2026-10-12}

clone() { # url dir sha
  if [ ! -d "$FX/$2/.git" ]; then
    git clone -q --single-branch --branch main --shallow-since="$SINCE" "$1" "$FX/$2"
  fi
  git -C "$FX/$2" cat-file -e "$3^{commit}" || git -C "$FX/$2" fetch -q --shallow-since="$SINCE" origin main
  git -C "$FX/$2" checkout -q --detach "$3"
  echo "$2 $(git -C "$FX/$2" rev-parse HEAD) $(git -C "$FX/$2" rev-list --count HEAD) commits $(git -C "$FX/$2" ls-files | wc -l) files"
}
clone https://github.com/pingdotgg/t3code.git t3code "$T3_SHA"
clone https://github.com/NousResearch/hermes-agent.git hermes-agent "$HERMES_SHA"
