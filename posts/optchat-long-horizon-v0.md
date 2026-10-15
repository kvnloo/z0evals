---
title: "does optchat stay small after fifty tool calls?"
subtitle: "the sol-pi task was twelve files. this is the same idea, run until the transcript is no longer a toy."
study: optchat-long-horizon-v0
status: evidence-pending
author: "zer0 research"
date: "october 5, 2026"
mock_data: false
toc:
  - id: what-we-used
    label: what we used before
  - id: this-run
    label: fifty cats
  - id: numbers
    label: the numbers
  - id: limits
    label: what this does not prove
---

<div class="lede">
optchat is supposed to keep the next turn small while the tool log keeps growing. the question is not whether a two-turn demo can say that. the question is whether it is still true at turn fifty.
</div>

<div class="hero-rule"></div>

## what we used before {#what-we-used}

sol-pi, and the observationpack port of it, was not a 100-turn chat benchmark. the house task is `benchmarks/claude_code/tasks/backend-review`. family: `long_horizon_recall`. the agent must `cat` twelve source files, in order, with no head, tail, or grep, then answer questions about those files without opening them again.

that is why it stresses context. the tool results are the files. later turns have to remember them. the published observationpack result on that task was n=12 paired trials, −30.3% total tokens, 12/12 verified. short tasks were a null. we did not have a 50-turn or 100-turn suite for it.

swe-bench and terminal-bench last longer, and they are the right public suites if the question is "did the agent finish the job." they are the wrong suite if the question is "did the next request stay small." those runs mix task success, tool choice, and context size. this plugin only owns the last one.

## fifty cats {#this-run}

same protocol, more files. fifty public python files from the pinned z0intelligence tree, each between 800 and 12,000 bytes. each turn is a user line, the file as the tool echo (capped at 8,000 characters), and a one-line reply.

two arms, one variable:

- off: the accumulated transcript. that is what a normal session resends.
- on: the optchat view, after `qwen3-0.6b-q8` on the local vulkan router (`127.0.0.1:11520`) builds the due nodes.

no private chat. no paid model. the router’s context window is 2048 tokens, so a compaction request that does not fit is a 400. the measured compactor saw a 1,600-character excerpt. the off arm still kept the full echo.

## the numbers {#numbers}

| turn | raw transcript | optchat view | view / raw |
|---:|---:|---:|---:|
| 1 | 2,656 | 516 | 0.194 |
| 6 | 33,208 | 2,671 | 0.080 |
| 10 | 61,301 | 3,818 | 0.062 |
| 25 | 132,943 | 8,480 | 0.064 |
| 50 | 270,271 | 16,621 | 0.062 |

at turn 50 the view is 16.6 kb and the transcript is 270 kb. about 6% of the raw log. placeholders left at the end: 0. the free model did build the nodes. the view did not fold into higher tree levels, because 16 kb is still under the 128 kb budget. the saving is the per-message line, not a deep merge.

turn 1 is the smallest saving. the first file is small. by turn 6 the gap is already the shape that matters: the transcript has jumped, the view has not.

## what this does not prove {#limits}

this is not an answer-quality result. nobody checked whether the one-line summaries were enough to answer a later question. sol-pi’s n=12 trial did that. this run did not.

it is also not the live omp hook. that hook adds the view beside the host transcript. it does not replace the session. the table is the gist comparison: view versus accumulated text. a fresh omp process that only sends the view would see this reduction. a continued omp session that also keeps the history would not.

the free router cannot hold the gist’s 64k-token compactor context. 2048 tokens is what this laptop’s current server allows. longer summaries, or a model that refuses, would move these numbers. one request in the run did 400 and was recorded as a fallback line. it did not stop the trajectory.

do not read 16× as a promotion. it is one 50-turn context-size trajectory, on public files, with a free local model, unscored.
