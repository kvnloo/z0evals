# RLM paper-v1 protocol adaptation on Hermes

Status: **ongoing, provisional collection evidence**, not a full paper replication or validated protocol-success result.

P1 review found that collected Hermes `valid=true` could bypass host-validated FINAL and citations, accept iteration-budget exit prose, or mask an unrecovered child failure behind a later root HTTP 200. Current `data/summary.json` is `audit_policy: collection_snapshot`. Its scores must not be cited as completed paper-protocol outcomes. Every observed row's adherence is unknown until strict post-adjudication. The parent runner owns final counts, source-commit updates, and publication. `data/summary.json` is a reproducible partial snapshot, not a completion claim. No raw task rows, prompts, answers, question text, or long contexts belong in this study.

The target is 20 materialized tasks, five arms, and three repeats: 300 scheduled executions for the primary root model. Missing executions remain missing. Invalid executions are not scored as wrong. The [protocol](protocol.md) defines coverage, scoring, intervals, and deviations.

## Current evidence

- The corrected normal-reasoning S-NIAH smoke collected five valid arms at score 1.0 and no child calls. This is process-level retrieval evidence only, not proof of validated FINAL, citations, semantic delegation, or general accuracy.
- The legacy pilot was interrupted after empty answers from reasoning-budget exhaustion and tool timeouts. Those rows remain exploratory and never enter the primary table.
- The revised protocol explicitly disables NIM thinking across arms. Its CLI smoke has two valid rows, base and nano, and three invalid Hermes rows. That failed gate remains preserved.
- The library-ingress smoke has five collection-valid arms, each scoring 1.0. The P1 review verified missing validated finals in real smoke rows, so this is not a protocol-pass gate. Primary runs now use the same library ingress and thinking-off policy. Both adaptations followed pilot inspection and were not preregistered. This tiny retrieval smoke does not establish superiority or general task quality.
- The primary summary includes every scheduled family, size, and arm even before observations exist. A zero observed count means no recorded execution, not a score of zero.
- Independent plugin-worker checks reported 46 Linux tests passing, real HTTP cancellation, and a live two-child PONG/PING probe. These are source-reported implementation evidence, not scored matrix rows.

Read the generated `primary`, `smoke`, and `pilot` arrays separately. Counts and results must be regenerated after the parent closes the runs. Each row in those arrays is a family-size-arm-root aggregate, never a task execution.

| Snapshot cohort | Observed | Collection valid | Collection invalid | Provisional interpretation |
|---|---:|---:|---:|---|
| Library primary | 34 of 300 scheduled | 28 | 6 | Provisional; 266 missing, no audited protocol outcomes |
| Corrected normal CLI smoke | 5 | 5 | 0 | Five scores of 1.0, insufficient task clusters for CIs |
| Thinking-off CLI smoke | 5 | 2 | 3 | Failed gate; invalid scores null, no meaningful CI |
| Library thinking-off smoke | 5 | 5 | 0 | Five scores of 1.0, insufficient task clusters for CIs |
| Interrupted pilot | 14 | 9 | 5 | Exploratory only, see separate aggregate groups |

Snapshot captured at `2026-11-14T21:18:21Z` UTC. This table describes the persisted rows read during aggregation, not a synchronized view of the live controllers. Collection remains `ongoing`. The parent must update it together with `data/summary.json`.

## Paper-reported comparison, not our measurements

