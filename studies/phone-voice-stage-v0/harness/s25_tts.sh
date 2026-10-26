#!/bin/bash
# Block S25-1: Pocket TTS on owner's daily S25 Ultra, only under the owner-activity guard.
# usage: s25_tts.sh pilot|scored|soak|cleanup
source ~/tmp/voice-evals/ph.sh
MODE=${1:-pilot}
D=2026-10-27; OUT=$R/results/$D/s25/tts; mkdir -p $OUT
Z=/data/local/tmp/z0v; M=sherpa-onnx-pocket-tts-int8-2026-01-26
P25() { # guarded call with backoff; never proceeds while busy
  local n=0
  while :; do
    out=$(ph25 "$@"); rc=$?
    if [ "$out" = BUSY ] || [ $rc = 75 ]; then n=$((n+1)); echo "$(date -Is) S25 BUSY (attempt $n), backing off 300s" | tee -a $LOG >&2; [ $n -ge 8 ] && return 75; sleep 300; continue; fi
    echo "$out"; return $rc
  done
}
gate() { # S25: status 0 and skin <=38 (37 unreachable at idle: SKIN reads 37.7 on an idle S25) ; wait up to 4 min then proceed (flagged in data)
  for i in $(seq 1 4); do l=$(therm_line $S25); st=$(echo $l | cut -d, -f2); sk=$(echo $l | cut -d, -f3)
    if [ "$st" = 0 ] && awk "BEGIN{exit !($sk<=38)}"; then echo "gate ok $l"; return 0; fi; echo "thermal wait $l"; sleep 60; done; echo "gate TIMEOUT $l"; return 1; }
if [ "$MODE" = cleanup ]; then
  P25 shell "rm -rf $Z; ls /data/local/tmp | grep -c z0v; pm list packages | grep -c z0"
  exit 0
fi
if [ "$MODE" = pilot ]; then
  df=$(P25 shell "df /data | tail -1"); echo "S25 df: $df" | tee $OUT/df.txt
  P25 shell "getprop ro.build.fingerprint; getprop ro.product.model; cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor; cat /sys/devices/system/cpu/possible; dumpsys audio | grep -A3 'STREAM_MUSIC:' | head -5" > $OUT/device.txt
  P25 shell "mkdir -p $Z/bin $Z/lib $Z/models $Z/out" || exit 75
  P25 push $R/stage/bin/ttsbench $Z/bin/ >/dev/null
  P25 push $R/stage/lib/. $Z/lib/ >/dev/null
  P25 push $R/pocket/$M $Z/models/ >/dev/null
  P25 push $R/stage/tts_texts.tsv $Z/ >/dev/null
  P25 shell "chmod +x $Z/bin/ttsbench; cd $Z/models/$M && sha256sum *.onnx *.json" > $OUT/model_sha_on_device.txt
  gate
  P25 shell "cd $Z && LD_LIBRARY_PATH=$Z/lib bin/ttsbench --model models/$M --threads 4 --texts tts_texts.tsv --ids s01,m01 --reps 1 --gap-ms 0 --tag pilot --out out/pilot.jsonl 2>&1 | tail -3; cat out/pilot.jsonl"
  exit 0
fi
cd $OUT
S=s01,s02,s03,s04,s05,s06,s07,s08; MI=m01,m02,m03,m04,m05,m06,m07,m08; LI=l01,l02,l03,l04,l05,l06,l07,l08
RUN() { P25 shell "cd $Z && LD_LIBRARY_PATH=$Z/lib bin/ttsbench --model models/$M --threads $2 --texts tts_texts.tsv --ids $3 --reps $5 --gap-ms 4000 --seed $RANDOM --tag $4 --out out/trials.jsonl 2>&1 | tail -2"; }
if [ "$MODE" = scored ]; then
  P25 shell "rm -f $Z/out/trials.jsonl"
  sampler $S25 $OUT/therm.csv $OUT/sampler.pid
  for b in "short $S" "medium $MI" "long $LI"; do set -- $b
    for arm in $(shuf -e t2 t4 t6); do gate; RUN pocket18 ${arm#t} $2 "$1/$arm" 3 || { echo ABORT; break 2; }; done
  done
fi
if [ "$MODE" = soak ]; then
  P25 shell "rm -f $Z/out/soak.jsonl"; sampler $S25 $OUT/therm_soak.csv $OUT/sampler.pid; gate
  P25 shell "cd $Z && LD_LIBRARY_PATH=$Z/lib bin/ttsbench --model models/$M --threads 4 --texts tts_texts.tsv --soak-sec 600 --soak-id l01 --tag soak --out out/soak.jsonl 2>&1 | tail -2"
fi
kill $(cat $OUT/sampler.pid) 2>/dev/null
P25 pull $Z/out/. $OUT/dev_out/ >/dev/null 2>&1
echo DONE $MODE
