---
title: "three small decisions, three pre-registered bars"
subtitle: "no small model beats the 8b at forming z0's own calls, a learned recovery controller beats a constant but not an mlp, and 'auto-merge on green' fails on our own history."
study: factory-intelligence-v0
status: draft
author: "zer0 research"
date: "september 30, 2026"
mock_data: false
toc:
  - id: question
    label: three small decisions
  - id: toolcall
    label: who forms z0's calls
  - id: recovery
    label: what to do after a failed call
  - id: promotion
    label: which promotions can skip a human
  - id: limits
    label: what this does not prove
---

<div class="lede">
three of today's experiments were written down before they ran, with the arms, the bar and what would count as failure. one is a clean null: none of the small tool-callers beat or could replace the 8b we already run. one is split: a learned recovery controller beats a constant on cost, but misses the bar for being as good as an mlp by 0.006. one failed: the auto-merge rule we picked on the first 70% of our history let through 11 bad promotions on the last 30%.
</div>

<div class="hero-rule"></div>

## three small decisions {#question}

a factory of agents makes many small decisions that should not need the frontier model or a human. which local model should form a call to z0's own router. what to do when a tool call fails. whether a branch can merge without anyone looking. each experiment below was pre-registered in its source repository, and each pinned commit was pushed before the scored run. nothing here changed runtime behaviour.

## who forms z0's calls {#toolcall}

z0intelligence#20 asked which small local models on groot (an rtx 3080 ti) form z0's own function calls correctly, and at what latency and vram. the pre-registration (6d56416) froze 184 items: 48 z0 `route_worker` / `delegate_worker` calls built from real claude code turns (text stays private, git has hashes), 125 bfcl v4 items across five categories, and the 11-item pinned action-selector cohort. every arm ran with thinking off, temperature 0, and one shared parser chain. the comparator was the farm default, qwen3-8b.

<table class="result-table">
<thead><tr><th>arm</th><th>pooled exact</th><th>z0 exact (form)</th><th>bfcl</th><th>irrelevance</th><th>p50 ms</th><th>vram mib</th><th>vs qwen3-8b</th></tr></thead>
<tbody>
<tr><td>functiongemma-270m (zero-shot)</td><td>63/184</td><td>0/48 (0)</td><td>61/125</td><td>0.84</td><td>3274</td><td>892</td><td>worse, p=2e-22</td></tr>
<tr><td>hammer2.1-3b</td><td>81/184</td><td>0/48 (0)</td><td>78/125</td><td>0.88</td><td>619</td><td>2504</td><td>worse, p=2e-17</td></tr>
<tr><td>qwen3.5-4b</td><td>137/184</td><td>22/48 (31)</td><td>106/125</td><td>0.84</td><td>1454</td><td>3486</td><td>worse, p=0.028</td></tr>
<tr><td>hammer2.1-7b</td><td>86/184</td><td>3/48 (6)</td><td>81/125</td><td>0.84</td><td>658</td><td>5052</td><td>worse, p=1e-16</td></tr>
<tr class="primary"><td>qwen3-8b (farm default)</td><td><strong>152/184</strong></td><td>29/48 (38)</td><td>113/125</td><td>0.76</td><td>1069</td><td>6004</td><td>—</td></tr>
<tr><td>qwen3.5-9b</td><td>121/184</td><td>9/48 (14)</td><td>103/125</td><td>0.80</td><td>1697</td><td>5850</td><td>worse, p=2e-6</td></tr>
<tr><td>qwen3-14b</td><td>150/184</td><td>26/48 (38)</td><td>114/125</td><td>0.92</td><td>1601</td><td>9872</td><td>not distinguishable, p=0.86</td></tr>
<tr><td>nemotron-orchestrator-8b</td><td>148/184</td><td>28/48 (38)</td><td>110/125</td><td>0.72</td><td>953</td><td>6004</td><td>not distinguishable, p=0.39</td></tr>
</tbody>
</table>

no candidate was better than qwen3-8b, and none passed the gates for a cheaper substitute. the hammers are cheap and fast but form almost no valid z0 call: they return `[]`, invent a tool named after the function, or shorten the task. qwen3.5-4b uses less vram but is slower and 15 items behind. qwen3.5-9b scores below the 4b because it called `delegate_worker` instead of `route_worker` on 24 of 43 routing items. functiongemma does not stop at its own turn boundary on this llama.cpp build and runs on to `max_tokens` in 120 of 184 replies; it was run zero-shot, and its card says to fine-tune it first, so this only says it is not usable off the shelf.

