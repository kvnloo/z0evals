# Study-owned DSH diagnostic runner

This is a **capture runner, not a scorer or canonical receipt emitter**. It does
not implement memory or boot a product profile. The real cohort remains blocked
until the parent can retrieve and independently validate all six source-backed
cases. A boolean `preflight_passed` alone never authorizes a launch.

## Boundaries

- Executes the pinned source checkout with Bun `-e` from that checkout. No
  installed first-party DSH modules, source transformations, dependency installs,
  profile boot, SettingsForms, credentials writes, or policy overrides.
- Preserves `deepseek-official` / `deepseek-flash` / `high`, mounts source
  `llm-retry`, and refuses a changed selected route, environment, or settings.
  Settings are read as data. CredentialsLocal is mounted with `watch:false`;
  only the real provider resolves a credential, after authorization.
- Runtime manifests pin Bun, source HEAD/resolution files, runner bytes, evaluated
  ESM/CJS module URLs and SHA256s, package manifests/versions, and any borrowed
  native objects present in `/proc/self/maps`. OS shared libraries are **not**
  locked. Borrowed dependency versions are explicitly **not source-lock parity**.
  Bun's evaluated-module cache is the observation boundary, not a claim of
  function-level execution coverage. A newly loaded, unpinned module blocks the
  next admission/request check. The import guard remains active for installed
  first-party packages.
- Approval hashes are an out-of-band **parent/operator trust root**, not signatures
  or protection against a malicious same-UID process. The parent must perform
  real retrieval and the current cohort contract's claim/source-file checks
  before approving a plan. This runner verifies artifact integrity, six-case
  completeness, source-packet consistency, and prompt binding; it does not repeat
  the parent's source retrieval or independent answer scoring.
- Private directories must be new absolute canonical paths outside every Git
  worktree. Directories are `0700`, files `0600`; no headers, credentials,
  environment dumps, or raw product error diagnostics are recorded. Private
  source text, requests, and responses stay there. Existing files are never
  overwritten. Use `realpath` on the parent directory if its spelling is a link.

## No-model operation (safe now)

From the study checkout:

```sh
python studies/unified-memory-v0/dsh/runner.py \
  --mode seam --dsh-root /home/kvn/tmp/dsh \
  --task-cwd /home/kvn/zer0 --out /ABSOLUTE/PRIVATE/NEW-SEAM-DIRECTORY
```

`seam` is a clearly labeled UNIT diagnostic, not a cohort. It creates a real
Agent, follows up once, reaches the real scoped prompt waterfall, and rejects at
`agent/pre-step`. Both the neutral and native fetch boundaries default-deny.
The output `runtime-manifest.json` is a **candidate** pin for parent review.

## Parent-approved cohort preflight (not available until retrieval works)

`--plan` consumes `z0eval.unified_memory_run_plan.v1` from the parent. The first
six cases must be canonical, in contract order. Optional full case objects may
follow in `cases` or appear in `controls`, with variants:

- `supersession-old-only`: question `supersession`, only `state_old`, intentionally
  missing `state_new`.
- `supersession-after-new`: question `supersession`, both old and new sources.
- `missing-evidence-mutation`: question `exact-identifier`, no evidence,
  intentionally missing `identifier`.

Controls keep their canonical prompt and prompt ID. They run in separate fresh
Agents, as evidence-set mutations, **not a claim of longitudinal learning**.
Exact replay of canonical `exact-identifier` instead retains its actual Agent.

