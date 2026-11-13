"""Run harness: load a frozen model, distill ZHA routers, and decode with ZHA routing.

  python zha_run.py train --model qwen3-0.6b --geometry deep-c4l6 --corpus DIR --out CKPT.pt
  python zha_run.py check-rope --model qwen3-0.6b

Evaluation drivers import `Runner` from here.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import random
import time
from pathlib import Path

import torch
from transformers import AttentionInterface, AutoModelForCausalLM, AutoTokenizer
from transformers.integrations.sdpa_attention import sdpa_attention_forward

import zha

MODELS = {
    # z0intelligence lanes (manifests/models.z0int.json) plus nearby open models that fit 12GB.
    "qwen3-0.6b": ("Qwen/Qwen3-0.6B", "c1899de289a04d12100db370d81485cdf75e47ca"),
    "qwen3-1.7b": ("Qwen/Qwen3-1.7B", "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"),
    "qwen2.5-1.5b": ("Qwen/Qwen2.5-1.5B-Instruct", "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"),
    "qwen3.5-0.8b": ("Qwen/Qwen3.5-0.8B", "2fc06364715b967f1860aea9cf38778875588b17"),
    "qwen3.5-4b": ("Qwen/Qwen3.5-4B", "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"),
}


class State:
    mode = "dense"  # dense | train | sparse
    runner: "Runner | None" = None


def zha_attention(module, query, key, value, attention_mask, scaling=None, **kw):
    r = State.runner
    scale = scaling if scaling is not None else query.shape[-1] ** -0.5
    if State.mode == "sparse" and query.shape[2] == 1 and r is not None and r.trees is not None:
        return r.sparse_decode(module, query, key, value, scale)
    out = sdpa_attention_forward(module, query, key, value, attention_mask, scaling=scaling, **kw)
    if r is not None and State.mode == "train":
        r.train_layer(module, query, key, scale)
    if r is not None and State.mode == "sparse" and query.shape[2] > 1:
        r.prefill_layer(module, key)
    if r is not None and callable(r.capture):
        r.capture(module, query.detach(), key.detach())
    elif r is not None and r.capture is not None:
        r.capture[module.layer_idx] = (query.detach(), key.detach())
    return out


AttentionInterface.register("zha", zha_attention)


class Runner:
    def __init__(self, model_key: str, max_len: int = 40960):
        repo, rev = MODELS[model_key]
        self.key = model_key
        self.tok = AutoTokenizer.from_pretrained(repo, revision=rev)
        self.model = AutoModelForCausalLM.from_pretrained(
            repo, revision=rev, dtype=torch.bfloat16, device_map="cuda", attn_implementation="zha")
        self.model.eval().requires_grad_(False)
        self.revision = getattr(self.model.config, "_commit_hash", None) or rev
        self.layers = zha.full_attention_layers(self.model)
        a = self.layers[0]
        self.kvh = a.config.num_key_value_heads
        self.heads = a.config.num_attention_heads
        self.d = a.head_dim
        self.rope = zha.Rope(self.model, max_len, "cuda")
        self.refs: zha.ReferenceQueries | None = None
        self.geometry: zha.Geometry | None = None
        self.trees: dict[int, zha.LayerTree] | None = None
        self.p = 0.95
        self.capture = None
        self.stats: list[float] = []
        self.train_q = 128
        self.level_losses: dict[int, list[float]] = {}
        State.runner = self

    # ---------- training ----------
    def init_refs(self, g: zha.Geometry, init_text_ids: list[int]):
        """Init each layer's references from real pre-RoPE queries of its KV group (un-rotated)."""
        self.geometry = g
        self.refs = zha.ReferenceQueries([m.layer_idx for m in self.layers], self.kvh, g.refs, self.d).cuda()
        self.capture = {}
        with torch.no_grad():
            self.model(torch.tensor([init_text_ids], device="cuda"), use_cache=False, logits_to_keep=1)
            gen = torch.Generator(device="cpu").manual_seed(0)
            for m in self.layers:
                q, _ = self.capture[m.layer_idx]
                q = q[0].float()  # [H, T, d]
                t = q.shape[1]
                pos = torch.randint(1, t, (self.kvh, g.refs), generator=gen).cuda()
                grp = self.heads // self.kvh
                head = torch.arange(self.kvh, device="cuda")[:, None] * grp
                picked = q[head, pos]  # [KVH, R, d] post-RoPE at pos
                # Undo RoPE by rotating with the negative angle (sin -> -sin).
                cos = self.rope.cos[pos].reshape(-1, 1, self.rope.cos.shape[-1])  # [KVH*R, 1, rd]
                sin = self.rope.sin[pos].reshape(-1, 1, self.rope.sin.shape[-1])
                x = picked.reshape(-1, 1, 1, self.d)  # [KVH*R, 1 head, 1 pos, d]
                un, _ = self.rope.apply(x, x, cos, -sin)
                self.refs.q.data[self.refs.index[m.layer_idx]] = un.view(self.kvh, g.refs, self.d)
        self.capture = None

    def train_layer(self, module, query, key, scale):
        with torch.enable_grad():
            q = query[0].float()
            k = key[0].float()
            t = q.shape[1]
            lo = self.geometry.chunk  # need at least one complete level-1 chunk
            pos = torch.randint(lo, t, (self.train_q,), device="cuda")
            losses = zha.distill_loss(q, k, self.refs[module.layer_idx], self.rope, self.geometry, scale, pos)
            total = sum(losses)
            (total / (len(self.layers) * self.accum)).backward()
            for i, l in enumerate(losses):
                self.level_losses.setdefault(i + 1, []).append(l.item())

    # ---------- sparse decode ----------
    def start_sparse(self, g: zha.Geometry, refs: zha.ReferenceQueries, p: float):
        self.geometry, self.refs, self.p = g, refs, p
        self.trees = {m.layer_idx: zha.LayerTree(refs[m.layer_idx].detach(), self.rope, g, m.scaling, torch.bfloat16) for m in self.layers}
        self.stats = []

    def prefill_layer(self, module, key):
        if self.trees is not None:
            self.trees[module.layer_idx].update(key[0].float())

    def sparse_decode(self, module, query, key, value, scale):
        tree = self.trees[module.layer_idx]
        k = key[0].float()
        n = k.shape[1]
        tree.update(k)
        grp = self.heads // self.kvh
        q = query[0, :, 0].float().view(self.kvh, grp, self.d)
        mask = tree.route(q, n, self.p)  # [KVH, G, n]
        s = torch.einsum("hgd,hnd->hgn", q, k) * scale
        s = s.masked_fill(~mask, float("-inf"))
        out = torch.einsum("hgn,hnd->hgd", torch.softmax(s, -1), value[0].float())
        self.stats.append(mask.float().mean().item())
        return out.reshape(1, 1, self.heads, self.d).to(query.dtype), None

    # ---------- generation with shared dense prefill ----------
    @torch.no_grad()
    def generate_arms(self, ids: list[int], arms: list[tuple[str, zha.Geometry | None, object, float]], max_new: int,
                      stop_ids: set[int]):
        """Dense prefill of ids[:-1] once; each arm then decodes from the last prompt token onward.

        Every generated token, including the first, comes from a routed decode step.
        Returns {arm: (text, mean decode key share, generated tokens)}.
        """
        from transformers import DynamicCache

        x = torch.tensor([ids[:-1]], device="cuda")
        results = {}
        State.mode = "dense"
        self.trees = None
        cache = DynamicCache(config=self.model.config)
        self.model(x, past_key_values=cache, use_cache=True, logits_to_keep=1)
        snapshot = copy.deepcopy(cache)  # KV + recurrent (hybrid) state after the dense prefill
        for name, g, refs, p in arms:
            cache = copy.deepcopy(snapshot)
            if g is None:
                State.mode, self.trees = "dense", None
            else:
                State.mode = "sparse"
                self.start_sparse(g, refs, p)
                for m in self.layers:  # build each layer's tree from the prompt keys
                    self.trees[m.layer_idx].update(cache.layers[m.layer_idx].keys[0].float())
            toks: list[int] = []
            nxt = ids[-1]
            while len(toks) < max_new and (not toks or toks[-1] not in stop_ids):
                o = self.model(torch.tensor([[nxt]], device="cuda"), past_key_values=cache, use_cache=True)
                nxt = int(o.logits[0, -1].argmax())
                toks.append(nxt)
            share = sum(self.stats) / len(self.stats) if (g is not None and self.stats) else 1.0
            results[name] = (self.tok.decode([t for t in toks if t not in stop_ids], skip_special_tokens=True), share, len(toks))
        State.mode, self.trees = "dense", None
        return results