the bfcl subset barely separates the qwen-family arms (103–114 of 125). z0's own call formation does. the farm default's weak spot is irrelevance: it makes a call on 6 of 25 bfcl items where it should make none. the 14b rejects 23 of 25, at 1.6x the vram.

two deviations, both stated in the pre-registration file. smoke testing found two parser gaps (functiongemma's turn boundary, hammer's python-literal lists), fixed in the adapter before scoring (01c6dd9). and while scoring, the `z0 form_exact >= 0.90` gate turned out to be unreachable for every arm: the gold for the 5 `delegate_worker` items compared `task` with the whole "use provider p with model m for this: …" line, while every arm put only the subtask there. that caps form at 43/48 = 0.896. a labelled post-hoc check against the subtask moves qwen3-8b to 157/184 and changes no verdict. this study re-derived each arm's pooled count and its mcnemar discordant pairs from the committed per-item pass flags, and they match.

## what to do after a failed call {#recovery}

evolution lab's t3b asks whether a small learned controller can choose the recovery after a real tool failure. the first pass mapped hermes failure episodes onto a gym action space and collapsed to noop-vs-retry, so every learner landed on the majority. v1 (pre-registered 3cb0e50, before any labels were mined) uses six actions agents actually take: `noop`, `retry`, `edit_retry`, `switch_tool`, `ask`, `abort`. a structural rule labels each episode from the next three turns with no text, a verifier keeps only recoveries that worked, and a cost matrix makes a wrong abort cost 5 and a missed ask cost 4. the harness was committed (4b1015b) before the single test read.

of 2,340 episodes, 2,043 got a verified label (edit_retry 1,218, noop 468, switch_tool 299, ask 26, retry 25, abort 7). the test split is 379 episodes from held-out lineages.

<table class="result-table">
<thead><tr><th>controller (test, cost-decoded)</th><th>mean cost [95% ci]</th><th>accuracy</th><th>Δ vs best constant [95% ci]</th></tr></thead>
<tbody>
<tr><td>best constant (edit_retry)</td><td>0.368 [0.319, 0.422]</td><td>0.631</td><td>—</td></tr>
<tr><td>hand-written rule (a priori)</td><td>0.433 [0.382, 0.488]</td><td>0.546</td><td>+0.065 [+0.008, +0.119]</td></tr>
<tr><td>ridge, rich features</td><td><strong>0.252</strong> [0.201, 0.303]</td><td>0.749</td><td>−0.117 [−0.162, −0.072]</td></tr>
<tr><td>mlp, rich features</td><td>0.295 [0.240, 0.352]</td><td>0.712</td><td>−0.073 [−0.135, −0.011]</td></tr>
<tr class="primary"><td>mushroom body, rich features (primary)</td><td>0.288 [0.234, 0.345]</td><td>0.720</td><td><strong>−0.081 [−0.131, −0.030]</strong></td></tr>
</tbody>
</table>

- **primary: pass.** the mushroom-body controller beats the constant on expected cost; the ci excludes 0. across five seeds its test cost was 0.263–0.288.
- **secondary: fail, narrowly.** against the mlp the difference is −0.007 [−0.069, +0.056]. the bar for "competitive" was an upper bound below 0.05, and it misses by 0.006. ridge is the best single model, and not significantly better than the mushroom body.
- the hand-written rule is worse than always choosing `edit_retry`. mapping error classes to actions by hand does not match what recovering agents do.
- **ask and abort are untested.** the test split has one of each, and no model ever predicts abort, so the expensive cells of the cost matrix barely enter the result. this is a result about noop, retry, edit_retry and switch_tool.

a blind audit of 67 stratified episodes, done on structural skeletons without the rule's output, agreed with the rule on 0.970 of actions (kappa 0.964) and on every recovery verdict. that checks that the rule implements its definitions. it does not check what the text meant; the owner's content audit is still to do.

## which promotions can skip a human {#promotion}

decision #7 for the factory is how much may auto-merge. the promotion simulator (37b5678) replays every promotion the factory made from 2026-09-02 to 09-30: 324 events across nine repos (150 merged prs, 166 direct default-branch commits, 8 branch merges), with features at merge time and an outcome label. an event is bad if it was reverted, broke the target's code ci, or had its lines rewritten by a fix commit within 3 days (szz). one repo is private; its titles, branches and paths are hashed upstream and it is reported here only as a count.

