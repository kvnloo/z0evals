"""Small CUDA correctness checks for the feasibility probe, not ZHA validation."""
import unittest
from types import SimpleNamespace

import torch

from zha_probe import Probe, Router, route, top_p_mask, zha_probe_attention
from transformers.integrations.sdpa_attention import sdpa_attention_forward


class ProbeTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(3)
        self.device = 'cuda'
        Probe.mode = 'off'
        Probe.decode_stats = []

    def test_top_p_minimal_mass_and_no_candidates(self):
        scores = torch.tensor([[0.6, 0.3, 0.1]], device=self.device).log()
        mask = top_p_mask(scores, torch.ones_like(scores, dtype=torch.bool), 0.8)
        self.assertEqual(mask.tolist(), [[True, True, False]])
        none = top_p_mask(scores, torch.zeros_like(mask), 0.8)
        self.assertFalse(none.any().item())

    def test_oracle_meets_mass(self):
        q = torch.randn(2, 3, 8, device=self.device)
        k = torch.randn(2, 127, 8, device=self.device)
        sel, _ = route(q, k, 8**-0.5, Router('oracle', 'oracle', p=.9, sinks=0, window=0))
        probs = (torch.einsum('hmd,hnd->hmn', q, k) * 8**-0.5).softmax(-1)
        self.assertGreaterEqual((probs * sel).sum(-1).min().item(), .9 - 1e-6)

    def test_ragged_tree_p_one_keeps_every_key(self):
        q = torch.randn(2, 3, 8, device=self.device)
        k = torch.randn(2, 131, 8, device=self.device)
        sel, scored = route(q, k, 8**-0.5, Router('all', 'tree', depth=6, p=1.0))
        self.assertTrue(sel.all().item())
        self.assertTrue((scored >= 131).all().item())

    def test_window_control_exactly_sinks_and_window(self):
        q = torch.randn(2, 3, 8, device=self.device)
        k = torch.randn(2, 131, 8, device=self.device)
        sel, _ = route(q, k, .1, Router('window', 'tree', p=0., sinks=4, window=16))
        self.assertTrue(sel[..., :4].all().item())
        self.assertTrue(sel[..., -16:].all().item())
        self.assertFalse(sel[..., 4:-16].any().item())

    def test_masked_gqa_all_keys_equals_sdpa(self):
        q = torch.randn(1, 6, 1, 8, device=self.device)
        k = torch.randn(1, 2, 131, 8, device=self.device)
        v = torch.randn_like(k)
        module = SimpleNamespace(num_key_value_groups=3, training=False, is_causal=False)
        expected, _ = sdpa_attention_forward(module, q, k, v, None, scaling=8**-0.5, is_causal=False)
        Probe.mode = 'sparse'
        Probe.sparse = Router('all', 'tree', depth=3, p=1.0)
        actual, _ = zha_probe_attention(module, q, k, v, None, scaling=8**-0.5, is_causal=False)
        torch.testing.assert_close(actual, expected, atol=1e-5, rtol=1e-5)
        self.assertEqual(Probe.decode_stats[0][0], 1.)


if __name__ == '__main__':
    unittest.main()
