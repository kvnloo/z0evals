# free-taskfit-v0

Measures how often each free model lane gets a router task family right, so O14 (`score = latency × (1 + λ·pace) / p_accept`) has a measured `p_accept` instead of "unknown". Protocol: [PREREGISTRATION.md](PREREGISTRATION.md).

```
run_taskfit.py  (free lanes, frozen tasks, full answer text)  -> data/runs/<run>/rows.jsonl
certify.py      (re-grade with frozen graders, Wilson CIs)    -> data/runs/<run>/result.json  (z0eval.result.v1)
z0int policy ingest  (source kind z0eval_result)               -> findings ledger
generate_catalog.py  --findings <ledger>                       -> models[].task_classes[taskfit.*].p_accept
                                                                  models[].performance.{ttft_p50_ms,tokens_per_second}
kerdoios plan_routing (O14)                                    -> ranks lanes once burn/remaining/reset are known too
```

z0evals owns the frozen task set and the grading. z0intelligence consumes the certified receipt; Kerdoios owns the objective. Nothing here routes traffic.

## Pilot, 2026-11-03 (rows.jsonl, 160 calls, 4 lanes × 20 tasks × 2 repeats, 20:39–20:48 UTC)

| lane | extract | classify | format | reason | verify | longctx | TTFT p50 | decode tok/s p50 |
|---|---|---|---|---|---|---|---|---|
| groq openai/gpt-oss-20b | 6/6 | 2/2 | 6/6 | 14/14 | 6/6 | **1/6** | 303 ms | 888 |
| groq openai/gpt-oss-120b | 6/6 | 2/2 | 6/6 | 14/14 | 6/6 | **1/6** | 287 ms | 483 |
| openrouter nvidia/nemotron-3.5-super-vl:free | 6/6 | 2/2 | 6/6 | 14/14 | 6/6 | 6/6 | 452 ms | 227 |
| nvidia (NIM) nemotron-3-ultra-550b-a55b | 6/6 | 2/2 | 5/6 | 10/14 | 3/6 | 4/6 | 615 ms | 84 |

What limits these numbers: every non-accepted call was a transport failure, not a wrong answer. Groq's free plan returned 413 on the 32k-token needle tasks (8K TPM per model) and one 429 on needle-8k; NIM returned ten 429s at a 2 s request gap. All 140 answered rows were re-graded from their full text and the runner's own flag disagreed on none. So in this pilot `p_accept` is "did the route answer and was it right", dominated by the first half. The easy tier saturates; the hard tier has 8 tasks.

Fed through z0int's ingest and catalog generator and then Kerdoios `plan_routing`, these priors change the longctx order: with the pace term held neutral, OpenRouter nemotron ranks first and both Groq lanes last, because a 1/6 acceptance multiplies their latency term by 6. Without burn/remaining/reset (Kerdoios capacity), every lane is still unscored.
