"""Aggregate raw ZHA reproduction outputs into the study's public data files (stdlib only).

Inputs (explicit allowlist under --ops): ckpt/<model>-<geometry>.pt.log.jsonl training logs,
raw/ruler-<model>.jsonl, raw/mc-<model>.jsonl, raw/scaling-<model>.jsonl.
Outputs under --study/data: training.json, ruler.json, ruler-rows.json, mc.json, scaling.json.
RULER rows keep only short predictions on public synthetic tasks; no private text is imported.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import random
import statistics as st
from pathlib import Path

MODELS = ["qwen3-0.6b", "qwen3.5-0.8b", "qwen2.5-1.5b", "qwen3-1.7b", "qwen3.5-4b"]
GEOMS = ["deep-c4l6", "wide-c256l1"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def boot_ci(diffs: list, n: int = 4000, seed: int = 0) -> list[float]:
    rng = random.Random(seed)
    m = len(diffs)
    means = sorted(sum(rng.choice(diffs) for _ in range(m)) / m for _ in range(n))
    return [means[int(0.025 * n)], means[int(0.975 * n) - 1]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ops", type=Path, required=True)
    ap.add_argument("--study", type=Path, required=True)
    a = ap.parse_args()
    out = a.study / "data"
    out.mkdir(parents=True, exist_ok=True)
    prov = []

    training = []
    for m in MODELS:
        for g in GEOMS:
            log = a.ops / "ckpt" / f"{m}-{g}.pt.log.jsonl"
            if not log.exists():
                continue
            recs = [json.loads(l) for l in log.open()]
            last = recs[-10:]
            levels = sorted({int(k) for r in last for k in r["kl_levels"]})
            training.append({"model": m, "geometry": g, "steps": len(recs), "tokens": recs[-1]["tokens"],
                             "minutes": recs[-1]["sec"] / 60,
                             "kl_first": recs[0]["kl_sum"], "kl_final": st.mean(r["kl_sum"] for r in last),
                             "kl_final_levels": {str(l): st.mean(r["kl_levels"][str(l)] for r in last) for l in levels},
                             "kl_curve": [[r["step"], r["kl_sum"]] for r in recs[:: max(1, len(recs) // 30)]]})
            prov.append({"file": f"ckpt/{log.name}", "sha256": sha(log), "rows": len(recs)})
    (out / "training.json").write_text(json.dumps(training, indent=1) + "\n")

    ruler, rows_pub = [], []
    for m in MODELS:
        f = a.ops / "raw" / f"ruler-{m}.jsonl"
        if not f.exists():
            continue
        rows = [json.loads(l) for l in f.open()]
        prov.append({"file": f"raw/{f.name}", "sha256": sha(f), "rows": len(rows)})
        seen = set()
        for r in rows:
            k = (r["length"], r["task"], r["index"], r["arm"])
            assert k not in seen, k
            seen.add(k)
            rows_pub.append({x: r[x] for x in ["model", "length", "task", "index", "arm", "score", "key_share",
                                               "gen_tokens", "prompt_tokens", "pred"]})
        by = collections.defaultdict(dict)
        for r in rows:
            by[(r["length"], r["arm"])][(r["task"], r["index"])] = r
        for (length, arm), d in sorted(by.items()):
            dense = by[(length, "dense")]
            keys = sorted(set(d) & set(dense))
            tasks = sorted({t for t, _ in keys})
            per_task = {t: 100 * st.mean(d[k]["score"] for k in keys if k[0] == t) for t in tasks}
            diffs = [100 * (d[k]["score"] - dense[k]["score"]) for k in keys]
            ruler.append({"model": m, "length": length, "arm": arm, "n_examples": len(keys), "n_tasks": len(tasks),
                          "ruler_score": st.mean(per_task.values()), "per_task": per_task,
                          "key_share": st.mean(d[k]["key_share"] for k in keys),
                          "paired_diff_vs_dense": st.mean(diffs), "paired_diff_ci95": boot_ci(diffs) if arm != "dense" else [0, 0],
                          "complete": len(tasks) == 13})
    (out / "ruler.json").write_text(json.dumps(ruler, indent=1) + "\n")
    (out / "ruler-rows.json").write_text(json.dumps(rows_pub) + "\n")

    mc = []
    for m in MODELS:
        f = a.ops / "raw" / f"mc-{m}.jsonl"
        if not f.exists():
            continue
        rows = [json.loads(l) for l in f.open()]
        prov.append({"file": f"raw/{f.name}", "sha256": sha(f), "rows": len(rows)})
        by = collections.defaultdict(dict)
        for r in rows:
            by[r["arm"]][r["id"]] = r
        for arm, d in by.items():
            ids = sorted(set(d) & set(by["dense"]))
            diffs = [100 * (int(d[i]["correct"]) - int(by["dense"][i]["correct"])) for i in ids]
            mc.append({"model": m, "arm": arm, "n": len(ids), "accuracy": 100 * st.mean(int(d[i]["correct"]) for i in ids),
                       "unparsed": sum(d[i]["pred"] is None for i in ids),
                       "key_share": st.mean(d[i]["key_share"] for i in ids),
                       "paired_diff_vs_dense": st.mean(diffs), "paired_diff_ci95": boot_ci(diffs) if arm != "dense" else [0, 0],
                       "mean_gen_tokens": st.mean(d[i]["gen_tokens"] for i in ids)})
    (out / "mc.json").write_text(json.dumps(mc, indent=1) + "\n")

    scaling = []
    for m in MODELS:
        f = a.ops / "raw" / f"scaling-{m}.jsonl"
        if not f.exists():
            continue
        acc = collections.defaultdict(list)
        n_rows = 0
        for l in f.open():
            r = json.loads(l)
            n_rows += 1
            for p, sizes in r["sizes"].items():
                acc[(p, r["n"])].extend(sizes)
        prov.append({"file": f"raw/{f.name}", "sha256": sha(f), "rows": n_rows})
        for p in sorted({p for p, _ in acc}):
            pts = sorted((n, st.mean(v)) for (pp, n), v in acc.items() if pp == p)
            fit = [(math.log(n), math.log(s)) for n, s in pts if n >= 1024]
            slope, _ = st.linear_regression([x for x, _ in fit], [y for _, y in fit])
            scaling.append({"model": m, "p": float(p), "points": [[n, s] for n, s in pts], "exponent_1k_plus": slope,
                            "fit_range": [min(n for n, _ in pts if n >= 1024), max(n for n, _ in pts)]})
    (out / "scaling.json").write_text(json.dumps(scaling, indent=1) + "\n")
    (out / "provenance.json").write_text(json.dumps({"raw_inputs": prov}, indent=1) + "\n")
    print(json.dumps({"training": len(training), "ruler_cells": len(ruler), "ruler_rows": len(rows_pub), "mc": len(mc),
                      "scaling": len(scaling)}))


if __name__ == "__main__":
    main()
