# genui-openui-vs-html-v0

Status: **source-reported local measurement, not independently reproduced**

Question: when an agent answers a data question with an inline chart, how much does the answer
format cost? We compare a self-contained HTML page (what T3 Code's agents are told to produce today,
through `html_render`) with a program in OpenUI's chart-board language (`openui-v2`), rendered by
the T3 Code fork's chart catalog.

## What ran

- **Format A/B** (`data/ab-rows.json`): 5 chart requests with literal synthetic data, 2 repetitions,
  both formats, one model (`gpt-6.1-sol`) through the same `hermes chat` harness. Order alternates
  per repetition so warm-up and caching hit both formats. Script: `scripts/ab.ts`.
  - openui prompt = `data/catalog-prompt.txt` + request + "reply with one openui-v2 block and a
    two-sentence summary".
  - html prompt = request + "reply with one self-contained interactive HTML page and a two-sentence
    summary".
- **Generation sweep** (`data/generation-rows.json`): 10 openui-only requests, including an
  unsupported chart type (pie), sparse zeros and deep paths, on two models: `gpt-6.1-sol` and the
  harness default model at the time (its id was not recorded). Script: `scripts/generate.ts`.
- **Inside T3** (`data/t3-live-verdicts.json`): 9 of the requests sent as ordinary messages in one
  T3 Code thread (Hermes over ACP, `gpt-6.1-sol`), judged with the same oracle. Script:
  `scripts/judge-t3.ts`.

`scripts/analyze.py` recomputes `data/summary.json`, the source of every number in the post.

## Results

| | html | openui |
|---|---:|---:|
| passed | 10/10 | 10/10 |
| output tokens, all 10 runs | 26,951 | 3,748 |
| mean output tokens | 2,695 | 375 |
| mean input tokens | 21,759 | 22,681 |
| mean total time | 52.7 s | 20.7 s |
| mean time to first text | 19.6 s | 18.1 s |
| mean time after first text | 33.1 s | 2.6 s |

OpenUI used 7.2× fewer output tokens and finished 2.5× sooner on average, for about 922 extra input
tokens of catalog instructions per request. Nearly all of the time difference is after the first
text arrives: both formats spend about 18–20 s before any text appears.

Generation sweep: 9/10 for each model under the original oracle. Both misses were the same case,
where the model wrote full weekday names for `Mon`…`Sun`; after the case was changed to compare the
first three letters, both models scored 10/10 (`data/generation-rescore.json`). In T3: 9/9 passed.

## How the judging works

- openui: `scripts/oracle.ts` parses the program with OpenUI's own parser, validates it with the
  shipped catalog module (`OpenUiCharts.tsx` at the t3code commit in the manifest), and checks every
  expected value positionally.
- html: there is no schema, so the check is weak: an `html` fence exists and every expected number
  appears in it. It does not render the page or check that the chart is correct.

## What this does not show

- Not reproduced by anyone else; one harness, one provider account, one machine, small n (2 reps).
- The two formats do different jobs: the HTML prompt asks for an interactive page with no limits;
  openui is a bounded read-only catalog of four chart types. The result is about the cost of the
  formats an agent would reach for, not equal-capability output.
- The HTML pass rate rests on the weak check above; the openui pass rate rests on a much stricter one.
- Synthetic fixtures only. No user data, prompts or private traces are included.
- The live T3 run pasted the catalog instructions into each message by hand. T3 Code does not yet
  tell agents to write openui on its own.
- Rendering speed, accessibility and native mobile rendering are not measured here.

## Files

| path | what |
|---|---|
| `data/ab-rows.json` | 20 A/B rows: verdict, tokens, timings, artifact size; openui programs kept, HTML pages dropped |
| `data/generation-rows.json` | 20 openui sweep rows with programs |
| `data/generation-rescore.json` | recorded re-judging tally |
| `data/t3-live-verdicts.json` | 9 in-T3 verdicts |
| `data/catalog-prompt.txt` | the exact catalog instructions sent with every openui request |
| `data/summary.json` | derived; regenerate with `python3 scripts/analyze.py` |
| `scripts/*.ts`, `scripts/cases.mjs` | harness, cases and oracle as run (paths in fixtures anonymized) |
