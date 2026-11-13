"""CUDA unit tests for the ZHA reimplementation (zha.py)."""
import math
import unittest

import torch

import zha


class IdentityRope:
    """RoPE stub with zero angle, so footnote 2 (merge == direct summary) holds exactly."""

    def rotate(self, x, positions):
        return x[:, :, None, :].expand(*x.shape[:2], positions.shape[0], x.shape[-1])


class TrigRope:
    """Full-dim rotate-half RoPE for routing tests."""

    def __init__(self, d, n):
        inv = 1.0 / (10000 ** (torch.arange(0, d, 2, device="cuda").float() / d))
        f = torch.arange(n, device="cuda").float()[:, None] * inv[None]
        emb = torch.cat([f, f], -1)
        self.cos, self.sin = emb.cos(), emb.sin()

    def apply(self, q, k, cos, sin, unsqueeze_dim=1):
        cos, sin = cos.unsqueeze(unsqueeze_dim), sin.unsqueeze(unsqueeze_dim)
        rh = lambda x: torch.cat([-x[..., x.shape[-1] // 2:], x[..., : x.shape[-1] // 2]], -1)
        return q * cos + rh(q) * sin, k * cos + rh(k) * sin

    rotate = zha.Rope.rotate


class ZHATests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(0)

    def test_tangent_is_exact_at_reference_query(self):
        d, c = 16, 8
        keys = torch.randn(1, c, d, device="cuda")
        ref = torch.randn(1, 1, d, device="cuda")
        s = 1 / math.sqrt(d)
        kh, bh = zha.summarize_leaves(keys, ref, IdentityRope(), c, 0, s)
        approx = (ref[0, 0] @ kh[0, 0, 0]) * s + bh[0, 0, 0]
        exact = torch.logsumexp(keys[0] @ ref[0, 0] * s, 0)
        torch.testing.assert_close(approx, exact)
        q = torch.randn(d, device="cuda")  # tangent of a convex function lower-bounds it
        self.assertLessEqual(((q @ kh[0, 0, 0]) * s + bh[0, 0, 0]).item(), torch.logsumexp(keys[0] @ q * s, 0).item() + 1e-5)

    def test_merge_equals_direct_summary_without_rope(self):
        d, c = 16, 4
        keys = torch.randn(2, c * c, d, device="cuda")
        ref = torch.randn(2, 3, d, device="cuda")
        s = 1 / math.sqrt(d)
        k1, b1 = zha.summarize_leaves(keys, ref, IdentityRope(), c, 0, s)
        k2, b2 = zha.merge_nodes(k1, b1, ref, IdentityRope(), c, 2, 0, s)
        kd, bd = zha.summarize_leaves(keys, ref, IdentityRope(), c * c, 0, s)
        torch.testing.assert_close(k2, kd, atol=1e-5, rtol=1e-5)
        torch.testing.assert_close(b2, bd, atol=1e-5, rtol=1e-5)

    def test_incremental_tree_equals_batch_build(self):
        d, n = 16, 300
        rope = TrigRope(d, 512)
        g = zha.Geometry("t", 4, 3, 4)
        k = torch.randn(2, n, d, device="cuda")
        ref = torch.randn(2, 4, d, device="cuda")
        s = 1 / math.sqrt(d)
        full = zha.build_tree(k, ref, rope, g, s)
        tree = zha.LayerTree(ref, rope, g, s)
        tree.update(k[:, :37])
        for m in range(38, n + 1):
            tree.update(k[:, :m])
        for (a, b), (x, y) in zip(full, tree.levels):
            torch.testing.assert_close(a, x, atol=1e-5, rtol=1e-5)
            torch.testing.assert_close(b, y, atol=1e-5, rtol=1e-5)

    def test_route_p_one_keeps_all_and_small_p_keeps_sink_and_current(self):
        d, n = 16, 203
        rope = TrigRope(d, 512)
        g = zha.Geometry("t", 4, 3, 4)
        k = torch.randn(2, n, d, device="cuda")
        tree = zha.LayerTree(torch.randn(2, 4, d, device="cuda"), rope, g, 1 / math.sqrt(d))
        tree.update(k)
        q = torch.randn(2, 3, d, device="cuda")
        self.assertTrue(tree.route(q, n, 1.0).all().item())
        m = tree.route(q, n, 1e-9)
        n1 = (n - 1) // 4
        self.assertTrue(m[..., 0].all().item())
        self.assertTrue(m[..., 1 + n1 * 4:].all().item())
        sel_leaf = m[..., 1:1 + n1 * 4].view(2, 3, n1, 4)
        self.assertTrue((sel_leaf.all(-1) == sel_leaf.any(-1)).all().item())  # whole chunks only
        self.assertTrue((sel_leaf.any(-1).sum(-1) >= 1).all().item())

    def test_distill_loss_decreases(self):
        d, t = 16, 257
        rope = TrigRope(d, 512)
        g = zha.Geometry("t", 4, 2, 4)
        k = torch.randn(2, t, d, device="cuda")
        q = torch.randn(4, t, d, device="cuda") * 2
        ref = torch.nn.Parameter(torch.randn(2, 4, d, device="cuda") * 0.1)
        opt = torch.optim.Adam([ref], lr=5e-2)
        pos = torch.arange(16, t, device="cuda")
        first = None
        for _ in range(60):
            loss = sum(zha.distill_loss(q, k, ref, rope, g, 1 / math.sqrt(d), pos))
            first = first if first is not None else loss.item()
            opt.zero_grad(); loss.backward(); opt.step()
        self.assertGreater(first, 0)
        self.assertLess(loss.item(), first)


if __name__ == "__main__":
    unittest.main()
