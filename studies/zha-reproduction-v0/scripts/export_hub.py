"""Export trained ZHA routers to one Hugging Face model repo (safetensors + config + model card).

Layout: <model>/<geometry>/router.safetensors (tensor "reference_queries" [layers, kv_heads, R, head_dim], fp32)
        <model>/<geometry>/config.json (base model + revision, geometry, layer ids, training recipe, final KL)

  python export_hub.py --ckpt-dir DIR --repo kvnloo/zha-routers-qwen-small [--private] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from pathlib import Path

import torch
from safetensors.torch import save_file

CARD = """---
license: apache-2.0
library_name: pytorch
tags: [sparse-attention, long-context, zha, hierarchical-attention, distillation]
base_model: {base_models}
---

# ZHA routers for small Qwen models (independent reimplementation)

Reference-query routers for **Zyphra Hierarchical Attention**
([arXiv:2610.42112](https://arxiv.org/abs/2610.42112v1)), trained by the z0evals project with our own
reimplementation of the paper's Section III. **These are not Zyphra's weights**; Zyphra has not released any.

Each router is the only trainable part of ZHA: 16 reference queries per KV head of every full-attention layer,
distilled with a per-level KL against the frozen model's dense attention. Two geometries are provided:
`deep-c4l6` (chunk 4, six levels) and `wide-c256l1` (chunk 256, one level).

| base model | revision | geometry | params | training tokens | final KL (level sum) |
|---|---|---|---:|---:|---:|
{rows}

Training used about 3–5M tokens of public-domain Project Gutenberg books at 8K context (the paper used ~4B
tokens of a mid-training mixture at 32K), AdamW (0.9, 0.95), eps 1e-15, peak LR 3.2e-2 with WSD, gradient clip 1.0.

Loading: `reference_queries[i]` belongs to full-attention layer `layer_ids[i]` in `config.json`. Queries are in the
model's post-q_norm, pre-RoPE space and are rotated to each tree node's last position at use. The reference
implementation, evaluation harness and results live in the z0evals study
[`zha-reproduction-v0`](https://github.com/kvnloo/z0evals/tree/main/studies/zha-reproduction-v0).

Limitations: research artifacts at a very small training budget; evaluated only on RULER-13 at 4K/8K and a small
MMLU-Pro subset; no kernels, no latency claims.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt-dir", type=Path, required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--private", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stage", type=Path, required=True)
    a = ap.parse_args()
    rows, bases = [], set()
    for ck_path in sorted(a.ckpt_dir.glob("*.pt")):
        ck = torch.load(ck_path)
        log = [json.loads(l) for l in open(str(ck_path) + ".log.jsonl")]
        g = ck["geometry"]
        d = a.stage / ck["model"] / g["name"]
        d.mkdir(parents=True, exist_ok=True)
        save_file({"reference_queries": ck["refs"].float().contiguous()}, str(d / "router.safetensors"))
        from zha_run import MODELS  # base repo id + pinned revision
        repo, rev = MODELS[ck["model"]]
        final_kl = st.mean(r["kl_sum"] for r in log[-10:])
        cfg = {"base_model": repo, "base_revision": ck["revision"] or rev, "geometry": g, "layer_ids": ck["layer_ids"],
               "shape": list(ck["refs"].shape), "dtype": "float32",
               "training": {"steps": ck["steps"], "batch": ck["batch"], "seq_len": ck["seq"], "tokens": log[-1]["tokens"],
                            "peak_lr": ck["lr"], "schedule": "WSD (20 warmup, linear decay over last 20% to 1%)",
                            "optimizer": "AdamW betas=(0.9,0.95) eps=1e-15 wd=0", "grad_clip": 1.0,
                            "queries_per_layer_per_sequence": ck["queries_per_layer"], "seed": ck["seed"],
                            "corpus": "Project Gutenberg books (public domain), 8K windows",
                            "final_kl_level_sum_last10": final_kl,
                            "final_kl_levels_last_step": log[-1]["kl_levels"]}}
        (d / "config.json").write_text(json.dumps(cfg, indent=1) + "\n")
        n = ck["refs"].numel()
        rows.append(f"| {repo} | `{(ck['revision'] or rev)[:7]}` | {g['name']} | {n:,} | {log[-1]['tokens']:,} | {final_kl:.3f} |")
        bases.add(repo)
    (a.stage / "README.md").write_text(CARD.format(base_models=json.dumps(sorted(bases)), rows="\n".join(rows)))
    print("\n".join(rows))
    if a.dry_run:
        return
    from huggingface_hub import HfApi
    api = HfApi()
    api.create_repo(a.repo, repo_type="model", private=a.private, exist_ok=True)
    info = api.upload_folder(repo_id=a.repo, folder_path=str(a.stage), repo_type="model",
                             commit_message="ZHA routers: reimplementation of arXiv:2610.42112 for small Qwen models")
    print("uploaded", info.commit_url)


if __name__ == "__main__":
    main()
