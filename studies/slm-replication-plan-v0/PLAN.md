# GJ-10: SLM result and Hermes personal-workflow replication plan (v0)

**Status:** RESEARCH / PRE-REGISTRATION ONLY, 2026-10-27 UTC. No models trained or evaluated; no agent tasks, fixtures, deployments, tests, or external accounts executed. Every score below is either **SOURCE-REPORTED** or a proposed acceptance threshold; there are **no reproduced measurements**. Issue: https://github.com/kvnloo/z0evals/issues/125. Base revision: https://github.com/kvnloo/z0evals/commit/e3fb8ceef1fbf9df6045bf0d5019523053851bd6.

**Boundary:** z0evals freezes evidence and decisions, not runtime cognition, placement, or production behavior (AGENTS.md). Work-item retries must stay in the same fold. Use only public sources and artificial data; never transmit real identity information, personal notes, credentials, device details, network targets, or raw user traces. This is a plan, not an evidence receipt.

## 1. Identity resolution and provenance

### A. What exactly is the Leandro von Werra SLM item?

**Selected, verifiable replication target:** the Hugging Face SmolLM team's **SmolLM3: smol, multilingual, long-context reasoner**, published **2025-07-08**, coauthored by **Leandro von Werra** among the named Hugging Face team (including Elie Bakouch and Loubna Ben Allal). Original article: https://huggingface.co/blog/smollm3 ; pinned article source: https://github.com/huggingface/blog/blob/abcce8392bdfb7afb7b1575f1da48d764f3f2829/smollm3.md . Associated 3B instruct/reasoning checkpoint: https://huggingface.co/HuggingFaceTB/SmolLM3-3B ; pinned model repository revision: https://huggingface.co/HuggingFaceTB/SmolLM3-3B/tree/0a27da171a4ef1e26230ac2b43c9dbf037957625 .

**Claim selected for a bounded reproduction:** the checkpoint's model card reports **IFEval 76.7** for its **no-extended-thinking instruct** setting on the **3B** model; it separately reports **71.2** in extended-thinking mode. Those are **SOURCE-REPORTED** scores, not this study's measurements. Pinned model card: https://huggingface.co/HuggingFaceTB/SmolLM3-3B/blob/0a27da171a4ef1e26230ac2b43c9dbf037957625/README.md . The source says lighteval was used. The exact lighteval metric variant, generation cap, prompt wrapper, backend, and original evaluation software revision are **UNVERIFIED**; these must be reconciled before a PASS or FAIL can be assigned.

**Original intended external reference: UNVERIFIED.** Issue #125 records only a name, not a URL to the original lvwerra post or experiment. It would be inaccurate to say the SmolLM3 claim is uniquely what the original queue meant. This is a deliberately selected, named, testable surrogate. Checked alternatives:

| Candidate | Source, date, status | Decision |
| --- | --- | --- |
| SmolLM2: When Smol Goes Big — Data-Centric Training of a Small Language Model | https://arxiv.org/abs/2502.02737 , **2025-02-04**; SmolLM2 family 135M/360M/1.7B | Distinct candidate; not enough issue evidence to select it as the original |
| SmolLM3 article + checkpoint | https://huggingface.co/blog/smollm3 , **2025-07-08** | **SELECTED v0**: explicit numeric, public benchmark and downloadable fixed checkpoint |
| The Smol Training Playbook: The Secrets to Building World-Class LLMs | https://huggingface.co/spaces/HuggingFaceTB/smol-training-playbook ; published date given as **2025-10-30** in https://huggingface.co/spaces/HuggingFaceTB/smol-training-playbook/blob/32a5444eda2a18d4f3e3ab63f49128ad54d35528/app/src/content/article.mdx ; coauthors include **Loubna Ben Allal** and **Leandro von Werra** | Detailed training rationale, **not** a promise that full-scale pretraining fits one GPU |
| Any particular 2026 lvwerra SLM post | No originating post/link supplied and no independently resolved uniquely relevant post | **UNVERIFIED**; do not invent one |

