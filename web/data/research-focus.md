## where our attention is going, and why {#focus}

as of 2026-10-23. this is a ranked working agenda, not a claim that the loops are running. a merged library, a registered client and a verified behavior are different states. the public memory contract keeps those distinctions explicit. [continuity plan](https://github.com/kvnloo/z0intelligence/issues/22)

### the metric and the rule

our north-star metric is **context re-explanations per day**. count the occasions when the user restates context an agent should have recalled. do not substitute search hits for this number. use, ignore and restatement need explicit witnesses. the daily count is not yet reported in the sources reviewed here. [outcome contract](https://github.com/kvnloo/z0intelligence/pull/194#issuecomment-6375090545)

our rule for each system is a closed self-improvement loop: **receipt → replay → gated promotion → rollback**. capture what happened. replay real failures against a frozen baseline. require held-out evidence on the exact candidate revision and separate owner acceptance. keep the previous policy available when validity breaks. these are required boundaries, not evidence that every lane already has them. [compilation and deoptimization](https://github.com/kvnloo/z0intelligence/issues/56) · [protected-search argument](https://kvnloo.github.io/z0intelligence/bend-autoresearch/)

### 1. useful continuity before more memory machinery

**why now.** the memory foundation moved. freshness, capture and the read-only facade merged into preview on october 23. the final facade integration reports 291 passing tests. the last synthesis comment still describes drafts; that status is now historical. none of these merges proves that a fresh client used a real correction. [merged facade](https://github.com/kvnloo/z0intelligence/pull/194) · [capture](https://github.com/kvnloo/z0intelligence/pull/197) · [freshness](https://github.com/kvnloo/z0intelligence/pull/198)

**next experiment.** qualify the deployed read path with explicit grants. then witness one authorized decision and later correction in a fresh second client. compare memory enabled and disabled with the same model, prompt and budget. preserve source citations, the actual model input and an independent answer check. the frozen agent-policy-to-user-correction variant must stay distinct from the still-blocked pure user-to-user pair. [current synthesis](https://github.com/kvnloo/z0intelligence/issues/22#issuecomment-6358732148)

**what would change our mind.** if ordinary scoped source retrieval gives the same corrected behavior with fewer waits and less maintenance, keep that simpler control. a scope leak, stale required source or missing input witness blocks promotion. semantic compaction is optional. [research synthesis](https://github.com/kvnloo/z0intelligence/issues/195#issuecomment-6356363333)

### 2. compaction economics, including the retries

**why now.** the frozen internal replay qualified terra at 4/5 recall against sol at 5/5. terra used 8.35% more input-plus-output tokens but 29.05% fewer uncached input tokens. the luna runs exceeded the byte target on roughly 84% of reported responses. a cheaper-family label did not mean fewer calls or fewer tokens. these are internal aggregate measurements; the public link exposes the instrumentation, not the benchmark corpus or report. [usage ledger](https://github.com/kvnloo/uniichat/pull/5)

**next experiment.** freeze another authorized cohort and recall key. compare the existing retry policy with a bounded size-control candidate. count maintenance calls, cached and uncached input, output, failed attempts and recall. keep missing usage unknown. inspect the actual call context rather than reconstructing it from display history. this is proposed work, not a restarted held optchat trial. [ledger contract](https://github.com/kvnloo/uniichat/pull/5) · [call-context inspector](https://github.com/kvnloo/uniichat/pull/4#issuecomment-6357187131) · [trial hold](https://github.com/kvnloo/z0intelligence/issues/120#issuecomment-6355828240)

**what would change our mind.** a repeated recall loss, more stale corrections or worse full-system cost would favor the control. uncached-token savings alone cannot establish subscription-quota or dollar savings when those weights are unknown. [instrumentation and private-replay boundary](https://github.com/kvnloo/uniichat/pull/5)

### 3. capacity for the experiments, not another scheduler

**why now.** the steward dry-run turns 624 job logs into 16 findings, but most historical queue, runtime and peak-memory fields remain missing. the earlier 557-job research snapshot has 13 unclassified observations. a later build stall was in controller storage before worker admission. these are evidence and infrastructure problems before they are learned-placement problems. [steward](https://github.com/kvnloo/.files/pull/46) · [earlier coverage gap](https://github.com/kvnloo/z0intelligence/issues/131#issuecomment-6356843385) · [stall receipt](https://github.com/kvnloo/.files/pull/41#issuecomment-6372080224)

**next experiment.** add source-bound gate-stage receipts to the existing execution path. distinguish pre-start holds from started or uncertain attempts. qualify one hermetic cpu evaluation for a reversible kueue canary only after physical health and task/image provenance pass. the existing placement smoke only prints its node; it cannot stand in for an evaluation. phones remain host-lane workers. [canary audit and blockers](https://github.com/kvnloo/z0intelligence/issues/131#issuecomment-6375347339)

**what would change our mind.** if queueing, image work or control-plane i/o raises time to independently verified output, retain the host path. stop on duplicate execution, unsafe admission or unknown effects. do not scale optimization on top of unqualified capacity. [hybrid migration decision](https://github.com/kvnloo/z0intelligence/issues/131#issuecomment-6356821555)

### 4. give autoresearch a real reward signal

**why now.** the bend story makes a useful boundary executable: a law pass is not owner acceptance. it also states the current limit plainly. the factory autoresearch replay mutates context policy against a deterministic simulated cost model. it does not rerun agent turns, train weights or establish learning gains. [laws-to-autoresearch artifact](https://kvnloo.github.io/z0intelligence/bend-autoresearch/)

**next experiment.** start with read-only query rewrite or reranking on genuine memory misses. preserve the champion, a held-out cohort and failed attempts. use the existing outcome receipts rather than creating a new reward database. only then compare workflow search and supervised training on the same episode and evaluation budgets. [miss-replay contract](https://github.com/kvnloo/z0intelligence/pull/194#issuecomment-6375090545) · [training proposal](https://github.com/kvnloo/z0intelligence/issues/143) · [search-before-training idea](https://github.com/kvnloo/z0intelligence/issues/143#issuecomment-6139105175)

**what would change our mind.** reject a challenger that wins only on simulated cost, teacher agreement or replayed duplicate credit. require better held-out outcomes after optimization and maintenance cost. on drift, fall back rather than quietly weakening the judge. [credit contract](https://github.com/kvnloo/z0intelligence/issues/54) · [deoptimization contract](https://github.com/kvnloo/z0intelligence/issues/56)

### 5. local routing needs discrimination, not just calibration

**why now.** the observer lead did not confirm on the fresh cohort: brier worsened by 0.0094 and log-loss by 0.052. several models chose the safe argmax on every confirmatory turn. that does not prove their probabilities have no ranking value. the later comment correctly asks for discrimination metrics. [confirmatory result](https://github.com/kvnloo/z0intelligence/issues/14#issuecomment-5961789232) · [threshold caveat](https://github.com/kvnloo/z0intelligence/issues/14#issuecomment-6207743038)

**next experiment.** retain full distributions. compare simple priors, rules and local candidates on grouped fresh work items, with discrimination, calibration, risk/coverage and fallback cost. record cold loads, unavailable backends and timeouts separately. measure actual resource fit before placement. [observer protocol](https://github.com/kvnloo/z0intelligence/issues/14) · [local shadow evidence](https://github.com/kvnloo/z0intelligence/issues/20) · [placement boundary](https://github.com/kvnloo/kerdoios/issues/50)

**what would change our mind.** if a simple prior plus deterministic gates matches held-out value, use it. a fast warm call cannot compensate for a cold-load miss, unmeasured outcome quality or false confidence. no learned score grants execution permission. [selective autonomy](https://github.com/kvnloo/z0intelligence/issues/55)

### 6. keep speculative methods small and falsifiable

**why now.** two ideas pull in different directions. shared-context research separates filesystem coordination from model-state reuse. the byte-distillation triage suggests exact end-of-token targets, but its larger-model advantage is a scaling-law prediction and inference economics remain unresolved. neither is a local win yet. [shared-context experiments](https://github.com/kvnloo/z0intelligence/issues/185) · [byte-distillation triage](https://github.com/kvnloo/z0intelligence/issues/203)

**next experiment.** test path-scoped write ownership and ordinary shared-prefix caching before cross-model cache transfer. for byte distillation, verify probability conversion and real storage/memory cost before training. retain the same legal actions, frozen outcomes and simpler controls. [smallest-first context plan](https://github.com/kvnloo/z0intelligence/issues/185) · [conversion-first byte plan](https://github.com/kvnloo/z0intelligence/issues/203)

**what would change our mind.** stop if leases only move contention, caching changes outputs, exact targets require unavailable logits or byte serving costs erase training savings. defer expensive reproduction until the bounded system comparison justifies it. [context hypotheses](https://github.com/kvnloo/z0intelligence/issues/185) · [byte feasibility gates](https://github.com/kvnloo/z0intelligence/issues/203)

### public artifacts

- [bend laws to autoresearch](https://kvnloo.github.io/z0intelligence/bend-autoresearch/): executable models and a proposed protected search loop. not proof of universal interception or weight learning.
- [k3s fleet handoff](https://kvnloo.github.io/z0intelligence/k3s-fleet/): recorded incidents and questions for infrastructure review. its promotion widget is illustrative. reference agreement is not independent task success.
