#!/usr/bin/env bash
# Install pinned release binaries of every tool under test into $TOOLS (default
# ~/.cache/agent-vcs-tools/bin) and write tools.json with versions and sha256.
# Linux x86_64 only. Re-running skips tools that are already present.
set -euo pipefail
TOOLS=${TOOLS:-$HOME/.cache/agent-vcs-tools}
BIN=$TOOLS/bin
mkdir -p "$BIN" "$TOOLS/dl"
cd "$TOOLS/dl"

JJ_V=v0.46.0
OAK_V=v0.109.1
RIFT_V=v0.0.13
WEAVE_V=v0.7.1
MERGIRAF_V=v0.20.0

fetch() { [ -s "$2" ] || curl -fsSL --retry 3 -o "$2" "$1"; }

if [ ! -x "$BIN/jj" ]; then
  fetch "https://github.com/jj-vcs/jj/releases/download/$JJ_V/jj-$JJ_V-x86_64-unknown-linux-musl.tar.gz" jj.tgz
  tar -xzf jj.tgz ./jj 2>/dev/null || tar -xzf jj.tgz jj
  install -m755 jj "$BIN/jj"
fi
if [ ! -x "$BIN/oak" ]; then
  fetch "https://github.com/oakdotspace/oak/releases/download/$OAK_V/oak-linux-x86_64" oak
  install -m755 oak "$BIN/oak"
fi
if [ ! -x "$BIN/rift" ]; then
  fetch "https://github.com/anomalyco/rift/releases/download/$RIFT_V/rift-$RIFT_V-x86_64-unknown-linux-gnu.tar.gz" rift.tgz
  mkdir -p rift.x && tar -xzf rift.tgz -C rift.x
  install -m755 "$(find rift.x -type f -name rift | head -1)" "$BIN/rift"
fi
if [ ! -x "$BIN/weave" ]; then
  fetch "https://github.com/Ataraxy-Labs/weave/releases/download/$WEAVE_V/weave-cli-x86_64-unknown-linux-gnu.tar.gz" weave.tgz
  fetch "https://github.com/Ataraxy-Labs/weave/releases/download/$WEAVE_V/weave-driver-x86_64-unknown-linux-gnu.tar.gz" weave-driver.tgz
  mkdir -p weave.x && tar -xzf weave.tgz -C weave.x && tar -xzf weave-driver.tgz -C weave.x
  for f in $(find weave.x -type f -perm -u+x); do install -m755 "$f" "$BIN/$(basename "$f")"; done
fi
if [ ! -x "$BIN/mergiraf" ]; then
  fetch "https://codeberg.org/mergiraf/mergiraf/releases/download/$MERGIRAF_V/mergiraf_x86_64-unknown-linux-musl.tar.gz" mergiraf.tgz
  mkdir -p mergiraf.x && tar -xzf mergiraf.tgz -C mergiraf.x
  install -m755 "$(find mergiraf.x -type f -name mergiraf | head -1)" "$BIN/mergiraf"
fi
if [ ! -x "$BIN/but" ]; then
  fetch "https://releases.gitbutler.com/installers/latest/linux/x86_64/but-installer" but-installer
  chmod +x but-installer
  # The installer drops `but` under ~/.local/bin; give it a private HOME so it
  # does not touch the job user's profile, then copy the binary out.
  BH=$TOOLS/but-home; mkdir -p "$BH"
  HOME="$BH" ./but-installer --yes >/dev/null 2>&1 || HOME="$BH" ./but-installer >/dev/null 2>&1 || true
  found=$(find "$BH" -type f -name but -perm -u+x | head -1)
  [ -n "$found" ] && install -m755 "$found" "$BIN/but"
fi

python3 - "$BIN" > "$TOOLS/tools.json" <<'PY'
import hashlib, json, os, subprocess, sys
b = sys.argv[1]
out = {}
for name in sorted(os.listdir(b)):
    p = os.path.join(b, name)
    if not os.access(p, os.X_OK):
        continue
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    v = ""
    for flag in ("--version", "version", "-V"):
        try:
            r = subprocess.run([p, flag], capture_output=True, text=True, timeout=20)
            v = (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else ""
            if v and r.returncode == 0:
                break
        except Exception:
            pass
    out[name] = {"sha256": h, "version": v}
print(json.dumps(out, indent=1))
PY
cat "$TOOLS/tools.json"
