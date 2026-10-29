---
title: "prefill won. decode lost. the cache changed an action."
subtitle: "short s25 native bursts, an unqualified cache, and no gold-label result."
study: hobbylm-s25-native-v0
status: evidence-pending
author: "zer0 research"
date: "october 29, 2026"
mock_data: false
toc:
  - id: question
    label: what did we measure?
  - id: backends
    label: backends
  - id: cache
    label: prefix cache
  - id: failed
    label: what failed
  - id: limits
    label: what this does not prove
  - id: sources
    label: sources
---

## what did we measure? {#question}

we tested a local hobbylm action chooser on a galaxy s25 ultra, not an autonomous phone agent. the q4_k_m gguf is 727 mb with 1,088,634,048 parameters. llama.cpp b11759 plus a qkv patch supplied backend bursts at b128/ub128 and a separate resident-server cache probe. these receipts were supplied by the experiment owner, not reproduced or frozen here. the study remains evidence-pending.[1][2]

## backends {#backends}

the table reports the pp128 and tg32 burst means in tokens per second. each of these arms has three samples. the separate cpu-load pp16/tg4 probes are not comparable.[1]

| backend | prefill t/s | decode t/s | spread note |
|---|---:|---:|---|
| cpu4 (mask 33, -t 4) | 283.7 | 124.3 | stddev pp 1.0; tg 1.2 |
| cpu8 (mask ff, -t 8) | 473.8 | 156.2 | pp 562.539, 562.903, 296.028; tg 105.173–186.905 |
| cpu-prime2 (mask c0, -t 2) | 319.2 | 161.9 | stddev pp 1.0; tg 0.4 |
| opencl (gpu) | 595.6 | 60.8 | stddev pp 22.7; tg 0.4 |
| htp0 (npu) | 620.8 | 65.5 | stddev pp 4.8; tg 1.0 |

opencl and htp0 more than doubled cpu4 prefill throughput but decoded at roughly half its rate. the two prime cores alone decoded faster than cpu4 (161.9 versus 124.3 t/s). cpu8 cannot be reliably ranked: one prefill sample fell to 296.028 after two around 562, and decode varied sharply. these are bursts, not a sustained or thermally controlled result.[1]

## prefix cache {#cache}

for an identical 295-token request, cache-off wall time was 616–838 ms versus 44–88 ms with cache on (cache_n 294; prompt_n 1). after a reset, five changed goals took 620–830 ms without caching versus 47–165 ms with it (cache_n 244; prompt_n 48–54). the server reported ready in 1,361 ms.[2]

the wall-time reduction is substantial, but only four of five changed-goal outputs matched. the eggs request returned `TIMER 35` without caching and `UNKNOWN` with it. the requested seven-minute action would be `TIMER 7`; the fp32 reference also said `UNKNOWN`. caching has not passed action-agreement qualification.[2]

## what failed {#failed}

the semantic smoke could not use `llama-completion`: the first attempt exited 127 because the binary was missing; the next exited 134 because the custom template required `--jinja`. a raw `SYSTEM:/USER:/ASSISTANT:` string was sent through the server instead. equivalence with the reference tokenizer and prompt template is unknown.[3]

the frozen 58-decision replay uses the reference model's own trajectory as expected outputs, not independent gold labels. it even expects `UNKNOWN` for the eggs timer and an `EVENT` for a quarter of an hour. the earlier fp32 cua comparison (hobbylm 22/31; qwen2.5-0.5b 9/31) was a separate semantic desktop experiment, not a phone correctness result.[4]

## what this does not prove {#limits}

we have no gold-label action accuracy, sustained throughput, thermal stability, energy result, or end-to-end phone-control result. autonomous phone control remains disabled. the model/build/patch hashes and public copies of the native receipts are not available in this study. source-reported timing is not independent reproduction. freeze the inputs and receipts, verify prompt equivalence, and test action agreement against gold labels before promoting any backend or cache setting.[1][2][3][4]

## sources {#sources}

[1] `hobby-s25-native-matrix-20261029-v2/summary.json` — owner-supplied backend burst receipt; not yet imported or pinned.

[2] `cache-results.json` — owner-supplied prefix-cache receipt; not yet imported or pinned.

[3] `semantic-smoke-final.json` — owner-supplied semantic-smoke receipt; not yet imported or pinned.

[4] https://github.com/kvnloo/cua/pull/158 — prior fp32 hobbylm semantic-text comparison.
