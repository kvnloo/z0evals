# RLM paper-v1 protocol adaptation on Hermes

Completed 2026-11-14. **Bounded collection and strict post-adjudication are complete; full paper replication is not.** The frozen subset contains 20 task items, five arms, and three repeats, all 300 unique scheduled executions. `data/summary.json` records `bounded_complete` and `paper_strict_v1`.

Collection marked 176 executions valid. Strict adjudication retained 123 and marked 177 invalid. These are validity counts, not numbers of correct answers or a model ranking. The strict total includes base and nano reference-deviation outcomes; it is not 123 paper-RLM protocol successes.

## Frozen evidence

| Cohort | Observed | Collection valid | Current valid | Current invalid | Policy |
|---|---:|---:|---:|---:|---|
| Primary | 300/300 | 176 | 123 | 177 | Strict post-adjudication |
| Normal CLI smoke | 5 | 5 | 5 | 0 | Historical collection only |
| Thinking-off CLI smoke | 5 | 2 | 2 | 3 | Historical failed gate |
| Library thinking-off smoke | 5 | 5 | 3 | 2 | Strict post-adjudication |
| Interrupted pilot | 14 | 9 | 9 | 5 | Exploratory collection only |

Primary adherence counts are 28 adherent, 152 nonadherent, 24 unknown, and 96 not applicable. Only the 28 adherent Hermes executions meet the audited host-FINAL contract. Base and declared nano reference outcomes are not counted as adherent. Invalid does not mean wrong; no score exists for invalid outcomes.

The four canonical primary files cover CodeQA 45 executions, semantic OOLONG/Pairs 75, S-NIAH 45, and local aggregation 135. All first three repeats were retained. An operator rebalanced disjoint groups from the same 50 seed executions without changing protocol or choosing best results. Rebalancing invalids remain in evidence. Smokes and pilot never enter primary scores.

P1 review found collection-valid Hermes answers could bypass validated FINAL/citations or accept budget-exit prose. It also reproduced masking an unrecovered child failure with a later root HTTP 200. Strict evaluation uses only host-validated FINAL answers linked to actual transcript tool results, rejects incomplete/budget exits and plugin child errors/cancellation, and never promotes collection-invalid rows. Recovered physical 400/429 attempts remain allowed when logical plugin calls succeeded. Nano has no host-FINAL requirement as an explicit reference deviation, but unknown recovery of non-200 child attempts is conservatively invalid. Base outcomes are preserved.

## Primary results

The following 45 aggregate groups come directly from `data/summary.json`. Scores use the 0 to 1 scale. OOLONG is a graded score, Pairs is F1, CodeQA is parsed-choice accuracy, S-NIAH is substring hit, and local scores follow the existing exact rules. `mean_score` weights task means equally over valid repeats. It conditions on the valid subset, not all scheduled executions.

