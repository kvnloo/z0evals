# Unified Memory v0

Tracker: https://github.com/kvnloo/z0evals/issues/56

Goal: run the same source-grounded memory/state questions through DSH, Hermes, OMO, and OMP, then compare retrieval, model-visible injection, answer support, provenance, abstention, idempotency, supersession, latency, and context cost.

Stages stay separate:

1. retrieval
2. injection
3. answer use
4. verification

A configured index alone is not a passing harness integration.

Public study artifacts must contain stable question IDs and scrubbed evidence metadata rather than copied conversation history.

Expected outputs:

- `question-contract.json`
- `receipt.schema.json`
- `results/harness-receipts.jsonl`
- `results/summary.json`
- `../../posts/unified-memory-v0.md`

Do not add a new memory database. Use the source systems and provenance contracts already owned by z0intelligence and the harnesses.

## Executable source-slot cohort (v1)

`question-contract.json` preserves the original six IDs/outcome classes and points
at `executable-cohort.v1.json`. That versioned fixture freezes exact prompt
templates, evidence slots, behavioral outcomes, oracle types, verification rules,
and the replay/supersession/missing-source controls. `cohort.json` is the older
public synthetic OMP unit fixture: it is not a real source binding and must not
be promoted into this run's evidence.

The six source slots are `identifier`, `state_old`, `state_new`, `foreign`,
`conflict_a`, and `conflict_b`. The same concrete local binding is shared by all
four harnesses; no harness may replace its facts, prompt templates, or sources.
Each instantiated prompt has an ID consisting of its question ID and the SHA256
of the final UTF-8 prompt (template plus the frozen response instruction).

### Local source binding

`source-binding.schema.v1.json` defines the local-only wire format:

- stable source ID, message-text SHA256 revision, trust class, locator;
- originating native harness/session identity and authentic observation time;
- a single-valued fact key, exact string value, scope and validity;
- real AgentsView session/message coordinates and expected content digest;
- an executable literal-span oracle with checked key, scope, validity and value
  spans in one unique verbatim source quote;
- a defined full-source baseline: original source paths, hashes, byte counts,
  and the slots each original file supports.

The frozen native-message identity encoding is lowercase hexadecimal of the
**unaltered UTF-8 session ID** plus the nonnegative base-10 ordinal (no leading
zeroes except `0`): `agentsview:<session-hex>:<ordinal>`. Its canonical study
provenance URL is `agentsview://sessions/<session-hex>/messages/<ordinal>`; it is
not a promise that AgentsView's browser UI serves that route. Preflight derives
both fields from independently retrieved coordinates and rejects any differing
binding ID/URL, including alternate encodings or path traversal suffixes.

`literal-span-v1` now requires `key_start`/`key_end`, `scope_start`/`scope_end`,
`validity_start`/`validity_end`, and `value_start`/`value_end`. These are half-open
Unicode character offsets within `quote`, not UTF-8 byte offsets. Each slice
must equal the claimed field exactly; invented labels, normalized words and
implicit scopes/periods are inadmissible. This is deliberately conservative
source admission, **not general NLP truth verification**. Independent curator
semantic review must establish that the quote actually asserts the fact in the
claimed scope/validity, is single-valued (not a list of alternatives, a negation,
or a hypothetical), and that the paired assertions really describe an update
or mutually exclusive states. Literal spans alone cannot prove these semantic
relationships. If authentic sources do not meet the rule, leave the case
unbound/NOT RUN; never rewrite a real source into the UNIT fixture's wording.

Keep the concrete binding and all private retrieval/model captures OUTSIDE the
repository. `studies/unified-memory-v0/.local/` and `*.local.json` are also ignored
as a defensive guard, not permission to copy raw transcripts into z0evals.
Original raw files remain authoritative. An unavailable archive/transport is an
infrastructure blocker, never a successful missing-evidence case.

### Preflight and independent oracle

`cohort_contract.py` is study-only tooling, not production memory behavior.
Its `preflight(contract, binding, reader, consumer=...)` interface requires a
reader backed by actual AgentsView retrieval. It resolves and pins every source
before any model invocation; missing versions, changed bytes, fabricated native
origin, incomplete baseline or incoherent case definitions fail closed.

