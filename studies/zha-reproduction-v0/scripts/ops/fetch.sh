#!/usr/bin/env bash
# Public copy of the input fetch. Set OPS (work dir). Downloads only public data.
set -euo pipefail
: "${OPS:?}"
mkdir -p $OPS/corpus
git clone -q https://github.com/NVIDIA/RULER.git $OPS/ruler-src && git -C $OPS/ruler-src checkout -q db43f92ff634bbce1c33d1fb15858aec4bba509a
cd $OPS/ruler-src/scripts/data/synthetic/json
python download_paulgraham_essay.py
curl -sL -o squad.json https://rajpurkar.github.io/SQuAD-explorer/dataset/dev-v2.0.json
curl -sL -o hotpotqa.json https://huggingface.co/datasets/namlh2004/hotpotqa/resolve/7e54db4656209750ff487f6fdf8e39a66dba136b/hotpot_dev_distractor_v1.json
# english_words.json is a Git LFS object in RULER (sha256 affcd6d4...bc2eca)
curl -sL -o english_words.json https://media.githubusercontent.com/media/NVIDIA/RULER/db43f92ff634bbce1c33d1fb15858aec4bba509a/scripts/data/synthetic/json/english_words.json
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
# Training corpus: 40 Project Gutenberg books; excludes the scaling-probe books 98, 1342, 2701.
cd $OPS/corpus
for id in 1661 84 11 1080 64317 2600 345 174 43 46 1260 1952 768 25344 2542 5200 4300 1400 730 158 120 2554 16328 36 205 1232 3207 2591 74 76 1184 135 996 28054 3296 41 6130 1497 8800 2814; do
  curl -sL -o pg$id.txt https://www.gutenberg.org/cache/epub/$id/pg$id.txt
done
