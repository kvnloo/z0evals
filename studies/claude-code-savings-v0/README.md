# claude-code-savings-v0

Dogfooding z0intelligence inside Claude Code, measured the way other harnesses are studied here:
paired same-task arms, pinned sources, verifier-scored quality, Claude Code's own billed usage
(never tool-reported "tokens saved"), negative results kept.

## Findings so far

| lever | result | status |
| --- | --- | --- |
| Per-session static prefix (user settings + skills + MCP) | 30.6k -> 15.6k prefix tokens; cold-session billed cost -64.7% median (10/10 pairs) at equal quality | cold -63.8% (5/5); **warm -27.2% median (15/15)** at equal quality; cold start itself costs ~3x warm |
| Task-conditioned skill exposure (`skillOverrides: user-invocable-only`) | hiding 45 user skills: -5.7k prefix tokens; lexical selector 3/30 recall failures | not promoted; semantic selector under test |
| State Packet at SessionStart (+ tools), z0int#22 | held-out 14/14 vs raw 12/14; half the tool calls; -30% mean / -53% median input tokens; packet-only 8/14, abstention 0/4 | aid to tools; abstention gap open |
| **Lean x State Packet (S2 composition)** | stock+raw \$1.773 15/20 -> lean+packet \$0.467 18/20 (**-74%**); factors multiply (packet 0.70, lean 0.38) | composes; dev set |
| **Lean x State Packet, pinned held-out** | stock+raw \$2.186 21/22 -> lean+packet \$0.861 22/22 (**-61%**); predicted 0.404 vs observed 0.394 | composes on held-out; smaller than dev |
| Model routing headroom (Haiku, pinned held-out, lean) | raw: 16/22 \$1.230 (worse *and* costlier than Sonnet); packet: 20/22 \$0.632 (-27%, -2 answers) | no router promoted; packet helps weaker model most |
| ObservationPack, immediate pack (after SoL-Pi) — short tasks | billed cost -1.3% / +0.3% median, n.s.; pack rarely triggers | null |
| ObservationPack — long recall task (n=12) | **-30.3% total, median -26.7%, Wilcoxon p=0.0068**, 12/12 verified both | promote for long sessions (opt-in) |
| lean → lean + ObservationPack (long recall, n=6) | **-37.4% total, median -38.2%, 6/6 cheaper, Wilcoxon p=0.031**, 6/6 verified both | composes with lean |
| Plugin usage receipts vs billed usage | exact on all four token fields after a SessionEnd sweep (Stop fires before the final message is written) | measurement fixed |

## Mechanism notes (measured)

- ~10.3k tokens of Claude Code's core prefix are shared across sessions; everything after is rewritten on
  each cold session. A second session in the same directory reused the full 30.6k prefix ($0.083 -> $0.006).
- In a real long session, tool results >= 6k chars were 68% of tool-output replay; tool replay ~29% of cache
  reads. Immediate packing's ceiling is therefore ~11% of session cost, consistent with SoL-Pi's reported
  -6.1% for ObservationPack alone (arXiv 2609.20519, Table 4).
- PostToolUse `updatedToolOutput` for Bash must mirror the `tool_response` object; a bare string is ignored.

Aggregate data: `data/summary.json` (regenerate with `summarize.py`).
