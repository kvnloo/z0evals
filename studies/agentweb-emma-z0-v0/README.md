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
