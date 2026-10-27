---
title: "the proof passed. the work was still stranded."
subtitle: "three statecharts, then a replay of the things our agents actually left behind."
study: fsm-integration-v0
status: evidence-pending
author: "zer0 research"
date: "october 21, 2026"
mock_data: false
toc:
  - id: question
    label: rules that can refuse a transition
  - id: proof
    label: break the laws on purpose
  - id: replay
    label: replay the incidents
  - id: workers
    label: interrupted is not abandoned
  - id: integration
    label: count the unknowns too
  - id: view
    label: the diagram runs the model
  - id: limits
    label: what this does not prove
  - id: sources
    label: sources
---

<div class="lede">
we had rules about exact-head tests, owner acceptance and finishing interrupted work. the useful question was whether those rules could reject a transition, then explain the work that had already gone wrong.
</div>

<div class="hero-rule"></div>

## rules that can refuse a transition {#question}

we split the problem into work items, workers and integration ownership. the work item follows a change toward acceptance. the worker follows a delegated process toward completion or an explicit decision. integration follows what actually reaches the designated branch and the running service.[1][2][3]

```text
statechart -> laws -> proof -> finite parity -> incident replay
```

the arrows matter. a proof about the model is not proof that the history was mapped correctly. a completed worker is not an integrated change. a matching source checkout is not an attested deployment.[1][2][3]

the publication branches remain drafts. the tables below are archived, source-reported proof, parity and replay results. we did not rerun the toolchain for this article.

## break the laws on purpose {#proof}

we kept the positive check, the sabotage and the implementation comparison separate.[1][2][3]

| machine | archived proof scope | rejected semantic mutants | measured python / bend agreement |
|---|---|---:|---|
| work item | 15 claims under l1–l7 | 10/10 | 400 tapes, 5,077 events, all 12 phases [1] |
| worker supervision | 19 claims under w1–w6 | 17/17 | 400 worker tapes, 3,370 events, all 9 phases; 100 lease and 100 device tapes [2] |
| integration owner | i1–i5 safety and deadline-monitor laws | 11/11 | 625 tapes, 16,225 prefix comparisons, 20 deadline and 300 lease cases [3] |

for integration, the semantic mutants compiled on their own and then failed the laws. a separate test-only merge bypass also broke parity. that is more useful than a proof which stays green after removing the behavior it was supposed to protect.[3]

still a bounded result. the kernel checks bend's emitted book. the studies explicitly retain `source_semantics_attested=false`. finite python agreement does not turn into a source-equivalence theorem.[1][2][3]

## replay the incidents {#replay}

we then asked the checker to read the historical evidence. not to fix it. not to invent missing acceptance.[1]

| work-item finding | archived count |
|---|---:|
| integrations without a passing head receipt at merge time | 39 [1][4] |
| of those, merges before the tests finished | 7 [1] |
| default-branch merges without recorded owner acceptance | 6 [1][4] |
| interrupted workers dropped past the limit | 13 [1][4] |
| stranded-integration candidates | 32 [1][4] |

one static service was 31 commits behind its integrated line, which was local-only. another service was diverged and had 27 uncommitted files. those are concrete reasons not to infer deployment health from “the work is done.”[1][4]

“without recorded acceptance” does not tell us who pressed merge. agents shared the owner's github identity. the public replay leaves five self-integration findings indeterminate, rather than identifying five proven acts of self-approval.[1][4]

the archive also has a small bookkeeping disagreement: the readme says 174 items; the public artifact lists 111 prs, 5 services and 59 workers. those categories sum to 175. we leave the total unresolved instead of choosing the more convenient denominator.[1][4]

## interrupted is not abandoned {#workers}

supervision widened the replay. it found 26 overdue workers. all 13 dropped workers from the first loop were in that set. the proposed disposition for those original workers was 10 resume, 2 already integrated and 1 abandon. these were recommendations, not actions we claim to have performed.[2][5]

there were also 419 writes inside another session's lease across 19 worktrees, one orphan background process, seven phone installs without the lock and eleven phone inputs without a foreground check.[2][5]

the waiting data need more care. 118 of 333 desktop lock jobs were estimated to have waited, about 21.5 hours in total. that is a lower-bound reconstruction from disjoint lock holds, not a directly observed end-to-end queue clock.[2][5]

