# claude-code-savings-v1

This study re-measures the [v0](https://github.com/kvnloo/z0evals/tree/study/claude-code-savings-v0) Claude Code savings study against the **current** z0 integration, with these changes:

- The analysis was pre-registered before any measured run.
- There are about 5× more pairs: 124 per contrast.
- 19 fresh repo tasks were added, taken from z0intelligence, tokenomics, kerdoios and evolution-lab.
- Both billed tokens and Claude Code's own cost estimate are counted.

The study ran 496 real `claude -p` trials with Sonnet and Claude Code 2.1.286. There were no infrastructure failures.

- Pre-registration, runner, tasks and analysis: kvnloo/z0intelligence `study/claude-code-savings-v1`. Pre-registration is in `28caf90` and `ef3f828`; results are in `0948bc1`.
- `data/` holds the imported aggregates. `summarize.py` re-derives the headline numbers from `data/trials.csv`.

| contrast (pooled, n=124) | tokens | 95% CI | cost | success | guard |
| --- | --- | --- | --- | --- | --- |
| **stock → lean+packet+obspack** (primary) | **−34.2%** | −40.3 … −28.1 | −45.4% | 121 → 124 | PASS |
| stock → lean | −31.8% | −36.2 … −26.9 | −42.8% | 121 → 121 | PASS |
| lean → +packet | −6.5% (n.s.) | −17.0 … +4.1 | +1.0% | 121 → 124 | PASS |
| +packet → +obspack | +3.0% (n.s.) | −2.9 … +9.0 | −5.5% | 124 → 124 | PASS |

The pooled packet result is near zero because it averages two opposite effects. On current-work questions, the packet cut tokens 35.5% and fixed the last two misses. On fresh coding tasks, it added 10.8% tokens and did not change quality.

ObservationPack showed no effect on short tasks. On the long recall task it cut cost 41.5%, but that is n=4 and exploratory.

Lean was the lever that held up everywhere.

**Addendum v1b (2026-10-01):** a prompt-gated packet (`packet: "gated"`) failed both pre-registered tests against the SessionStart packet. On repo tasks it was −7.3% tokens, but the CI reached +0.8%. On qa it was +16.6% against a +5% margin. See [ADDENDUM-v1b.md](ADDENDUM-v1b.md) and `data/v1b/`. The same branch makes route_worker loadable under lean.

See the post `posts/claude-code-savings-v1.md` and the claims in `manifest.yaml`.
