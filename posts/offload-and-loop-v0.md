---
title: "a format check is not a faithfulness check"
subtitle: "one local worker class passed our offload bar and then failed on faithfulness, and the loop that should learn from verified outcomes does not have the data yet."
study: offload-and-loop-v0
status: draft
author: "zer0 research"
date: "september 30, 2026"
mock_data: false
toc:
  - id: question
    label: two questions
  - id: offload
    label: speed-first offload
  - id: faithfulness
    label: the faithfulness check
  - id: density
    label: how many turns are verified
  - id: loop
    label: the loop has no data yet
  - id: utilization
    label: how often z0 changes anything
  - id: lesson
    label: what we take from it
  - id: limits
    label: what this does not prove
---

<div class="lede">
tonight we ran five measurements. one local worker class passed our speed-first offload bar, then failed a faithfulness test against haiku by a wide margin, so no class is offloaded. the verifier that labels turns had a bug that called about a quarter of its test passes passes when they were not. and the loop that should learn a better gate from verified outcomes has six usable rows: by its own pre-registered rule, insufficient data, with about half a year to go at current volume.
</div>

<div class="hero-rule"></div>

## two questions {#question}

z0 should do two things for the agents it sits beside. it should move work off the frontier model when a cheaper or faster model gives the same answer. and it should learn, from outcomes that someone or something independently checked, when its own gate is right. tonight asked whether either is ready. every experiment below was pre-registered in its source repository, every pinned commit was pushed, and only aggregates are published. the only runtime change was a shadow-only demotion.

## speed-first offload {#offload}

under the burn posture, z0 sends bounded work back to the frontier even when a local model on groot (an rtx 3080 ti running qwen3-8b) would answer as well and sooner. the speed-offload pre-registration (d716a38) defined five worker task classes, built frozen sets from z0 artefacts, and fixed a rule per class: the paired 95% lower bound of local minus the better frontier arm above −0.10, local pass rate at least 0.80, local warm p95 below the faster frontier arm's p95, errors at most 5%.

<table class="result-table">
<thead><tr><th>class</th><th>local</th><th>haiku</th><th>sonnet</th><th>lower bound</th><th>p95 local / frontier ms</th><th>status</th></tr></thead>
<tbody>
<tr class="primary"><td>summarize_tool_output</td><td>60/60</td><td>59/60</td><td>37/60</td><td>+0.000</td><td>893 / 2054</td><td>speed_qualified, then demoted</td></tr>
<tr><td>classify_file_type</td><td>48/60</td><td>59/60</td><td>59/60</td><td>−0.267</td><td>370 / 1419</td><td>not_equivalent</td></tr>
<tr><td>evidence_sufficiency</td><td>31/48</td><td>47/48</td><td>48/48</td><td>−0.479</td><td>146 / 1863</td><td>not_equivalent</td></tr>
<tr><td>extract_json</td><td>8/60</td><td>49/60</td><td>60/60</td><td>−0.933</td><td>1794 / 1970</td><td>not_equivalent</td></tr>
<tr><td>short_rewrite</td><td>2/53</td><td>48/53</td><td>22/53</td><td>−0.943</td><td>741 / 4224</td><td>not_equivalent</td></tr>
</tbody>
</table>

the local model is faster on every class, but only one class held quality, and the speed gain there is about 2×, not the 30× the logprob decision mode suggests. the frontier latency is `duration_api_ms`, which leaves out the cli start and so favours the frontier.

the one pass was weaker than it looked. the check for `summarize_tool_output` was format and facts: at most 40 words, the files-changed count written as digits, and at least one changed file named, on git-stat items only. sonnet's 37/60 was mostly that check's strictness (it writes "two files changed"). the write-up said so at the time, and the class was put in front of a faithfulness test before anything acted on it.

## the faithfulness check {#faithfulness}

decision 20 (pre-registration 2870516) built 160 new items from real invocations on z0 repos and ci: pytest on mutated code, git stat and diff ranges, build and lint output, and gh run and check pages, with 403 deterministic critical facts. a blinded sonnet judge marked unsupported or contradicted claims. the bar was non-inferiority to haiku, paired, one-sided 95%: hallucinated items no more than 2 points worse, critical-fact recall no more than 5 points worse.

