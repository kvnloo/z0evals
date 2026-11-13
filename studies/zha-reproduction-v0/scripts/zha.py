"""Zyphra Hierarchical Attention (ZHA), reimplemented from arXiv:2610.42112v1, Section III.

Only the reference queries are trainable. The backbone is frozen. Section numbers
below refer to the paper.

Tree (III-A). Each tree level ``l`` covers ``C**l`` keys per node. Key 0 is left
out of the tree and is always attended. For a level-1 node holding keys K, a
reference query q_r is rotated with RoPE to the node's last position. The node
stores one tangent per reference:
    k_hat_r = softmax(q_r K^T / sqrt(d)) K
    b_hat_r = LSE(q_r K^T / sqrt(d)) - q_r . k_hat_r / sqrt(d)
A parent applies the same construction to its C children, evaluating each child
tangent at the parent's rotated reference query. A query q scores a node as
max_r (q . k_hat_r / sqrt(d) + b_hat_r).

Training (III-B). Per-level KL between the dense attention mass pooled into
chunks and the softmax of the node scores. The current incomplete chunk uses its
exact log mass. Reference queries are shared across nodes, levels and the query
heads of one KV group, with one set per KV head per full-attention layer.

Routing (III-C). Start from the complete top-level nodes. At each level keep the
smallest score-ordered prefix reaching top-p estimated mass, expand it to its
children and add the parentless complete nodes of the next level. The attended
set is key 0, the selected level-1 chunks and the current incomplete level-1 chunk.

This is a reference implementation. Routing scores all nodes and then masks, so
the selected-key share is real but no latency is measured.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass

import torch
from torch import nn


@dataclass(frozen=True)
class Geometry:
    name: str
    chunk: int
    levels: int
    refs: int = 16


DEEP = Geometry("deep-c4l6", 4, 6)
WIDE = Geometry("wide-c256l1", 256, 1)
GEOMETRIES = {g.name: g for g in (DEEP, WIDE)}


class Rope:
    """Model-exact RoPE table plus the model's own apply_rotary_pos_emb (handles partial RoPE)."""

    def __init__(self, model, max_len: int, device):
        rot = [m for n, m in model.named_modules() if n.endswith("rotary_emb") and "visual" not in n]
        assert len(rot) == 1, [n for n, _ in model.named_modules() if n.endswith("rotary_emb")]
        attn = next(m for m in model.modules() if hasattr(m, "q_proj") and hasattr(m, "layer_idx"))
        self.apply = sys.modules[type(attn).__module__].apply_rotary_pos_emb
        pos = torch.arange(max_len, device=device)[None]
        dummy = torch.zeros(1, max_len, 1, device=device, dtype=torch.float32)
        cos, sin = rot[0](dummy, pos)
        self.cos, self.sin = cos[0].float(), sin[0].float()  # [T, rot_dim]

    def rotate(self, x: torch.Tensor, positions: torch.Tensor) -> torch.Tensor:
        """x: [A, B, d] reference queries; positions: [N] -> [A, B, N, d]."""
        a, b, d = x.shape
        n = positions.shape[0]
        xx = x[:, :, None, :].expand(a, b, n, d).reshape(1, a * b, n, d)
        cos, sin = self.cos[positions][None], self.sin[positions][None]
        out, _ = self.apply(xx, xx, cos, sin)
        return out.view(a, b, n, d)


def full_attention_layers(model) -> list[nn.Module]:
    mods = [m for m in model.modules() if hasattr(m, "q_proj") and hasattr(m, "k_proj") and hasattr(m, "layer_idx")]
    return sorted(mods, key=lambda m: m.layer_idx)


class ReferenceQueries(nn.Module):
    """One [KVH, R, d] parameter per full-attention layer (fp32)."""

    def __init__(self, layer_ids: list[int], kvh: int, refs: int, d: int):
        super().__init__()
        self.layer_ids = list(layer_ids)
        self.q = nn.Parameter(torch.zeros(len(layer_ids), kvh, refs, d))
        self.index = {lid: i for i, lid in enumerate(layer_ids)}

    def __getitem__(self, layer_idx: int) -> torch.Tensor:
        return self.q[self.index[layer_idx]]