| Family | Size | Arm | Strict valid / observed | Mean | Descriptive 95% CI |
|---|---:|---|---:|---:|---|
| CodeQA | 483107 | `base-truncated` | 3/3 | 1.000 | insufficient_task_clusters |
| CodeQA | 483107 | `rlm-no-subcalls` | 0/3 | null | insufficient_task_clusters |
| CodeQA | 483107 | `released-rlm` | 1/3 | 1.000 | insufficient_task_clusters |
| CodeQA | 483107 | `fork-rlm` | 0/3 | null | insufficient_task_clusters |
| CodeQA | 483107 | `nano-rlm` | 2/3 | 1.000 | insufficient_task_clusters |
| CodeQA | 1043432 | `base-truncated` | 3/3 | 0.667 | insufficient_task_clusters |
| CodeQA | 1043432 | `rlm-no-subcalls` | 0/3 | null | insufficient_task_clusters |
| CodeQA | 1043432 | `released-rlm` | 0/3 | null | insufficient_task_clusters |
| CodeQA | 1043432 | `fork-rlm` | 0/3 | null | insufficient_task_clusters |
| CodeQA | 1043432 | `nano-rlm` | 2/3 | 0.000 | insufficient_task_clusters |
| CodeQA | 1061947 | `base-truncated` | 3/3 | 0.000 | insufficient_task_clusters |
| CodeQA | 1061947 | `rlm-no-subcalls` | 0/3 | null | insufficient_task_clusters |
| CodeQA | 1061947 | `released-rlm` | 0/3 | null | insufficient_task_clusters |
| CodeQA | 1061947 | `fork-rlm` | 0/3 | null | insufficient_task_clusters |
| CodeQA | 1061947 | `nano-rlm` | 2/3 | 0.000 | insufficient_task_clusters |
| OOLONG | 1024 | `base-truncated` | 9/9 | 0.667 | [0.000, 1.000] |
| OOLONG | 1024 | `rlm-no-subcalls` | 3/9 | 0.667 | insufficient_repeats |
| OOLONG | 1024 | `released-rlm` | 2/9 | 0.000 | insufficient_task_clusters |
| OOLONG | 1024 | `fork-rlm` | 1/9 | 1.000 | insufficient_task_clusters |
| OOLONG | 1024 | `nano-rlm` | 5/9 | 0.833 | insufficient_repeats |
| OOLONG-Pairs | 1024 | `base-truncated` | 6/6 | 0.178 | [0.000, 0.356] |
| OOLONG-Pairs | 1024 | `rlm-no-subcalls` | 1/6 | 0.000 | insufficient_task_clusters |
| OOLONG-Pairs | 1024 | `released-rlm` | 0/6 | null | insufficient_task_clusters |
| OOLONG-Pairs | 1024 | `fork-rlm` | 0/6 | null | insufficient_task_clusters |
| OOLONG-Pairs | 1024 | `nano-rlm` | 3/6 | 0.000 | insufficient_repeats |
| S-NIAH | 4096 | `base-truncated` | 9/9 | 1.000 | [1.000, 1.000] |
| S-NIAH | 4096 | `rlm-no-subcalls` | 3/9 | 1.000 | insufficient_repeats |
| S-NIAH | 4096 | `released-rlm` | 2/9 | 1.000 | insufficient_repeats |
| S-NIAH | 4096 | `fork-rlm` | 6/9 | 1.000 | insufficient_repeats |
| S-NIAH | 4096 | `nano-rlm` | 7/9 | 1.000 | insufficient_repeats |
| local-aggregation | 32000 | `base-truncated` | 8/9 | 0.333 | insufficient_repeats |
| local-aggregation | 32000 | `rlm-no-subcalls` | 1/9 | 1.000 | insufficient_task_clusters |
| local-aggregation | 32000 | `released-rlm` | 3/9 | 1.000 | insufficient_task_clusters |
| local-aggregation | 32000 | `fork-rlm` | 1/9 | 1.000 | insufficient_task_clusters |
| local-aggregation | 32000 | `nano-rlm` | 5/9 | 0.333 | insufficient_repeats |
| local-aggregation | 300000 | `base-truncated` | 9/9 | 0.000 | [0.000, 0.000] |
| local-aggregation | 300000 | `rlm-no-subcalls` | 0/9 | null | insufficient_task_clusters |
| local-aggregation | 300000 | `released-rlm` | 1/9 | 1.000 | insufficient_task_clusters |
| local-aggregation | 300000 | `fork-rlm` | 0/9 | null | insufficient_task_clusters |
| local-aggregation | 300000 | `nano-rlm` | 4/9 | 0.667 | insufficient_repeats |
| local-aggregation | 2000000 | `base-truncated` | 9/9 | 0.000 | [0.000, 0.000] |
| local-aggregation | 2000000 | `rlm-no-subcalls` | 0/9 | null | insufficient_task_clusters |
| local-aggregation | 2000000 | `released-rlm` | 2/9 | 1.000 | insufficient_task_clusters |
| local-aggregation | 2000000 | `fork-rlm` | 1/9 | 1.000 | insufficient_task_clusters |
| local-aggregation | 2000000 | `nano-rlm` | 6/9 | 0.500 | insufficient_repeats |

CIs require at least two task clusters and three valid repeats in every included cluster. `insufficient_task_clusters` and `insufficient_repeats` mean null intervals, not zero uncertainty. Each CodeQA size has only one task, so its three repeats cannot support a task-population interval. Shared contexts and convenience sampling make every available bootstrap interval descriptive, not evidence of inferential superiority.

Selected base intervals are OOLONG [0.000, 1.000], Pairs F1 [0.000, 0.356], and S-NIAH [1.000, 1.000]. S-NIAH's separate all-three-repeats-correct task outcome is 3/3 eligible tasks, with Wilson 95% interval [0.439, 1.000], conditional on an independent-task assumption not established by this convenience sample. Repeats are never treated as IID trials. The degenerate S-NIAH bootstrap is not proof of certainty or superiority. Local base intervals at nominal 300K and 2M are [0.000, 0.000].

## Paper-reported comparison, not our measurements