def retry_oom(fn, tries: int = 40, wait: float = 30.0):
    """The GPU is shared with other jobs: on CUDA OOM free the cache, wait, retry the same example."""
    for i in range(tries):
        try:
            return fn()
        except torch.OutOfMemoryError:
            State.mode = "dense"
            if State.runner is not None:
                State.runner.trees = None
            torch.cuda.empty_cache()
            print(f"cuda oom, retry {i + 1}/{tries} in {wait:.0f}s", flush=True)
            time.sleep(wait)
    raise RuntimeError("persistent CUDA OOM")


def corpus_ids(tok, corpus: Path) -> list[list[int]]:
    """Tokenized Gutenberg bodies (header/footer stripped), cached per tokenizer vocabulary."""
    import hashlib
    names = "".join(sorted(f.name for f in corpus.glob("pg*.txt")))
    tag = hashlib.sha256((tok.name_or_path + str(len(tok)) + names).encode()).hexdigest()[:16]
    cache = corpus / f".tok-{tag}.pt"
    if cache.exists():
        return torch.load(cache)
    docs = []
    for f in sorted(corpus.glob("pg*.txt")):
        raw = f.read_text(encoding="utf-8", errors="ignore")
        a, b = raw.find("*** START OF"), raw.find("*** END OF")
        body = raw[raw.find("\n", a) + 1 : b] if a >= 0 and b > a else raw
        docs.append(tok(body, add_special_tokens=False).input_ids)
    torch.save(docs, cache)
    return docs


