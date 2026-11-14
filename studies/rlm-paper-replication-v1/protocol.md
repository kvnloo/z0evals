# Protocol reference

## Scope and frozen coverage

Collection and strict post-adjudication completed on 2026-11-14: 300 unique executions, 176 collection-valid, 123 strict-valid, and 177 strict-invalid. All 20 task items received five arms and their first three repeats. This completes the bounded subset, not full paper replication. Primary adherence is 28 adherent, 152 nonadherent, 24 unknown, and 96 not applicable; the total valid count includes base and nano reference-deviation outcomes, not only paper-RLM successes. Canonical execution counts are CodeQA 45, semantic 75, S-NIAH 45, and local 135. One operator rebalance used disjoint groups from the same 50 seed executions without protocol changes or best-result selection; invalids were preserved.

The reference is arXiv:2512.24601v1, not the later v3. The task-agnostic method holds `context` in a persistent Python REPL, shows metadata to the root, and permits depth-one ordinary LM subcalls. Hermes adapts the v1 guidance to `rlm_load`, `rlm_exec`, `FINAL`, `FINAL_VAR`, and source character spans. Citation validation checks span integrity, not entailment.

| Family | Materialized task items | Size labels | Score |
|---|---:|---|---|
| S-NIAH | 3 | 4096, mirror's nominal Llama label | RULER case-insensitive substring hit |
| OOLONG | 3 | 1024, original validation `trec_coarse` | Upstream-style graded score |
| OOLONG-Pairs | 2 | 1024, appendix tasks 1 and 11 | Pair-set F1 |
| CodeQA | 3 | 483107, 1043432, 1061947 | Parsed A-D choice |
| Local aggregation | 9 | Three questions each at 32000, 300000, 2000000 nominal | Existing local exact-score rules |

Coverage is 20 task items, not 20 independent corpora. Some questions share the same context. CodeQA uses the first three source rows, not a random sample or a shortest-context sample. Its size is `ceil(context characters / 4)`, not measured source-model or root-model tokens. The local 2M label is nominal. No root tokenizer was measured to validate either label.

Available but blocked sources include three S-NIAH 1M items; larger OOLONG/Pairs at 32768, 131072, and 1048576; BrowseComp-Plus 20 questions over 1000 documents each; and the remaining 47 optional CodeQA rows. Downloads and selection manifests exist. Context materialization is blocked, not the public availability of the data. BrowseComp extraction needs a roughly 484 MiB Parquet page. The MBP Kubernetes route was unavailable and the phone fallback exited 75. No heavy local fallback or completed BrowseComp measurement is claimed.

The separate all-20 Pairs query manifest is preparation coverage, not executed primary coverage. The small task-1 gold set is empty, so that item tests the explicit empty-set convention rather than recovery of nonempty pairs.

## Arms and models

| Arm | Root input | Runtime policy |
|---|---|---|
| `base-truncated` | Context head and question, no system prompt | No tools |
| `rlm-no-subcalls` | File metadata and question | Released Hermes, discovery off, depth zero |
| `released-rlm` | File metadata and question | Released Hermes, discovery off, depth one |
| `fork-rlm` | File metadata and question | Fork Hermes, discovery on, eager `rlm`, depth one |
| `nano-rlm` | File metadata and question | nano ACP reference, depth one |

Primary root is `nvidia/nemotron-3-ultra-550b-a55b`. Child is `nvidia/nemotron-3.5-lightning-30b-a3b`. `qwen/qwen3.8-27b` is an optional second-root lane, not a completed run claim. No OpenAI-family models run. Each root gets separate aggregates and its own 300-row schedule.

Nano has no native child-model override. The existing proxy maps the first ACP session to root and distinct child sessions to the child model. Nano children remain agents, unlike the paper's plain LM subcalls. A retrieval smoke without children does not validate live mixed-model recursion. The plugin worker's independent live two-child probe is separate evidence.

The base primary window is the first 240000 Unicode characters. This is a heuristic head cap, not a measured token window. The normal smoke used 48000 characters. No exact context-window equivalence to the paper is claimed.

## Execution and protocol revision

The legacy pilot stopped after reasoning consumed the output allowance without an answer, and tool rows timed out. Preserve the original pilot rows. Do not relabel them as primary or backfill them as successes.

The revised setting adds `--disable-thinking`. The proxy sends `chat_template_kwargs.enable_thinking=false` uniformly for NIM root, base, and child requests. The revised CLI smoke failed its gate with two valid and three invalid rows. The subsequent library smoke collected five valid arms at score 1.0 under the old collector. This was a process-level smoke, not a validated FINAL/citation protocol pass. Both changes followed pilot inspection. This is a revised protocol, not preregistration and not the paper's reasoning policy.

Primary execution explicitly selects `--hermes-ingress library`, now the upstream default. `bench/hermes_client.py` constructs the actual selected-source `AIAgent`. Plugin discovery, get-tools assembly, tool dispatch, and auxiliary model routing remain Hermes-owned. The adaptation omits per-home CLI gateway startup, not the plugin path under test. Public protocols include `hermes_ingress` and `hermes_client_sha256` in their fingerprint and closed schema. Legacy rows without an ingress field are explicitly classified as CLI. Normal CLI, failed thinking-off CLI, and library-thinking-off smoke cohorts stay separate.

