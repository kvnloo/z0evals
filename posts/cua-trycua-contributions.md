---
title: "what we have sent to cua, and what is still only a fixture"
subtitle: "a living record of our trycua/cua work: merged fixes, open rfcs, and experiments that have not earned a claim yet."
study: cua-trycua
status: living
author: "zer0 research"
date: "october 26, 2026"
dek: "a living record of our trycua/cua work: merged fixes, open rfcs, and experiments that have not earned a claim yet."
area: speed-ux
published: 2026-10-26
kind: living
series: cua
featured: true
mock_data: false
toc:
  - id: now
    label: where things stand
  - id: setup
    label: how we work in someone else's repo
  - id: start
    label: how it started
  - id: progress
    label: what changed along the way
  - id: pomerado
    label: "this week, pomerado on real machines"
  - id: h2h
    label: "head-to-head: cua vs opencli"
  - id: credit
    label: credit and collaboration
  - id: limits
    label: what this does not claim
  - id: sources
    label: sources
---

<div class="lede">
this page tracks everything we have contributed to cua, the open-source computer-use stack from trycua. the table below refreshes from github and our run receipts each time the site builds. the sections after it explain how the work is set up and how it got here.
</div>

<div class="hero-rule"></div>

## where things stand {#now}

<!-- generated:cua-status -->
| where things stand | |
|---|---:|
| upstream prs merged into trycua/cua | 7 |
| upstream prs open for review | 4 |
| rfcs (upstream + downstream) | 4 (3 open) |
| downstream experiments tracked | 6 |
| remote experiment runs | 9 (6 pass, 1 partial, 1 blocked), latest 2026-10-27 |
| remote compute so far | 17.2 min, $0.0099 |

**latest runs**

| run | date | class | result | what it showed |
|---|---|---|---|---|
| cua161-h2h-valid | 2026-10-27 | real | pass | CUA (cua-driver 0.38.0, pinned by sha256) vs opencli 2.0.2, 8 cells x n=80, ABBA/BAAB, 640/640 oracle-verified, 0 unsafe effects. Median ms CUA vs opencli: warm read 50.5 vs 778.0; warm write 261.5 vs 918.4; cold read 731.8 vs 1350.3; cold write 2216.6 vs 1528.3. Synthetic loopback fixture only; Pomerado NOT_RUN (no completed mint). |
| cua161-probe | 2026-10-26 | setup | pass | root cause of the driver refusal: the Boat image ships /opt and /opt/google owned by user; Chrome 151 itself is root-owned; DISPLAY=:0 with a running X server |
| cua161-b2 | 2026-10-26 | feasibility | pass | pomerado-mcp mint starts in isolation with no API key; MCP 2025-06-18 handshake lists 4 tools: get_job, provide_input, cancel_job, mint |
| cua161-b | 2026-10-26 | feasibility | pass | Node v24.21.0 checksum-verified; pomerado 0.4.0-canary.399, MIT, Pomerado AI, Inc.; engines node >=24.21 <25; serve needs no model credentials |
| cua161-ac-readonly | 2026-10-26 | invalid | invalid | INVALID, numbers withdrawn; superseded by cua161-h2h-valid. Stale unpinned cua-driver 0.23.2, CUA cold-started every attempt while opencli reused a warm Chrome, read-only tasks only. |
| cua161-a4 | 2026-10-26 | setup | partial | after chown root:root /opt /opt/google: verify_setup wrote summary.json and the mock baseline logged 3 events, but with the image's preinstalled cua-driver v0.23.2 (latest v0.38.0), not this branch's driver |
| cua161-a3 | 2026-10-26 | fixture_browser_only | pass | real Chromium 151 fixture smoke 40/40 PASSED (5 repeats x 8 cases incl. duplicate-target, renamed-target, visual-only and origin-escape refusals, wrong input refuted, uncertain commit reconciled without repeat); no CUA or Pomerado trial |
| cua161-a2 | 2026-10-26 | setup | blocked | cua-driver refused browser_prepare: browser_route_unavailable (no root-owned, non-writable system Chromium); smoke probe needed playwright 1.57 |

**open review and experiments**

