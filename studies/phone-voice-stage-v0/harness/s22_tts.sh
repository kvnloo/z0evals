#!/bin/bash
# Block S22-1: Pocket TTS via sherpa-onnx C API, S22+. usage: s22_tts.sh pilot|scored|soak
source ~/tmp/voice-evals/ph.sh
MODE=${1:-pilot}
D=2026-10-27; OUT=$R/results/$D/s22/tts; mkdir -p $OUT
Z=/data/local/tmp/z0v
M=sherpa-onnx-pocket-tts-int8-2026-01-26
gate() { # wait until thermal ok for S22+ (status 0, skin<=38)
  for i in $(seq 1 30); do l=$(therm_line $S22); st=$(echo $l | cut -d, -f2); sk=$(echo $l | cut -d, -f3)
    if [ "$st" = 0 ] && awk "BEGIN{exit !($sk<=38)}"; then return 0; fi; echo "thermal wait $l"; sleep 60; done; return 1; }
if [ "$MODE" = pilot ]; then
  ph22 shell "mkdir -p $Z/bin $Z/lib $Z/models $Z/out"
  ph22 push $R/stage/bin/ttsbench $Z/bin/ >/dev/null
  ph22 push $R/stage/lib/. $Z/lib/ >/dev/null
  ph22 push $R/pocket/$M $Z/models/ >/dev/null
  ph22 push $R/stage/tts_texts.tsv $Z/ >/dev/null
  ph22 shell "chmod +x $Z/bin/ttsbench; ls -la $Z/models/$M | head -3; sha256sum $Z/models/$M/*.onnx" > $OUT/model_sha_on_device.txt
  ph22 shell "cd $Z && LD_LIBRARY_PATH=$Z/lib taskset f0 bin/ttsbench --model models/$M --threads 4 --texts tts_texts.tsv --ids s01,m01 --reps 1 --gap-ms 0 --tag pilot --out out/pilot.jsonl 2>&1 | tail -5; cat out/pilot.jsonl"
  exit 0
fi
cd $OUT
S=$(printf '%s,' s01 s02 s03 s04 s05 s06 s07 s08 | sed 's/,$//')
mids=$(echo m01,m02,m03,m04,m05,m06,m07,m08); lids=$(echo l01,l02,l03,l04,l05,l06,l07,l08)
gate || { echo thermal gate failed; exit 3; }
sampler $S22 $OUT/therm.csv $OUT/sampler.pid
P=$(ph22 shell "taskset" 2>&1 | head -1) # noop; keeps lock semantics
RUN() { # arm threads ids tag reps pin
  ph22 shell "cd $Z && LD_LIBRARY_PATH=$Z/lib $6 bin/ttsbench --model models/$M --threads $2 --texts tts_texts.tsv --ids $3 --reps $5 --gap-ms 4000 --seed $RANDOM --tag $4 --out out/trials.jsonl 2>&1 | tail -2"; }
if [ "$MODE" = scored ]; then
  ph22 shell "rm -f $Z/out/trials.jsonl"
  for b in "short $S" "medium $mids" "long $lids"; do set -- $b
    for arm in $(shuf -e t2 t4 t4pin); do gate
      case $arm in t2) RUN pocket18 2 $2 "$1/$arm" 3 "taskset f0";; t4) RUN pocket18 4 $2 "$1/$arm" 3 "";; t4pin) RUN pocket18 4 $2 "$1/$arm" 3 "taskset f0";; esac
    done
  done
fi
if [ "$MODE" = soak ]; then
  ph22 shell "rm -f $Z/out/soak.jsonl"
  ph22 shell "cd $Z && LD_LIBRARY_PATH=$Z/lib taskset f0 bin/ttsbench --model models/$M --threads 4 --texts tts_texts.tsv --soak-sec 600 --soak-id l01 --tag soak --out out/soak.jsonl 2>&1 | tail -2"
fi
kill $(cat $OUT/sampler.pid) 2>/dev/null
ph22 pull $Z/out/. $OUT/dev_out/ >/dev/null 2>&1
echo DONE $MODE
