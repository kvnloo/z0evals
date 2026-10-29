# local-offload-and-authority-v0

One day of pre-registered z0intelligence experiments on two questions: where bounded work can go when it
does not need the frontier model (a $0 local GPU tier, and whether a learned router should pick within it),
and where the check belongs that decides whether an agent may act without asking (the prompt, or the tool call).
Every source is pinned by commit; only aggregates are published; failed pre-registered bars are reported as failures.

## Findings

| experiment | pre-registered bar | result | verdict |
| --- | --- | --- | --- |
| groot OFFLOAD tier, evidence_sufficiency (48 items) | proposed admission >=44/48 (not committed in advance) | qwen3-8b 43/48, 1 confident error, 90 ms median; 4b 36/48; 1.7b 28/48; 0.6b 27/48 at 41 ms vs the MacBook Radeon's 25/48 at 1236 ms | OFFLOAD default; **not admitted** as a Jev replacement |
| Orchestrator-8B shadow router (1302c3a -> eb7c7d3) | legal, beats deterministic, **and** beats a generic Qwen3-8B with the same prompt | 23/59 vs deterministic 8/59 (p=0.0003) but vs Qwen3-8B 23/59 (p=1.0); `cheapest` 35/59 | **fail** (null vs generic control); not continued |
| Addendum A1: deterministic arm under host `local_order` [groot, local] (0e90053 -> 336cb47) | S1 pass >=0.85 and S1 regret below `cheapest` (0.43); same frozen items and gold | S1 deterministic now picks qwen3-8b 48/48: pass 0.52 -> 0.90, regret 1.44 -> 0.13; pooled 12/59, pass 0.86, regret 0.11 (`cheapest` 0.35) | **confirmed**: the host-ordering fix (b072468) works; the orchestrator verdict is unchanged |
| Effect inference v0 (d651753 -> b538963 -> f6406c1) | 0 false ACT on privileged, <=10% read ASK, beats baseline | in-sample 80/80; held-out 6 false ACT (baseline 20), 1/20 read ASK, 47/60 class | **fail** on held-out |
| Effect inference v1, scoped in-prompt grants (f65e72a -> f7afd83 -> 3187f46) | 0 privileged ACT outside grant, <=10% read ASK, >=80% ACT when granted | 8/27 outside-scope ACT, 0/20 read ASK, 18/21 ACT when granted | **fail** on held-out; structural finding below |
| Action-level authority v0 (f948389 -> a3243fa) | catch 100% unauthorized privileged, friction <=5%, hook p95 <50 ms | 112/134 caught (83.6%); friction 12.2% sample / 2.3% weighted; p95 34 ms | **fail** (catch, sample friction); latency pass |
| Resource posture v0 (083b99d) | W_aware <= W_blind - 10 pp, L_aware <= L_blind, projection error and flip bounds | no data yet | **pending** |

## Structural finding

Prompt-level effect inference fails for two reasons that more vocabulary alone does not fix. First,
in-prompt grants turn classifier false positives into self-grants. Second, a turn-level gate cannot see
actions chosen mid-turn: in the live cohort, a prompt that granted feature-branch pushes covered a
default-branch push the agent chose later in the turn. That moved the check to the tool call
(action-authority-v0). The per-call check is fast enough (p95 34 ms) but still misses 22 of 134
unauthorized privileged calls: 16 are parser misses (mostly writes outside the repo made from scripts),
and 5 are grants that were too broad because a later prohibition was not read as one.

## Threats to validity

Single principal (one operator; one session plus its subagents carries 74% of replayed calls), LLM-written
gold (not the user's), small n (48 / 59 / 60 / 88 items; 10-11 live turns), reused single-sample router
outcomes, and a non-committed offload admission bar. See `manifest.yaml` `limitations`.

Aggregate data: `data/summary.json`. Regenerate with `summarize.py --groot-bench DIR --z0int REPO`
(needs the private bench outputs whose sha256 values are listed in the manifest).