All JSON digests below use sorted keys, UTF-8, `ensure_ascii=False`, compact
separators (the parent contract's `digest_json` algorithm). `approval.json`:

```json
{
  "schema": "z0eval.dsh_approval.v1",
  "preflight_passed": true,
  "plan_sha256": "PARENT_APPROVED_COMPLETE_PLAN_DIGEST",
  "contract_sha256": "FROZEN_CURRENT_CONTRACT_DIGEST",
  "binding_sha256": "FROZEN_REAL_BINDING_DIGEST",
  "binding_id": "EXACT_PLAN_BINDING_ID",
  "runtime_pin_sha256": "REVIEWED_RUNTIME_MANIFEST_DIGEST",
  "question_ids": ["exact-identifier", "supersession", "cross-harness", "contradiction", "missing-evidence", "minimal-context"],
  "source_versions": {"COPY": "THE_EXACT_PLAN_SOURCE_VERSIONS_MAP"}
}
```

The placeholders are documentation, never an executable approval. Obtain the
approval digest from the parent after review; do not automatically approve a
new candidate by hashing it yourself. Contract revisions are frozen through this
approval, not silently tied to an obsolete embedded contract hash.

```sh
python studies/unified-memory-v0/dsh/runner.py \
  --plan /PRIVATE/plan.json --binding /PRIVATE/binding.json \
  --contract studies/unified-memory-v0/executable-cohort.v1.json \
  --approval /PRIVATE/approval.json \
  --approved-approval-sha256 "$PARENT_APPROVED_DIGEST" \
  --runtime-pin /PRIVATE/runtime-manifest.json \
  --dsh-root /home/kvn/tmp/dsh --task-cwd /home/kvn/zer0 \
  --out /PRIVATE/NEW-ALL-SIX-PREFLIGHT
```

Default mode is `preflight`, **never run**. It executes every case/control with
real source assembly but no model request, records blocked `turn/end`, verifies
unchanged configuration and exact runtime pin, and produces `summary.json`.
Oracle/expected fields never enter the child process payload.

Only after independent parent authorization, use the same arguments with a NEW
output directory and these additional flags:

```sh
--mode run \
--source-preflight /PRIVATE/NEW-ALL-SIX-PREFLIGHT/summary.json \
--approved-source-preflight-sha256 "$PARENT_APPROVED_NO_MODEL_SUMMARY_DIGEST"
```

The proof must match every case/packet, the plan, binding, contract, approval and
runtime. No such real plan/proof is supplied or claimed by this implementation.

## Capture semantics

Each numbered case directory separates:

- `assembly.json`: retrieval-linked packet digest and real driver/recomputed
  assemblies. The scoped waterfall calls `next()` once, preserves all assembly
  fields, and appends exactly one stable section with `interpolate:false`.
- `neutral-NNNN.json`: detached actual `llm/stream` options without the signal;
  the observer forwards unchanged via `next()`.
- `wire-NNNN-request.body`, `wire-NNNN-response.body`, `wire-NNNN.json`: exact
  native fetch request bytes, concurrently streamed `Response.clone()` bytes,
  status, hashes, attempts and join identities. The original Response and exact
  fetch arguments are returned/forwarded unchanged. No request/response headers
  are persisted. Retries are separate wire attempts, not new evidence admissions.
- `committed-answer.json`: authoritative `assistant/message` events, source,
  usage, stream, text, sequence/turn/step and interruption flag; these are NEVER
  reserialized into a later case's context.
- `turn-end.json`, `system-admission.json`, `attempts.json`, `case-stage.json`:
  separate durable settlement and admission facts. Raw error messages are
  intentionally omitted. Error, abort, incomplete tee, missing final answer, or
  missing wire admission blocks the case and stops the run, even if `whenIdle`
  resolves. Captures are unscored, never canonical passes.
- `identical-replay.json`: on the SAME retained Agent, identical packet/session/
  trace/question re-offer does not enqueue another followup. Real assembly is
  recomputed and the real source `SystemPromptProjection`, restored over that
  retained Session, returns zero updates. Session-event, neutral-request and
  native-fetch deltas must all be zero. This is **no second driver turn plus a
  real projection decision**, not a second model delivery or cross-process
  resume proof.

## Tests

```sh
# Before integration, point to the parent's contract; after integration omit it.
export DSH_STUDY_CONTRACT=/path/to/executable-cohort.v1.json
python -m unittest discover -s studies/unified-memory-v0/dsh/tests -v
ulimit -c 0
BUN_RUNTIME_TRANSPILER_CACHE_PATH=0 /home/kvn/.bun/bin/bun test \
  studies/unified-memory-v0/dsh/tests/capture.test.mjs
```

Python covers admission/corrupt-plan/fake-preflight refusal, full six-case
no-model CLI preflight, policy mismatch, source Agent assembly, and actual source
adapter/Agent capture and replay with explicit UNIT-only protocol Responses.
The source adapter tests mount **no real credentials** and never call the
network. The Bun test exercises transparent **native loopback HTTP streaming**,
not a provider/model. UNIT protocol text is not a fabricated cohort answer.
RED failures were observed before the launcher gate, six-case projection,
malformed-plan gate, source seam, mutations, native tee, real Agent executor,
runtime policy pin, source-preflight gate, and contract-revision support were
implemented; then each slice was run GREEN.
