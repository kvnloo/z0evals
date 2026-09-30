---
title: "four pre-registered bars, four misses"
subtitle: "a $0 gpu tier that works, a learned router that doesn't beat a generic one, and why the authority check has to live on the tool call."
study: local-offload-and-authority-v0
status: draft
author: "zer0 research"
date: "september 30, 2026"
mock_data: false
toc:
  - id: question
    label: two questions
  - id: offload
    label: a $0 tier on the gpu box
  - id: router
    label: the learned router is a generic one
  - id: effects
    label: reading authority from the prompt
  - id: actions
    label: moving the check to the tool call
  - id: pending
    label: what is still pending
  - id: limits
    label: what this does not prove
---

<div class="lede">
four of today's experiments were written down before they ran: the question, the arms, the bar, and what would count as failure. all four reached a verdict, and none of them cleared its bar. one changed where the next experiment should look. a fifth is registered and still waiting for data, and a benchmark of a new $0 gpu tier came out well but short of the bar we proposed for it.
</div>

<div class="hero-rule"></div>

## two questions {#question}

z0intelligence decides two things for an agent harness. **where** bounded work runs when it does not need the frontier model, and **whether** the agent may do something without asking the human. today we tested one lever on the first question and three on the second, plus a fifth that is only registered so far. all of it ran in shadow; nothing was enforced on live traffic.

## a $0 tier on the gpu box {#offload}

groot is an rtx 3080 ti on the tailnet running a llama.cpp router server with four qwen3 sizes. z0intelligence `feat/groot-offload-provider` (8053faa) lets a host declare it as a keyless local provider: whitelisted keys only, a capped concurrency, the $0 route still has to pass its evidence hash check, and there is no remote fallback. we benched it on the frozen 48-item evidence_sufficiency set (supported / insufficient / contradicted).

<table class="result-table">
<thead><tr><th>backend</th><th>correct</th><th>confident errors</th><th>median ms/item</th></tr></thead>
<tbody>
<tr><td>macbook radeon (vulkan), qwen3-0.6b q8</td><td>25/48</td><td>3</td><td>1236</td></tr>
<tr><td>groot, qwen3-0.6b q8</td><td>27/48</td><td>3</td><td>41</td></tr>
<tr><td>groot, qwen3-1.7b q4_k_m</td><td>28/48</td><td>8</td><td>48</td></tr>
<tr><td>groot, qwen3-4b q4_k_m</td><td>36/48</td><td>4</td><td>63</td></tr>
<tr class="primary"><td>groot, qwen3-8b q4_k_m</td><td><strong>43/48</strong></td><td><strong>1</strong></td><td>90</td></tr>
</tbody>
</table>

the same 0.6b weights run about 30x faster on groot. qwen3-8b reached 43/48 with one confident error, one item short of the ≥44/48 bar we proposed for replacing jev (46/48, from earlier work) on this task. so it is the offload default, not an admitted replacement. one honest caveat: that bar was written next to the bench, not committed before it.

## the learned router is a generic one {#router}

with a legal candidate set already filtered by policy, would nvidia's nemotron-orchestrator-8b pick the right local model more often than the deterministic order? the pre-registration (1302c3a) had three conditions: legal proposals, beat the deterministic choice, **and** beat a generic qwen3-8b given the identical prompt. the last one is there so a "learned router" cannot win just by being an 8b llm.

- orchestrator with thinking: 23/59 correct choices versus 8/59 for the deterministic order (mcnemar p=0.0003). conditions (a) and (b) pass.
- generic qwen3-8b with thinking, same prompt: also 23/59 (9 vs 9 discordant, p=1.0). condition (c) **fails**. result (eb7c7d3): not continued in shadow.
- a trivial `cheapest` rule got 35/59, and a fixed `strongest` rule delivered a 0.90 pass rate on the 48 evidence items. the orchestrator never proposed the 4b or 8b candidate. it optimised the stated latency preference and did not predict difficulty.
- it costs about +6 gb of vram and a 3.6 s p50 per decision with thinking on.

the deterministic arm scored 0 on the evidence set for a boring reason: the host listed its own 1236 ms copy of the 0.6b model before groot's 41 ms copy of the same weights. that is a host-ordering bug, not a routing insight, and z0intelligence b072468 lets the host choose the order. we have not re-run the eval on it.

## reading authority from the prompt {#effects}

claude code's decision records used to hard-code every turn as read-only, so the gate could never ask for permission. effect inference classifies each request as read, write or privileged (push, merge, deploy, messages, secrets, installs, …) from the prompt text.

