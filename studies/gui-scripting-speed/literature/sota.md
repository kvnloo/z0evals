# SOTA notes: fast and accurate GUI agents (retrieved 2026-10-20)

Source classes: primary papers (arXiv abstract pages read on 2026-10-20) and live
leaderboard aggregators. Aggregator numbers are **source-reported**, not reproduced here,
and are kept separate from our measurements (z0evals rule 2).

## Benchmarks

| Benchmark | What it measures | Note for us |
| --- | --- | --- |
| OSWorld / OSWorld-Verified [1] | 369 real desktop tasks (Ubuntu VMs), execution-based checkers | Our fork `kvnloo/OSWorld` carries no kvnloo commits (mirror of upstream `main` @ `1a572e62`); our OSWorld work lives in `kvnloo/cua` branches (see prior-work.md). |
| OSWorld-Human [2] | Same tasks with human-minimal trajectories; measures **steps and wall time**, not just success | The right efficiency yardstick: report steps/human-steps and wall time next to success. |
| AndroidWorld [3] | 116 programmatic Android tasks, 20 apps, reward from device state | Our S22+ tasks are a tiny read-only analogue; AndroidWorld needs an emulator (not run). |
| AndroidLab [4] | 138 Android tasks + 94.3k-step instruction set for fine-tuning | Candidate SFT source for the GUI-step chooser curriculum (license check pending). |
| ScreenSpot-Pro [5,6] | Pixel grounding on high-res professional UIs | Only relevant to screenshot-first agents; our Android/browser path is tree-first. |

Leaderboard state, source-reported by aggregators on 2026-10-20 (not verified against the
official OSWorld site): OSWorld-Verified top entry ~90% (Intelligence-Indeed Agent, 100
steps) per aievals.co / presenc.ai; AndroidWorld top ~85-87% (Qwen3.8 family) per
paperswithcode.co / benchlm.ai. Treat as orientation only.

## Mechanisms that cut latency (and what they map to here)

1. **Latency is dominated by large-model calls, and agents take 2.7-4.3x more steps than
   humans** (OSWorld-Human [2]: planning/reflection/judging calls dominate; later steps can
   take 3x longer than early ones). Maps to: delete model turns first (macro compilation,
   one-call goal loops), then shrink each remaining decision (Jev / SLM choosers).
2. **Verifier-style choice over a discretized action set instead of free generation**
   (V-Droid [7]: LLM scores candidate actions with prefill-only verification; 59.5%
   AndroidWorld, 4.3 s/step, 6.1x faster than prior mobile agents; pairwise progress-
   preference training). This is the same shape as our compiled legal action table +
   Jev choice, and its pairwise training is the published analogue of our Bradley-Terry
   chooser and of SFT for shadow SLMs.
3. **Speculative actions** [8]: a fast model predicts the next action while the slow
   authoritative actor validates; up to 55% next-action prediction accuracy, up to 20%
   latency reduction, lossless when only matching predictions commit. Maps to: a shadow SLM
   whose prediction is executed only when it agrees with Jev (or pre-fetches the next
   observation), the natural first "credited" use of a shadow candidate.
4. **Speculative multi-action planning + deep OS integration** (UFO2 [9], Windows): one
   planning call emits several actions; UIA/a11y control detection beats screenshot-only.
   Maps to: `--plan` / compiled phone_exec scripts; tree-first observation (u2 / AT-SPI /
   CDP).
5. **Scale by parallel rollouts, then select** (Agent S3 / behavior best-of-N [10]) raises
   success but multiplies cost and wall time; it is an accuracy lever, not a speed lever.
6. **Small on-device GUI models** (Ferret-UI Lite [11], MAI-UI device-cloud split [12]:
   >40% fewer cloud calls) show the offload pattern the Shadow Network targets: a small
   local model handles easy steps, the large model only the hard ones.
7. Survey of efficiency levers (observation compression, memory, action batching,
   runtime) [13].

## References

1. Xie et al., *OSWorld*, arXiv:2404.07972.
2. WukLab, *OSWorld-Human: Benchmarking the Efficiency of Computer-Use Agents*, arXiv:2506.16042. https://arxiv.org/abs/2506.16042
3. Rawles et al., *AndroidWorld*, arXiv:2405.14573.
4. *AndroidLab: Training and Systematic Benchmarking of Android Autonomous Agents*, arXiv:2410.24024. https://arxiv.org/abs/2410.24024
5. *GTA1: GUI Test-time Scaling Agent*, arXiv:2507.05791.
6. *MVP: Multiple View Prediction Improves GUI Grounding*, arXiv:2512.08529.
7. *Advancing Mobile GUI Agents: A Verifier-Driven Approach to Practical Deployment (V-Droid)*, arXiv:2503.15937 (MobiCom 2026). https://arxiv.org/abs/2503.15937
8. Ye et al., *Speculative Actions: A Lossless Framework for Faster Agentic Systems*, arXiv:2510.04371. https://arxiv.org/abs/2510.04371
9. *UFO2: The Desktop AgentOS*, arXiv:2504.14603. https://arxiv.org/abs/2504.14603
10. Simular AI, *The Unreasonable Effectiveness of Scaling Agents for Computer Use (Agent S3, bBoN)*, arXiv:2510.02250.
11. *Ferret-UI Lite: Lessons from Building Small On-Device GUI Agents*, arXiv:2509.26539.
12. *MAI-UI Technical Report*, arXiv:2512.22047.
13. Bai et al., *Efficient GUI Agents: A Systems Survey of Observation, Memory, Action, and Runtime Optimization*, arXiv:2609.02309. https://arxiv.org/abs/2609.02309
14. Wang et al., *UI-TARS-2 Technical Report*, arXiv:2509.02544.