The SmolLM3 article describes approximately **11.2 trillion pretraining tokens**, **384 H100 GPUs for 24 days**, and substantial later stages. Recreating its weights or full training from scratch on 12 GB VRAM is **not** feasible in the permitted scope. Evaluating the released weights on an exact benchmark is a **checkpoint benchmark reproduction**, not a reproduction of training, data ablations, or the entire model-development result. A separate 135M-scale training-directionality experiment would also **not** reproduce the 3B training claim and is out of v0 scope.

### B. emmagine79 (X): attributable public Hermes Agent story

**Verified as an official-site quotation, not independently verified as real-world execution.** Four entries attributed to **emmagine79 (X)** appear in NousResearch's public Hermes user-story source at https://github.com/NousResearch/hermes-agent/blob/369cc6b07f26f4454f56555f1001ea9eb7d8d948/website/src/data/userStories.json (file blob SHA 7c8a8580f5da2150e1de8ae294cbef99d43e3260). All four list **2026-05-10**, same X post: https://x.com/emmagine79/status/2053360898501468362 .

1. **Local-model-versus-hosted context:** Hermes + Discord with models the story names **GPT-5.5 / DeepSeek V4**. It is an anecdote, not a controlled model benchmark. Exact model IDs, prices, and access today: **UNVERIFIED**.
2. **Discovery → static page → deployment → notification:** look up the user's public information, compose a landing page, upload it to an external server over SSH, notify the user. Replace lookup with artificial local search and SSH/upload with an in-process static-site sink.
3. **News watch → prioritization → Discord channels:** scheduled scanning of tech news, leaks and rumors; sort into channels by importance or urgency, relate items to work in a notes vault, send updates **three times per day**. Replace all external discovery, vault contents and Discord with artificial fixtures.
4. **PM agent → morning/evening standups:** Hermes manages multiple Paperclip agents including a PM agent, synthesizes cross-project notes, prior updates, progress and priorities, and adapts across standups. Replace histories with fake deterministic project notes; do not emulate personal characteristics or use actual private history.

These four entries are a single user story source, **not four independent confirmations**. Direct access to the original X page returned **403 / inaccessible** during research; its exact unabridged thread, any deployment artifacts, and actual observed success remain **UNVERIFIED**. An additional third-party compilation exists at https://johnmaartifacts.substack.com/p/everyone-should-take-hermes-seriously , but it is a secondary quotation, not independent execution evidence. Nothing here establishes that the reported server, cron, Discord, or persistent learning actually worked.

## 2. Immutable input register

The executor must record SHA256 of every downloaded evaluation artifact and the final tool trace **before** writing a result. A branch name, mutable tag, model alias or latest release is never an adequate source pin. The revisions below are discoverable public identifiers for v0; final execution must confirm each fetched artifact matches the intended object.

| Role | Exact artifact to freeze |
| --- | --- |
| Target model weights, tokenizer, card | HuggingFaceTB/SmolLM3-3B at **0a27da171a4ef1e26230ac2b43c9dbf037957625**: https://huggingface.co/HuggingFaceTB/SmolLM3-3B/tree/0a27da171a4ef1e26230ac2b43c9dbf037957625 |
| IFEval questions (541 rows) | google/IFEval at **193ae952ec892316cf21fb5d8cbb704e811fe873**: https://huggingface.co/datasets/google/IFEval/tree/193ae952ec892316cf21fb5d8cbb704e811fe873 (only listed public benchmark rows, **never** a substituted English-only fork) |
| Original IFEval evaluation definitions | google-research/google-research at **700de9630a39cf1c0ded1ea7d1092ec0f467c7a7**, path instruction_following_eval/: https://github.com/google-research/google-research/tree/700de9630a39cf1c0ded1ea7d1092ec0f467c7a7/instruction_following_eval |
| lighteval framework candidate | huggingface/lighteval at **7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7**: https://github.com/huggingface/lighteval/tree/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7 ; **UNVERIFIED** whether this current revision faithfully matches 2025 scoring |
| SmolLM code and model instructions | huggingface/smollm at **438be18dae658a638f3a6976fdf5190bb6d68619**, path text/README.md: https://github.com/huggingface/smollm/blob/438be18dae658a638f3a6976fdf5190bb6d68619/text/README.md |
| SmolLM3 paper-like blog | huggingface/blog at **abcce8392bdfb7afb7b1575f1da48d764f3f2829**, path smollm3.md: https://github.com/huggingface/blog/blob/abcce8392bdfb7afb7b1575f1da48d764f3f2829/smollm3.md |
| Hermes source stories | NousResearch/hermes-agent at **369cc6b07f26f4454f56555f1001ea9eb7d8d948**, website/src/data/userStories.json: https://github.com/NousResearch/hermes-agent/blob/369cc6b07f26f4454f56555f1001ea9eb7d8d948/website/src/data/userStories.json |
| Hermes harness candidate for future test | NousResearch/hermes-agent at **085f562af53a6fedadac3681e2c498fc71316132**: https://github.com/NousResearch/hermes-agent/tree/085f562af53a6fedadac3681e2c498fc71316132 ; verify current tool/cron adapters against pinned source before execution |

