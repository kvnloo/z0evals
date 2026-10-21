# harness-speed-v1

Same model (`gpt-6.1-sol`, effort low, ChatGPT subscription), four coding-agent harnesses:
Hermes, fx (libfx engine), pi, omp. One variable changes per comparison. Preregistered in
[`protocol.md`](protocol.md); results in [`analysis/summary.md`](analysis/summary.md); write-up in
[`posts/harness-speed-v1.md`](../../posts/harness-speed-v1.md).

| path | what |
| --- | --- |
| `protocol.md` | design, arms, workloads, analysis rules, amendments (all committed before the runs they govern) |
| `manifest.yaml` | pinned harness versions, SHAs and hashes, host |
| `tasks/` | 8 coding tasks: `repo/` (agent-visible, with visible tests), `hidden/` (verifier-only tests), `reference/` (solution used only to validate the verifier), `prompt.txt` |
| `harness/bench.py` | cold runner (latency + tasks), exact argv per arm in `arm_cmd()` |
| `harness/warm.py` | warm runner (pi/omp `--mode rpc`, fx `--serve`) |
| `harness/fx_run.ts` | libfx driver for the fx arm (four host tools) |
| `harness/verify.py` | independent task verifier |
| `harness/analyze.py` | medians, bootstrap CIs, Wilson intervals, planned contrasts |
| `harness/run_s1.sh`, `run_s2.sh`, `env.sh` | the exact session scripts run on the MBP |
| `data/s1`, `data/s2` | raw rows (JSONL) and runner logs; `data/s0-aborted` kept, not analysed |
| `analysis/` | `summary.json`, `summary.md` |

Reproduce on a host with all four harnesses signed in: copy `harness/` and `tasks/` to
`~/.cache/harness-speed-v1/`, install `libfx@0.0.14` in `~/.cache/harness-speed-v1/fx/` with
`fx_run.ts` next to it, then run `harness/run_s1.sh` under `harness/env.sh`.