def wsd(step: int, total: int, peak: float, warm: int = 20) -> float:
    if step < warm:
        return peak * (step + 1) / warm
    decay_start = int(total * 0.8)
    if step < decay_start:
        return peak
    frac = (step - decay_start) / max(total - decay_start, 1)
    return peak * (1 - frac * 0.99)


def train(args):
    r = Runner(args.model)
    g = zha.GEOMETRIES[args.geometry]
    docs = [d for d in corpus_ids(r.tok, Path(args.corpus)) if len(d) > args.seq + 1]
    rng = random.Random(args.seed)
    torch.manual_seed(args.seed)
    init_doc = docs[0]
    r.init_refs(g, init_doc[: args.seq])
    opt = torch.optim.AdamW(r.refs.parameters(), lr=args.lr, betas=(0.9, 0.95), eps=1e-15, weight_decay=0.0)
    r.accum = args.batch
    r.train_q = args.queries
    log = open(args.out + ".log.jsonl", "w")
    t0 = time.time()
    for step in range(args.steps):
        for gr in opt.param_groups:
            gr["lr"] = wsd(step, args.steps, args.lr)
        r.level_losses = {}
        State.mode = "train"
        for _ in range(args.batch):
            d = docs[rng.randrange(len(docs))]
            off = rng.randrange(0, len(d) - args.seq)
            with torch.no_grad():
                r.model(torch.tensor([d[off : off + args.seq]], device="cuda"), use_cache=False, logits_to_keep=1)
        State.mode = "dense"
        gn = torch.nn.utils.clip_grad_norm_(r.refs.parameters(), 1.0).item()
        opt.step()
        opt.zero_grad(set_to_none=True)
        per_level = {lvl: sum(v) / len(v) for lvl, v in sorted(r.level_losses.items())}
        rec = {"step": step, "lr": opt.param_groups[0]["lr"], "grad_norm": gn, "kl_levels": per_level,
               "kl_sum": sum(per_level.values()), "tokens": (step + 1) * args.batch * args.seq, "sec": time.time() - t0}
        log.write(json.dumps(rec) + "\n")
        log.flush()
        if step % 10 == 0 or step == args.steps - 1:
            print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in rec.items() if k != "kl_levels"}), flush=True)
    torch.save({"model": args.model, "revision": r.revision, "geometry": g.__dict__, "layer_ids": r.refs.layer_ids,
                "refs": r.refs.q.detach().cpu(), "steps": args.steps, "batch": args.batch, "seq": args.seq,
                "lr": args.lr, "queries_per_layer": args.queries, "seed": args.seed}, args.out)
    print("saved", args.out, flush=True)


