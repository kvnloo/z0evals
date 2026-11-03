# Harvesting experiments into the log

The research log should list every experiment we ran or designed, not only the ones that became studies. Experiments are scattered across private operation folders and issues in many repos, so we harvest them in batches. Each batch goes through three tiers of scrutiny, and each tier is cheaper than the one after it.

| tier | who | reads | decides |
|---|---|---|---|
| 1. screen | Claude Haiku 5.5 | a capped digest of each candidate: its file list and the head of each report | experiment, proposal, tooling, idea or noise; area and techniques; whether it duplicates an existing entry; which files hold the evidence. It copies numbers word for word and never judges them. |
| 2. scrutiny | Claude Sonnet 5.5 | the real evidence files (up to 30 KB), or the full issue thread | accept, revise or reject. Every number it keeps must be quoted with the file it came from. It separates what was measured from what was planned, and rewrites the entry in public form. |
| 3. gates and audit | a script, then Claude Opus 5.5 | the tier-2 output | Two gates run without a model: each number in the public text must appear in the evidence, and no private token (path, host name, device nickname, address) may appear. Opus then reads every gate failure and a sample of accepted entries against their evidence, rejects anything off-mission or personal, and flags the entries worth reading first. |

## What counts as research

An entry needs a question about speed, cost, quality, reliability or method. It also needs a measurement that answers that question, or a design for one, with a baseline, a comparison or an explicit pass or fail rule. A negative result counts.

The following are not research, and tier 2 rejects them:

- bug fixes and feature delivery checked by tests or CI
- one-host incident postmortems
- inventories, migrations and status reports

Run folders from one experiment (for example one folder per commit) become a single entry.

## Statuses

Harvested entries use one of these statuses:

| status | meaning |
|---|---|
| `frozen-internal` | measured; the evidence stays private, so the entry has no link to it |
| `in-progress` | partly run |
| `proposal` | designed but not run |

Issues in public repos are linked. Private evidence is described, not linked.

## Batch of 2026-11-03

All three tiers produced valid output from the model they asked for.

| step | count |
|---|---|
| candidates (operation folders plus experiment issues across our repos) | 260 |
| screened by Haiku (13 already in the log) | 260 |
| scrutinized by Sonnet (one per run-folder family) | 146 |
| rejected by Sonnet (mostly QA receipts and chores) | 31 |
| failed a mechanical gate | 1 |
| rejected in the Opus audit (personal, incident or duplicate) | 15 |
| added to the log | 99 |

The added entries break down as follows:

| status | entries |
|---|---|
| `frozen-internal` (measured) | 39 |
| `in-progress` | 15 |
| `proposal` | 45 |

The screen cost about $0.48 and scrutiny about $5.66, both at list price on a subscription.

Open limits:

- Tier 1 can miss an experiment whose digest hides its results.
- Tier 2 checks numbers against evidence, but it does not rerun anything. A `frozen-internal` entry is only as good as the private report behind it.
- Promoting an entry to a frozen study still needs its own artifacts and manifest.
