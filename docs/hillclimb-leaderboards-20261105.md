# Which hillclimb leaderboards help this agent system?

Local-only research draft for Z11, checked 2026-11-05 UTC. No benchmark was run. This document compares source-reported evaluation contracts, not reproduced scores.

## Answer

Yes, relevant leaderboards exist. My relevance ranking is Terminal-Bench and SWE-bench for end-to-end terminal and repository work, then BFCL for tool-use diagnostics. Sierra's tau-bench tests policy-bound tool interactions. KernelBench is useful only for a measured GPU-operator bottleneck. RE-Bench supplies historical examples of research hillclimbing, but its repository now marks the tasks deprecated. These are task-fit judgments, not a ranking of models. The contracts and limits appear below. [TER] [SWE] [BFCL] [TAU] [KB] [RE]

None of these public scores establishes improvement in this system. The local profile prioritizes discovery turns, repeated empty searches, and blocking waits. It does not establish that GPU kernels or small CLI startup costs dominate agent wall time. [P:31-49]

## Local task correspondence

The profile is an existing analysis, not a measurement reproduced for Z11. It uses completion-message timestamps as timing proxies. Its coverage excludes several agent runtimes and historical host metrics. Therefore, its bottleneck ordering is a relevance guide, not a complete causal model. [P:3-13]

| Existing task or cost | What a useful benchmark must expose | Correspondence judgment |
|---|---|---|
| Find the correct file or prior evidence, including recovery after an empty search. [P:35-41] | Correct evidence and task completion, plus discovery turns and failed searches. | SWE-bench and Terminal-Bench offer task-level outcomes. BFCL V4 search and memory are narrower diagnostics. Their aggregate scores cannot isolate saved local discovery turns. [SWE] [TER] [BFCL] |
| Wait for tools without unnecessary foreground polling. [P:36] | End-to-end time, blocking time, tool invocations, and correct completion. | Terminal tasks can exercise long commands, but a resolution rate alone does not identify polling overhead. No source inspected here establishes a local wait-management score. [TER] |
| Batch independent calls without breaking dependencies. [P:37] | Dependency-correct tool use and successful final state. | BFCL's parallel-call and multi-turn categories are relevant diagnostics. They do not prove that the local scheduler or tool adapter preserves those dependencies. [BFCL] |
| Complete coding and verified-tool-use work. [L:69-73] | Independently checked artifact or state, not a claim of success. | SWE-bench patches, Terminal-Bench task verification, and tau-bench database outcomes are closer than answer-only rankings. Their task domains still differ from the owner's work. [SWE] [TER] [TAU] |
| Improve actual kernel execution. [L:69] | Correctness on unseen inputs and speed on the target hardware, followed by whole-task timing. | KernelBench is a direct operator-level comparison. RE-Bench is a historical research-task comparison. Neither demonstrates fewer local discovery turns or waits. [KB] [RE] [P:35-49] |

## Public comparisons

The last column contains my transfer judgments. The score descriptions are source-reported. No cross-benchmark average or current model winner is asserted.