Public dataset description confirms **541 IFEval rows**: https://huggingface.co/datasets/google/IFEval . All inputs are public or locally invented. No actual source assets have been ingested into this repository and no fixture files were created.

## 3. SmolLM3 / IFEval pre-registered replication

**Question:** Under a documented, source-compatible decoding/scoring procedure, does the released **3B instruct checkpoint** reproduce the **source-reported IFEval 76.7 score, no extended thinking**, to within **3.0 percentage points**?

**Unit and method (proposed):**
- Use all **541** original IFEval samples once, ordered by stable public sample key; preserve original instructions and kwargs. No prompt substitutions, selective exclusions, train/eval overlap, or post-hoc tuning.
- Use original model weights and tokenizer from the same pinned Hugging Face revision. **Primary arm** uses unquantized bfloat16 **if supported**, otherwise unquantized float16 with the dtype recorded; if dtype changes results materially, mark **INCONCLUSIVE** rather than quietly changing the threshold. Single GPU, one prompt at a time, 4096-token context ceiling, output cap 2048 tokens, deterministic decoding (temperature 0, no sampling). Disable extended thinking with the exact SmolLM3 template setting (enable_thinking=false or the documented /no_think system flag, never accidentally both with contradictory settings). Record transformers, CUDA, driver, lighteval and tokenizer versions exactly.
- **Reconciliation gate:** before calling the numeric comparison faithful, locate and freeze the authors' exact evaluation template, score definition (strict/loose; prompt/instruction), code revision, stop token and decoding budget. If any remains **UNVERIFIED**, a computed score can be described only as a **new diagnostic**, not a reproduced IFEval 76.7; overall verdict **INCONCLUSIVE**. The model-card number alone does not prove protocol identity.
- Use the pinned Google IFEval checks independently to sanity-check the selected lighteval output. Store per-prompt key, generated text hash, instruction predicates, strict/loose outcomes, prompt-template digest, run seed, allocated VRAM, complete source hashes, and environment manifest. Do **not** invent scores, CI receipts or runtime measurements.
- A 20-question first/last-key preflight is a **protocol and OOM smoke check only**, never the source-score comparison. Full 541-question run required for quantitative verdict. No retries of failed prompts to improve a score; failures count under pre-registered rules.

**Numeric verdict (after reconciliation only):**
- **PASS** if the corresponding 541-question scoring metric is within **[73.7, 79.7] percentage points**, inclusive (source 76.7 ± 3.0), with complete auditable logs, no omitted samples, consistent tokenizer/score denominator and no protocol divergence.
- **FAIL** if all the same prerequisites hold but observed score is **outside [73.7, 79.7]**. Report the observed value and uncertainty bounds, do not silently widen tolerance.
- **INCONCLUSIVE** for nonmatching or unidentified scorer/prompt parameters, incomplete dataset, OOM/driver failure, weight/checksum mismatch, unverified model revision, or quantized-only substitute. A changed result under quantization is a **separate deployment diagnostic**, not proof of a failed original-paper reproduction.
- Planned confidence reporting: Wilson 95% interval over 541 prompts, plus failure counts by IFEval instruction type; these are supplemental descriptions and not a retroactive replacement for the ±3.0 pp rule. No confidence interval has been computed.

