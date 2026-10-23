---
title: "claude code savings, re-measured"
subtitle: "496 pre-registered runs against the current z0 integration: one lever holds everywhere, one depends on the task, one barely shows up."
study: claude-code-savings-v1
status: draft
author: "zer0 research"
date: "october 1, 2026"
mock_data: false
toc:
  - id: question
    label: the question
  - id: method
    label: how we measured
  - id: headline
    label: the headline
  - id: levers
    label: lever by lever
  - id: gating
    label: gating did not clear the bar
  - id: long-followup
    label: long is not the same as output-heavy
  - id: limits
    label: what this does not prove
---

<div class="lede">
v0 found big savings, but on samples of 6 to 22 runs per cell. since then the z0 plugin has gained a posture fact, decisionopportunity emission and worker routing. so tonight we wrote the analysis down first, ran 496 real claude code sessions, and checked whether the savings survive at about five times the sample size.
</div>

<div class="hero-rule"></div>

## the question {#question}

how much does the current z0 integration cut from what claude code bills, compared with stock claude code, without lowering task success? and do v0's per-lever effects (lean profile, state packet, observationpack) replicate on fresh tasks?

## how we measured {#method}

- **pre-registration.** arms, tasks, metric, tests and a quality guard were committed and pushed before the first measured run.
- **four arms.** stock, lean, lean + packet, lean + packet + observationpack. every arm turns off the user-installed z0 plugins, so z0 enters only where the arm says it does.
- **two suites.** the qa suite is v0's pinned held-out current-work questions, 11 questions × 4 reps. the repo suite is 20 tasks × 4 reps: 19 fresh tasks across four z0 repos plus v0's long recall task. the repo tasks are bug fixes, small features and code-navigation questions, each pinned by sha and checked by a program (restored tests, hidden tests or exact keys). every task was checked to fail as given and pass with the reference fix before any run.
- **cold and warm sessions.** in the repo suite, rep 0 of each task × arm is a cold session and reps 1–3 are warm.
- **primary metric.** billed tokens (input + cache reads + cache writes + output) from claude code's own usage report. we report its cost estimate alongside.
- **analysis.** paired wilcoxon test with holm correction and a task-cluster bootstrap. a saving counts only if success does not drop.

## the headline {#headline}

<table class="result-table">
<thead><tr><th>pooled, 124 pairs</th><th>tokens</th><th>cost</th><th>success</th></tr></thead>
<tbody>
<tr class="primary"><td>stock → lean + packet + obspack</td><td><strong>−34.2%</strong> [−40, −28]</td><td>−45.4%</td><td>121 → 124</td></tr>
<tr><td>stock → lean</td><td>−31.8% [−36, −27]</td><td>−42.8%</td><td>121 → 121</td></tr>
<tr><td>lean → + packet</td><td>−6.5% (n.s.)</td><td>+1.0%</td><td>121 → 124</td></tr>
<tr><td>+ packet → + obspack</td><td>+3.0% (n.s.)</td><td>−5.5%</td><td>124 → 124</td></tr>
</tbody>
</table>

the full current integration passes its pre-registered test: a third fewer billed tokens and 45% lower estimated cost, with success equal or better. the quality guard passed on every contrast and every stratum.

## lever by lever {#levers}

- **lean holds everywhere.** it saved 38.5% of tokens on cold repo sessions, 33.8% on warm ones and 25.5% on qa, and 118 of 124 pairs were cheaper. on cost, that is −54% cold and −32% warm, close to v0's −64% and −27%. this is the dependable lever.
- **the state packet depends on the task.** on current-work questions it cut a further 35.5% of tokens over lean and fixed the last two misses (42/44 → 44/44). stock → lean + packet came out at −62.7% cost, against v0's −61%, so that replicates. on fresh coding tasks in a new directory there is no history for the packet to report, and it *added* 10.8% tokens (holm p = 2.5e-4) with no change in quality. pooled, the two effects cancel. an always-on packet is the wrong default; it should be on when the session is about current work, not for every fresh worktree.
- **observationpack does nothing on short tasks.** it never packed anything on the qa questions and rarely on short repo tasks, and the token effect was not significant. on v0's long recall task it packed seven outputs per run and cut cost 41.5%, but total tokens only 4.7%: it halved the expensive cache writes and added one cheap cache-read turn. that is n = 4, so it is consistent with v0's long-session result, not a new confirmation. it is also a reminder that an unweighted token count can hide a real billing saving.
- **two new plugin features were not measured.** worker routing never ran in the original trial: under the lean profile's `--strict-mcp-config`, the plugin's `route_worker` mcp server does not load. decisionopportunity emission is shadow-only by design, so it could not change what the model saw.