| Benchmark and public comparison | What it scores and what can be hillclimbed | Practical usefulness here | Transfer limits |
|---|---|---|---|
| [SWE-bench leaderboards](https://www.swebench.com/), especially Verified. [SWE] | GitHub issue-to-patch tasks. Verified contains 500 human-filtered problems. The board reports percentage resolved. Improve repository navigation, patch construction, and verification under a fixed agent budget. | High for repository discovery and accepted fixes. | Passing benchmark tests does not prove general patch correctness, review quality, or deployment. Public historical issues invite memorization and repeated-test tuning. Model, scaffold, tools, budget, and dataset split must stay identifiable. |
| [Terminal-Bench](https://www.tbench.ai/), current continuous-release family. [TER] | Terminal tasks with agent/model resolution rates. The archived contract includes task tests and oracle solutions. Current releases use Harbor and versioned datasets. Improve autonomous command workflows and recovery. | High for command-driven work. Best broad correspondence to the profile's tools and waits. | A moving `latest` dataset is not a frozen experiment. The legacy repository resolves to `terminal-bench-1`, not the current repository. Do not mix its task set with the current board. Resolution alone cannot attribute a gain to fewer discovery turns or waits. |
| [Berkeley Function Calling Leaderboard V4](https://gorilla.cs.berkeley.edu/leaderboard.html). [BFCL] | Function-call accuracy, with AST or state-transition verification by category. V4 adds web search, memory, and format sensitivity. Improve function selection, arguments, parallel calls, and multi-turn recovery. | High as a diagnostic for verified tool use. Search and memory are relevant to discovery. | A syntactically correct call is not proof of an authorized or successful local action. Public web-search questions are not local file-location tasks. Category gains can disappear in the overall average. |
| [Sierra tau-bench](https://taubench.com/), repository `sierra-research/tau2-bench`. [TAU] | Conversations with a simulated user and tools, scored against verifiable database outcomes and a reliability metric. The current repository separates frozen text and voice releases. Improve policy-bound multi-step interactions. | Medium for tool-state consistency and permission-aware work. | Customer-service policies and simulated users do not reproduce local owner approvals. Text and voice scores answer different questions. The repository explicitly says 2.0 and 1.x inputs differ and scores are not comparable. No phone or voice run is proposed here. |
| [KernelBench / Kernelsseum](https://scalingintelligence.stanford.edu/KernelBenchLeaderboard/). [KB] | Replace PyTorch operations with correct, faster kernels. `fast_p` is the fraction both correct and faster than threshold `p` relative to the reference. Kernelsseum compares solutions per problem. | Conditional fit for Autokernel, not the default target for agent orchestration. | GPU type, tensor shapes, dtype, tolerances, reference implementation, compilation, and timing method affect speedup. Public fixed-shape kernels are easy to over-specialize. Operator speedup is not end-to-end agent speedup. |
| [METR RE-Bench published comparisons](https://metr.org/blog/2024-11-22-evaluating-r-d-capabilities-of-llms/). [RE] | Seven research-engineering environments with scoring functions and fixed time budgets. Tasks include kernel and training-loop optimization. Compare research progress under matched resources, not raw scores across different objectives. | Conceptually relevant to iterative research and allocating experiment time. | This is a historical comparison, not an established maintained leaderboard. The pinned repository marks tasks deprecated and asks users to avoid overfitting and frontier-model training outside its intended safety-evaluation use. Do not adopt it as the system's tuning set. METR also notes clear goals and short feedback loops differ from real research. |

## What would count as local improvement

These are interpretation requirements for existing evaluations, not a new queue, controller, or experiment run. They follow the lane's held-out correctness and latency/token/tool acceptance standard. [L:69-73]

- Keep public benchmark performance separate from locally executed outcomes. Record the benchmark release, task IDs, model, agent, prompts, tool versions, budget, hardware, and verifier. Moving releases and different tau-bench inputs make unqualified score comparisons invalid. [TER] [TAU]
- For discovery changes, inspect correct evidence and final task success alongside discovery turns, empty retries, tokens, and end-to-end latency. A faster wrong answer is not a gain. [P:35-49] [L:73]
- For wait changes, separate command execution from polling and foreground blocking. Exclude owner approval time from the optimization target. [P:7-13,36,42]
- For kernel changes, keep the same correctness checks and target workload. Compare whole-task wall time as well as operator time. The profile does not cover historical GPU utilization, so it cannot establish kernel headroom. [KB] [P:11-13] [L:73]
- Keep related work-item attempts together when defining holdouts. Exclude public solutions and test answers from tuning. Preserve failed attempts and budget consumption. Include baseline and negative controls, such as a fixed model and a change unrelated to discovery. These are proposed safeguards, not checks executed here. [Z:18-30] [L:73]
- Repeated leaderboard feedback can become training feedback. Reserve an untouched local task set with an independent verifier before attributing transfer. Public scores remain candidate-selection evidence only. [Z:23-30] [RE] [L:73]

The immediate research conclusion is to use Terminal-Bench and SWE-bench for broad task-fit screening, with BFCL category results for diagnosis. Do not choose a kernel optimization solely because its leaderboard has a dense reward. The local profile points first to unnecessary turns and waits, while lane acceptance still requires independently checked outcomes. This is a recommendation from the cited contracts, not measured improvement. [P:31-49] [L:69-73] [TER] [SWE] [BFCL] [KB]

## Sources and acquisition limits

Repository links below use immutable revisions. Website snapshots are dated evidence, not immutable benchmark releases. The operation bundle contains HTTP headers, downloaded bodies, SHA-256 hashes, and exact acquisition commands in `SOURCE-MANIFEST.json`, `DETAIL-MANIFEST.json`, and `CORRECTION-MANIFEST.json`. HTTP 200 proves reachability, not correctness or freshness. Reader output can be cached or omit dynamic content. No rank or score from search snippets is used.

`tau-bench.github.io` returned HTTP 200 but describes video-anomaly tracking. It is explicitly excluded as a tool-use source. The corrected Sierra leaderboard is `taubench.com`, linked from its pinned README. The initial `gh api --include repos/.../commits/HEAD` collector stalled and was cancelled. Unauthenticated public API requests then supplied the repository pins. No credentials were inspected or changed.

- [SWE] [Pinned SWE-bench README](https://raw.githubusercontent.com/SWE-bench/SWE-bench/02e7a74ffd0b707aab73d203fe87bdc7c76afc8e/README.md), lines 38-45, and [official score definition](https://www.swebench.com/).
- [TER] [Current pinned README](https://raw.githubusercontent.com/harbor-framework/terminal-bench/73d6279f91eb773bd51af2e2572a6fa044342e7a/README.md), lines 6-20 and 50-54. [Archived v1 contract](https://raw.githubusercontent.com/laude-institute/terminal-bench/d28711d0da2675d0bb1d56de45ae5df6082438a3/README.md), lines 23-29 and 55-88. [Current board](https://www.tbench.ai/).
- [BFCL] [Pinned README](https://raw.githubusercontent.com/ShishirPatil/gorilla/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard/README.md), lines 33-46, [V4 methodology](https://gorilla.cs.berkeley.edu/blogs/15_bfcl_v4_web_search.html), and [category columns](https://gorilla.cs.berkeley.edu/leaderboard.html).
- [TAU] [Pinned README](https://raw.githubusercontent.com/sierra-research/tau2-bench/033bf082f48e4a3c6a1256208e93cf2ce9c3bb6f/README.md), lines 9, 15-50, 89-119, and 124-141. [Official comparison and outcome definition](https://taubench.com/).
- [KB] [Pinned README](https://raw.githubusercontent.com/ScalingIntelligence/KernelBench/423217d9fda91e0c2d67e4a43bf62f96f6d104f1/README.md), lines 40-55 and 147-153. [Benchmark methodology and leaderboard link](https://scalingintelligence.stanford.edu/blogs/kernelbench/), including correctness checks and hardware-specific performance.
- [RE] [Pinned README](https://raw.githubusercontent.com/METR/RE-Bench/a0cc6d4a91b20f84ebef505d5c72358f88b3b389/README.md), lines 1-4, 12, and 28-38. [METR comparison and stated real-world limits](https://metr.org/blog/2024-11-22-evaluating-r-d-capabilities-of-llms/).
- [P] Local profile `/mnt/zer0models/worktrees/autokernel-agentsys/agentsys/PROFILE-20261103.md`, file revision `579a2dcafb76e9ce7f1319d8536351acaff37601`, SHA-256 `fb9ff9d52140dc0c73e581db521d94b7405e840d5dee2e3f82d3ed677d6717d1`. Line ranges above refer to this file. Only aggregate task categories inform this draft. No private raw traces enter the repository.
- [L] `/mnt/zer0models/workspace/zer0/data/operations/owner-message-audit-20261104/REPORT.md:65-73`.
- [Z] `AGENTS.md:18-30` at the z0evals base revision `39af35a3d4fc331924db6b2ae592d5180a3e3c90`.
- Acquisition bundle: `/mnt/zer0models/workspace/zer0/data/operations/intent-analyzer-20261104/ayo-runs/exec-Z11/`. Public sources are research evidence. Local references and the draft need a privacy review before any public action. Nothing was pushed or published.

[SWE]: https://www.swebench.com/
[TER]: https://www.tbench.ai/
[BFCL]: https://gorilla.cs.berkeley.edu/leaderboard.html
[TAU]: https://taubench.com/
[KB]: https://scalingintelligence.stanford.edu/blogs/kernelbench/
[RE]: https://metr.org/blog/2024-11-22-evaluating-r-d-capabilities-of-llms/
