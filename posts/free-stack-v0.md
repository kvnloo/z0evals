---
title: "the free stack every contributor already has"
subtitle: "17 free llm lanes, used all at once: 149 small tasks in 1.4 s. a case study in speeding up open-source work."
study: free-stack-v0
status: evidence-local
author: "zer0 research"
date: "november 2, 2026"
mock_data: false
toc:
  - id: signup
    label: get every key in ten minutes
  - id: menu
    label: the menu
  - id: roles
    label: match the job to the lane
  - id: burst
    label: everything at once
  - id: router
    label: one endpoint for all of it
  - id: oss
    label: why open source can use all of it
  - id: gap
    label: what an orchestrator is missing
  - id: limits
    label: what this does not prove
---

most people who contribute to open source have free llm api access they never use: groq, openrouter `:free`, nvidia nim, google ai studio, vercel ai gateway, nous portal, and often a cerebras trial. each lane alone is small. we put all of them in parallel and gave each model the work its speed suits. on november 2, 2026, that did **149 small tasks in 1.44 s** and **40 ~250-word answers in 2.26 s**. one at a time, the same 149 calls take 54.6 s.

the models are fast enough now. what slows agent work down is orchestration. this post is the evidence, the recipe, and the gap we are asking coding-agent tools to close ([pingdotgg/t3code#29886](https://github.com/pingdotgg/t3code/discussions/29886)).

## get every key in ten minutes {#signup}

every provider below has a web sign-up, most with github or google sign-in. creating each key is a few clicks and a paste. one script opens every key page, takes the pasted keys without echoing them, checks each one, and saves them to `~/.config/free-stack/keys.env` (mode 600):

```bash
curl -fsSLO https://raw.githubusercontent.com/kvnloo/z0evals/main/studies/free-stack-v0/scripts/onboard.py
python3 onboard.py --open-all     # opens every key page; paste each key when asked
python3 onboard.py --check        # which keys work, how many models each can see
python3 onboard.py --export opencode > free-providers.json   # opencode provider entries for nim, vercel, nous
```

| provider | key page | what is free |
|---|---|---|
| groq | [console.groq.com/keys](https://console.groq.com/keys) | free tier, limits per model (e.g. 30 rpm / 8k tpm) |
| openrouter | [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys) | `:free` models; the daily cap rises after a one-time $10 credit purchase |
| nvidia nim | [build.nvidia.com](https://build.nvidia.com/settings/api-keys) | developer program, ~40 rpm, prototyping only |
| google ai studio | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | free tier; prompts may be used to improve products |
| vercel ai gateway | [vercel ai keys](https://vercel.com/d?to=%2F%5Bteam%5D%2F%7E%2Fai%2Fapi-keys) | monthly credit for unpaid teams, free-eligible models |
| nous portal | [portal.nousresearch.com](https://portal.nousresearch.com/) | free plan: free models only, 50 rpm / 500k tpm |
| cerebras | [cloud.cerebras.ai](https://cloud.cerebras.ai/) | trial credit, not a permanent free tier (optional) |
| opencode zen | [opencode.ai/auth](https://opencode.ai/auth) | rotating `-free` models, also keyless inside the opencode cli |

the script cannot click through sign-up for you, and it should not: email confirmation, captchas and terms belong to the person who owns the account. one account per provider; multiplying free tiers breaks most providers' terms.

## the menu {#menu}

each free route, called directly with streaming ([data](https://github.com/kvnloo/z0evals/blob/main/studies/free-stack-v0/data/menu.json)). ttft is the time to the first token on a one-word prompt; tok/s is output speed on a ~400-word answer, first to last token.

| provider | model | ttft | tok/s | billing |
|---|---|---|---|---|
| cerebras | qwen-3.8-27b | 0.17 s | 2,015 | trial credit |
| cerebras | gpt-oss-120b | 0.21 s | 1,669 | trial credit |
| groq | gpt-oss-20b | 0.34 s | 895 | free |
| groq | qwen3.8-27b | 0.20 s | 502 | free |
| groq | gpt-oss-120b | 0.20 s | 486 | free |
| vercel | nemotron-3.5-lightning-free | 0.51 s | 313 | free credit |
| google | gemini-3.5-flash-lite | 0.57 s | 310 | free (may train) |
| openrouter | nemotron-3.5-super-vl:free | 0.47 s | 147 | free |
| nim | nemotron-3.5-lightning-30b-a3b | 0.30 s | 117 | free (dev program) |
| nim | nemotron-3.5-super-vl-120b-a12b | 0.42 s | 115 | free (dev program) |
| vercel | ling-3.1-flash-1019 | 0.99 s | 108 | free credit |
| openrouter | dots-3-note-preview:free | 0.62 s | 98 | free |
| openrouter | nemotron-3.5-lightning:free | 0.38 s | 96 | free |
| openrouter | north-mini-code:free | 0.28 s | 77 | free |
| openrouter | nemotron-3-ultra-550b-a55b:free | 0.51 s | 59 | free |
| nim | nemotron-3-ultra-550b-a55b | 0.72 s | 34 | free (dev program) |
| openrouter | xing4.0-29b-a4b:free | 0.29 s | 32 | free |

every lane starts in under a second. what separates them is output speed, from 2,000 tok/s down to 32.

six more routes did not answer that night: opencode zen free (free usage limit), openrouter gemma-4 (429), inkling-small (403, harness-only), vercel beam-free (403, paid only) and nim step-5-preview (timeout). we could not test nous portal or opencode go because our own logins had expired. free routes come and go, so anything built on them has to probe first.

## match the job to the lane {#roles}

| role | lanes | job | why |
|---|---|---|---|
| sprinters | ttft < 0.6 s, ≥ 300 tok/s | fan-out of small tasks, drafts, bulk text | fast start and fast output. spread load by each model's rate limit. |
| checkers | ttft < 1 s, 60–300 tok/s | pass/fail verdicts, racing | a short answer costs ttft, not tok/s. a lane from another provider gives an independent check. |
| racing | two checkers on different providers | keep the first good answer | free lanes are noisy: one nim model took 2.8 s to 12.6 s across five races. |
| long thinkers | < 60 tok/s | background jobs nobody waits on | free quality, as long as nobody is waiting on it. |

## everything at once {#burst}

one burst, 15 lanes, 6 providers ([summary](https://github.com/kvnloo/z0evals/blob/main/studies/free-stack-v0/data/orchestra-summary.json), [calls](https://github.com/kvnloo/z0evals/blob/main/studies/free-stack-v0/data/orchestra.jsonl)):

| pattern | ok | wall time | result |
|---|---|---|---|
| fan-out: 150 one-word classifications | 149 / 150 | **1.44 s** (0.25 s median per call) | 5,387 tok/s; 54.6 s if run one at a time |
| bulk: 40 ~250-word explanations | 38 / 40 | **2.26 s** | 36,141 tokens, about 16,000 tok/s |
| draft → check | 7 drafts, 6 checks | drafts 0.3–2.5 s, checks 6–32 s | 2 drafts failed on substance, 2 passed, 1 check caught an empty draft, 1 checker spent its whole budget reasoning |
| racing ([data](https://github.com/kvnloo/z0evals/blob/main/studies/free-stack-v0/data/hedge.jsonl)) | 12 / 12 | first good answer: ~0.7 s median | waiting for both: ~5 s median, 12.6 s worst |
| background (nemotron ultra 550b) | 2 / 3 | 81 s and 150 s | long answers while everything else finished |

across the fan-out, bulk and draft calls, 194 calls returned about 49,000 tokens in 3.6 s.

about 97% of the bulk tokens came from cerebras, which is trial credit. groq is truly free but allows 8k tokens per minute per model, so its share of long answers stays small. each lane's limits have to drive the plan.

## one endpoint for all of it {#router}

we run the lanes behind one openai-compatible endpoint, [vllm semantic router](https://github.com/vllm-project/semantic-router), on a small k3s cluster. it falls back on 413/429/5xx and exposes one virtual model per goal: `turbo`, `free-quality`, `free-reasoning`, `free-verify`, `free-longctx`, `free-public`. through it, 60 small calls went from 13–18 s one at a time to 1.2 s at 20 in flight, and 200 calls at 50 in flight all succeeded, 39 of them rescued by fallback after groq 429s ([router runs](https://github.com/kvnloo/z0evals/tree/main/studies/free-stack-v0/data/router)). a re-run on the evening of november 2 took 7.7 s instead of 1.2 s, because groq's free buckets throttled the burst. that is why the next step is placement by remaining capacity rather than random choice.

our downstream work, all public:

- [z0intelligence#289](https://github.com/kvnloo/z0intelligence/pull/289): the router deploy, profiles, fan-out bench and rate-limit inventory. roadmap epic [#296](https://github.com/kvnloo/z0intelligence/issues/296), phases [#290](https://github.com/kvnloo/z0intelligence/issues/290) to [#295](https://github.com/kvnloo/z0intelligence/issues/295).
- [z0intelligence#176](https://github.com/kvnloo/z0intelligence/pull/176) and rfc [#175](https://github.com/kvnloo/z0intelligence/issues/175): the turbo runtime, a planner with fast workers and an independent verifier.
- [kerdoios#69](https://github.com/kvnloo/kerdoios/pull/69) and [#64](https://github.com/kvnloo/kerdoios/pull/64): the placement objective and live free-tier inventory that will pick the lane.
- [kvnloo/semantic-router](https://github.com/kvnloo/semantic-router): our fork, for upstream fixes such as tolerating cerebras' extra response fields.

## why open source can use all of it {#oss}

some free tiers may train on your prompts. for most work in a public repository that does not matter: the code, the issues and the diffs are already public. a turbo mode for open-source work can use every free lane without a privacy trade-off, as long as it keeps secrets out. `.env` files, tokens and private repositories stay on paid routes.

that is the case for the study: every contributor gets a large pool of free, fast capacity for the small, checkable calls agents make all day.

## what an orchestrator is missing {#gap}

we tried this in [t3 code](https://github.com/pingdotgg/t3code), which already lets a coordinator delegate to an opencode provider with groq or cerebras keys. a delegated task on cerebras gpt-oss-120b finished end to end in 4.0 s. three things stop it from going further:

1. **agent-sized prompts don't fit free tiers.** the same delegation to groq free failed with `tpm: limit 8000, requested 16772`. the child agent's own prompt is twice the budget. free lanes suit small calls without tools; a delegation starts a full agent.
2. **nothing fans out.** in a matched a/b, a coordinator with fast helpers saved 4–5% of wall time, because the helpers never ran at the same time ([z0intelligence#176](https://github.com/kvnloo/z0intelligence/pull/176)).
3. **the coordinator cannot see limits.** spreading load by remaining capacity is what stops 429 cascades.

other tools are working on the same idea: [claude-code-router](https://github.com/musistudio/claude-code-router) sends background and subagent calls to cheap providers, [claude-code-multirouter](https://github.com/daviddawson/claude-code-multirouter) keeps opus for the main session and sends subagents to cerebras, and cognition runs its parallel code-search subagent on cerebras ([case study](https://www.cerebras.ai/blog/case-study-cognition-x-cerebras)).

## what this does not prove {#limits}

- single runs on one evening. free capacity is shared and changes by the hour.
- cerebras is trial credit and carried most of the bulk tokens.
- token counts include reasoning tokens.
- the tasks are easy and checkable: classification, explanations, verdicts. this is not a quality ranking and shows nothing about code edits.
- nous portal and opencode go were not measured.

study files, scripts and pinned sources: [studies/free-stack-v0](https://github.com/kvnloo/z0evals/tree/main/studies/free-stack-v0).