<table class="result-table">
<thead><tr><th>arm</th><th>hallucinated items</th><th>contradicted</th><th>critical-fact recall</th><th>p95 ms</th></tr></thead>
<tbody>
<tr class="primary"><td>groot qwen3-8b</td><td>42/160 (26.3%)</td><td>23</td><td>0.816</td><td>2233 (wall)</td></tr>
<tr><td>groot qwen3-14b (exploratory)</td><td>35/160 (21.9%)</td><td>17</td><td>0.860</td><td>2914 (wall)</td></tr>
<tr><td>haiku</td><td>21/159 (13.2%)</td><td>7</td><td>0.893</td><td>20375 (api)</td></tr>
<tr><td>sonnet (also the judge)</td><td>18/160 (11.3%)</td><td>5</td><td>0.975</td><td>2054 (api)</td></tr>
</tbody>
</table>

- **hallucination: fail.** qwen3-8b minus haiku is +12.6 points, with an upper bound of +18.9 against a +2 margin. the bounds exclude equality too, not just non-inferiority.
- **recall: fail.** −7.7 points, lower bound −10.5 against a −5 margin.
- **where.** pytest summaries were nearly fine on recall (0.99) but swapped expected and actual values. on git items the 8b invented line counts and outcomes (recall 0.67, 14/40 hallucinated); on gh pages it miscounted runs and dropped failed jobs (0.73, 16/40). none of this was visible to the v0 format check.
- **qwen3-14b**, run for information only, is closer but fails both margins as well.

so the class was demoted to `not_equivalent` (2c0c339). no task class is speed-qualified, and no capability entry was added.

## how many turns are verified {#density}