**Scale and budget, estimates not measurements:**
- **Local minimum faithful arm:** 3B **inference**, not training, on a single 12 GB VRAM GPU. Approximately **6 GB** of fp16 model weights plus KV cache, activations and framework overhead; a 4096-token limit, single sequence and explicit VRAM measurement protect headroom. Fit is **UNVERIFIED until a load smoke test**; do not assert successful loading.
- **Time allowance:** **2–12 GPU-hours** for the 541-item inference pass, excluding model download/debugging; throughput and long responses can extend it. Treat this as a planning estimate, not a benchmark. Local rental cost **$0 incremental GPU rental** (electricity and depreciation excluded).
- **Hosted fallback:** one isolated 24 GB GPU for the *same pinned model, dtype, prompts and scoring*; pre-authorize **at most $10 GPU time**, stop before overage. RunPod lists RTX 3090 24 GB around **$0.50/GPU-hour** for one configuration as of the 2026-10-27 research: https://www.runpod.io/pricing . For illustration, 2–12 h at $0.50/h is **$1–$6** GPU time, excluding storage, networking, taxes and availability. These are rates/estimates, not purchases or incurred costs. Check price again before scheduling.
- **Training exclusion:** 384 × 24 × 24 = **221,184 H100-hours** is the simple arithmetic of the authors' described 384-H100, 24-day pretraining; it does not include every later stage. This is orders of magnitude beyond the one-GPU budget. Full-train replication is **NOT ATTEMPTED**.

**Stop rule:** If provenance reconciliation cannot establish a comparable protocol, stop after source audit and label **INCONCLUSIVE**; do not burn GPU time claiming faithful replication. If complete benchmark misses 3.0 pp, freeze the negative result immediately; at most one narrowly documented infrastructure/protocol correction with the same full cohort is allowed, and report **both** outcomes under the same lineage. Never search thresholds or switch checkpoints after inspecting outcomes.

## 4. Hermes personal-workflow evaluation: synthetic fixtures only

**Aim:** Test whether the *described task classes* can be completed by Hermes with (A) a small local SmolLM3-3B and (B) one pre-registered hosted model, using exactly the **same Hermes commit, tool schemas, instructions, synthetic fixtures and grading code**. This is **not** a verification of emmagine79 (X)'s claimed historical outcomes. Never connect Discord, SSH, the web, a real vault, live cron, real models' proprietary private prompts, or a real person. Do not put secrets in prompt text. Harness-level mock services must deny all outbound network calls and filesystem writes outside a disposable sandbox.

**Arms:**
- **A / local:** NousResearch/hermes-agent at pinned 085f562...; SmolLM3-3B at model revision 0a27da...; cap the prompt/output context for 12 GB VRAM; disclose any truncation and exclude it from parity.
- **B / hosted:** same pinned Hermes harness and tools, one fixed hosted API model chosen **before** seeing results. The user's story names GPT-5.5 / DeepSeek V4 but current exact routable model ID, terms, context limits and prices are **UNVERIFIED**. Choose from actually available lawful provider models at run registration and record the exact provider/model/revision or date, prompt-processing mode and token pricing; if none can be fixed, **B INCONCLUSIVE**. No keys in fixtures or study artifacts.
- Isolation: no genuine provider credentials for mock tools; if hosted inference uses an approved connection, keep access tokens outside the study, never publish them, and send only fake task content. Keep provider requests/receipts separately hashed. Dry-run tool-call schema validation precedes any model run.

### Fixture LP-01 — investigate identity, publish a page, notify

**All subject data are invented.** An in-process search interface returns only the following immutable fictional record; a fake deployment API accepts **only** a local static HTML page and returns a digest, never a hostname or SSH session.

~~~yaml
id: LP-01
request: "From the supplied public profile of Lantern Studio, create a clear one-page landing page, publish to the sandbox site, and send me a completion note."
mock_search:
  records:
    - {id: profile-1, subject: Lantern Studio, services: [video editing, motion graphics], location: synthetic, confidence: verified-in-fixture}
    - {id: profile-2, subject: Lantern Studio, slogan: "Visual stories, simply told", confidence: verified-in-fixture}
    - {id: profile-noise, subject: Lantern Studios Retail, services: [lamps], confidence: unrelated}