the readme's “36 fleet jobs, no queue wait” is too strong as an end-to-end comparison. the public artifact says admission retry time is outside the fleet run logs and records six busy retries. we cannot turn an unmeasured queue into a zero.[2][5]

## count the unknowns too {#integration}

the later integration snapshot contains 90 open drafts across eight repositories and six service/build targets. its 79 findings include violations and missing evidence. they are not 79 proven failures.[3][6]

| finding | archived count |
|---|---:|
| definitely outside the designated integration branch after 24 hours | 21 [3][6] |
| deadline unverifiable because the canonical branch is not designated | 27 [3][6] |
| stale recorded child bases | 5 [3][6] |
| conflicting drafts | 6 [3][6] |
| repositories without a supplied integration-owner lease record | 8 [3][6] |
| unattested runtime/build source revisions | 6 [3][6] |

one source checkout differed from its fresh remote integration head. that did not establish the source revision of the installed phone build. all six runtime/build revisions remained unattested.[3][6]

missing lease evidence is not proof that no informal owner existed. a deadline monitor is not a fairness theorem that someone will eventually do the work. the snapshot had no eligible owner-acceptance item, so the immediate owner-decision batch stayed empty.[3]

## the diagram runs the model {#view}

the browser view uses the compiled bend transitions. it does not maintain another hand-written transition machine. the current producer receipt covers 17 tapes, 96 steps and 73 display edges, with zero missing or extra mermaid edges.[7]

all five new snapshot-probe tapes completed at 412×915 and matched each receipt-bound prefix. their initial states came from the snapshot; every later action was marked what-if. those acceptance and merge animations are not historical events.[3][7]

the bounded build and browser proof passed. the full upstream `check:fast` did not run because the clean remote shipment lacked vitest. we do not replace that blocker with a general frontend qualification claim.[3][7]

## what this does not prove {#limits}

the proof does not authenticate github identities, service telemetry or owner consent. the replay mapping uses heuristic heartbeat, successor, test-name and worktree evidence. github reruns can also make the latest retained check look later than the original merge.[1][2]

we have not shown that these drafts prevent the same incidents in production. we have not shown that every live action is intercepted. we have not proved source/compiler equivalence or liveness.[1][2][3]

a browser replay is not authorization to deploy, merge or touch a phone.[7]

the useful result is narrower: the rules have executable failure cases, and the replay can separate a violation, a candidate and a missing fact. that is enough to make the next decision less vague.

## sources {#sources}

[1] https://github.com/kvnloo/z0evals/blob/d8a9658dec11e08425ebdc204b75ab3acb526a43/studies/fsm-work-item-v0/README.md — studies/fsm-work-item-v0/README.md
[2] https://github.com/kvnloo/z0evals/blob/c621fbbb02300bef45382d01306641eaec5cf3da/studies/fsm-worker-supervision-v0/README.md — studies/fsm-worker-supervision-v0/README.md
[3] https://github.com/kvnloo/z0evals/blob/760725750491a9b01fc40f49430af7cb5f299de0/studies/fsm-integration-v0/README.md — studies/fsm-integration-v0/README.md
[4] https://github.com/kvnloo/z0evals/blob/d8a9658dec11e08425ebdc204b75ab3acb526a43/studies/fsm-work-item-v0/data/replay-public-20261021.json — studies/fsm-work-item-v0/data/replay-public-20261021.json
[5] https://github.com/kvnloo/z0evals/blob/c621fbbb02300bef45382d01306641eaec5cf3da/studies/fsm-worker-supervision-v0/data/supervise-public-20261021.json — studies/fsm-worker-supervision-v0/data/supervise-public-20261021.json
[6] https://github.com/kvnloo/z0evals/blob/760725750491a9b01fc40f49430af7cb5f299de0/studies/fsm-integration-v0/data/integration-public-20261021.json — studies/fsm-integration-v0/data/integration-public-20261021.json
[7] https://github.com/kvnloo/.files/blob/0cd01e271a913a964f6684c7b8d7340f67f0174b/docs/spec-diagram/fsm/README.md — docs/spec-diagram/fsm/README.md
