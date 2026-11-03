# Free stack v0

Run `free-stack-20261102T2148`, Nov 2 2026. Every free LLM API lane we could reach, measured one by one and then used all at once. Write-up: [`posts/free-stack-v0.md`](../../posts/free-stack-v0.md). Upstream discussion: [pingdotgg/t3code#29886](https://github.com/pingdotgg/t3code/discussions/29886).

## Reproduce

```bash
python3 scripts/onboard.py --open-all          # get the keys: opens every key page, you paste, it checks
set -a; . ~/.config/free-stack/keys.env; set +a
python3 scripts/free_stack.py out/             # speed table, 61 s pause, then everything at once
python3 scripts/free_stack.py out2/ out/menu.json   # all-at-once again, reusing the speed table
```

Standard library only. Lanes without a key fail their probe and are left out of the plan.

## Files

| File | What it is |
|---|---|
| `data/menu.json` | Per-lane TTFT (one-word prompt) and output tok/s (~400-word answer), 23 lanes, 17 answered |
| `data/orchestra.jsonl`, `data/orchestra-summary.json` | All-at-once run: 220 calls, 15 lanes, 6 providers |
| `data/hedge.jsonl` | Racing two lanes on one question: time to first good answer vs time for both |
| `data/speed-probe.jsonl` | Groq and Cerebras repeat probe, 3 runs per model |
| `data/router/*.jsonl` | Fan-out through vLLM Semantic Router: 60 calls at 20 in flight (twice) and 200 calls at 50 in flight |

Answers are trimmed to 200 characters. Provider account ids in error messages are redacted.

## What it does not show

- Single runs. Free capacity is shared and changes by the hour.
- Cerebras is trial credit, not a free tier, and served about 97% of the bulk-pattern tokens.
- Token counts include reasoning tokens for reasoning models.
- Only easy, checkable tasks (classification, explanations, verdicts). No code edits, no quality ranking.
- Nous Portal and OpenCode Go were not measured (expired logins on our side).