def load_refs(path: str):
    ck = torch.load(path)
    g = zha.Geometry(**ck["geometry"])
    refs = zha.ReferenceQueries(ck["layer_ids"], ck["refs"].shape[1], ck["refs"].shape[2], ck["refs"].shape[3]).cuda()
    refs.q.data.copy_(ck["refs"].cuda())
    return g, refs, ck


@torch.no_grad()
def check_rope(args):
    """Model-exact RoPE check: rotate captured pre-RoPE queries and compare with the attention input."""
    r = Runner(args.model, max_len=4096)
    pre = {}
    m = r.layers[0]
    if hasattr(m, "q_norm"):
        hook = m.q_norm.register_forward_hook(lambda mod, i, o: pre.__setitem__("q", o.detach()))
    else:  # Qwen2.5: q_proj output is the pre-RoPE query
        hook = m.q_proj.register_forward_hook(lambda mod, i, o: pre.__setitem__("q", o.detach().view(*o.shape[:2], -1, m.head_dim)))
    r.capture = {}
    ids = r.tok("The quick brown fox jumps over the lazy dog. " * 40, add_special_tokens=False).input_ids[:300]
    r.model(torch.tensor([ids], device="cuda"), use_cache=False, logits_to_keep=1)
    hook.remove()
    q_attn = r.capture[m.layer_idx][0][0].float()  # [H, T, d]
    q_pre = pre["q"][0].float().transpose(0, 1)  # [H, T, d]
    t = q_pre.shape[1]
    cos, sin = r.rope.cos[:t], r.rope.sin[:t]
    want, _ = r.rope.apply(q_pre[None], q_pre[None], cos[None], sin[None])
    err = (want[0] - q_attn).abs().max().item()
    print(json.dumps({"model": args.model, "max_abs_err": err, "scale": q_attn.abs().max().item()}))
    assert err < 2e-2 * max(1.0, q_attn.abs().max().item()), err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["train", "check-rope"])
    ap.add_argument("--model", required=True, choices=list(MODELS))
    ap.add_argument("--geometry", default="deep-c4l6", choices=list(zha.GEOMETRIES))
    ap.add_argument("--corpus")
    ap.add_argument("--out")
    ap.add_argument("--steps", type=int, default=150)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--seq", type=int, default=8192)
    ap.add_argument("--queries", type=int, default=128)
    ap.add_argument("--lr", type=float, default=3.2e-2)
    ap.add_argument("--seed", type=int, default=20261103)
    args = ap.parse_args()
    {"train": train, "check-rope": check_rope}[args.cmd](args)


if __name__ == "__main__":
    main()
