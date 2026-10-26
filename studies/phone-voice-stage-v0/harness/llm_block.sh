#!/bin/bash
# usage: llm_block.sh s22|s25 MODEL_PATH_ON_DEVICE TAG [threads]   (device llama-server from z0bench, warm TTFT via n_predict=1)
source ~/tmp/voice-evals/ph.sh
DEV=$1; MP=$2; TAG=$3; TH=${4:-4}
Z=/data/local/tmp/z0v; OUT=$R/results/2026-10-27/$DEV/llm; mkdir -p $OUT
if [ $DEV = s22 ]; then A() { ph22 "$@"; }; BIN=/data/local/tmp/z0bench/llama-server; else A() { local n=0; while :; do o=$(ph25 "$@"); rc=$?; if [ "$o" = BUSY ]; then n=$((n+1)); echo BUSY $n >&2; [ $n -ge 8 ] && return 75; sleep 300; continue; fi; echo "$o"; return $rc; done; }; BIN=$Z/llama-server; fi
A push $R/llm60.json $Z/llm60.json >/dev/null
A shell "cd $Z; $BIN -m $MP -c 1024 -t $TH -tb $TH --host 127.0.0.1 --port 8091 --no-webui -np 1 > $Z/llm-server.log 2>&1 &
echo \$! > $Z/llm.pid; i=0; while [ \$i -lt 200 ]; do curl -s http://127.0.0.1:8091/health | grep -q ok && break; sleep 0.5; i=\$((i+1)); done; echo health_wait=\$i
rm -f $Z/llm_$TAG.jsonl
for k in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23; do
  curl -s -o $Z/llm_out.json -w '%{time_total}' -H 'Content-Type: application/json' --data @$Z/llm60.json http://127.0.0.1:8091/completion > $Z/t.txt
  echo \"{\\\"tag\\\":\\\"$TAG\\\",\\\"k\\\":\$k,\\\"warmup\\\":\$([ \$k -lt 4 ] && echo 1 || echo 0),\\\"curl_s\\\":\$(cat $Z/t.txt),\\\"epoch\\\":\$(date +%s),\\\"resp\\\":\$(cat $Z/llm_out.json | head -c 1500)}\" >> $Z/llm_$TAG.jsonl
  sleep 4
done
kill \$(cat $Z/llm.pid); grep -m3 -E 'model size|n_params|CPU' $Z/llm-server.log | cut -c1-200; wc -l $Z/llm_$TAG.jsonl"
A pull $Z/llm_$TAG.jsonl $OUT/ >/dev/null
A pull $Z/llm-server.log $OUT/server_$TAG.log >/dev/null
echo done
