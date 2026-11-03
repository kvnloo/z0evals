---
title: "a chart is not a web page"
subtitle: "same model, same data: an openui board took 7.2× fewer output tokens and finished 2.5× sooner than an html page."
study: genui-openui-vs-html-v0
status: evidence-local
author: "zer0 research"
date: "november 2, 2026"
published: '2026-11-02'
area: generative-ui
kind: study
tags: [generative-ui, openui, t3code, tokens]
featured: false
mock_data: false
toc:
  - id: question
    label: what we compared
  - id: result
    label: the result
  - id: where
    label: where the time goes
  - id: valid
    label: are the boards right?
  - id: next
    label: what changes in t3
  - id: limits
    label: what this does not prove
---

## what we compared {#question}

when you ask a coding agent in t3 code for a chart, it writes a whole html page and hands it to `html_render`. that page carries its own css, layout and drawing code, every time. the [openui chart-board catalog](https://github.com/kvnloo/t3code/tree/d5627b91afe5bf2b1d7411185282f284e7b783a6) on our t3 code fork takes a different route: the agent writes a few lines in openui's language, like `root = Board(...)` plus `Treemap`, `BarChart`, `StackedArea` or `Heatmap` calls with literal data, and the client draws it.

we held everything else still. five chart requests with literal synthetic data, two repetitions each, both formats, one model (`gpt-6.1-sol`) through the same harness, with the order alternated so warm-up hit both formats. the openui arm also got the [catalog instructions](https://github.com/kvnloo/z0evals/blob/main/studies/genui-openui-vs-html-v0/data/catalog-prompt.txt). protocol and files: [study readme](https://github.com/kvnloo/z0evals/blob/main/studies/genui-openui-vs-html-v0/README.md).

## the result {#result}

every number below is recomputed by [`analyze.py`](https://github.com/kvnloo/z0evals/blob/main/studies/genui-openui-vs-html-v0/scripts/analyze.py) from the [frozen rows](https://github.com/kvnloo/z0evals/blob/main/studies/genui-openui-vs-html-v0/data/ab-rows.json).

| | html page | openui board |
|---|---:|---:|
| passed | 10/10 | 10/10 |
| output tokens, all runs | 26,951 | 3,748 |
| mean output tokens | 2,695 | 375 |
| mean input tokens | 21,759 | 22,681 |
| mean total time | 52.7 s | 20.7 s |

openui used **7.2× fewer output tokens** and finished **2.5× sooner**. the price is about 922 extra input tokens per request for the catalog instructions. no run here hit a prompt cache, so that cost is shown in full.

per case, the gap held every time:

| case | html tokens | openui tokens | html s | openui s |
|---|---:|---:|---:|---:|
| activity heatmap | 2,062 | 282 | 44.0 | 22.5 |
| disk usage | 3,372 | 586 | 63.4 | 21.1 |
| stacked area | 2,080 | 186 | 41.4 | 21.7 |
| repo treemap | 2,880 | 287 | 54.4 | 17.2 |
| dense review load | 3,080 | 534 | 60.2 | 20.9 |

## where the time goes {#where}

both formats waited about the same before any text appeared: 19.6 s for html, 18.1 s for openui. after that, html spent 33.1 s writing its page and openui spent 2.6 s writing its board. the saving is almost all output, which is what you would expect when the answer shrinks from about 8,600 characters to about 660.

## are the boards right? {#valid}

a short answer is only a win if it is correct. the openui [oracle](https://github.com/kvnloo/z0evals/blob/main/studies/genui-openui-vs-html-v0/scripts/oracle.ts) parses each program with openui's own parser, validates it with the catalog the client ships, and checks every expected value in place.

- a wider sweep of 10 openui requests, including a pie chart the catalog cannot draw, sparse zeros and deep paths, passed 9/10 on each of two models. both misses were the same case: the model spelled out `Monday` where the data said `Mon`. once the oracle compared weekday labels by their first three letters, both models passed 10/10 ([rows](https://github.com/kvnloo/z0evals/blob/main/studies/genui-openui-vs-html-v0/data/generation-rows.json), [rescore](https://github.com/kvnloo/z0evals/blob/main/studies/genui-openui-vs-html-v0/data/generation-rescore.json)).
- sent as ordinary messages in a real t3 code thread, 9/9 boards passed ([verdicts](https://github.com/kvnloo/z0evals/blob/main/studies/genui-openui-vs-html-v0/data/t3-live-verdicts.json)).

the html check is much weaker: a fenced page exists and every expected number appears somewhere in it. nothing rendered or graded those pages.

## what changes in t3 {#next}

in the live run we pasted the catalog instructions into each message by hand. t3 code itself still tells agents to answer charts with `html_render`, so none of this saving happens by default. the next step is a server-side instruction on the fork's nightly channel, and a fresh measurement of that instruction, since a shorter prompt is a different treatment from the one measured here.

## what this does not prove {#limits}

these are source-reported local measurements, not an independent reproduction. one model, one harness, one provider account and two repetitions per case. the two formats do different jobs: the html prompt asked for an unbounded interactive page, openui is a bounded read-only catalog of four chart types. so this is the cost of the format an agent reaches for, not of equal-capability output. fixtures are synthetic. rendering speed, accessibility and native mobile drawing were not measured. full limits are in the [manifest](https://github.com/kvnloo/z0evals/blob/main/studies/genui-openui-vs-html-v0/manifest.yaml).
