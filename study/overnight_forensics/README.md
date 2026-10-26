# Overnight-run forensics (WP2, provisional)

A local, retrospective, **clock-only** study of agent-session completion. This
folder contains code and synthetic tests, not a public dataset. It does not
change dispatch, scheduling, promotion, resource placement, or runtime policy.
It never reads circadian state, sleep, wearable, or phone telemetry.

## Run locally

Python 3.12+ with the system IANA timezone database is sufficient. No pandas,
model downloads, remote inference, or third-party statistics packages are used.
Run from the repository root:

```sh
python3 study/overnight_forensics/extract.py
python3 study/overnight_forensics/analyze.py
uv run --no-project --with pytest python -m pytest -q study/overnight_forensics
```

To run the exact unscoped pytest command against **only this study**, use:

```sh
export PYTHONPATH="$PWD"
cd study/overnight_forensics
uv run --no-project --with pytest python -m pytest -q
```

The existing repository-wide tests require its declared dependencies:

```sh
uv run --no-project --with pytest --with-requirements requirements.txt python -m pytest -q
```

Extraction discovers the existing AgentsView database in the usual home-directory
locations and Hermes databases under `Path.home() / ".hermes"`. It never starts
AgentsView, reindexes, migrates, or calls a potentially writable export CLI.
All source SQLite connections use URI `mode=ro`, `query_only=ON`, a bounded
SQLite page cache, and a per-source read transaction. WAL/SHM presence and main
file metadata are recorded before/after; no claim is made that concurrently
running producers stopped writing or that SQLite cannot touch coordination
sidecars. Aliased Hermes database paths are resolved and deduplicated.

Optional arguments:

- `extract.py --agentsview "$AGENTSVIEW_DB"`: explicitly nominate a database.
- `extract.py --hermes-root "$HERMES_ARCHIVE_ROOT"`: choose an existing archive.
- `extract.py --kanban "$KANBAN_DB"`: nominate an existing board database.
- `extract.py --needs-owner "$NEEDS_OWNER_SNAPSHOT"`: inspect an explicitly
  nominated needs-owner JSON snapshot and adjacent matching JSON/JSONL history.
  No unrelated files or referenced ledger paths are followed.
- `extract.py --output "$PRIVATE_OUTPUT"` and
  `analyze.py --input-dir "$PRIVATE_OUTPUT"`: choose an alternate private
  directory **outside every Git worktree**. Otherwise the scripts use
  `Path.home() / ".local/state/overnight-forensics"`.

Output directories are mode `0700`; files are mode `0600`, atomically replaced.
Existing output-file symlinks are refused. Stdout contains aggregates only.
`runs.jsonl` contains derived features, hashed identities/project keys, time
anchors, source-reported signals, and label/proxy values: **no prompt, title,
message, source path, machine name, or network identifiers**. Hashes are linkage
keys, not an anonymization guarantee; keep even this derived dataset private.

Outputs:

| File | Purpose |
|---|---|
| `runs.jsonl` | Local derived session-level dataset, serialized one row at a time |
| `extraction.json` | Source availability/schema hashes, source metadata, cutoff, code commit and script/data hashes |
| `receipt.json` | Counts, known/unknown denominators, Wilson intervals, feature tables, verdicts and model status |
| `readiness_rubric.json` | Supported hard gates (possibly none), unvalidated proposals, weights or explicit null reason |
| `RECEIPT.md` | Short local summary with the four verdicts |

Analysis verifies the frozen JSONL hash before using it. Extractions are reruns
of a live corpus, not immutable copies of the source databases. The manifest
pins the study commit plus exact script hashes; no source repositories or
private worktrees are imported. Rows are streamed from SQLite, and only compact
derived records are retained in memory for sorting/aggregation. This is bounded
by the local corpus size, not a constant-memory external sort.

## Definitions fixed before observing the results

All definitions are **PROVISIONAL constants in the scripts**. Local time means
`America/Chicago`; this is not an estimate of anybody's sleep.

An overnight session either starts in `[22:00, 05:00)` and is observed active
(or has an independent native termination) at least 60 minutes after starting,
or has an observed activity interval spanning local 03:00. DST is handled using
`zoneinfo`. A session spanning several nights still contributes **one row**;
interval endpoints do not prove uninterrupted activity. Invalid/naive timestamp
strings are not assigned an invented timezone.

The unit is a session, with native Hermes exits and exact Kanban events used
for enrichment, not extra copies of those sessions. AgentsView mirrors are
preferred, deduplicated by harness/native session identity. Independent native
Hermes exit timestamps enrich exact matches; unrelated tasks are never joined
by their prose, title, project resemblance, or worker name.

### Labels and missingness

- `completed_unattended`: source success-like outcome **and** normal termination.
  AgentsView `completed`/`success`/`succeeded` plus `clean`/`normal`/`completed`
  qualifies. Native Hermes `agent_close`, `cli_close`, `cron_complete`,
  `tui_close`, and `tui_shutdown` count as normal exits **only when joined to
  a success-like source outcome**, not as proof of success on their own.
  **The requested name is only a completion surrogate**: no-owner-intervention
  negatives are unavailable, and this is not independently verified success.
- `stalled`: a known independent termination timestamp at least two hours after
  the last event, or an explicit killed/timeout/orphan-reap exit. AgentsView's
  `ended_at` is the transcript endpoint, **not** an independent process exit;
  subtracting it from last transcript activity cannot measure a silent tail.
- `needed_owner`: an exact task/session (including run-specific admission-journal)
  link with a timestamped Kanban blocked event during the session interval.
  Missing links never become negative labels. Needs-owner snapshots without
  stable session IDs **and** raised-at events cannot establish this label;
  generated-at timestamps or goal prose are not substitutes. The snapshot
  adapter reports availability only, never invents joins.
