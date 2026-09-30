---
title: "where do claude code tokens actually go?"
subtitle: "one night of dogfooding z0intelligence inside claude code, measured on the bill instead of on vibes."
study: claude-code-savings-v0
status: draft
author: "zer0 research"
date: "september 30, 2026"
mock_data: false
toc:
  - id: question
    label: the question
  - id: method
    label: how we measured
  - id: prefix
    label: the prefix is the bill
  - id: packet
    label: a state packet helps tools
  - id: compose
    label: the wins multiply
  - id: nulls
    label: what did and did not work
  - id: limits
    label: what this does not prove
---

<div class="lede">
every harness we integrate with z0intelligence gets the same question: does the integration make the frontier model do less work, measured in billed cost per verified task, without making it worse? tonight it was claude code's turn.
</div>

<div class="hero-rule"></div>

## the question {#question}

the tool-compression ecosystem reports "tokens saved". the only paired studies we could find on claude code (jetbrains on rtk, quesma on terminal-bench) found those savings mostly vanish on the bill, because cached reads are already cheap and most tool output never passes through the hook. so we only counted what claude code itself reports as billed usage, and we only counted an answer if a programmatic verifier agreed.

## how we measured {#method}

- claude code 2.1.285, headless, sonnet (plus one haiku arm), pinned source commits, paired arms on the same task instance, arms interleaved per rep.
- a z0 plugin writes per-message usage receipts into tokenomics. after one fix (the `Stop` hook fires before the final message reaches the transcript, so we sweep again at `SessionEnd`) the receipts equal claude code's billed usage on all four token fields.
- current-work questions drift as repos change — two answer keys went stale during the night because of our own pushes — so the final held-out set runs against pinned fixture clones and a frozen transcript subset, with keys computed before any run.

## the prefix is the bill {#prefix}

on short tasks, almost none of the cost is the task. about 10.3k tokens of claude code's core prompt are shared across sessions; everything after it — user hooks' output, skill listings, mcp — is rewritten on every cold session and re-read on every request. the cache is scoped to directory and startup git snapshot, so every fresh worktree starts cold: stock claude code cost about 3x more cold than warm on the same task ($0.126 vs $0.0425).

a lean launch profile (project settings only, explicit mcp, no skill listing) cut billed cost a median 63.8% on cold sessions and **27.2% on warm ones** (15/15 pairs cheaper), with verified quality unchanged (20/20 both arms). z0 now ships it as `z0int claude-code launch --profile lean`, plus `warm` to place work where the prefix is still cached.

## a state packet helps tools {#packet}

the z0 state packet reconstructs "what is true now" from git, docs and local session history, with a source pointer on every claim, and injects it at session start. on a held-out question set frozen before any run, packet plus normal tools answered 14/14 versus 12/14 for raw tools, with half the tool calls and 30% fewer input tokens. on its own, without tools, it scored 8/14 — it is an aid, not a replacement.

it also failed a test we built to break it: with session history removed it never abstained, because "0 transcripts scanned" read like a scanner bug. distinguishing *source unavailable* from *nothing recorded*, plus an explicit abstain rule, took that from 0/4 to 4/4 (a dev-set result, since we wrote the fix after seeing the failure) with no over-abstention on the rest of the set.

## the wins multiply {#compose}

<table class="result-table">
<thead><tr><th>pinned held-out (22 trials/cell)</th><th>correct</th><th>total cost</th></tr></thead>
<tbody>
<tr><td>stock + raw tools</td><td>21/22</td><td>$2.186</td></tr>
<tr><td>stock + packet</td><td>22/22</td><td>$1.815</td></tr>
<tr><td>lean + raw tools</td><td>20/22</td><td>$1.063</td></tr>
<tr class="primary"><td>lean + packet</td><td><strong>22/22</strong></td><td><strong>$0.861</strong></td></tr>
</tbody>
</table>

the packet factor was 0.83 / 0.81 and the lean factor 0.49 / 0.47 regardless of the other lever; the product predicts 0.404 of the baseline and we observed 0.394. **lean + packet cost 61% less than stock claude code with raw tools, at equal or better correctness.** on the drifting dev set the same composition read -74%; we report the held-out number.

## what did and did not work {#nulls}

- **observationpack on short tasks** (after nvlabs/sol-pi): claude code has no seam to rewrite history later, so our port packs large bash output immediately. on short tasks it rarely triggered — sonnet already pipes big output through `tail`, and claude code natively spills anything over ~30k characters — and billed cost did not move (paired medians -1.3% and +0.3%).
- **but not on long sessions.** on a long recall task (twelve full-file outputs, eight over the pack threshold, then seven detail questions answered without re-reading sources) it cut total billed cost **30.3%** ($4.159 to $2.900; median paired -26.7%, 9/12 cheaper, wilcoxon p=0.0068) with 12/12 verified in both arms. we extended the sample twice after looking (n=3, n=6), which we disclose; the p-value still clears a 0.05/3 bar. the paper reports -6.1% for this mechanism alone; our real long session suggested a ~11% ceiling for mixed work, and this task is deliberately output-heavy. verdict: opt-in for long sessions, off for short ones.
- **task-conditioned skill exposure**: hiding irrelevant skill descriptions saves ~5.7k prefix tokens, but neither a lexical selector (3/30 misses) nor decider-2b (best 2/30) met the bar of hiding a needed skill at most once in 30.
- **routing to a cheaper model**: haiku without the packet was *worse and more expensive* than sonnet (16/22, $1.230 vs 20/22, $1.063) because it explored more; with the packet it was 27% cheaper but lost two answers. no router. the packet helped haiku more than sonnet, which is the more interesting finding.

## what this does not prove {#limits}

- small samples: 5–11 questions per set, 2–4 reps, one host, one night.
- the savings are on short tasks and current-work questions; long coding sessions are dominated by different terms.
- costs are claude code's reported `total_cost_usd` on a subscription, not an invoice.
- the dev-set numbers carry overfit risk; the pinned held-out set is the headline.

<details>
<summary><strong>references</strong></summary>

- [jetbrains — does rtk make claude code cheaper?](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/) — the paired-trial design we copied.
- [quesma — does rtk make ai coding cheaper?](https://quesma.com/blog/does-rtk-make-ai-coding-cheaper/)
- [nvlabs/sol-pi](https://github.com/NVlabs/SoL-Pi) and [arXiv:2609.20519](https://arxiv.org/abs/2609.20519) — observationpack and its per-mechanism ablation.
- [claude code: prompt caching](https://code.claude.com/docs/en/prompt-caching) — cache layers, scope and ttl.
- [z0intelligence](https://github.com/kvnloo/z0intelligence) — branches `feat/claude-code-harness`, `feat/state-packet-v0`, `integrate/claude-code-z0-stack`.

</details>
