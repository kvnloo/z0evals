#!/bin/bash
# per-process PATH for the bench (no global env changes)
export PATH=$HOME/.npm-global/bin:$HOME/.local/bin:$HOME/.bun/bin:/usr/local/bin:/usr/bin:/bin
cd $HOME/.cache/harness-speed-v1
exec "$@"
