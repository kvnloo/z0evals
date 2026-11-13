#!/usr/bin/env bash
# Public copy of the run pipeline. Set OPS (work dir), PY (python with torch 2.11 + transformers 5.20),
# STUDY (this study directory) and TEXTS (dir with pg98.txt, pg1342.txt, pg2701.txt) before running.
# Per model: RULER-13 data (official generator) -> distill deep+wide routers -> RULER eval -> top-p scaling.
set -uo pipefail
: "${OPS:?}" "${PY:?}" "${STUDY:?}" "${TEXTS:?}"
S=$STUDY/scripts
export PYTHONPATH=${PYTHONPATH:-} HF_HUB_OFFLINE=1 TQDM_DISABLE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
declare -A REPO=([qwen3-0.6b]="Qwen/Qwen3-0.6B c1899de289a04d12100db370d81485cdf75e47ca"
  [qwen3.5-0.8b]="Qwen/Qwen3.5-0.8B 2fc06364715b967f1860aea9cf38778875588b17"
  [qwen3-1.7b]="Qwen/Qwen3-1.7B 70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
  [qwen2.5-1.5b]="Qwen/Qwen2.5-1.5B-Instruct 989aa7980e4cf806f80c7fef2b1adb7bc71aa306")
declare -A STEPS=([qwen3-0.6b]=150 [qwen3.5-0.8b]=120 [qwen3-1.7b]=100 [qwen2.5-1.5b]=100)
declare -A SCALE_LEN=([qwen3-0.6b]=32768 [qwen3.5-0.8b]=16384 [qwen3-1.7b]=32768 [qwen2.5-1.5b]=32768)
RULER=$OPS/ruler-src/scripts/data   # git clone https://github.com/NVIDIA/RULER @ db43f92
for M in ${MODELS:-qwen3-0.6b qwen3.5-0.8b qwen3-1.7b qwen2.5-1.5b}; do
  read -r HFREPO REV <<< "${REPO[$M]}"
  TOK=$("$PY" -c "from huggingface_hub import snapshot_download as s; print(s('$HFREPO', revision='$REV'))")
  for L in 4096 8192; do
    for T in niah_single_1 niah_single_2 niah_single_3 niah_multikey_1 niah_multikey_2 niah_multikey_3 \
             niah_multivalue niah_multiquery vt cwe fwe qa_1 qa_2; do
      [ -s $OPS/ruler-data/$M/$L/$T/validation.jsonl ] || (cd $RULER && "$PY" prepare.py --save_dir $OPS/ruler-data/$M/$L \
        --benchmark synthetic --task $T --tokenizer_path "$TOK" --tokenizer_type hf --max_seq_length $L \
        --model_template_type base --num_samples 10 --random_seed 42)
    done
  done
  for G in deep-c4l6 wide-c256l1; do
    [ -s $OPS/ckpt/$M-$G.pt ] || (cd $S && "$PY" zha_run.py train --model $M --geometry $G --corpus $OPS/corpus \
      --out $OPS/ckpt/$M-$G.pt --steps ${STEPS[$M]} --batch 4)
  done
  (cd $S && "$PY" eval_ruler.py --model $M --data $OPS/ruler-data/$M --out $OPS/raw/ruler-$M.jsonl --n 10 \
    --lengths 4096 8192 --routers deep=$OPS/ckpt/$M-deep-c4l6.pt wide=$OPS/ckpt/$M-wide-c256l1.pt --extra deep-c4l6@0.8)
  [ -s $OPS/raw/scaling-$M.jsonl ] || (cd $S && "$PY" scaling.py --model $M --texts $TEXTS --length ${SCALE_LEN[$M]} \
    --out $OPS/raw/scaling-$M.jsonl)
  if [ "$M" = "qwen3-1.7b" ]; then
    "$PY" -c "
import json
rows=[json.loads(l) for l in open('$OPS/evals/mmlu-pro.jsonl')]; c={}; keep=[]
for r in rows:
    if c.get(r['category'],0)<5: c[r['category']]=c.get(r['category'],0)+1; keep.append(r)
open('$OPS/evals/mmlu-pro-70.jsonl','w').write(''.join(json.dumps(r)+'\n' for r in keep))"
    (cd $S && "$PY" eval_mc.py --model $M --data $OPS/evals/mmlu-pro-70.jsonl --out $OPS/raw/mc-$M.jsonl --max-new 384 \
      --routers deep=$OPS/ckpt/$M-deep-c4l6.pt wide=$OPS/ckpt/$M-wide-c256l1.pt)
  fi
done
