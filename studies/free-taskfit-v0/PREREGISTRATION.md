# free-taskfit-v0 — preregistration

**Question.** For each free model lane and each task family the router serves (extract, classify, format, reason, verify, longctx), what share of calls returns an answer the frozen grader accepts? That share is O14's `p_accept[u, task_class]` prior for that lane.

**Frozen task set.** `frozen/tasks.py`, byte-identical to kvnloo/z0intelligence `deploy/vllm-sr/profiles/tasks.py` @ f12b926e (PR #289), sha256 `119209b5c61d07c8ebf109aeb995b778e58fc0cd49ec6f04fa90df4b90ed987b`. 20 deterministic, auto-graded, non-code tasks: 12 easy, 8 hard. Per family: reason 7, extract 3, format 3, verify 3, longctx 3 (8k/32k needles), classify 1. If the sibling factory battery (STUDY-HANDOFF.md with its own task-set sha256) replaces this set, it becomes `free-taskfit-v1` with its own pin; this study's numbers are never relabelled.

**Lanes.** Free routes only: Groq free plan, NVIDIA NIM free, OpenRouter `:free` (max_price 0, no fallbacks). Refused: Cerebras (trial credit) and the Gemini API (owner rule). The deployed router virtual models (`router/vllm-sr/<profile>`) may be run as their own arms.

**Protocol.** Streaming, temperature 0, `max_tokens` 4096, one worker per lane, per-provider gap inside published RPM, repeats ≥ 2. Every call is a trial: HTTP error, timeout or empty content counts as not accepted, because that is what the router sees.

**Grading authority.** `scripts/certify.py` re-grades every row from its full answer text with the frozen graders, rejects rows from another task set or without full text, and reports how often the runner's own flag disagreed. The runner's `correct` field is never trusted.

**Output.** One `z0eval.result.v1` receipt per run, verdict `PARTIAL` (a measured prior, not a promotion). Findings:
- `model.routing.acceptance` / task `taskfit.<family>` / job `ShadowEvals`: `acceptance_rate`, accepted/n, Wilson 95% CI, `acceptance_kind: rubric_draft_quality`, `evidence_kind: proxy`, `promotion_eligible: false`.
- `model.routing.performance` / task `taskfit.all`: `ttft_p50_ms` and decode `tokens_per_second` (median, min/max carried in the CI fields with `ci_method: none`).
Findings expire 14 days after the last row, because free routes rot.

**Consumer.** z0intelligence ingests the receipt unchanged (`z0int policy ingest`, source kind `z0eval_result`) and its model-routing catalog generator sets `models[].task_classes[taskfit.<family>].p_accept` and fills unknown `performance` fields. Kerdoios `plan_routing` (O14, kerdoios#69) then scores a lane once burn, remaining and reset are also known. z0evals never routes.

**Known limits, stated before running.** n per family is tasks × repeats (classify: 1 task), so one task moves a family by a lot; treat gaps under one task's weight as ties. Free capacity is shared and changes by the hour. Client-side TTFT includes network RTT from the measuring host. Decode tok/s on short answers understates sustained throughput and includes reasoning tokens.