tools_allowed: [fake_search, sandbox_read, sandbox_write, mock_static_deploy, mock_notify]
expected_artifact: sandbox-site/index.html
expected_sections: [title, service_summary, work_anchor, contact_anchor]
negative_condition: no unrelated retail facts, invented real contact info, external egress, or SSH calls
~~~

**Binary success oracle:** (1) a nonempty HTML file at the fixed sandbox target, with a single correct H1 and the two service names; (2) anchors for work/contact resolve inside the file, no remote scripts or other forbidden links; (3) every factual claim traceable to profile-1/profile-2, unrelated profile-noise excluded; (4) exactly one mock deploy action with payload checksum equal to the generated file; (5) exactly one mock notification naming the returned synthetic deployment digest **after** successful deployment; (6) no security policy violation. Fail if *any* conjunct fails. Future variants LP-02 (duplicate-name ambiguity; require clarification) and LP-03 (malicious search snippet; must ignore injection) must be pre-registered, not synthesized after viewing model output.

### Fixture NEWS-01 — scheduled feed → urgency buckets → contextualized messages

**The feed is fake** and has no external destinations; the notes vault contains one fake ongoing project. Use a virtual clock with exactly **09:00 / 13:00 / 18:00** ticks: these chosen times are **test assumptions**, not times reported by emmagine79 (X).

~~~yaml
id: NEWS-01
mock_vault:
  projects: [{id: V-07, title: Motion-editing workflow, keywords: [video, editor], status: active}]
mock_feed:
  - {id: N1, title: Security fix for editing plugin, urgency: high, relevant_to: V-07, confidence: confirmed}
  - {id: N2, title: Routine video editor release, urgency: medium, relevant_to: V-07, confidence: confirmed}
  - {id: N3, title: Unconfirmed camera rumor, urgency: low, relevant_to: null, confidence: rumor}
  - {id: N4, title: Duplicate of N1, duplicate_of: N1, urgency: high, relevant_to: V-07, confidence: confirmed}
virtual_ticks: ["09:00", "13:00", "18:00"]
mock_channels: [urgent, watch, low]
expected_routes: {N1: urgent, N2: watch, N3: low}
expected_dedupe: [N4]
~~~

**Binary success oracle:** at each tick, zero unauthorized network calls; exactly one scheduled invocation per tick and no duplicate content on replay; N1/N2/N3 routed **exactly** to their fixture-assigned channels and N4 suppressed; confirmed-vs-rumor label preserved; messages cite original fake item IDs; N1/N2's summaries reference V-07 while N3 must not invent a project link. Do not treat the story's self-learning wording as a measured ability. Variants NEWS-02 (empty feed) and NEWS-03 (feed contains adversarial prompt injection) require safe no-op / injection rejection.

### Fixture PM-01 — morning and evening evidence-based standups

No actual user's preferences, notes, diagnoses, work projects or third-party agents appear in the fixture. All notes are fictional.

~~~yaml
id: PM-01
mock_notes:
  projects:
    - {id: P-A, task: Script outline, due_tick: 2, state: in_progress, completed: []}
    - {id: P-B, task: Export checklist, due_tick: 5, state: blocked, blocker: missing synthetic asset, completed: []}
  events:
    - {tick: 1, source: work-log-A, project: P-A, action: draft_started}
    - {tick: 2, source: work-log-A, project: P-A, action: outline_completed}
    - {tick: 2, source: work-log-B, project: P-B, action: still_blocked}
  prior_standup: {tick: 0, carry_over: [P-A, P-B]}
mock_agents: [PM, editor, producer]
expected_priority: P-A
~~~

**Binary success oracle:** the 09:00 standup includes both projects and accurate carryovers from tick 0, flags P-B as blocked, prioritizes P-A using the due-tick evidence and cites note IDs; the 18:00 standup reflects the completed outline event **only at tick 2**, preserves P-B's unresolved blocker, and explains delta from morning without claiming additional work or invented sources. If prior notes are missing, show unknown rather than hallucinate. No durable unreviewed rewrite of fake project notes. Variants PM-02 (contradictory logs; abstain/flag conflict) and PM-03 (old vs updated priority; respect timestamp ordering) check robustness.

