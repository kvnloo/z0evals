# Research areas and techniques

The log has two facets. **Area** is the system or field under study (one per entry).
**Techniques** are how an entry tries to make it better (any number, log entries only).

Every post and research-log entry has one `area`. The list lives in `web/lib/areas.ts`, and
`scripts/build_posts.py` (`AREAS`) must match it; `tests/test_build_posts.py` checks both and
every log entry.

## Pick the system under test first

| area | label | use it when the thing being measured is… | examples |
|---|---|---|---|
| `hermes` | hermes & harnesses | an agent harness or coding-agent app: Hermes, Claude Code, OMP, Unii, T3 Code. Speed, cost, compaction, voice, the agent loop. | harness-speed-v1, claude-code-savings, voice-omp-parity, turbo-app-fanout |
| `small-models` | small models & routing | which model or provider handles a decision: local SLMs, routing, quota, offload. | slm-router-v0, z0intelligence-function-routing, offload-and-loop, local-cognition-* |
| `generative-ui` | generative ui | an interface an LLM generates: answer formats, renderers, tokens and validity. | genui-openui-vs-html-v0 |
| `device-use` | phone & computer use | an agent driving a phone, a desktop or the web. | cua-trycua, z0live-phone-control, noop-hermes-agent-api, android-* |
| `applied-math` | applied math | a new mathematical result moved into (or ruled out of) a real OSS hot path. | math372-transfer, math372-openroad-kmedian |

## Otherwise, the cross-cutting areas

| area | label | use it for |
|---|---|---|
| `memory` | memory | what agents remember and whether it is still true, across harnesses |
| `governance` | laws & governance | statecharts, Bend/AODL laws, authority and admission rules |
| `fleet` | fleet | placement, capacity and the machines underneath |
| `research` | papers & ideas | syntheses, architecture notes and ideas nothing has measured yet |

Rules of thumb:

- A study that compares models *inside* one product goes to the product (an Android driver LLM vs
  SLM study is `device-use`); a study about *choosing* the model is `small-models`.
- Memory work stays in `memory` even when it runs in Hermes: it spans every harness.
- Add a new area only when a product gets its own line of studies (two or more), not for one post.
  Update `areas.ts`, `build_posts.py` and this table together.

## Techniques

`web/lib/techniques.ts` holds the list and `build_posts.py` `TECHNIQUES` must match it.
Tag what the experiment changes, not what it measures with, unless the method itself is the
contribution (`measurement`).

| technique | label | the experiment tries to… |
|---|---|---|
| `output-format` | output format | make the model write less (openui boards instead of html pages) |
| `context-reduction` | context reduction | send the model less: compaction, state packets, distilled corrections |
| `model-routing` | model routing | pick the cheapest model good enough per decision or task |
| `local-inference` | local inference | tune engines, quantization and devices for our own hardware |
| `caching-reuse` | caching & reuse | keep and reuse work: warm processes, prefix caches, copy-on-write workspaces |
| `scheduling` | scheduling & placement | decide where and when work runs: admission, fleets, fan-out, pacing |
| `algorithmic` | algorithms & math | apply a new algorithm or proved result to a hot path |
| `search-optimization` | search & autoresearch | search prompts, programs or configs with measured keep-or-revert loops |
| `formal-methods` | formal methods | prove laws, compile statecharts, fail closed |
| `measurement` | measurement method | change how we measure: ledgers, replays, referees, judges |

## Where things live

```text
studies/<study-id>/   frozen evidence: manifest.yaml, README.md, data/, scripts/
posts/<slug>.md       the write-up; frontmatter `study:` points at the study, `area:` files it
web/data/research-log.json   one entry per eval, experiment or idea; `area`, `post` link
imports/              pinned, allowlisted import specs for private sources
```

Study ids name the product and the question, then a version: `genui-openui-vs-html-v0`,
`harness-speed-v1`, `slm-router-v0`.
