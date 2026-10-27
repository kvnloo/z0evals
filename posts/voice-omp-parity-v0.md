---
title: "voice parity failed. the fixes still mattered."
subtitle: "we scored the audio, kept the failures, and did not call a partial rerun a pass."
study: voice-omp-parity-v0
status: evidence-local
author: "zer0 research"
date: "october 20, 2026"
mock_data: false
toc:
  - id: method
    label: what we measured
  - id: results
    label: round 2 still failed
  - id: followup
    label: the narrow fix was narrow
  - id: limits
    label: what this does not prove
---

## what we measured {#method}

we compared output audio, not whether the transcript looked responsive. the [protocol](https://github.com/kvnloo/z0evals/blob/e3c6c2c8cdc2f3b73be8bc3a1a8b9c8e98c07d3c/studies/voice-omp-parity-v0/README.md) defines acoustic windows and non-inferiority gates before the scored baseline. the arms differ in model, voice, transport and delegation. this compares products, not a single changed component.

## round 2 still failed {#results}

the [round 2 scoreboard](https://github.com/kvnloo/z0evals/blob/e3c6c2c8cdc2f3b73be8bc3a1a8b9c8e98c07d3c/studies/voice-omp-parity-v0/results/voice-parity-20261020-r2.md) keeps the earlier omp control rather than rerunning it. direct-turn end-of-speech to first-audible:

| arm | p50 ms | p95 ms |
|---|---:|---:|
| omp-live | 1,112 | 1,539 |
| z0live-bidi | 1,265 | 1,960 |
| z0live-realtime | 1,815 | 2,978 |

both candidates were `FAIL`. realtime missed the direct-response latency gates. bidi also missed interruption gates. all arms got the repository answer correct 5/5 in this round; that did not make the latency failures disappear.

barge-in to silence p50 / p95 was 974 / 1,220 ms for omp, 1,190 / 1,392 ms for bidi and 237 / 239 ms for realtime. the control itself misses the absolute interruption-tail gate. it is not ground truth for acceptable experience.

## the narrow fix was narrow {#followup}

the [later bidi subset](https://github.com/kvnloo/z0evals/blob/e3c6c2c8cdc2f3b73be8bc3a1a8b9c8e98c07d3c/studies/voice-omp-parity-v0/results/voice-parity-20261020-r2c.md) covers only barge-in and rapid follow-up. missing audible replies went to 0/15, and bidi barge p50 / p95 was 885 / 1,167 ms. there was still 1 stale resume. the scoreboard remains `FAIL`, with delegation gates undetermined. its absent repository scenarios are not evidence of incorrect answers; they were not run.

we can credit the buffered-tail fix without promoting the whole voice stack.

## what this does not prove {#limits}

the [protocol](https://github.com/kvnloo/z0evals/blob/e3c6c2c8cdc2f3b73be8bc3a1a8b9c8e98c07d3c/studies/voice-omp-parity-v0/README.md) uses a headless client and synthetic speech, not a physical phone microphone and speaker. omp is metered before speaker buffering; chromium after its jitter buffer. 19 omp turns were excluded for harness stalls in the [round 2 scoreboard](https://github.com/kvnloo/z0evals/blob/e3c6c2c8cdc2f3b73be8bc3a1a8b9c8e98c07d3c/studies/voice-omp-parity-v0/results/voice-parity-20261020-r2.md); the included-stall alternative is also reported there. later blocks are not a fresh matched control, and the host was loaded. no acoustic-naturalness or mobile-background claim follows. raw audio and transcripts stay out of this draft.