Source: [arXiv:2512.24601v1, Table 1](https://arxiv.org/html/2512.24601v1), not v3. Percent scale. Stars mean the paper encountered its context limit, not our truncation policy.

| Paper Qwen3-Coder-480B method | CodeQA | BrowseComp+ 1K | OOLONG grade | Pairs F1 |
|---|---:|---:|---:|---:|
| Base | 20.00* | 0.00* | 36.00 | 0.06 |
| CodeAct + BM25 | 24.00* | 12.66 | 38.00 | 0.28 |
| Summary | 50.00 | 38.00 | 44.06 | 0.31 |
| RLM | 56.00 | 44.66 | 48.00 | 23.11 |
| RLM without subcalls | 66.00 | 46.00 | 43.50 | 17.34 |

Our Nemotron-root/Lightning-child measurements above use different tasks, sizes, prompts, budgets, and runtimes. They are not matched-model comparisons. No OpenAI-family model ran. Exact S-NIAH paper chart values were not recovered and are not invented.

## Deviations and limits

- Thinking-off and library ingress were selected after pilot inspection, not preregistered. The root uses metadata rather than raw context in Hermes arms. Library ingress calls the real selected-source AIAgent and retains Hermes plugin discovery, tool assembly, dispatch, and auxiliary routing without per-home gateway startup.
- Base context is a head cap of 240000 Unicode characters, not a measured root-token window. CodeQA sizes are characters/4 estimates; local 2M and RULER sizes are nominal, not measured root tokens.
- Nano children are agents, not the paper's plain LM calls. Nano's `max_tokens=3072` is an agent completion budget inherited by children; the plugin child cap is 1536 per call. Child limits are not matched across these arms.
- BrowseComp 20 questions over 1000 documents and larger Parquet task materialization remain blocked by unavailable fleet compute. Optional Groq Qwen returned HTTP 403. The full suite and original paper task instances were not reproduced.
- Retries, failed executions, and reported-known partial usage remain visible. Physical requests, plugin child attempts, host tool calls, and cells remain distinct. The shared provider cap is 2700 attempts; four external probes require separate accounting. No missing usage or cost is invented.

## Reproduce the frozen analysis

Use a separate measured-source checkout at `10918473fbb90d04af08221725baa671369fb31e`, containing plugin implementation `184f7367465601f6e190fdff1bcd091903bef8ad`. `reproduce.sh` delegates collection to that checkout. Audit frozen copies with a separate checkout at `9baf85a649f656479ad376a1d4958818d342ee4b`. Do not use the newer repaired runner and claim identical collection behavior. Immutable task/runtime/dataset pins and measured hashes are in `manifest.yaml` and [protocol.md](protocol.md).

The implementation repository is private. Reproduction requires access to its pinned source and the private raw artifacts. Supply private locations through environment variables. Raw JSONL, task text, contexts, transcripts, citations, and answers remain outside this study.

```sh
python3 "$AUDIT_SOURCE/bench/audit_results.py" \
  --raw "$FROZEN_SEMANTIC" "$FROZEN_CODEQA" "$FROZEN_LOCAL" "$FROZEN_SNIAH" \
  --ops-dir "$OPS_DIR" --tasks "$FROZEN_TASKS" --out-dir "$AUDITED_OUTPUT"
PYTHONDONTWRITEBYTECODE=1 python3 summarize.py \
  --raw "$AUDITED_SEMANTIC" "$AUDITED_CODEQA" "$AUDITED_LOCAL" "$AUDITED_SNIAH" \
  --tasks "$FROZEN_TASKS" --require-audit --closed \
  --smoke "$NORMAL_SMOKE" "$THINKING_OFF_SMOKE" "$AUDITED_LIBRARY_SMOKE" \
  --pilot "$PILOT_SEMANTIC" "$PILOT_CODEQA" "$PILOT_LOCAL" "$PILOT_SNIAH" \
  --out data/summary.json
```

Audited inputs retain canonical basenames. Strict and unaudited primary inputs cannot mix. The auditor writes a new private directory, never collection sources. Library-smoke adjudication uses the same auditor separately. Missing executions stay missing and invalid scores stay null. The initial timed-out/locked audit attempt produced no output; the final adjudication completed all 300 canonical primary rows.

## Follow-up repairs, not measured matrix code

Plugin repair `74a7aa2e29fdd017b8330423e6976894fd6d2212` and harness repair `6ed40c6e83f339221f860fe59d7b9c34dcbae626` were applied only after collection. They require quoted host FINAL, completed=true, and logical child outcomes; they also fix unique per-call legacy hashed-log collection. The finalized matrix was not rerun with these fixes and no negative was backfilled.

Parent verification reports 59 checked-out plugin tests passing in 34.46 seconds with HTTP peer EOF, and 59 staged released-source tests passing in 172.1 seconds. Initial bootstrap failures are preserved. Separate final benchmark suites report 11 hardening, 15 matrix, 13 audit, and 11 task tests passing. FINAL gating is a finished-response check, not streaming hold or semantic entailment validation; native IDs avoid stale cross-session final reuse. A later two-arm engineering probe at runner commit `8ee34f587e0d524fcfb84a0149f7c31e074f537b` passed on released Hermes and the eager fork, each with a citation-validated FINAL and score 1.0. It corrected conflicting prose instructions, with 16 matrix regression checks passing. The preceding probe correctly withheld an uncited released-arm answer. These are follow-up engineering checks, not matrix measurements.

## Verify and publication scope

Run from this study directory:

```sh
timeout 9s env PYTHONDONTWRITEBYTECODE=1 python3 test_summarize.py
PYTHONDONTWRITEBYTECODE=1 python3 summarize.py --check data/summary.json
PYTHONDONTWRITEBYTECODE=1 python3 check_public.py
bash -n reproduce.sh
```

From repository root, run `ruff check --no-cache --select F,E9 studies/rlm-paper-replication-v1`, `python3 scripts/validate.py`, and `git diff --check`. These checks make no model calls. Only the eight allowlisted study files are public; artifact hashes exclude the manifest itself.

Publication remains draft: plugin PR #1 and study PR #191, with tracking issue comment 6885497675. Study PR #191 targets `main`, not `preview`, because the preview comparison included 248 files. This is a documented rollout deviation to keep the review to eight study files, not a merge-history rewrite. No full-replication or ranking claim follows from this bounded evidence.
