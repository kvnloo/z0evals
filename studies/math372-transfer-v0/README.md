# math372-transfer-v0

Status: **living program, no measured transfer yet**

Question: can any result family in OpenAI's math release ([openai/math](https://github.com/openai/math),
"372 result families") produce a measured, user-visible improvement in an open-source project we
already contribute to? A clean, reproducible "no" is an acceptable answer.

This directory is the program, the candidate queue and the append-only verdict ledger. Each
experiment that reaches a verdict freezes as its own study (`studies/math372-<slug>-v0/`) with a
post and a research-log entry; this study links them.

## How we got here

- October 2026: a ChatGPT triage mapped families onto PyTorch, ctx, Kerdoios, CUA/OMP,
  Newton/OpenUSD, gods-eye-view and OpenROAD ([frontier-kb#42](https://github.com/kvnloo/frontier-kb/issues/42),
  [gods-eye-view#202](https://github.com/kvnloo/gods-eye-view/issues/202),
  [gods-eye-view#204](https://github.com/kvnloo/gods-eye-view/issues/204),
  [oss-factory#99](https://github.com/kvnloo/oss-factory/issues/99)). It produced 15+ work orders,
  two negative-fit counterexamples and one conventional batching speedup, and no end-to-end
  measurement.
- 2026-11-03: a four-seat model council (Claude Opus 5.5, Claude Fable 5.1, gpt-6-astra,
  gpt-6.1-sol; independent openings, no cross-examination yet) reviewed that record. Its
  synthesis is in `data/council-2026-11-03.md`; the program below adopts the points all four
  seats made and lists where they disagreed.

## Program

**Direction: profile first, theorem second.** Start from a measured hot path in a registry repo,
then look for a family whose hypotheses match it. The October funnel ran the other way (theorem →
"which repo?") and every candidate that reached an experiment failed on fit (all four seats).

**Scored objective.** For each study: the end-to-end ratio R = challenger / incumbent on a frozen,
real workload (p50 and p95, paired bootstrap 95% CI), at verified quality parity, reported next to
R_control = simplest conventional control / incumbent on the same inputs. Program score: frozen
verdicts per 30 days, wins weighted above nulls (the exact weights and win threshold are open,
see below).

**Stage gates** (each one is a kill point, recorded in `data/ledger.jsonl`):

| gate | passes when | fails as |
|---|---|---|
| G0 pin | one openai/math commit and its `history.md` hash are recorded; no withdrawn manuscript | `BLOCKED_SOURCE` |
| G1 fit | every hypothesis of the theorem is checked against the actual module (metric? capacity? exact arithmetic? log-concave?) | `REJECTED_FIT` + counterexample |
| G2 executable | a finite algorithm exists, with a written crossover estimate for real sizes | `REJECTED_NONCONSTRUCTIVE` |
| G3 hot | a profile shows the routine is ≥10% of wall time or memory on the real path | `REJECTED_COLD` + profile |
| G4 measured | incumbent, simple control and challenger run interleaved on identical frozen inputs; quality parity signed by a referee from a different model family than the proposer | `NULL` or `WIN` |
| G5 reproduced | a second machine (hosted runner for public repos) reruns from the manifest alone | `UNREPRODUCED` |

**Attribution rule.** A gain that the simple control also delivers is a conventional win for the
project, recorded with no Math372 credit. A win also needs an ablation: remove the theorem-derived
part and the gain must disappear.

**Artifact class.** Each candidate declares one: executable algorithm, bound used to pick a
parameter, impossibility guard, or existence-only. Only the first two can claim speed.

**Budget and cadence.** At most two or three experiments in flight. Weekly cycle: the phone lane
drafts fit checks and preregistrations, hosted runners and the desktop execute, a referee rules,
results freeze. A candidate with no executed measurement after two cycles closes as `STALLED`
(logged, not a null). Lanes: phone chats for source deltas, fit checklists, prior art and drafts
(never execution claims); paid seats only at contested fits and verdicts; hosted runners for public
repos and reruns; the desktop GPU only for admitted candidates in an exclusive window.

**Stop rule.** If several weekly cycles pass without one theorem-derived candidate clearing G3,
pause active transfer work, publish the audit of rejections and nulls, and keep only monthly
source-delta monitoring.

## Open questions the council did not settle

- Win threshold: R ≤ 0.8 and beat the control by 10% (Fable), ≥10% reduction (Sol), CI lower bound
  above 1.05× on a weighted task basket (Astra), or beat both arms by a preregistered MDE (Opus).
- Stop horizon: four weekly cycles (Astra, Sol) or six weeks (Opus).
- OpenMC and Kerdoios are not in the factory registry; they need admission before implementation.
- Whether the durable product is an "assumption checker" of guard results (Fable) rather than speedups.

## Files

| path | what |
|---|---|
| `data/candidates.json` | the queue: family, target, artifact class, gate reached, next falsifier |
| `data/ledger.jsonl` | append-only verdicts, one JSON object per line |
| `data/council-2026-11-03.md` | facilitator synthesis of the four council openings |