def summarize_leaves(keys: torch.Tensor, ref: torch.Tensor, rope: Rope, chunk: int, first_node: int, scale: float):
    """keys: [KVH, N*C, d] tree keys (absolute positions 1+first_node*C ...); ref: [KVH, R, d].

    Returns k_hat [KVH, R, N, d], b_hat [KVH, R, N].
    """
    kvh, m, d = keys.shape
    n = m // chunk
    if n == 0:
        return keys.new_zeros(kvh, ref.shape[1], 0, d), keys.new_zeros(kvh, ref.shape[1], 0)
    ends = (torch.arange(first_node, first_node + n, device=keys.device) + 1) * chunk
    qr = rope.rotate(ref, ends)  # [KVH, R, N, d]
    kc = keys.view(kvh, n, chunk, d)
    s = torch.einsum("hrnd,hncd->hrnc", qr, kc) * scale
    lse = torch.logsumexp(s, -1)
    k_hat = torch.einsum("hrnc,hncd->hrnd", torch.softmax(s, -1), kc)
    b_hat = lse - (qr * k_hat).sum(-1) * scale
    return k_hat, b_hat


def merge_nodes(k_child, b_child, ref, rope: Rope, chunk: int, level: int, first_node: int, scale: float):
    """Children [KVH, R, Np*C, d] -> parents [KVH, R, Np, d] at tree level `level` (>=2)."""
    kvh, r, m, d = k_child.shape
    n = m // chunk
    if n == 0:
        return k_child.new_zeros(kvh, r, 0, d), b_child.new_zeros(kvh, r, 0)
    ends = (torch.arange(first_node, first_node + n, device=k_child.device) + 1) * chunk**level
    qr = rope.rotate(ref, ends)  # [KVH, R, Np, d]
    kc = k_child.view(kvh, r, n, chunk, d)
    t = torch.einsum("hrpd,hrpcd->hrpc", qr, kc) * scale + b_child.view(kvh, r, n, chunk)
    lse = torch.logsumexp(t, -1)
    k_hat = torch.einsum("hrpc,hrpcd->hrpd", torch.softmax(t, -1), kc)
    b_hat = lse - (qr * k_hat).sum(-1) * scale
    return k_hat, b_hat


def build_tree(k: torch.Tensor, ref: torch.Tensor, rope: Rope, g: Geometry, scale: float):
    """k: [KVH, n, d] all keys (absolute positions 0..n-1). Returns [(k_hat, b_hat)] for levels 1..L."""
    tree_keys = k[:, 1:]
    n1 = tree_keys.shape[1] // g.chunk
    levels = [summarize_leaves(tree_keys[:, : n1 * g.chunk], ref, rope, g.chunk, 0, scale)]
    for lvl in range(2, g.levels + 1):
        kc, bc = levels[-1]
        np_ = kc.shape[2] // g.chunk
        levels.append(merge_nodes(kc[:, :, : np_ * g.chunk], bc[:, :, : np_ * g.chunk], ref, rope, g.chunk, lvl, 0, scale))
    return levels


def node_scores(q: torch.Tensor, k_hat: torch.Tensor, b_hat: torch.Tensor, scale: float) -> torch.Tensor:
    """q: [KVH, G, Q, d]; k_hat [KVH, R, N, d] -> s [KVH, G, Q, N] = max_r tangent."""
    t = torch.einsum("hgqd,hrnd->hgqrn", q, k_hat) * scale + b_hat[:, None, None]
    return t.max(dim=3).values


