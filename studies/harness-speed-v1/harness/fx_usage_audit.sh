#!/bin/bash
# diagnostic: does libfx's turn `usage` sum all model calls? Compare with per-call hook usage.
cd $HOME/.cache/harness-speed-v1
cp harness/fx_run.ts fx/fx_run.ts
mkdir -p data/diag
for t in t01-paginate t05-lru t07-rename; do
  d=$(mktemp -d); cp -r tasks/$t/repo $d/r
  bun fx/fx_run.ts --cwd $d/r --model gpt-6.1-sol --effort low --audit-usage --prompt-file tasks/$t/prompt.txt | grep '"type":"result"' | python3 -c "
import json,sys
d=json.loads(sys.stdin.read()); print(json.dumps({'task':'$t','turn_usage':d['usage'],'hook_audit':d.get('audit'),'tool_calls':d['toolCalls']}))" | tee -a data/diag/fx-usage-audit.jsonl
  rm -rf $d
done
