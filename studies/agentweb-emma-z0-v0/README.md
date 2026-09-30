# AgentWeb + Emma + z0 v0

Tracker: https://github.com/kvnloo/z0evals/issues/67

This is the downstream-only acceptance study for the first-class z0intelligence integration under Emma. It must answer two separate questions:

1. is the boundary safe and semantically correct?
2. after it is safe, does it improve latency/token economics without reducing quality?

The study does not treat a configured adapter, HTTP 200, tool success, or completed agent turn as quality evidence.

## Frozen surfaces

- AgentWeb experiment branch: `lab/z0-agentweb-emma-v0`
- z0intelligence experiment branch: `lab/agentweb-emma-v0`
- Emma surface: internal `z0_route` tool plus the incumbent `jev_decide` comparison path
- z0evals owns the cohort and result receipts

## Stages

1. static contract checks
2. mocked failure injection
3. shadow planning (`/v1/plan`, zero physical specialist calls)
4. active canary with frozen fixtures
5. incumbent-vs-z0 paired replay
6. performance/economics analysis
7. exact-SHA freeze

## Hard gates

A promotion candidate must have all safety scenarios passing. In particular:

- no raw AgentWeb user/session identifiers cross the boundary;
- active ambiguity never creates a fresh execution identity;
- changed requests cannot reuse a completed/uncertain trace;
- unknown stays unknown;
- generic worker calls remain free-only;
- remote context requires explicit authorization;
- AgentWeb confirmation/evaluation/scheduled-publish/funding guards remain authoritative;
- observational ReliabilityEvent data never mints verified-quality gold.

Only after those pass do latency, token reduction and quality parity count toward promotion.


## Bounded decision campaigns

The first two measured decision seams deliberately keep AgentWeb's incumbent
behavior authoritative. z0 executes only the paired shadow decision and owns its
trace, physical-call idempotency and receipt.

### report_type_v1

Corpus: `report-type-fixtures.jsonl` — 30 authored cases, balanced 10/10/10
across creative, performance and research.

From the AgentWeb lab branch:

```bash
cd backend
Z0INT_AGENTWEB_MODE=shadow \
Z0INT_REPORT_CLASSIFY_ALLOW_REMOTE=1 \
npm run study:z0-report-type -- \
  /path/to/z0evals/studies/agentweb-emma-z0-v0/report-type-fixtures.jsonl \
  /tmp/agentweb-report-type-results.jsonl
```

The z0intelligence authority must independently opt in with
`Z0INT_EXPERIMENTAL_JEV_SHADOW=1`.

Score:

```bash
python scripts/score_agentweb_report_type.py \
  /tmp/agentweb-report-type-results.jsonl
```

The authored set is a regression/design corpus only. Review eligibility remains
false until at least 1,000 paired live decisions satisfy the scorer's coverage,
quality, receipt, non-application and latency gates.

### stop_request_v1

Corpus: `stop-request-fixtures.jsonl` — 40 cases: 20 explicit stops and 20
adversarial non-stops, including negation, quotations, code/process stop
conditions and changed-mind phrasing.

From the AgentWeb lab branch:

```bash
cd backend
Z0INT_AGENTWEB_MODE=shadow \
Z0INT_STOP_REQUEST_ALLOW_REMOTE=1 \
npm run study:z0-stop-request -- \
  /path/to/z0evals/studies/agentweb-emma-z0-v0/stop-request-fixtures.jsonl \
  /tmp/agentweb-stop-request-results.jsonl
```

Score:

```bash
python scripts/score_agentweb_stop_request.py \
  /tmp/agentweb-stop-request-results.jsonl
```

Candidate future assist bands are `P(stop) >= 0.90` and `P(stop) <= 0.10`,
but the shadow path never applies either band. Review requires at least 1,000
paired live decisions, at least 200 explicit stops, >=99.5% precision in the
high-stop band, and zero explicit stops in the high-continue band.

## Reliability observation lane

When AgentWeb enables `Z0INT_AGENTWEB_OBSERVE=shadow`, both live Emma and
external-MCP dispatch boundaries emit metadata-only ReliabilityEvents to
z0intelligence. The exporter is default-off, fail-open, capped at 16 in-flight
requests and uses a short timeout.

The z0 endpoint accepts only the privacy-minimized projection: pseudonymous
session identity, bounded tool name/platform/outcome/latency, partial measurement
state and no user id, prompt, tool args/results, free-form error text or verified
quality signal. Duplicate identical observations replay; changed payloads under
the same observation id are rejected.
