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

## Known limits are enforced, not remembered

`frozen/limits.json` (built by `scripts/freeze_limits.py` from z0intelligence `deploy/vllm-sr/limits.json` + `profiles/catalog.json` at a pinned commit) is the only place limits live. `scripts/plan_taskfit.py` estimates every request as `ceil(len(prompt)/3.5) + max_tokens` (max_tokens floored at 4096 for reasoning models) and plans out any (task, lane) above the lane's TPM, context or max request size, and anything past its daily RPD/TPD budget. `run_taskfit.py` writes those as `not_eligible:<reason>` and never sends them, stops a lane on a daily-quota 429 or on a 413, and skips (lane, family) pairs already measured in an unexpired committed receipt unless `--force`. `certify.py` keeps `not_eligible` and quota-stopped rows out of every p_accept denominator (reported under `evidence.not_eligible`) and fails any run that contains a 413 or a sent row the limits rule out.

Run it in GitHub Actions, not on groot: `scripts/dispatch_taskfit.sh` (repo root) triggers `.github/workflows/free-taskfit.yml` and downloads rows + receipt into `data/runs/<run>/`.

## Pilot, 2026-11-03: withdrawn

The pilot (rows.jsonl, 160 calls, 4 lanes × 20 tasks × 2 repeats) sent the 8k/32k/multi-needle tasks to Groq gpt-oss-20b/120b, whose free plan allows 8K tokens per minute per model. Eight came back 413 and two 429; the receipt counted them as wrong answers and reported Groq longctx as 1/6. That number measured our request sizing, not the models. `python3 scripts/plan_taskfit.py --rows data/runs/pilot-20261103/rows.jsonl` lists the 12 rows the frozen limits rule out, and `certify.py` now refuses the run. The receipt is deleted; rows.jsonl stays as the record of the mistake.