The measured budgets are 100 seconds per execution, 70 seconds per cell, 10 turns, 3072 root output tokens, a 1536 per-call plugin child token cap, 12 child calls, and a 2700-attempt provider cap. Nano differs: its 3072-token agent completion budget is inherited by children, not the plugin's 1536 per-call cap. Child limits are not matched across runtimes. The authoritative values are the typed protocol objects in the generated summary. Plugin, runner, proxy, scorer, and runtime hashes separate snapshots. Different primary protocols for one root cannot be silently pooled.

The upstream runner rotates arm order per task and repeat. It uses fresh homes with only the allowed template and plugin files, isolates the context from evaluator gold, and resumes terminal invalid rows without retry storms. HTTP 429 and 401 allow at most three upstream attempts with exponential backoff, then invalidate the row. Shared durable provider accounting includes retries. The cap is 2700 ledger attempts per provider, leaving headroom below 3000. Four external probe calls need separate parent accounting. Physical HTTP 400 retries and HTTP 429 backoff remain in the evidence; missing failure usage cannot be invented. The optional Qwen Groq route returned HTTP 403 and is blocked, not a reproduced second-root measurement.

Execution completion, collection validity, strict protocol adherence, and correct outcome are different events. The measured collector checked process/provider completion, exposed tools, and REPL activity, but did not require a host-validated FINAL or citations. It could also accept iteration-exhaustion prose and hide an unrecovered child failure behind a later root HTTP 200. Review verified the FINAL gap in real rows and reproduced the child-outcome gap locally. Thus collection `valid` and scores alone are not paper-protocol outcomes. Final primary results use completed strict adjudication instead, while original collection fields remain preserved.

Evaluator-side `bench/audit_results.py` performs post-adjudication on frozen copies. It retains private `collection_*` fields and never promotes collection-invalid rows. Hermes grading uses only a successful host-validated FINAL with citations linked to the corresponding real transcript tool result. Incomplete, budget-exhausted, failed, or interrupted conversations, missing validated finals, and plugin child error/cancel events are invalid. Successful logical plugin calls may retain recovered physical 400/429 attempts. A root 200 is not evidence of child recovery. Nano retains its explicit reference deviation without requiring host FINAL; non-200 child attempts with unknown recovery are conservatively invalid. Base collection outcomes remain unchanged.

The summarizer never implements a second auditor or scorer. `--require-audit` requires `paper-strict-v1` on every primary input row and a typed auditor SHA-256. It uses the adjudicated `valid` and score fields and rejects collection-invalid promotion or contradictory valid audit states. Audited and unaudited primary inputs cannot mix. Without this flag, primary inputs must remain unaudited collection snapshots. The top-level `audit_policy` names the primary policy; historical smoke and pilot remain separately identified collection evidence unless separately adjudicated.

## Dataset revisions and grading

| Source | Immutable revision |
|---|---|
| `self-long/RULER-llama3-1M` | `5da49e4000224d3289ffb14fc32cbd20211765ed` |
| `oolongbench/oolong-synth`, validation | `49898a421f4b14f2c9cae084d2d270f930ff4c90` |
| `zai-org/LongBench-v2` | `2b48e494f2c7a2f0af81aae178e05c7e1dde0fe9` |
| `Tevatron/browsecomp-plus` | `144cff8e35b5eaef7e526346aa60774a9deb941f` |
| `Tevatron/browsecomp-plus-corpus` | `b27b02bc3e45511b8b82a13e6f90ce761df726f6` |

S-NIAH uses third-party RULER instances with a Llama chat wrapper removed, not the authors' unrecovered exact sample. OOLONG filters original-revision validation `trec_coarse`, not test and not the later corrected revision. Numeric credit is `0.75 ** abs(gold - prediction)`. Its date parser rejects incomplete dates to avoid dependence on today's date. That strictness is a parser deviation.

Pairs reconstructs gold from labeled contexts that never enter model input. Predicates retain strict dates, literal counts, asymmetric orientations, and unordered deduplication. Universal dates over a missing category are vacuously true. F1 is `2 * intersection / (predicted_count + gold_count)`. Explicit empty predictions against empty gold score one. A single empty side, malformed output, or self-pair scores zero. Pairs F1 and numeric OOLONG grades are never renamed accuracy.

CodeQA includes the original A-D choices. Local scoring reuses the checked corpus generator and `run_bench.score` semantics, including ties. The local generator revision is its source SHA-256 in private task provenance. BrowseComp's implemented deterministic casefold-and-whitespace exact scorer differs from the official LLM judge and has not produced a primary measurement.

## Aggregate and interval definitions

