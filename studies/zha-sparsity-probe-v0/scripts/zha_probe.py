"""Training-free probe of the two load-bearing ZHA claims on small local models.

ZHA (Lufkin et al., arXiv:2610.42112) routes each decode query top-down through a
tree of compressed key summaries using top-p selection. This script does not
reimplement ZHA: its summaries are learned reference queries distilled from the
dense model. Here every summary is a plain key centroid with a log-count bias, so
the tree is a zero-training comparator, not a bound on trained ZHA.

Two experiments:

  scaling   Prefill long public-domain books with dense attention. At log-spaced
            positions t, take the query at t and compute (a) the size of the
            token-level top-p set over keys[0..t] and (b) how much true attention
            mass a centroid tree / flat chunk router keeps, and at what cost.
  niah      Multi-key needle-in-a-haystack. Prefill densely, then decode with the
            router masking every full-attention layer's decode step.

Usage:
  python zha_probe.py scaling --model qwen3-0.6b --texts DIR --out raw.jsonl
  python zha_probe.py niah    --model qwen3-0.6b --texts DIR --out raw.jsonl
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import torch
from transformers import AttentionInterface, AutoModelForCausalLM, AutoTokenizer
from transformers.integrations.sdpa_attention import sdpa_attention_forward

MODELS = {
    # Pins match the z0intelligence SLM lanes (AGENTS.md: OpenJev 0.6B test lane, OpenJev 4B).
    "qwen3-0.6b": ("Qwen/Qwen3-0.6B", "c1899de289a04d12100db370d81485cdf75e47ca"),
    "qwen3.5-4b": ("Qwen/Qwen3.5-4B", "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"),
}


@dataclass(frozen=True)
class Router:
    name: str
    kind: str  # "tree" | "oracle" | "dense"
    chunk: int = 4
    depth: int = 1
    p: float = 0.95
    sinks: int = 4
    window: int = 128


def scaling_routers() -> list[Router]:
    rs = [Router(f"oracle-p{p}", "oracle", p=p, sinks=0, window=0) for p in (0.5, 0.8, 0.9, 0.95)]
    for p in (0.9, 0.95, 0.99):
        rs.append(Router(f"flat64-p{p}", "tree", chunk=64, depth=1, p=p))
        rs.append(Router(f"tree4x3-p{p}", "tree", chunk=4, depth=3, p=p))
        rs.append(Router(f"tree4x6-p{p}", "tree", chunk=4, depth=6, p=p))
        rs.append(Router(f"tree16x2-p{p}", "tree", chunk=16, depth=2, p=p))
    # Same per-level budget folded to the depth: 0.99^6 ~ 0.94 cumulative.
    rs.append(Router("tree4x6-p0.999", "tree", chunk=4, depth=6, p=0.999))
    return rs


def niah_routers() -> list[Router]:
    return [
        Router("dense", "dense"),
        Router("flat64-p0.9", "tree", chunk=64, depth=1, p=0.9),
        Router("flat64-p0.99", "tree", chunk=64, depth=1, p=0.99),
        Router("tree4x3-p0.95", "tree", chunk=4, depth=3, p=0.95),
        Router("tree4x3-p0.99", "tree", chunk=4, depth=3, p=0.99),
        Router("tree4x6-p0.99", "tree", chunk=4, depth=6, p=0.99),
        Router("tree4x6-p0.999", "tree", chunk=4, depth=6, p=0.999),
        Router("window-only", "tree", chunk=4, depth=1, p=0.0),
    ]


def top_p_mask(scores: torch.Tensor, cand: torch.Tensor, p: float) -> torch.Tensor:
    """Smallest candidate set whose softmax mass reaches p (always >=1 candidate when any exist)."""
    s = scores.masked_fill(~cand, float("-inf"))
    probs = torch.softmax(s, dim=-1).nan_to_num(0.0)
    sp, idx = probs.sort(dim=-1, descending=True)
    before = sp.cumsum(-1) - sp
    keep_sorted = (before < p) & (sp > 0)
    keep_sorted[..., 0] |= sp[..., 0] > 0
    keep = torch.zeros_like(cand)
    keep.scatter_(-1, idx, keep_sorted)
    return keep & cand


def route(q: torch.Tensor, k: torch.Tensor, scale: float, r: Router):
    """q: [KVH, M, d] fp32, k: [KVH, n, d] fp32 -> (token_sel [KVH,M,n] bool, scored [KVH,M]).

    scored is an IDEALIZED operation count: selected-candidate summary scores
    plus finally selected keys. This reference code actually scores all nodes
    at every level, rebuilds all centroids and uses dense masked decode; the
    count excludes construction, sorting, and memory traffic. It is neither
    measured work nor a latency / GPU-speedup estimate. Oracle counts exclude
    its full scan and describe support size only.
    """
    kvh, m, _ = q.shape
    n = k.shape[1]
    dev = q.device
    pos = torch.arange(n, device=dev)
    if r.kind == "dense":
        return torch.ones(kvh, m, n, dtype=torch.bool, device=dev), torch.full((kvh, m), float(n), device=dev)
    extra = (pos < r.sinks) | (pos >= n - r.window)
    if r.kind == "oracle":
        probs = torch.softmax(torch.einsum("hmd,hnd->hmn", q, k) * scale, -1)
        sel = top_p_mask(probs.log(), torch.ones_like(probs, dtype=torch.bool), r.p) | extra
        return sel, sel.sum(-1).float()
    # Centroid tree: level l node j covers keys [j*c^l, (j+1)*c^l).
    levels = []
    for lvl in range(1, r.depth + 1):
        span = r.chunk**lvl
        nn = math.ceil(n / span)
        node = (pos // span).clamp(max=nn - 1)
        sums = torch.zeros(kvh, nn, k.shape[2], device=dev).index_add_(1, node, k)
        cnt = torch.bincount(node, minlength=nn).float()
        levels.append((sums / cnt[None, :, None], cnt))
    cent, cnt = levels[-1]
    cand = torch.ones(kvh, m, cent.shape[1], dtype=torch.bool, device=dev)
    scored = cand.sum(-1).float()
    for lvl in range(r.depth, 0, -1):
        cent, cnt = levels[lvl - 1]
        s = torch.einsum("hmd,hnd->hmn", q, cent) * scale + cnt.log()
        sel = top_p_mask(s, cand, r.p) if r.p > 0 else torch.zeros_like(cand)
        if lvl > 1:
            child_n = levels[lvl - 2][0].shape[1]
            parent = torch.arange(child_n, device=dev) // r.chunk
            cand = sel[..., parent]
            scored += cand.sum(-1)
        else:
            tok_sel = sel[..., pos // r.chunk] | extra
    attended = tok_sel.sum(-1).float()
    return tok_sel, scored + attended


class Probe:
    """Global switchboard read by the registered attention function."""

    mode = "off"  # off | scaling | sparse
    positions: list[int] = []
    routers: list[Router] = []
    sparse: Router | None = None
    rows: list[dict] = []
    decode_stats: list[tuple[float, float]] = []
    ctx: dict = {}


def zha_probe_attention(module, query, key, value, attention_mask, scaling=None, **kw):
    scale = scaling if scaling is not None else query.shape[-1] ** -0.5
    q_len = query.shape[2]
    if Probe.mode == "sparse" and q_len == 1 and Probe.sparse and Probe.sparse.kind != "dense":
        h, kvh = query.shape[1], key.shape[1]
        g = h // kvh
        q = query[0, :, 0].float().view(kvh, g, -1)
        k = key[0].float()
        sel, scored = route(q, k, scale, Probe.sparse)
        s = torch.einsum("hgd,hnd->hgn", q, k) * scale
        s = s.masked_fill(~sel, float("-inf"))
        out = torch.einsum("hgn,hnd->hgd", torch.softmax(s, -1), value[0].float())
        n = k.shape[1]
        Probe.decode_stats.append((sel.float().sum(-1).mean().item() / n, scored.mean().item() / n))
        return out.reshape(1, 1, h, -1).to(query.dtype), None
    out = sdpa_attention_forward(module, query, key, value, attention_mask, scaling=scaling, **kw)
    if Probe.mode == "scaling" and q_len > 1:
        _scaling_capture(module, query, key, scale)
    return out


def _scaling_capture(module, query, key, scale):
    h, kvh = query.shape[1], key.shape[1]
    g = h // kvh
    for t in Probe.positions:
        if t >= query.shape[2]:
            continue
        q = query[0, :, t].float().view(kvh, g, -1)
        k = key[0, :, : t + 1].float()
        probs = torch.softmax(torch.einsum("hgd,hnd->hgn", q, k) * scale, -1)
        n = t + 1
        for r in Probe.routers:
            sel, scored = route(q, k, scale, r)
            recall = (probs * sel).sum(-1)
            Probe.rows.append(
                {
                    **Probe.ctx,
                    "layer": module.layer_idx,
                    "n": n,
                    "router": r.name,
                    "attended": sel.sum(-1).float().flatten().tolist(),
                    "scored": scored.flatten().tolist(),
                    "recall": recall.flatten().tolist(),
                }
            )


AttentionInterface.register("zha_probe", zha_probe_attention)


def load(model_key: str):
    repo, rev = MODELS[model_key]
    tok = AutoTokenizer.from_pretrained(repo, revision=rev)
    model = AutoModelForCausalLM.from_pretrained(
        repo, revision=rev, dtype=torch.bfloat16, device_map="cuda", attn_implementation="zha_probe"
    )
    model.eval()
    return tok, model


def book_tokens(tok, texts: Path) -> dict[str, list[int]]:
    out = {}
    for f in sorted(texts.glob("pg*.txt")):
        raw = f.read_text(encoding="utf-8", errors="ignore")
        start = raw.find("*** START OF")
        end = raw.find("*** END OF")
        body = raw[raw.find("\n", start) + 1 : end] if start >= 0 and end > start else raw
        out[f.stem] = tok(body, add_special_tokens=False).input_ids
    return out


def log_positions(lo: int, hi: int, per_octave: int = 4) -> list[int]:
    pts = sorted({int(round(lo * 2 ** (i / per_octave))) - 1 for i in range(int(per_octave * math.log2(hi / lo)) + 1)})
    return [p for p in pts if p < hi]


@torch.no_grad()
def run_scaling(args):
    tok, model = load(args.model)
    books = book_tokens(tok, Path(args.texts))
    Probe.mode, Probe.routers = "scaling", scaling_routers()
    Probe.positions = log_positions(256, args.length)
    out = open(args.out, "a")
    for name, ids in books.items():
        for w in range(args.windows):
            off = w * (len(ids) // max(args.windows, 1)) // 2
            seg = ids[off : off + args.length]
            if len(seg) < args.length:
                continue
            Probe.rows, Probe.ctx = [], {"model": args.model, "doc": f"{name}@{off}"}
            t0 = time.time()
            model(torch.tensor([seg], device="cuda"), use_cache=False, logits_to_keep=1)
            for row in Probe.rows:
                out.write(json.dumps(row) + "\n")
            out.flush()
            print(f"{name}@{off}: {len(Probe.rows)} rows in {time.time() - t0:.1f}s", flush=True)
    Probe.mode = "off"


WORDS = "amber basil cobalt delta ember falcon garnet harbor indigo juniper kestrel lantern meadow nickel orchid pepper quartz raven saffron tundra umber violet willow yarrow zephyr".split()


def niah_example(rng: random.Random, tok, filler: list[int], length: int, keys: int = 4):
    names = rng.sample(WORDS, keys)
    nums = [str(rng.randint(1_000_000, 9_999_999)) for _ in names]
    needles = [tok(f" One of the special magic numbers for {w} is: {v}. ", add_special_tokens=False).input_ids for w, v in zip(names, nums)]
    target = rng.randrange(keys)
    q = f"What is the special magic number for {names[target]} mentioned in the provided text? Answer with only the number."
    budget = length - sum(map(len, needles)) - 80
    off = rng.randrange(0, len(filler) - budget)
    hay = filler[off : off + budget]
    depths = sorted(rng.sample(range(0, len(hay)), keys))
    ctx: list[int] = []
    prev = 0
    for d, nd in zip(depths, needles):
        ctx += hay[prev:d] + nd
        prev = d
    ctx += hay[prev:]
    depth = depths[target] / len(hay)
    return ctx, q, nums[target], depth


@torch.no_grad()
def run_niah(args):
    tok, model = load(args.model)
    books = book_tokens(tok, Path(args.texts))
    filler = [t for ids in books.values() for t in ids]
    rng = random.Random(args.seed)
    out = open(args.out, "a")
    routers = niah_routers()
    for length in args.lengths:
        for i in range(args.n):
            ctx, q, answer, depth = niah_example(rng, tok, filler, length)
            head = tok.apply_chat_template(
                [{"role": "user", "content": "<<CTX>>\n\n" + q}],
                tokenize=False, add_generation_prompt=True, enable_thinking=False,
            )
            pre, post = head.split("<<CTX>>")
            ids = tok(pre, add_special_tokens=False).input_ids + ctx + tok(post, add_special_tokens=False).input_ids
            x = torch.tensor([ids], device="cuda")
            for r in routers:
                Probe.mode, Probe.sparse, Probe.decode_stats = "sparse", r, []
                gen = model.generate(x, max_new_tokens=args.max_new, do_sample=False, temperature=None, top_p=None, top_k=None)
                text = tok.decode(gen[0, x.shape[1] :], skip_special_tokens=True)
                st = Probe.decode_stats
                row = {
                    "model": args.model, "length": length, "i": i, "depth": round(depth, 3), "router": r.name,
                    "correct": answer in text, "output": text.strip()[:40],
                    "attended_frac": sum(a for a, _ in st) / len(st) if st else 1.0,
                    "scored_frac": sum(b for _, b in st) / len(st) if st else 1.0,
                    "prompt_tokens": len(ids),
                }
                out.write(json.dumps(row) + "\n")
            out.flush()
            print(f"len={length} i={i} done", flush=True)
    Probe.mode = "off"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exp", choices=["scaling", "niah"])
    ap.add_argument("--model", default="qwen3-0.6b", choices=list(MODELS))
    ap.add_argument("--texts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--length", type=int, default=32768)
    ap.add_argument("--windows", type=int, default=2)
    ap.add_argument("--lengths", type=int, nargs="+", default=[4096, 8192, 16384])
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--max-new", type=int, default=16)
    ap.add_argument("--seed", type=int, default=20261103)
    args = ap.parse_args()
    torch.manual_seed(0)
    {"scaling": run_scaling, "niah": run_niah}[args.exp](args)


if __name__ == "__main__":
    main()