## gating did not clear the bar {#gating}

the prompt-gated follow-up ran 372 trials. it failed both pre-registered tests against the session-start packet. on repo tasks, tokens changed −7.3%, but the interval ran from −13.8% to +0.8%. on current-work questions, they changed +16.6%, with an interval from −4.8% to +45.6%, against a +5% margin. correctness held. the overhead looked smaller. the registered claim still failed.

worker routing became callable in 3/3 lean probe sessions, but returned PARENT_ONLY every time. that is a loadability result, not offload savings.

source: [gated-packet addendum](https://github.com/kvnloo/z0evals/blob/913efb6f4b7b4ea9e318262281b250b3b485278b/studies/claude-code-savings-v1/ADDENDUM-v1b.md).

## long is not the same as output-heavy {#long-followup}

the longer follow-up ran 208 real sessions. across 10 long tasks, observationpack cut estimated cost 30.7% over lean, with an interval from −50.0% to −1.9% and success 39/40 in both arms. the primary test passed.

all of the saving came from directed recall: −64.2%, with 25 outputs packed per session. long multi-bug debugging changed +1.3% under lean and +5.3% under stock. it was long, but the large bash outputs mostly never reached the packing hook.

the aggregate quality guard passed. the recall subgroup did not: 12 → 11 correct sessions. one recall miss is not a general accuracy verdict, but it belongs beside the saving. 44 zero-token session-limit aborts were rerun after reset, so some nominally warm repetitions ran cold.

source: [long-session addendum](https://github.com/kvnloo/z0evals/blob/913efb6f4b7b4ea9e318262281b250b3b485278b/studies/claude-code-savings-v1/ADDENDUM-obspack-long.md) and [imported results](https://github.com/kvnloo/z0evals/blob/913efb6f4b7b4ea9e318262281b250b3b485278b/studies/claude-code-savings-v1/data/obspack-long/results.json).

## what this does not prove {#limits}

- one host, one model (sonnet), one night.
- the repo tasks are short, about five tool calls at the median, so long coding sessions may behave differently.
- costs are claude code's own estimate on a subscription, not an invoice.
- the qa suite shares one pinned directory per repo across arms, as in v0.
- the evolution-lab task ids were frozen after the qa suite started but before the repo suite. this is disclosed in the pre-registration.




<details>
<summary><strong>frozen study sources</strong></summary>

- [studies/claude-code-savings-v1/README.md](https://github.com/kvnloo/z0evals/blob/913efb6f4b7b4ea9e318262281b250b3b485278b/studies/claude-code-savings-v1/README.md)
- [studies/claude-code-savings-v1/manifest.yaml](https://github.com/kvnloo/z0evals/blob/913efb6f4b7b4ea9e318262281b250b3b485278b/studies/claude-code-savings-v1/manifest.yaml)
- [studies/claude-code-savings-v1/data/summary.json](https://github.com/kvnloo/z0evals/blob/913efb6f4b7b4ea9e318262281b250b3b485278b/studies/claude-code-savings-v1/data/summary.json)
- [studies/claude-code-savings-v1/ADDENDUM-v1b.md](https://github.com/kvnloo/z0evals/blob/913efb6f4b7b4ea9e318262281b250b3b485278b/studies/claude-code-savings-v1/ADDENDUM-v1b.md)
- [studies/claude-code-savings-v1/ADDENDUM-obspack-long.md](https://github.com/kvnloo/z0evals/blob/913efb6f4b7b4ea9e318262281b250b3b485278b/studies/claude-code-savings-v1/ADDENDUM-obspack-long.md)
- [studies/claude-code-savings-v1/data/results.json](https://github.com/kvnloo/z0evals/blob/913efb6f4b7b4ea9e318262281b250b3b485278b/studies/claude-code-savings-v1/data/results.json)
- [studies/claude-code-savings-v1/data/trials.csv](https://github.com/kvnloo/z0evals/blob/913efb6f4b7b4ea9e318262281b250b3b485278b/studies/claude-code-savings-v1/data/trials.csv)
- [studies/claude-code-savings-v1/data/v1b/results.json](https://github.com/kvnloo/z0evals/blob/913efb6f4b7b4ea9e318262281b250b3b485278b/studies/claude-code-savings-v1/data/v1b/results.json)
- [studies/claude-code-savings-v1/data/obspack-long/results.json](https://github.com/kvnloo/z0evals/blob/913efb6f4b7b4ea9e318262281b250b3b485278b/studies/claude-code-savings-v1/data/obspack-long/results.json)

</details>