def distill_loss(q: torch.Tensor, k: torch.Tensor, ref: torch.Tensor, rope: Rope, g: Geometry, scale: float,
                 positions: torch.Tensor):
    """Per-level KL (III-B) for sampled query positions.

    q: [H, T, d] post-RoPE queries, k: [KVH, T, d] post-RoPE keys (both fp32, no grad).
    positions: [Q] query positions (absolute). Returns list of per-level mean KL (with grad).
    """
    h, t_len, d = q.shape
    kvh = k.shape[0]
    grp = h // kvh
    tree = build_tree(k, ref, rope, g, scale)
    qs = q[:, positions].view(kvh, grp, -1, d)  # [KVH, G, Q, d]
    with torch.no_grad():
        z = torch.einsum("hgqd,hnd->hgqn", qs, k) * scale
        key_pos = torch.arange(t_len, device=q.device)
        visible = (key_pos[None] <= positions[:, None]) & (key_pos[None] > 0)  # [Q, T]
        z = z.masked_fill(~visible, float("-inf"))[..., 1:]  # tree keys only
    losses = []
    for lvl in range(1, g.levels + 1):
        span = g.chunk**lvl
        n_all = math.ceil((t_len - 1) / span)
        with torch.no_grad():
            zp = torch.nn.functional.pad(z, (0, n_all * span - (t_len - 1)), value=float("-inf"))
            exact = torch.logsumexp(zp.view(*zp.shape[:-1], n_all, span), -1)  # [KVH,G,Q,n_all]
            target = torch.log_softmax(exact, -1)
            complete = torch.arange(n_all, device=q.device)[None] < (positions[:, None] // span)  # [Q, n_all]
            eligible = complete.any(-1)
        k_hat, b_hat = tree[lvl - 1]
        n_comp = k_hat.shape[2]
        s = node_scores(qs, k_hat, b_hat, scale)  # [KVH,G,Q,n_comp]
        s = torch.nn.functional.pad(s, (0, n_all - n_comp), value=0.0)
        pred = torch.where(complete[None, None], s, exact)
        logp_hat = torch.log_softmax(pred, -1)
        p = target.exp()
        kl = (p * (target - logp_hat)).nan_to_num(0.0).sum(-1)  # [KVH,G,Q]
        if eligible.any():
            losses.append(kl[..., eligible].mean())
    return losses


def top_p(scores: torch.Tensor, cand: torch.Tensor, p: float) -> torch.Tensor:
    """Smallest score-ordered prefix of candidates whose softmax mass is >= p."""
    s = scores.masked_fill(~cand, float("-inf"))
    probs = torch.softmax(s, -1).nan_to_num(0.0)
    sp, idx = probs.sort(-1, descending=True)
    before = sp.cumsum(-1) - sp
    keep = (before < p) & (sp > 0)
    out = torch.zeros_like(cand)
    out.scatter_(-1, idx, keep)
    return out & cand


class LayerTree:
    """Append-only decode-time tree for one layer and one sequence (batch 1)."""

    def __init__(self, ref: torch.Tensor, rope: Rope, g: Geometry, scale: float, store_dtype=torch.float32):
        """store_dtype=bfloat16 halves summary memory; all arithmetic stays fp32."""
        self.ref, self.rope, self.g, self.scale, self.dt = ref, rope, g, scale, store_dtype
        self.levels: list[list[torch.Tensor]] = []

    def update(self, k: torch.Tensor):
        """k: [KVH, n, d] fp32 keys at absolute positions 0..n-1."""
        g = self.g
        if not self.levels:
            self.levels = [[a.to(self.dt), b] for a, b in build_tree(k, self.ref, self.rope, g, self.scale)]
            return
        have = self.levels[0][0].shape[2]
        want = (k.shape[1] - 1) // g.chunk
        if want > have:
            kh, bh = summarize_leaves(k[:, 1 + have * g.chunk : 1 + want * g.chunk], self.ref, self.rope, g.chunk, have, self.scale)
            self.levels[0] = [torch.cat([self.levels[0][0], kh.to(self.dt)], 2), torch.cat([self.levels[0][1], bh], 2)]
        for lvl in range(2, g.levels + 1):
            kc, bc = self.levels[lvl - 2]
            have = self.levels[lvl - 1][0].shape[2]
            want = kc.shape[2] // g.chunk
            if want > have:
                lo, hi = have * g.chunk, want * g.chunk
                kh, bh = merge_nodes(kc[:, :, lo:hi].float(), bc[:, :, lo:hi], self.ref, self.rope, g.chunk, lvl, have, self.scale)
                self.levels[lvl - 1] = [torch.cat([self.levels[lvl - 1][0], kh.to(self.dt)], 2), torch.cat([self.levels[lvl - 1][1], bh], 2)]

    def route(self, q: torch.Tensor, n: int, p: float) -> torch.Tensor:
        """q: [KVH, G, d] one decode query per head. Returns token mask [KVH, G, n]."""
        g = self.g
        kvh, grp, _ = q.shape
        qq = q[:, :, None]
        counts = [lv[0].shape[2] for lv in self.levels]
        sel = None
        for lvl in range(g.levels, 0, -1):
            k_hat, b_hat = self.levels[lvl - 1]
            nl = counts[lvl - 1]
            idx = torch.arange(nl, device=q.device)
            if lvl == g.levels:
                cand = torch.ones(kvh, grp, nl, dtype=torch.bool, device=q.device)
            else:
                n_parent = counts[lvl]
                has_parent = idx < n_parent * g.chunk
                parent = (idx // g.chunk).clamp(max=max(n_parent - 1, 0))
                from_sel = sel[..., parent] if n_parent > 0 else torch.zeros(kvh, grp, nl, dtype=torch.bool, device=q.device)
                cand = (from_sel & has_parent) | ~has_parent
            if nl == 0:
                sel = torch.zeros(kvh, grp, 0, dtype=torch.bool, device=q.device)
                continue
            s = node_scores(qq, k_hat.float(), b_hat, self.scale)[:, :, 0]
            sel = top_p(s, cand, p)
        pos = torch.arange(n, device=q.device)
        n1 = counts[0]
        leaf = ((pos - 1) // g.chunk).clamp(min=0, max=max(n1 - 1, 0))
        tok = sel[..., leaf] if n1 > 0 else torch.zeros(kvh, grp, n, dtype=torch.bool, device=q.device)
        tok = tok & (pos >= 1) & (pos <= n1 * g.chunk)
        return tok | (pos == 0) | (pos > n1 * g.chunk)