| item | role | state | credit |
|---|---|---|---|
| [trycua/cua#4316](https://github.com/trycua/cua/pull/4316) perf(cua-driver): add guarded completion to jev-use | review | open | kvnloo |
| [trycua/cua#4734](https://github.com/trycua/cua/pull/4734) feat(jev-use): stop bounded native no-progress loops | review | open | kvnloo |
| [trycua/cua#5374](https://github.com/trycua/cua/pull/5374) fix(sandbox): honor shell timeout on Android ADB transport | review | open | kvnloo |
| [trycua/cua#5420](https://github.com/trycua/cua/pull/5420) fix(cua-sdk): keep HTTP MCP reply waits cancellable (code-only) | review | open | kvnloo |
| [kvnloo/cua#10](https://github.com/kvnloo/cua/issues/10) Whole-task accounting benchmark across current surviving routes | experiment | open | kvnloo |
| [kvnloo/cua#107](https://github.com/kvnloo/cua/issues/107) Live state mirror vs scoped reads and checked execution | experiment | open | kvnloo |
| [kvnloo/cua#161](https://github.com/kvnloo/cua/issues/161) Pomerado MCP as an opt-in website procedure cache for CUA | experiment | open | kvnloo; Pomerado AI, Inc. (MIT) retains credit for Pomerado |
| [kvnloo/cua#110](https://github.com/kvnloo/cua/pull/110) reduced-motion browser policy (draft) | experiment | open | kvnloo |
| [kvnloo/cua#166](https://github.com/kvnloo/cua/pull/166) valid warm/cold read/write CUA vs opencli head-to-head (draft) | experiment | open | kvnloo; opencli is jackwener/opencli |
| [kvnloo/cua#162](https://github.com/kvnloo/cua/pull/162) Pomerado × CUA pre-registration and fixture evidence (draft) | experiment | open | kvnloo |
| [trycua/cua#5338](https://github.com/trycua/cua/pull/5338) fix(cua-driver): verify foreground Document text insertion (salvage #4836) | collaboration | open | salvage by injaneity of the original #4836 by wszkxlllll; we review, no competing patch |

<p class="small">states refresh from github at each site build. runs are counted from studies/cua-trycua/receipts.jsonl.</p><!-- /generated:cua-status -->

the short version: seven fixes and tests are merged upstream. four more prs are waiting for review. the newest experiment, pomerado as an opt-in procedure tool, now runs on real linux machines, but only its fixture and setup checks have run. pomerado has no timing result yet, and its cells stay marked not run. a separate head-to-head between the cua driver and opencli is now valid, after the first attempt was withdrawn. it is below.[1][2][14]

## how we work in someone else's repo {#setup}

cua belongs to trycua. we work in a downstream fork, kvnloo/cua, and treat upstream as someone else's house.[3]

- **one queue.** fork issue #74 is the only promotion queue. every candidate waits there until it has evidence, and older dags and matrices feed into it rather than compete with it.[4]
- **exact heads.** a result counts only for the commit it ran on. a changed head needs a fresh check, not an inherited pass.[4]
- **downstream first.** experiments, drafts and receipts live in the fork. an upstream pr or issue needs a tested result and an explicit human decision.[4]
- **no competing patches.** when someone already owns a fix, we review theirs instead of opening our own.[4]
- **refusals are results.** failed, refuted and abstained attempts are kept, not trimmed.[4]

work runs through the zer0 oss factory: agents draft, verify and post receipts, and every upstream-facing action needs the owner's approval.[5]

## how it started {#start}

the work began with an rfc, "script-speed computer use for cua": fewer model decisions per task, bounded execution, and observation that knows which revision of the page it saw.[6] upstream discussed it and it is now closed as decided.

the first upstream changes were small and testable. between september 23 and october 2, seven of our prs were merged by f-trycua:[7]

| pr | change |
|---|---|
| #4049 | auto-link skills for pi |
| #4051 | refuse ambiguous macos browser applescript |
| #4052 | make jev-use timing phase-correct |
| #4164 | skip the accessibility walk for verify_state screenshot evidence |
| #4218 | reopen checkpoint locators returned by save (the bug from our issue #4007) |
| #4317 | prove jev-use session authority isolation |
| #4318 | constrain element_token tool schemas |

## what changed along the way {#progress}

the second research round turned into fork rfcs instead of new upstream ones: a semantic control plane (#93), whole-task accounting (#10), and state mirroring versus scoped reads (#107).[8][9][10]

two ideas were tested and then held back:

- **reduced motion.** we proposed an opt-in reduced-motion policy for driver-owned tabs, upstream as #4557 and downstream as #109. a 60-trial direct-cdp a/b found a paired median change of −0.69 ms, 95% ci [−1.99, +0.59]. that is no demonstrated latency gain, so cdp-only experiments stopped and #110 is on hold until a driver-owned semantic test exists.[11][4]
- **bend on the action path.** the cuda bend guard agreed with the python oracle on all 4,096 cases, but a plain cpu table did the same work faster. we wrote that up separately.[12]

## this week, pomerado on real machines {#pomerado}

pomerado mints a site-specific mcp tool from a described website task. once minted, the tool runs without model calls. the question in #161 is whether a cua caller can use such a tool for repeat website tasks without losing correctness, authorization or a safe fallback.[2]

the earlier attempt stalled in a chat container that blocked localhost in chrome. we moved it to boat.dev linux machines: ubuntu 24.04, 4 vcpu, deleted after each run. seven runs have used about 4.4 minutes of compute.[1]

- the experiment's own tests passed 56/56.
- a real chromium 151 probe against the fixture passed 40/40 checks. it refused ambiguous targets, renamed targets and an origin escape, and it reconciled an uncertain commit without repeating it.
- pomerado's mcp server started in isolation with no api key and exposed four tools. mint asks the user before choosing write.
- the cua driver at first refused to start the browser. the image ships /opt and /opt/google owned by the default user, and the driver correctly treats a user-owned ancestor as an unsafe browser path. making them root-owned let the preflight run. the run then used the image's preinstalled driver, v0.23.2, not the branch build, so it does not count as a driver result.

next is to pin the branch's own driver build on the machine. after that, the read-only a/b blocks can run once a mint budget is approved.[2]

## head-to-head: cua vs opencli {#h2h}

our first cua vs opencli run, on 2026-10-26, is **invalid**, and we withdrew its numbers. it had three problems. the driver was a stale, unpinned 0.23.2. cua started cold on every attempt while opencli reused a warm browser. it ran read-only tasks only.[2]

the rerun fixes all three problems. it pins cua-driver 0.38.0 and opencli 2.0.2 by digest. both tools run warm and cold, and both run a read task and a write task. ten fresh boat.dev machines (2 vcpu, 4 gb) each ran one shard. ABBA/BAAB blocks interleave the two tools on the same machine. that gives 80 attempts per cell and 640 timed attempts. an independent reset and oracle checked every attempt.[14]

| mode | task | cua median / p90 | opencli median / p90 |
|---|---|---|---|
| warm | read | 50.5 / 68.7 ms | 778.0 / 866.3 ms |
| warm | write | 261.5 / 304.5 ms | 918.4 / 1001.3 ms |
| cold | read | 731.8 / 1068.3 ms | 1350.3 / 1733.3 ms |
| cold | write | 2216.6 / 2775.0 ms | 1528.3 / 1910.6 ms |

- every timed attempt was verified, 640 of 640. there were no unsafe effects: no unauthorized commits, duplicate commits, wrong targets or uncertain effects.
- cua was faster warm, for both read and write, and cold for read. opencli was faster cold for write, by a paired median of 660 ms.
- this is one synthetic loopback page with one read task and one write task, not a real-site benchmark. the warm routes also differ in shape: cua keeps one driver process alive, while opencli starts one cli process per call.
- pomerado was not run. no full mint has completed, and the mint credential may not go to a public test machine.

## credit and collaboration {#credit}

- **trycua and f-trycua** reviewed and merged our upstream changes.[7]
- **wszkxlllll** wrote the original foreground text-insertion fix (#4836). **injaneity** carries it forward as #5338. we review that pr and do not compete with it.[13]
- **pomerado ai, inc.** builds pomerado under the mit license. our experiment only calls it from outside cua; it is never bundled into the driver.[2]
- **boat.dev** provides the linux machines the current runs use.

## what this does not claim {#limits}

- no speedup from pomerado. no mint has run and no a/b blocks exist.
- the 2026-10-26 cua vs opencli numbers are invalid and withdrawn. the 2026-10-27 head-to-head covers one synthetic fixture page only.
- the 40/40 browser probe exercises the fixture only. it is not a cua or pomerado trial.
- source and unit proofs are not desktop end-to-end proofs, and local runs are not hosted ci.
- open upstream prs are proposals until a maintainer decides.

## sources {#sources}

[1] https://github.com/kvnloo/z0evals/blob/main/studies/cua-trycua/receipts.jsonl — studies/cua-trycua/receipts.jsonl
[2] https://github.com/kvnloo/cua/issues/161 — kvnloo/cua#161 pomerado experiment
[3] https://github.com/trycua/cua — trycua/cua
[4] https://github.com/kvnloo/cua/issues/74 — kvnloo/cua#74 promotion queue
[5] https://github.com/kvnloo/oss-factory — zer0 oss factory
[6] https://github.com/trycua/cua/issues/3963 — rfc: script-speed computer use for cua
[7] https://github.com/trycua/cua/pulls?q=is%3Apr+author%3Akvnloo+is%3Amerged — merged upstream prs
[8] https://github.com/kvnloo/cua/issues/93 — semantic control plane rfc
[9] https://github.com/kvnloo/cua/issues/10 — whole-task accounting
[10] https://github.com/kvnloo/cua/issues/107 — state mirror vs scoped reads
[11] https://github.com/trycua/cua/issues/4557 — rfc: opt-in reduced-motion policy
[12] https://github.com/kvnloo/z0evals/blob/main/posts/cua-bend-hobbylm-v0.md — the guard passed. the gpu did not help.
[13] https://github.com/trycua/cua/pull/5338 — salvage of #4836
[14] https://github.com/kvnloo/cua/pull/166 — valid warm/cold read/write cua vs opencli head-to-head, raw per-attempt data