the learning side starts with verified outcomes (z0intelligence#54, 17a88ba): an append-only record, written after the fact, that attaches independent signals to past claude code turns: test and ci exit codes, whether commits survived or were fixed within days, pr outcomes, and the next user turn's correction cues. a turn is `verified_success` or `verified_failure` only on medium- or high-confidence signals; tests the turn wrote itself do not count.

verification density v0 (pre-registration 4431225, results bd370e6) tried to raise the share of live turns with such a label from a baseline to at least 0.20, adding verifiers that ship at low confidence until a labelled sample of at least 50 firings shows 0.90 precision.

<table class="result-table">
<thead><tr><th>test</th><th>bar</th><th>result</th><th>verdict</th></tr></thead>
<tbody>
<tr class="primary"><td>t1 live verified share</td><td>≥ 0.20</td><td>4/31 = 0.129</td><td>not met</td></tr>
<tr><td>t2 checked_later precision</td><td>≥ 0.90, n ≥ 50</td><td>0.38 (n=33)</td><td>demoted</td></tr>
<tr><td>t2 ended_on_error precision</td><td>≥ 0.90, n ≥ 50</td><td>0.20 (n=6)</td><td>demoted</td></tr>
<tr><td>t2 tests_suite_new_tests precision</td><td>≥ 0.90, n ≥ 50</td><td>1.00 (n=4)</td><td>demoted (too few)</td></tr>
<tr><td>t4 gh lookup time</td><td>cold ≤ 60 s, warm ≤ 30 s</td><td>36 s / 20 s</td><td>met</td></tr>
</tbody>
</table>

the labelling found a defect in v0 itself. `pytest … | tail` reports the exit code of `tail`, so a failing suite piped into a filter read as a pass. 15 of `checked_later`'s 20 wrong labels were such runs. with the fix, the 7-day count of in-turn test passes fell from 114 to 87: **about 24% of v0's test-success signals were not passes.** v0 `verified_success` labels from piped runs are suspect until re-verified. the fix was made after the labels were seen, so the higher share it gives (0.161) is exploratory and does not count toward t1.

most live turns are unverified for a plain reason: they are orchestration (12 of 31), ops (9) or questions (7), where the work happens in subagents or leaves no test, commit or ci trace attached to the user turn.

## the loop has no data yet {#loop}

the verified loop (evolution-lab, pre-registration ded915a) would compare the deterministic gate with a learned one on verified live rows, exported by z0int (5d0a85c). the rule allows three answers: `SHADOW_CANDIDATE`, `NO_IMPROVEMENT`, or `INSUFFICIENT_DATA` unless there are at least 300 rows, 30 not-success rows, 10 session groups and five folds with both classes.

the result (1b80a4e) is **insufficient data**. of 23 exported rows, 16 had no verified label and 1 was not an act, leaving 6 rows, 1 not-success, and one session. grouped cross-validation was impossible. the gate's numbers on those 6 are descriptive only.

<table class="result-table">
<thead><tr><th>population</th><th>turns/wk</th><th>resolved/wk</th><th>weeks to gate</th><th>weeks to 80% power</th></tr></thead>
<tbody>
<tr class="primary"><td>live (interactive + agent)</td><td>217</td><td>28</td><td>24.1</td><td>29.6</td></tr>
<tr><td>all cohorts, current coverage</td><td>2492</td><td>651</td><td>19.8</td><td>24.3</td></tr>
<tr><td>all cohorts, if eval harness sessions emitted features</td><td>2492</td><td>651</td><td>1.0</td><td>1.3</td></tr>
</tbody>
</table>

the binding constraint everywhere is not-success rows: at a pooled not-success rate of 0.043, 30 of them take months. live feature coverage since emission began is already 100%, so the plumbing is not the bottleneck. the eval and probe harness sessions (325 of 331 swept) would reach the gate in about a week, but they are a different distribution from the user's work. this projection is a linear extrapolation of one day with one observed live not-success; read it as an order of magnitude.

## how often z0 changes anything {#utilization}

the north-star metric (utilization v0, 5bc290f) counts frontier-bound units of the user's real interactive and agent work in which z0 displaced the work, shortened the context, or made an enforced decision that a verifier passed. an operator run of the pinned instrument gave **26.3% (51 of 194)**, and 27.9% (56 of 201) an hour later. all of it was observationpack shortening. there were 0 offloads (posture was burn, under which that is the designed behaviour) and 0 enforced decisions, because every gate decision is still shadow. these counts are source-reported, not a pinned artifact.

## what we take from it {#lesson}

- **format checks overstate local equivalence.** a check that a summary has the right shape and names a file passed 60/60. a check that its claims are true failed by 13 points. the next offload class needs a faithfulness or semantic bar from the start. typed decisions, where the answer can be checked exactly, look like the better place to look: the same 8b got 43/48 on evidence_sufficiency in logprob mode at about 90 ms on an earlier groot bench, against 31/48 generatively, but that bench is outside this study and was not tested against the frontier here.
- **the loop is data-bound by coverage and verification density.** the learner, the exporter and the pre-registered rule exist. what is missing is verified live not-success rows: most live turns are orchestration and ops that no verifier reaches, the new verifiers have not earned their confidence, and the old test signal over-reported passes. more coverage (other harnesses that are built but not installed) and more verified turns per session move the date; tuning the learner does not.

## what this does not prove {#limits}

- **one principal, about one day.** every set, transcript and session is one operator's.
- **small sets.** 48–60 items per offload class, synthetic wrappers rather than sampled worker traffic, on a gpu shared with another tenant.
- **one judge.** faithfulness was judged by sonnet, which is also an arm; deterministic recall and a contradicted-only check point the same way.
- **thin labels.** density precision rests on fewer than 50 firings per verifier and 31 live turns; the pipe fix came after the labels were seen.
- **a rough projection.** weeks-to-gate rest on one observed live not-success and a pooled base rate.
- **nothing was promoted.** no routing, capability entry, gate or verifier confidence changed, apart from the shadow-only demotion.

<details>
<summary><strong>references</strong></summary>

- [z0intelligence](https://github.com/kvnloo/z0intelligence): branches `feat/speed-offload-v0`, `exp/summarize-faithfulness-v0`, `feat/verified-outcomes-v0`, `feat/verification-density-v0`, `integrate/claude-code-z0-stack`, `feat/loop-export-v0` and `feat/utilization-v0`. commits are pinned in the study manifest.
- [evolution-lab](https://github.com/kvnloo/evolution-lab): branch `exp/verified-loop-v0`.
- [qwen3](https://huggingface.co/Qwen): the local models under test.

</details>
