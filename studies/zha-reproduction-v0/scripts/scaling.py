"""Dense top-p set size vs causal context length (paper Fig. 1 protocol, smaller cohort).

Prefill each book window densely; at log-spaced positions take that position's query in every
full-attention head and record the size of the smallest key set holding p of its attention.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import torch

import zha_run

PS = (0.5, 0.8, 0.9, 0.95)


@torch.no_grad()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--texts", required=True)
    ap.add_argument("--length", type=int, default=32768)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    r = zha_run.Runner(args.model, max_len=args.length + 8)
    books = zha_run.corpus_ids(r.tok, Path(args.texts))
    positions = sorted({int(256 * 2 ** (i / 4)) - 1 for i in range(int(4 * math.log2(args.length / 256)) + 1)})
    positions = [p for p in positions if p < args.length]
    out = open(args.out, "a")
    for bi, ids in enumerate(books):
        seg = ids[: args.length]
        def measure(module, q, k, bi=bi):
            q, k = q[0].float(), k[0].float()
            grp = q.shape[0] // k.shape[0]
            for t in positions:
                qq = q[:, t].view(k.shape[0], grp, -1)
                a = torch.softmax(torch.einsum("hgd,hnd->hgn", qq, k[:, : t + 1]) * q.shape[-1] ** -0.5, -1)
                sp = a.sort(-1, descending=True).values.cumsum(-1)
                sizes = {str(p): ((sp < p).sum(-1) + 1).flatten().tolist() for p in PS}
                out.write(json.dumps({"model": args.model, "book": bi, "layer": module.layer_idx, "n": t + 1,
                                      "sizes": sizes}) + "\n")

        r.capture = measure
        r.model(torch.tensor([seg], device="cuda"), use_cache=False, logits_to_keep=1)
        r.capture = None
        out.flush()
        print(f"{args.model} book {bi} done", flush=True)


if __name__ == "__main__":
    main()