- **v0** (pre-registered d651753 before the classifier existed, frozen at b538963): 80/80 in-sample, then on 60 held-out cases written by a fresh agent and committed unread, 6 privileged requests slipped through as ACT (the read-only baseline let 20 through). the bar was 0. **fail.** five of the six were phrasings the lexicon lacked ("send it up", "get this onto main").
- **v1** (pre-registered f65e72a, frozen f7afd83) added scoped in-prompt grants: "push the feature branches" authorises exactly that. on 88 new held-out cases it acted on 18/21 correctly granted requests with 0/20 unnecessary read-only asks, but let **8/27** privileged requests through outside their granted scope (3187f46). **fail.** without grants its lexicon alone let only 1/27 through, but then asked on 20 of the 21 requests that had in fact been granted.

the misses taught us something structural. grants turn classifier false positives into self-grants: a read-only question that mentions deploy gets classed as privileged and then covered by its own phrase. and in the live cohort, a prompt that granted feature-branch pushes covered a *default-branch* push the agent chose later in the same turn. a turn-level gate cannot see that. the check has to look at the action.

## moving the check to the tool call {#actions}

action authority v0 (f948389, frozen before any gold existed) takes grants from intent and effects from the actual tool call, and returns allow / ask / deny from a claude code `PreToolUse` hook. we replayed it over 3,716 historical tool calls and labelled 798 of them: every call a broad privileged-candidate net caught, plus 80 random others.

<table class="result-table">
<thead><tr><th>metric</th><th>result</th><th>bar</th></tr></thead>
<tbody>
<tr class="primary"><td>unauthorized privileged calls caught</td><td><strong>112/134 (83.6%)</strong></td><td>100% — fail</td></tr>
<tr><td>false friction, labelled sample</td><td>81/664 (12.2%)</td><td>≤5% — fail</td></tr>
<tr><td>false friction, population-weighted</td><td>2.3%</td><td>≤5% — pass</td></tr>
<tr><td>hook wall time p95, fresh interpreter</td><td>34 ms</td><td>&lt;50 ms — pass</td></tr>
</tbody>
</table>

of the 22 misses, 16 are parser misses: mostly writes outside the repo made from inside scripts or heredocs, which the shell parser cannot resolve. five are grants that were too broad, because a later "no github writes" was not read as a prohibition. ten of the 22 rest on low-confidence gold. the friction is mostly ssh, outside-repo writes and pushes that the gold judged authorised by broad but explicit instructions in scheduled prompts. it is fast enough and closer than the prompt-level gate. it is not safe enough to enforce.

## what is still pending {#pending}

**resource posture v0** (083b99d) labels each budget window BURN / BALANCED / OFFLOAD / RESERVE, so routing can spend frontier quota that is about to expire and offload when a window will run out first. the evaluation is registered: a 7-day replay with calibration on days 1–3 and scoring on days 4–7. to pass, posture-aware routing must waste at least 10 points less frontier capacity per weekly window than posture-blind routing, with no extra rate-limited time, a bounded projection error and at most 2 posture flips per group per day. there are no results yet, and we claim none.

## what this does not prove {#limits}

- **one principal.** every live cohort and replay comes from one operator's claude code usage. in the authority replay, one session and its subagents carry 2,765 of 3,716 calls and all 291 parsed-privileged calls.
- **llm-labelled gold.** held-out cases and all authority gold were written by separate llm agents from a label policy, not by the user. two v1 misses have disputed gold.
- **small n.** 48 evidence items, 59 routing items, 60 and 88 held-out prompts, 10–11 live turns. only large effects are detectable.
- router outcomes are reused single samples, and orchestrator-8b was trained for multi-turn orchestration with frontier experts, so a one-shot pick among small local models is off its distribution.
- all four verdicts are on shadow replays. none of these levers is enforced, and none is promoted by this study.

<details>
<summary><strong>references</strong></summary>

- [z0intelligence](https://github.com/kvnloo/z0intelligence): branches `feat/groot-offload-provider`, `exp/orchestrator-router-v0`, `feat/effect-inference-v0`, `feat/effect-inference-v1`, `feat/action-authority-v0`, `feat/resource-posture-v0`. commits are pinned in the study manifest.
- [nvidia/nemotron-orchestrator-8b](https://huggingface.co/nvidia/Nemotron-Orchestrator-8B) and [nvlabs/toolorchestra](https://github.com/NVlabs/ToolOrchestra): the model and the prompt format under test.
- [qwen3](https://huggingface.co/Qwen): the offload models.

</details>