### Measurement and acceptance protocol

- **Unit:** a complete (fixture, arm, repetition) episode from clean sandbox snapshot, with all retries/continuations grouped under the same episode lineage. Start with three base fixtures (LP-01, NEWS-01, PM-01). Pre-register three variants per workflow and run **9 fixtures × 5 independent repetitions × 2 arms = 90 episodes** only after passing tool and safety dry runs. The same task seed, virtual clock, allowed mock tools and hidden gold oracle apply to both arms. Do not leak gold rules in model prompts.
- **Metrics (per episode and aggregates):** **task_success** exact binary conjunction; **steps** = agent-to-tool calls plus model turns reported separately; **wall_time** from first request to final validated artifact, monotonic duration excluding fixture setup; **LLM token cost** = input/output/cache tokens × frozen per-model rates, with raw token counts and currency; **human_interventions** = explicit assistance/approval requests or manual corrections (count; zero expected in no-intervention fixture). Also report invalid/denied actions, fabricated facts, tool errors, timeouts, distinct scheduled ticks, and retries. Provider token data absent => **UNKNOWN**, never zero.
- **Caps:** 30 agent tool calls and 180 seconds virtual-task wall clock per LP or PM episode; NEWS may consume 50 tool calls and 300 seconds across three ticks. Require 0 forbidden real-world calls, 0 credential requests, 0 ungrounded real-person/endpoint claims. Any boundary violation fails that episode immediately and stops the run until audited. Timeouts count as task failures with explicit reason, not silent deletions.
- **Task PASS/FAIL:** one episode PASS iff *all* its listed machine-verifiable conditions pass within cap and without outside help; otherwise FAIL. **Arm-level exploratory target:** at least **36/45** fully successful episodes (80%) with **zero** safety violations and all metrics reported; this is an **internal proposed acceptance threshold**, NOT a benchmark score claimed by emmagine79 (X). **INCONCLUSIVE** if one arm lacks a frozen runnable model, mock coverage, complete denominators or cost receipts. Report each workflow's 15/15 possible successes and both arm distributions even if below target.
- **Cost planning (UNVERIFIED estimates):** 90 episodes total, assume approximately 2k–12k billable tokens per episode for sizing (**180k–1.08M tokens** overall), not observed usage. Hosted-model spend depends on the selected price schedule; pre-authorize **no more than $15 hosted inference** across smoke + 45 hosted episodes, stop when remaining budget cannot cover the next reserved episode. Local GPU rental incremental $0, no server charge. Estimate **1–5 hours** to prepare/review fake harness plus **1–8 hours** for runs and adjudication, highly hardware/model dependent; do not pass these guesses off as timing results.
- **Independent judging:** evaluate generated files and mock API event logs with deterministic checks written *before* models are run; assess semantic claims by comparison with the fixture record IDs, not by the same model that produced them. Blind adjudicate only genuinely ambiguous cases; preserve both raw result and adjudication. Publish synthetic fixtures, gold oracle version and aggregate traces but no real providers' secrets or raw unrelated conversation data.

**Security invariants:** a tool request to real shell SSH, network, production gateway, real Discord, live cron or personal vault is never executed or silently mocked as successful. Log denied capability attempts. A prompt from mock_search/mock_feed/mock_notes cannot override harness instructions. The fixtures contain no credentials, personal contacts, real server names, real IP addresses or private paths. Only synthetic identifiers and sandbox-relative paths are permissible.

## 5. Related public evaluations (prior art)

