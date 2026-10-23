---
title: "the guard passed. the gpu did not help."
subtitle: "bend agreed with the oracle. the best cpu algorithm made the large-batch chart beside the point."
study: cua-bend-action-laws-v0
status: evidence-pending
author: "zer0 research"
date: "october 23, 2026"
mock_data: false
toc:
  - id: question
    label: what are we trying to accelerate?
  - id: guard
    label: agreement is not speed
  - id: ablation
    label: the repeated work disappears
  - id: hobbylm
    label: the slower decision model
  - id: decision
    label: what we keep
  - id: limits
    label: what this does not prove
  - id: sources
    label: sources
---

<div class="lede">
we wanted to know whether bend belonged in the computer-use action path. the finite guard worked. the speed argument did not survive the cpu control.
</div>

<div class="hero-rule"></div>

## what are we trying to accelerate? {#question}

the public cua archive contains separate experiments: cuda bend action-law checks in pr #157, and a hobbylm semantic action loop in pr #158. neither is a production rollout.[8][9]

we report the committed measurements here. the bend readme points to an owner-held abab report, but the public artifacts we read do not provide a complete abab sequence. we are not reconstructing one, and we are not relabeling the hobbylm comparison as a bend treatment.[8][9]

## agreement is not speed {#guard}

the guard projection has sixteen action ids and 256 flag combinations: 4,096 finite inputs. bend cuda, the independent semantic python oracle and numpy agreed on all of them. the split was 236 allow and 3,860 deny.[8]

that is useful conformance. it is not yet a reason to call a gpu for each action.[8]

| measurement | archived result |
|---|---:|
| existing recipe-local python guard | approximately 4.8–5.0 microseconds |
| full-vector gpu job, including serialization | 103.8 ms |
| python generation of the equivalent complete guard table | 1.09 ms |
| projected-table lookup in python | 53.8 ns |
| handwritten bit-guard comparison | 136.3 ns |

these are different operations and timing scopes, not interchangeable per-action latencies. the table lookup beat the handwritten guard in that microbenchmark. python could generate the same table without bend, so the lookup result is not a bend-specific gain.[8]

we also tried robust filtering across four candidate actions and four possible states. it resolved 340/340 uniquely resolvable groups versus 104/340 for the first-candidate, single-state baseline. python made exactly the same decisions. the gain belongs to the finite decision rule, not to cuda.[8]

every kernel arm made zero model calls. there is no measured model-call saving to attach to this result.[8]

## the repeated work disappears {#ablation}

the large batches looked much better for the gpu. then the ablation asked what work was actually distinct.[8]

the model used only the low twelve input bits. every large batch repeated the same 4,096-case period. python could build the complete table once and fold the repeated checksum by period count in about 0.2 microseconds. the giant raw throughput ratios did not accelerate the actual finite verification problem.[8]

the same problem appears in a proposed deeper search. ten action categories at depth eight give 10^8 nominal paths. with a 256-state abstraction, dynamic programming needs at most 20,480 transition checks. enumerating every repeated path would manufacture gpu work rather than establish a useful crossover.[8]

so the decision is to leave cuda bend out of cua's per-action hot path on this evidence. a genuinely distinct, path-dependent workload could change that decision. this experiment did not supply one.[8]

## the slower decision model {#hobbylm}

the separate hobbylm experiment asks a different question: does the local model choose useful actions? its matched local controls used semantic text observations, the same owned desktop, initial states, capabilities, seeds and action allowlist. the model did not receive screenshots.[9]

| arm | supported success | decisions | model p50 / p95 | controller wall |
|---|---:|---:|---:|---:|
| hobbylm fp32 | 22/31 (71.0%) | 58 | 1.194 / 3.464 s | 275.67 s |
| qwen2.5-0.5b fp32 | 9/31 (29.0%) | 186 | 0.247 / 0.705 s | 340.20 s |

both local arms ran on the same gpu in fp32. the larger model's decisions were slower, but the archived controller run used fewer of them, finished sooner and completed more supported tasks. that is a descriptive matched comparison, not evidence that a bend guard caused the difference.[9]

the strong subscription control was unavailable: all 31 attempts failed before generation. that is an authentication/routing failure, not a model scoring zero. an exploratory richer-state prompt also produced only 1/31 and remains separate from the primary matrix.[9]

these failures matter. we cannot compare a working local arm to a nonexistent strong-model answer, and we cannot hide the prompt format that failed.[9]

## what we keep {#decision}

we keep the finite oracle and the negative runtime decision. robust filtering can be expressed on the cpu. the lookup table does not require a gpu. the semantic model comparison remains its own study.[8][9]

the next bend speed experiment needs a faithful transition model and the best cpu algorithm before a large gpu batch. distinct reachable states matter more than nominal path count. prediction, ingress, queue and response cost belong in the eventual comparison too.[8]

## what this does not prove {#limits}

finite guard agreement is not a universal bendtt proof, compiler equivalence, observation authenticity or real gui success. the guard excludes action-argument parsing, intent classification and the truth of the observed state.[8]

the gpu timing came from a shared host. the internal clock had 1 ms resolution, background load remained present, and a proposed finer timing run was refused before launch because io pressure exceeded its admission limit. no refined result replaces it.[8]

hobbylm's semantic command adapter is not screenshot-driven computer use. the adapted tasks and pinned osworld cases do not establish an official osworld aggregate or broad gui competence. unsupported tasks remain coverage failures, and the full unit/hosted qualification was not established by the archived matrix.[9]

we have a useful negative result and a bounded model comparison. we do not have a production speedup, a general computer-use benchmark win or a public reconstruction of the whole abab program.

## sources {#sources}

[8] https://github.com/kvnloo/cua/blob/c93ecbcb5087f435ae9dd733fa277c5ebabb2296/research/bend_action_laws/README.md — research/bend_action_laws/README.md
[9] https://github.com/kvnloo/cua/blob/0d135c06e75832446dc732e42227b9ebe33ed757/libs/python/agent/examples/hobbylm_eval/README.md — libs/python/agent/examples/hobbylm_eval/README.md