Source: [arXiv:2512.24601v1, Table 1](https://arxiv.org/html/2512.24601v1). Percent scale. OOLONG is a graded score and Pairs is F1, not accuracy. A star indicates the paper encountered an input context limit; it does not specify our head-truncation policy.

| Source model and method | CodeQA | BrowseComp+ 1K | OOLONG | OOLONG-Pairs |
|---|---:|---:|---:|---:|
| Paper Qwen3-Coder-480B base | 20.00* | 0.00* | 36.00 | 0.06 |
| Paper Qwen3-Coder-480B CodeAct + BM25 | 24.00* | 12.66 | 38.00 | 0.28 |
| Paper Qwen3-Coder-480B summary | 50.00 | 38.00 | 44.06 | 0.31 |
| Paper Qwen3-Coder-480B RLM | 56.00 | 44.66 | 48.00 | 23.11 |
| Paper Qwen3-Coder-480B RLM without subcalls | 66.00 | 46.00 | 43.50 | 17.34 |
| This study, Nemotron root and Lightning child | Ongoing | Blocked | Ongoing | Ongoing |

Our JSON scores use the 0 to 1 scale. Multiply by 100 only for presentation. The paper's table uses CodeQA inputs of 23K to 4.2M tokens, BrowseComp+ inputs of 6M to 11M, OOLONG at 131K, and Pairs at 32K. Our available sizes and task selection differ. These are not matched-model comparisons. No OpenAI-family model was run. Exact S-NIAH chart values were not recovered and are not fabricated here.

## Reproduce aggregates

Run from this study directory. Supply private input locations through shell variables. Do not copy raw inputs into the repository.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 summarize.py \
  --raw "$PRIMARY_SEMANTIC" "$PRIMARY_CODEQA" "$PRIMARY_LOCAL" "$PRIMARY_SNIAH" \
  --tasks "$FROZEN_TASKS" \
  --smoke "$NORMAL_SMOKE" "$THINKING_OFF_SMOKE" "$LIBRARY_SMOKE" \
  --pilot "$PILOT_SEMANTIC" "$PILOT_CODEQA" "$PILOT_LOCAL" "$PILOT_SNIAH" \
  --out data/summary.json
PYTHONDONTWRITEBYTECODE=1 python3 summarize.py --check data/summary.json
PYTHONDONTWRITEBYTECODE=1 python3 check_public.py
```

Use only existing completed JSONL files in an invocation. Omit unavailable primary paths rather than creating empty evidence. Without `--raw`, the CLI emits the frozen schedule with zero observations. `--tasks` checks identities against the private 20-task manifest without opening context files. Omit `--smoke` to exclude smoke entirely. Optional `--pilot` accepts the four legacy pilot files and writes a separate exploratory table.

The primary filename contract accepts only `matrix-v2-semantic.jsonl`, `matrix-v2-codeqa.jsonl`, `matrix-v2-local.jsonl`, and `matrix-v2-sniah.jsonl`. Primary rows must carry `disable_thinking: true`. Smoke accepts the corrected normal CLI `smoke.jsonl`, failed thinking-off CLI `matrix-v2-smoke.jsonl`, and passing `matrix-v2-smoke-library.jsonl`. The library cohort is `library-thinking-off-smoke`; earlier broken smokes are excluded. Pilot accepts only the four legacy `matrix-*.jsonl` names. These basenames select cohorts; no input path appears in the output.

Default collection status remains `ongoing`, even if every execution has arrived. Only after stopping collection, the parent can rerun the same command with `--closed`. It labels all 300 scheduled observations per root `bounded_complete`, including invalid executions, or `partial` when observations are missing. Neither status means full paper replication or all-valid success.

Mixed primary source hashes, `hermes_ingress`, `hermes_client_sha256`, or budgets for the same root fail closed. Summarize different snapshots separately. Duplicate task-arm-repeat rows fail rather than inflate counts. Malformed JSONL fails rather than silently skip evidence. Successful retries and invalid executions retain known usage.

## Require strict post-adjudication before publication

The current snapshot remains unchanged in coverage, scores, and collection status. Its new adherence counts are `protocol_unknown = observed`, with zero claimed adherent outcomes. No completed audited primary result is published here. The initial bulk audit timed out under its nine-second limit and encountered a locked ledger, producing no completed output. A bounded closed-smoke diagnostic is parent-owned and is not a completed primary audit.

The evaluator-side `bench/audit_results.py` preserves private `collection_*` fields and adjudicates frozen copies, without modifying live controllers or collection files. Hermes strict scores come only from the host-validated FINAL and citations linked to real transcript tool results. Incomplete, interrupted, failed, or budget-exhausted conversations and plugin child error/cancel outcomes are invalid. Recovered physical 400/429 attempts do not invalidate an otherwise successful logical plugin call. Base outcomes stay unchanged. Nano remains an explicit reference deviation without the host-FINAL requirement; a non-200 child attempt with unknown recovery is conservatively invalid.

After the parent completes auditing, set the primary variables to the audited files with the same basenames. Add `--require-audit` to the aggregation command above. This requires `audit_version: paper-strict-v1` and a typed auditor digest for every primary row, records `audit_policy: paper_strict_v1`, and rejects unaudited or mixed primary inputs. Without the flag, audited primary input is rejected. Historical smoke and pilot inputs can remain collection evidence in their separate cohorts. Only add `--closed` after collection stops. Audit policy and collection-closure status are independent.

Group fields `collection_valid` and `collection_invalid` preserve the original denominator. Strict `valid`, `invalid`, scores, and eligible task-cluster CIs use adjudicated rows. Four typed adherence counts partition observed rows: `protocol_adherent`, `protocol_nonadherent`, `protocol_unknown`, and `protocol_not_applicable`. Base and the explicitly declared nano reference deviation are not applicable after audit, never counted as adherent. No reason strings, transcript evidence, or raw `collection_*` answers enter the public JSON.

The parent has staged FINAL/child-outcome gate fixes and reports 59 gate checks plus 13 auditor tests. Those changes were not applied to the running controllers and were not measured by this matrix. The measured source remains benchmark commit `1091847` with plugin commit `184f736`. A future auditor commit and any patched-run source pins require parent updates before publication. A post-hoc audit is not a rerun with the staged fix.

## Reuse the upstream runner

`reproduce.sh` delegates to `bench/paper_tasks.py` or `bench/paper_matrix.py` in `HERMES_RLM_SOURCE`. It does not implement a second runner or scorer. Configure the environment variables named by the wrapper. Keep task manifests, output files, fresh homes, and contexts outside this checkout.

```sh
bash reproduce.sh prepare --reference "$REFERENCE" --legacy "$LEGACY_CORPORA" --out "$TASK_OUTPUT"
bash reproduce.sh smoke --dry-run
bash reproduce.sh matrix --dry-run
```

Remove `--dry-run` only in the parent-controlled credential and compute environment. The matrix wrapper uses all five arms and three repeats. The smoke wrapper selects one smallest S-NIAH task and one repeat. The upstream scheduler rotates arm order. Extra CLI arguments can override budgets, so review the row-recorded protocol before comparing results. Preparation defaults to the bounded sources; large extraction remains an off-host operation.

## Verify without model calls

```sh
timeout 9s env PYTHONDONTWRITEBYTECODE=1 python3 test_summarize.py
bash -n reproduce.sh
PYTHONDONTWRITEBYTECODE=1 python3 check_public.py
```

From the repository root, run `python3 scripts/validate.py` for manifest schema and artifact checks. No command above runs inference. All Python code here uses the standard library. The repository validator additionally requires its existing YAML and JSON Schema dependencies.

The manifest pins benchmark commit `10918473fbb90d04af08221725baa671369fb31e` and plugin implementation commit `184f7367465601f6e190fdff1bcd091903bef8ad`. The measured top-level production Python hash is unchanged; plugin tests are outside that hash. Frozen publication still needs parent-controlled closure, final coverage review, aggregate regeneration, and artifact hashes.

The wrapper explicitly selects `--hermes-ingress library`. It calls the selected source's real `AIAgent`; plugin discovery, tool-definition assembly, dispatch, and auxiliary model calls remain Hermes-owned. It avoids starting a gateway for each fresh home. CLI evidence is retained separately, not retroactively rewritten as library evidence.

Provider accounting retains physical HTTP 400 retries and HTTP 429 backoff. Reported-known usage is partial where failed requests omit counts. The shared cap is 2700 attempts per provider; four external probe calls also require parent accounting and headroom. The optional Qwen Groq root is blocked by HTTP 403, not a completed second-root comparison. Cross-family static review is not presented as a passing verification gate.