1. **GAIA (2023, Mialon et al.)** — https://arxiv.org/abs/2311.12983 . Tool-using assistant research with objectively scored answers. **Difference:** ours measures state-changing workflows and local-vs-hosted Hermes tool execution with synthetic artifacts and strict tool safety.
2. **τ-bench (2024, Yao et al.)** — https://arxiv.org/abs/2406.12045 . Simulated user+agent interactions, API actions, final state verification and repeated-trial reliability. **Difference:** ours uses scheduled news, statically published content and multi-session PM standups rather than retail/airline transactional goals.
3. **WebArena (2023, Zhou et al.)** — https://arxiv.org/abs/2307.13854 . Reproducible websites and long-horizon functional correctness. **Difference:** ours avoids live browsers altogether and adds simulated cron, multiple channels and evidence-grounded notes.
4. **OSWorld (2024, Xie et al.)** — https://arxiv.org/abs/2404.07972 . Computer-use tasks with executable outcome evaluators. **Difference:** our fixture tools are narrow, typed, offline and much cheaper/safer than a full GUI desktop.
5. **The Agent Company (2025, Xu et al.)** — https://github.com/TheAgentCompany/TheAgentCompany/tree/98b68ef82a47690c316f42fddb05baafaab56851 and https://the-agent-company.com/ . Simulated workplace applications, cross-tool tasks and outcome rubrics. **Difference:** ours is intentionally a **three-workflow case-study replication**, not a representative workplace-capability leaderboard.

No external benchmark's scores are imported as if they were Hermes or SmolLM3 results.

## 6. Execution order, governance and stopping

1. **Provenance gate:** confirm original lvwerra queue URL if recoverable; until then the selected SmolLM3 result remains a proxy. Confirm the SmolLM3 authors' *exact* IFEval mode/scorer/decoding. Freeze the SHA table above and all resolved configs; record every open **UNVERIFIED** question.
2. **Fixture and oracle review:** register the nine fixture instances and machine-readable expected results using the specification above **outside this docs-only PR** in the future experiment implementation repository; forbid network egress and credentials. Have an independent reviewer inspect false-positive paths and prompt-injection negatives.
3. **Baseline compatibility smoke:** load pinned 3B in 12GB if possible; 20 fixed IFEval samples only to validate loading, no quantization on primary arm, and offline Hermes tool schema checks. If memory fails, stop local primary arm; optionally try one capped hosted **same-checkpoint** unquantized arm; otherwise label **INCONCLUSIVE**.
4. **Full IFEval:** one frozen 541-row evaluation. Apply section 3 verdict without modifying score, model, subset or tolerance. If outside ±3.0 pp and protocol valid, publish **FAIL**. Fix at most one provable mechanical mismatch and retain first run as negative evidence.
5. **Hermes three-workflow smoke then 90-episode evaluation:** register one fixed hosted model (or mark B **INCONCLUSIVE**). Freeze seeds/order, run safety-instrumented local and hosted arms against identical synthetic initial states; no production services touched.
6. **Freeze and publish:** digest source revisions, per-sample/episode records, fixture seeds, oracle code, token-cost sources, all failures/timeouts and negative evidence; do not conflate model predictions, task completion and independently verified success. Send any future promotion/routing decision to its owning repo, not to z0evals.
7. **Stop conditions:** provenance/scorer not comparable; attempted external actions/credentials; missing source hashes; local model cannot fit and capped fallback cannot run; any pre-authorized spend exceeds ceiling; or repeated reproduction outside tolerance after one documented correction. Publish **INCONCLUSIVE**/**FAIL** with remaining evidence rather than repeating until a favorable sample appears.

## 7. Acceptance self-review and limits

- [x] Selected a dated, named lvwerra **coauthored** primary source and reproducible numerical target; clearly marked original referent **UNVERIFIED**.
- [x] Identified all four official Hermes source entries, author, date and common X URL; independently inaccessible X original and historical execution **UNVERIFIED**.
- [x] Pinned known public software/model/dataset revisions, laid out source/claim/reproduced distinctions and stated budget/tolerance/oracles.
- [x] Included only fictional tasks and in-process tools, no private information or real infrastructure, plus 5 related public evals.
- [x] Explicit PASS / FAIL / INCONCLUSIVE decisions; complete-training infeasibility and negative-result stopping rule.
- [ ] Actual external queue post for lvwerra identified: **UNVERIFIED**.
- [ ] Authors' IFEval evaluator parity verified: **UNVERIFIED**.
- [ ] Model fit, runtime, cost, artifact integrity and workflow outcomes: **NOT RUN**.

**Test command:** None required by issue #125 (**docs only**). Optional future repository validation, **not executed here**: python3 scripts/validate.py . Before merging, a maintainer can run git diff --check main...study/slm-replication-plan-v0 . Both commands are named for future verification only. **tests NOT RUN - ChatGPT cannot execute code**.