Every public group is one family, nominal size, arm, root model, and protocol hash. Public protocols include the fixed audit version and optional auditor SHA-256, so different adjudicators or collection policies cannot silently pool. Four adherence counts partition observed rows. Unaudited rows are all `protocol_unknown`. Audited base and declared nano reference-deviation rows are `protocol_not_applicable`, not adherent. Separate `collection_valid` and `collection_invalid` counts retain the collection denominator; strict validity cannot exceed collection validity. Raw audit reasons, private evidence digests by file, raw answers, and collection-answer strings are not public fields. It reports scheduled, observed, missing, valid, and invalid executions; task-cluster counts; repeat coverage; and score means. `mean_score` first averages valid repeats within each task, then weights tasks equally. `row_mean_score` is separately labeled and can differ under missingness. Invalid rows contribute no score. A measured zero score stays zero; no valid scores means null.

A descriptive 95% task-cluster percentile bootstrap samples task means with replacement. Seed is 20261114 plus a stable group digest, with 2000 draws and fixed nearest-rank endpoints. Repeats stay in their task cluster. Input order does not change the result. At least two valid task clusters and three valid repeats in every included task are required. Otherwise interval bounds are null and the status names the insufficiency. One task, even with three repeats, cannot provide a meaningful task-population interval. Equal observed task scores can still produce a degenerate descriptive interval with two or more clusters.

Missing tasks do not become failures. Bootstrap intervals condition on the observed valid task subset, not on all scheduled tasks. Report coverage beside every score. Shared contexts and deterministic task selection limit population inference even when the descriptive interval is available. No significance or model-ranking claim follows from these tiny sets.

For binary CodeQA or S-NIAH task outcomes, the event is all scheduled repeats scoring one. Only tasks with every scheduled repeat valid are eligible. Wilson 95% intervals use the number of eligible tasks, never the number of repeats. Mixed repeat outcomes count as failure of that all-repeats event, not as separate Bernoulli trials. Fractional substring grades make the binary summary inapplicable. Fewer than two eligible tasks suppresses the interval. These intervals are conditional on an independent-task assumption, which is not established by this convenience sample. No Wilson interval is offered for the shared-context semantic and local families.

Known usage and timing aggregate across valid and invalid executions. Timing includes wall seconds and sums of reported root and child request latency. Those sums can overlap under concurrency and are not elapsed time. Each measurement includes known-row and missing-row counts, sum-known, and mean-known. Token fields use actual request-level prompt and completion counts by root and child role, not the ledger's zero-filled totals. Partial counts remain reported-known sums. Explicit zero child requests yields zero child tokens; absent request evidence stays null. `usage_complete_rows`, `usage_partial_rows`, and `usage_unknown_rows` make incomplete accounting visible. Plugin child attempts, proxy physical requests, host tool calls, and cells remain distinct. They are not added together. Cost is omitted because provider prices were not measured.

## Provenance and privacy boundary

Measured benchmark commit `10918473fbb90d04af08221725baa671369fb31e` and plugin implementation `184f7367465601f6e190fdff1bcd091903bef8ad` remain pinned in `manifest.yaml`. Tests are outside the measured top-level production Python hash. Auditor commit `9baf85a649f656479ad376a1d4958818d342ee4b` completed separate post-hoc evaluation of all 300 canonical primary rows. The initial timed-out/locked attempt produced no output and was superseded by final adjudication.

Post-collection repairs `74a7aa2e29fdd017b8330423e6976894fd6d2212` and `6ed40c6e83f339221f860fe59d7b9c34dcbae626` were applied and tested separately, not measured by this matrix. They require quoted host FINAL, completed=true, and logical child outcomes, and fix unique per-call legacy hashed logs. Gating checks finished responses, not streaming hold or semantic entailment; native IDs avoid stale cross-session final reuse. No negative result was backfilled. Reproduction requires the measured collection checkout and a separate auditor checkout, not current repaired HEAD. Runtime release, fork, and nano commits remain pinned; generated protocols retain older CLI and library hashes without local paths.

The final summary was generated with `--require-audit --closed` and records `bounded_complete` with `paper_strict_v1`. The CLI default remains `ongoing` for future unclosed runs. Closed collection is `bounded_complete` only when all 300 scheduled executions per root are observed, including invalid rows; missing executions yield `partial`. This is execution coverage, not a claim of 300 valid scores, paper completeness, independent sampling, or inferential superiority. Cross-family static review is not used as a passing verification gate.

Only fixed enums, validated numeric aggregates, and SHA digests may enter the public JSON. The closed output validator rejects unknown keys at every level. It cannot emit task IDs, request rows, session IDs, errors, paths, raw protocol dictionaries, prompts, or outputs. `check_public.py` also scans the study's explicit file allowlist and rejects raw artifacts and private-location markers. Only standard `.ruff_cache`, `__pycache__`, and `.pytest_cache` directories are excluded from the workspace scan. Other unexpected files, including raw JSONL, still fail. No cache or user file is deleted. Private raw locations and commands belong only in the operator report.

Design choice: direct JSONL aggregation avoids coupling publication to plugin imports. Importing the upstream runner for summary work would pull execution dependencies and expose raw task dictionaries unnecessarily. The thin shell wrapper reuses that runner only for execution. Focused tests prove cohort separation, repeat-aware intervals, missingness, deterministic output, and closed-schema rejection.