the pre-registration (fa8de23, pushed before scoring) split the 305 scorable events by time: train is the first 214, holdout the last 91. the criterion, applied mechanically on train, picked `auto[all,<=inf,nonsrc]`: auto-merge when every check is green, or when the change touches no source code and nothing is red. on train it auto-merged 81 with 4 bad.

<table class="result-table">
<thead><tr><th>policy (holdout, base bad 0.231)</th><th>auto</th><th>bad auto</th><th>auto bad rate [95% ci]</th></tr></thead>
<tbody>
<tr><td>human merges everything (today)</td><td>0</td><td>0</td><td>—</td></tr>
<tr><td>auto on all-green</td><td>40</td><td>8</td><td>0.20 [0.10, 0.35]</td></tr>
<tr><td>auto on code-green</td><td>23</td><td>2</td><td>0.09 [0.02, 0.27]</td></tr>
<tr><td>promotion authority v0 clean pass + code-green (<code>pa_v0_auto</code>)</td><td>14</td><td><strong>0</strong></td><td>0.00 [0.00, 0.22]</td></tr>
<tr class="primary"><td>pre-registered pick</td><td>65</td><td><strong>11</strong></td><td>0.17 [0.10, 0.28] — bar 0.115</td></tr>
</tbody>
</table>

- **h1 (primary): fail.** the pick auto-merged 71% of the holdout, and 11 of the 21 bad events were among them. "all checks green" was often just the evidence-receipt workflow: 32 of the 71 all-green prs had no code check at all. 8 of the 11 bad auto-merges came from one z0evals site sprint, where each pr was followed by fixes within hours.
- **h2: true.** promotion authority v0's `ABSTAIN` caught 10 bad of 39 across all scorable events, against a 0.21 base. as a hard block it holds back about three good promotions per bad one, so it should route to a human, not block.
- **h3: unscorable.** no agent-to-integration-branch events landed in the holdout, and most agent work is not attributed as agent work (34 of 324 events are tagged).
- **h4: true.** `pa_v0_auto` auto-merged 14 holdout events with 0 bad, and 0 of 35 across train and holdout (wilson upper bound 0.099).

after seeing the holdout we looked at two narrower rules. these are exploratory, not pre-registered, and recomputed here from the pinned dataset: docs-only changes with nothing red had 0 bad in 40 (13% of events), and `pa_v0_auto` with `ABSTAIN` sent to a human plus docs-only had 0 bad in 74 (24%, upper bound 0.049). `auto_on_code_green` had 3 in 52. the pre-registered fail branch said "keep human merge for source changes; at most auto-merge docs-only". the narrower `pa_v0_auto` rule goes further than that, so it needs its own pre-registered test on new history before it decides anything.

## what this does not prove {#limits}

- **one principal.** the routing turns, the hermes episodes and the promotion history all come from one operator's agents and repos.
- **soft gold.** the acceptable `function` set for routing items is author-labelled, and the delegate items carry a known gold defect. t3b labels come from a structural rule with no content audit yet. promotion outcomes rest on an szz "fixed within 3 days" label; there were 0 reverts and 2 ci breaks in 305 events.
- **small or thin cells.** 48 z0 items and 11 action-selector items; 1 ask and 1 abort in the t3b test; 91 holdout promotions, 36 of them from one repo's sprint. zeros here have upper bounds of 5–22%, not proofs of safety.
- **one sample, one setting.** tool-calling ran once per item with thinking off on a shared gpu, and hammer's bfcl numbers are an upper bound because bfcl is public.
- **nothing was promoted.** no routing config, role default, controller or merge policy changed because of these results.

<details>
<summary><strong>references</strong></summary>

- [z0intelligence](https://github.com/kvnloo/z0intelligence): branches `exp/tool-calling-portfolio-v0` and `feat/promotion-sim-v0`. commits are pinned in the study manifest.
- [evolution-lab](https://github.com/kvnloo/evolution-lab): branch `exp/t3b-action-space-v1`.
- [berkeley function calling leaderboard](https://github.com/ShishirPatil/gorilla) (bfcl v4, apache-2.0): the 125-item subset, sampled with a fixed seed.
- [qwen3](https://huggingface.co/Qwen), [hammer 2.1](https://huggingface.co/MadeAgents), [functiongemma](https://huggingface.co/google), [nvidia/nemotron-orchestrator-8b](https://huggingface.co/nvidia/Nemotron-Orchestrator-8B): the models under test.

</details>