- `restarted_not_resumed`: a **project-level proxy**, not a reliable task label.
  After the earlier independent exit (or, if absent, last activity), take the
  first other same-project session starting within 12 hours. A first prompt
  without `resume`, `resuming`, `continue`, or `continuation` sets this proxy.
  These words need not explicitly identify the previous task, so both false
  positives and negatives are possible. Concurrent starts before that endpoint
  are not restarts. Complete 12-hour observation is required; missing prompt
  observations remain unknown.

These labels need not be mutually exclusive. The binary descriptive/model
endpoint is 1 for the completion surrogate, 0 for known stall or owner-block,
and missing otherwise. Missingness is reported rather than imputed as failure.
The restart proxy never enters the endpoint or predictors. If exact owner links
are unavailable, the owner label is dropped from observed targets. Health,
compaction, tool-failure and loop signals are retained **only for outcome audit**,
never as dispatch-time features.

### Dispatch-time features

Start hour, weekday, harness, first-prompt length, the requested acceptance/test/
DoD/checkbox and open-ended regexes, branch/PR/checkpoint/resume mentions,
source `is_automated`, and strictly preceding 30-/60-minute start counts.
Simultaneous starts are not counted as known prior starts. First prompts must
have timestamps within 60 seconds of start; later prompts are unavailable
features, not mined retrospectively. The initial prompt may be a task wrapper
or injected context, which remains a confound.

Session-level provider/model fields can change during a run and are not
immutable dispatch records. They therefore remain `null`/`unknown` and are
excluded from the model, not backfilled from later assistant messages. Harness
is allowlisted; arbitrary private metadata strings are not exported.

## Analysis and the four anti-patterns

Every feature table includes total rows, labeled n, unknown outcomes, successes,
rate and Wilson 95% interval. A cell with **labeled n < 15** is insufficient,
including a large cell whose outcomes are mostly missing. Intervals assume
independent Bernoulli trials; dependence within tasks/nights can make them
optimistic. There is no multiplicity correction or causal identification.

The predeclared comparison rule requires n >= 15 in each group. Nonoverlapping
Wilson intervals in the harmful direction produce `confirmed`; opposite
nonoverlap produces `rejected`; all other cases produce `insufficient`.
These verdicts describe this selected, labeled corpus, **not general causal
truth or evidence that increasing launch concurrency is beneficial**.

| Anti-pattern | Operationalization / interpretation |
|---|---|
| Open-ended bedtime prompts | Compare regex-positive vs negative prompts in the overnight cohort. Missing prompts excluded, not treated as negative. n = exposed labeled rows; also report exposed total/control n. |
| Many recent starts | At least **six other runs** in either preceding window, versus fewer. n = exposed labeled rows. Global observed start-count proxy, not actual concurrency or load. |
| Restart instead of resume | Count same-project/12-hour/prompt proxies, but always `insufficient` to confirm/reject the named task-level claim without task equivalence. n = positive proxies, not proven restarts of the same work. |
| Evening cut never resumed | In the full corpus, explicit failed exit ending `[17:00,23:00)`, no observed same-project resume-prompt start in the following **12 hours**, complete follow-up required. This does not establish "never" or task intent, so always `insufficient`. n = positive proxies; also report observable candidates. |

The latter two are **post-dispatch diagnostic proxies**, not predictors. No
circular association of "restart" or "cut" against a failure label that already
contains that event is presented. Negative and incomplete results are valid
outputs. The receipts distinguish counts of observed proxies from n used in
outcome comparisons.

### Optional regression

Only attempt fitting for >=100 overnight sessions. Also require >=100 labeled
rows, >=15 in each class, eligible historical training data, and four held-out
weeks. Otherwise report the exact reason and set `weights: null`.

Use a small stdlib-only L2 logistic model with fixed transforms/regularization,
no tuning. Numeric/regex dispatch features, missing indicators and train-only
harness vocabulary are allowed; model/provider and post-run metadata are not.
Validate in forward-only week blocks, using night dates anchored at local noon
so Sunday night and Monday morning stay together. Explicit parent chains and
conservative same-project start chains <=12 hours define leakage groups.
**Entire cross-week groups are excluded from cross-validation**, rather than
appearing in more than one held-out fold or moving nights across weeks. Within
eligible weeks, a group and each night's rows remain in a single held-out fold.
This conservative rule can make fitting impossible; that is reported, not
worked around with random splits.

Report pooled out-of-fold AUC and a seeded 400-draw held-out-week cluster
bootstrap percentile interval. Single-class/insufficient folds cannot justify
an AUC or weights. If fitted, also fit the fixed model to the labeled cohort
and export explicitly exploratory coefficients, with their transforms in code.
These are **not validated runtime readiness weights**.

## Readiness rubric

Acceptance criteria, a checkpoint/resume plan, no open questions, and approval
before 23:00 are proposed operator requirements, not facts established by this
retrospective study. Approval events and resolved questions are not measured.
The study therefore does not promote any necessary hard gates from association
alone. The rubric separates proposed unvalidated gates from supported gates
and carries null weights whenever the regression is not fitted. Enforcing
runtime policy is outside this public evidence repository.

## Verification

Synthetic tests cover Wilson intervals, missing outcomes and n<15, clock/DST
boundaries, label heuristics, same-project restart censoring, strictly prior
launch counts, forward weekly folds and cross-week lineage exclusion, verdict
direction, optional model/AUC execution, exact owner-block joins, read-only SQL,
mirror deduplication, late-prompt exclusion, private permissions, raw-text
exclusion, frozen-data hash checks, and the actual extraction/analysis CLIs.
No private source data or generated receipt belongs in a commit or PR diff.