The reader must return `text`, `session_id`, `ordinal`, `origin_harness`,
`observed_at`, and the authoritative `source_path`, `source_file_sha256`, and
`source_file_bytes`. The last three identify the file revision **from which the
message was actually retrieved**. Compute its digest/length from that revision
at retrieval; do not copy the expected binding's baseline pins, or hash a
replacement file after retrieving from a stale index. The baseline independently
reads the actual UTF-8 file and checks path, SHA256 and bytes against both the
binding and retrieval-side record. A refreshed binding hash cannot relabel an
unrelated replacement file as the retrieved revision. If the index/transport
cannot establish this linkage, retrieval is blocked. The reader is a trusted
retrieval boundary, not an arbitrary binder-authored record; this contract
cannot authenticate a reader that fabricates both messages and file pins.

It requires ordered, changed old/new states for the same fact/scope; incompatible
single-valued facts must share key/scope/validity. `foreign` must originate in a
different harness from the consumer. Prefer an origin outside all four consumers
so the same case remains genuinely cross-harness for every lane. The minimum
subset requires distinct fact keys and values, distinct native message identities
and distinct excerpts. Neither required value may occur in the other excerpt,
even incidentally. Thus either omission removes the literal support itself, not
merely its slot label. This rule rejects some otherwise usable sources and does
not claim semantic minimality against paraphrases or unstated knowledge.

The missing-evidence case is an explicit transformation of an otherwise complete
binding: omit `identifier` only from model-visible evidence. An accidentally
absent base binding cannot pass preflight. Exact prompt language and the response
instruction are frozen by a code-pinned SHA256; prompts use fixed slot referents,
never interpolated binding keys or values. The intentionally withheld literal
value must not occur anywhere in the case outside its private oracle, including
prompts and nested metadata. This check runs at preflight, mutation construction,
and answer verification; even an incidental occurrence in fixed language rejects
the missing-source control. The old-only mutation also checks for the omitted
new value and retains its oracle entry privately for subsequent leak checks;
only its model-visible evidence is omitted.

Only `prompt` and `evidence` form the model-visible payload. Other plan fields,
especially `oracle`, binding identifiers/digests and baseline measurements, are
private verification/accounting data and must never be injected. Evidence
contains the source-supported excerpt and its checked key/provenance; no separate
expected-value projection is injected. Harness-added context/metadata must obey
the same withheld-value rule and be independently audited at the real seam; the
contract cannot check context that the harness does not supply to it.

`verify_answer(case, actual_answer)` checks strict JSON, exact source values,
complete source/version/locator/origin provenance, explicit conflict, retained
supersession history, and abstention without guesses. It rejects duplicate JSON
keys. Before accepting source support it compares every supplied evidence field
and the exact evidence multiset against the preflight oracle projection (excluding
its private `value` field). Altered text, keys, trust/provenance, duplicate/extra
items and unauthorized omissions fail. Keep the preflight oracle independently
pinned and unchanged; this is input consistency checking, not authentication of
a caller that rewrites the trusted oracle itself. `mutation_cases(plan)` produces
old-only/new-introduced and missing-source arms without changing any prompt or
fabricating a newer fact. Public function signatures and the existing case field
shape remain unchanged.

Run deterministic contract tests with:

    python3 -m pytest tests/test_unified_memory_cohort.py -q

Synthetic inputs in those UNIT tests test the verifier; they are not live study
sources or replacement harness receipts.

### Execution and accounting boundary

All harnesses consume the same preflight-approved plan and exact concrete
binding. Each must expose its real model-visible seam; serializing a response or
intended context is not injection proof. DSH's required current-source seam is:

    Agent -> systemPrompt.assemble(assembleContextFor(...))
          -> system-prompt/assemble -> actual model request

Keep real retrieval, assembly/injection, serialized provider request, provider
response/committed answer, and independent verification as separate artifacts.
Emit only rows validating against the unchanged `receipt.schema.json`; put
contract/binding/prompt digests and arm names in its existing `notes` field, not
new unrecognized properties. Failed or not-run cases must not become passing
receipts. An exact replay is a no-op within the retained session/trace/question;
record zero extra model calls and zero new evidence admission separately from
retransmission of existing context by a provider retry.

Minimal-context records actual injected UTF-8 bytes and evidence count alongside
the measured, deduplicated full authoritative-source-file byte baseline. This is
a measurement lane, not proof of superiority from one observation. Pin actual
executed source/runtime dependencies; a source checkout SHA alone does not pin an
older installed harness or borrowed dependencies. Never change model/provider
policy to make a study case pass.
