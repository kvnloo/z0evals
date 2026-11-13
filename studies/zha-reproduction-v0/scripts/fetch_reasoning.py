"""Fetch pinned public reasoning eval subsets from the HF Hub (pinned revisions).

MMLU-Pro: 10 questions per subject (14 subjects) from the test split, first-N per subject in split order.
GPQA Diamond: all 198 questions (gated dataset; uses the local HF token). The correct answer is listed
first in the CSV, so options are shuffled with random.Random(Record ID).
Outputs JSONL with fields id, question, options (list), answer (letter), source.
"""
import csv
import json
import random
import string
import sys
from pathlib import Path

import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
MMLU = ("TIGER-Lab/MMLU-Pro", "b189ec765aa7ed75c8acfea42df31fdae71f97be")
GPQA = ("Idavidrein/gpqa", "83022cefff930aea54f654c0b282e74b9eeda5c6")

t = pq.read_table(hf_hub_download(MMLU[0], "data/test-00000-of-00001.parquet", repo_type="dataset", revision=MMLU[1])).to_pylist()
per, picked = {}, []
for x in t:
    if per.get(x["category"], 0) < 10:
        per[x["category"]] = per.get(x["category"], 0) + 1
        picked.append({"id": f"mmlupro-{x['question_id']}", "question": x["question"], "options": list(x["options"]),
                       "answer": x["answer"], "source": "mmlu-pro", "category": x["category"]})
(OUT / "mmlu-pro.jsonl").write_text("".join(json.dumps(p) + "\n" for p in picked))

items = []
try:
    gpqa_csv = hf_hub_download(GPQA[0], "gpqa_diamond.csv", repo_type="dataset", revision=GPQA[1])
except Exception as e:  # gated: the account must accept the dataset terms first
    gpqa_csv = None
    print(f"gpqa unavailable: {type(e).__name__}")
with open(gpqa_csv or __file__, newline="") as f:
    for x in (csv.DictReader(f) if gpqa_csv else []):
        opts = [x["Correct Answer"], x["Incorrect Answer 1"], x["Incorrect Answer 2"], x["Incorrect Answer 3"]]
        order = list(range(4))
        random.Random(x["Record ID"]).shuffle(order)
        items.append({"id": f"gpqa-{x['Record ID']}", "question": x["Question"].strip(),
                      "options": [opts[i].strip() for i in order], "answer": string.ascii_uppercase[order.index(0)],
                      "source": "gpqa-diamond"})
if items:
    (OUT / "gpqa-diamond.jsonl").write_text("".join(json.dumps(p) + "\n" for p in items))
meta = {"mmlu-pro": {"dataset": MMLU[0], "revision": MMLU[1], "n": len(picked), "categories": len(per),
                     "selection": "first 10 per category in test split order"},
        "gpqa-diamond": {"dataset": GPQA[0], "revision": GPQA[1], "n": len(items), "option_shuffle": "random.Random(Record ID)"}}
(OUT / "meta.json").write_text(json.dumps(meta, indent=1))
print(json.dumps({k: v["n"] for k, v in meta.items()}))
