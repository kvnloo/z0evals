# Sustained Android chat run: 100 requested tasks

This is a draft operational receipt, not a completed or policy-compliant comparative benchmark. It preserves the attempted run, its protocol corrections, and missing results. No speedup or quality claim follows from the current snapshot.

## Allocation and baseline

- 50 ChatGPT tasks assigned to Samsung Galaxy S25 Ultra.
- 50 DeepSeek tasks assigned to Samsung Galaxy S22+.
- Baseline dispatch: the existing `launch_queue.py` / `burst.py` / `cgdrv.py` uiautomator2 workflow, with phone-worker admission, UI flock locks, shared account pacing, and provider quota pauses.
- ChatGPT's established result path is the GitHub connector: real repository files on a named feature branch, at most one draft PR where code/doc changes are requested, and one exact tagged comment on the tracking issue, collected by the shared chat-poller. Effort must be Extra High or Pro; work finishes in one turn. Never merge from the phone worker.
- DeepSeek uses the existing deterministic dispatch and per-message Copy harvest. The reply's unique first-line tag is joined to exact prompt provenance. Only an intentional message Copy is read, not unrelated previous clipboard contents.
- No settings, permissions, or phone installs are authorized by this run.

CG1-CG5 require starting from the best reusable workflow and including it as a same-task, same-device baseline before comparing new methods. Future goal/CUA comparisons also need Jev, Groot Qwen3-4B, and the hermes-phone-goal goalkit loop; HobbyLM experiments start from the 8-thread CPU resident configuration. This chat run does not claim to have run those other benchmarks.

The one fx canary was an unpaired setup deviation, not a valid experimental arm. No comparative speedup is reported. Native app/provider work is not an on-phone HobbyLM inference measurement.

## Manifest lineage and connector correction

The original 100-task manifest froze at `2026-10-29T03:21:46+00:00`, SHA256 `51c0c3425a9a8175c309c6687a047b04ef930c1eb78937d0c42ef6027d7f923c`. All original prompt and rendered-message hashes were checked. Its ChatGPT no-repository-access instructions and clipboard result plan were a producer error relative to the established connector workflow.

The owner paused ChatGPT admission and supplied explicit repository/issue/base mappings. The connector-v2 manifest SHA256 is `6899e52f9ea80d5e463a64711033105e45b0a116e1366e481f5097c02f81a511`; amendment receipts SHA256 `08d1b9f4ec557c1d4347dcdaec3709cf451325e7b6e5952d402136da6e22e06e`.

- 26 task records were amended; 74 remained object-identical.
- 16 task bodies received only the owner's specified corrections to obsolete no-repo-access statements.
- Repository, tracking issue, base, Extra High effort, lowercase branch tag, and exact result channel were recorded.
- The parent independently recomputed every amended prompt and canonical rendered digest.
- All 26 passed the live LAWSv2 `chatgpt_refusals` check before admission; there were no unresolved placeholders or truncation.
- The largest amended rendered message is 8,090 characters. It exceeds the prior editorial 8,000-character budget; the existing native launcher and burst transport impose no corresponding runtime ceiling. The actual length is retained, not silently clipped.
- Original manifests and per-task old/new receipts remain private and immutable. Previously sent or ambiguous tasks were not replayed merely because a new prompt revision existed.

The four tracking issues are [Dash #614](https://github.com/kvnloo/dash/issues/614), [.files #124](https://github.com/kvnloo/.files/issues/124), [z0evals #153](https://github.com/kvnloo/z0evals/issues/153), and [z0intelligence #288](https://github.com/kvnloo/z0intelligence/issues/288). The existing poller was extended and restarted; no second poller was created.

## Outcome semantics

| Outcome | Evidence |
|---|---|
| Requested | Frozen allocation. Not evidence of admission. |
| Claimed without a receipt | Queue claim exists, but there is no canonical dispatch outcome. It is not assumed actively running or sent. |
| Sent | Canonical transport receipt. It does not prove a completed answer. |
| Unconfirmed | An ambiguous dispatch remains ambiguous. A later matching reply does not rewrite the original receipt. |
| Reply captured | Complete copied DeepSeek answer or complete authorized GitHub issue-comment body, exact first-line tag, source identity, byte digest, and observation time. |
| Draft PR observed | A PR is actually present in the poller data with the reported URL, expected branch/base, and draft state. A fabricated URL in an answer is not enough. |
| Verified quality | Independent consumer evidence bound to the exact reply digest. Model self-reports and successful dispatch are not grades. |

Answers are untrusted second opinions. Consumers verify before applying them. Missing verifier outcomes remain `not_run` / null; no zero-filled success rate is published.

## Measurements

The private collector reads only this run's allowlisted task receipts and reply metadata. Original append-only dispatch/launch logs remain authoritative. A separate delivery process checks reply bytes and frozen destinations before publishing complete private consumer artifacts.

Public `data/progress.json` contains only aggregate task states, reply/PR/verifier counts, per-control-path/result-channel timing distributions, source digests, and sampled phone telemetry. Prompts, answers, task tags, job IDs, device serials, local paths, screenshots, and raw logs are excluded.

- `dispatch_wall_ms`: canonical receipt start to end.
- `transport_ms`: transport-reported seconds converted to milliseconds.
- `reply_observed_after_dispatch_ms`: dispatch end to full reply observation. It includes app/connector work, poller cadence, and harvest scheduling; it is not inference latency.
- Percentiles use linear interpolation at `(n-1)*p`; every distribution includes its observed `n`. Available failed/unconfirmed timings are retained.
- The fx canary, legacy native app-response cohort, connector cohort, and DeepSeek clipboard channel are not pooled into one timing distribution.
- Phone temperatures, thermal status, battery, load, storage, and available memory come from the existing phone-worker log, roughly every five minutes, plus the last available pre-run baseline. This is not continuous throttling measurement and causes no extra UI activity.

Private progress history preserves observed snapshots. Polling can miss intermediate state transitions; native append-only logs and GitHub comment timestamps remain the primary evidence.

## Recorded deviations and blockers

The initial host execution path lacked `uv`; the affected claims were quarantined, not blindly retried. An initial S25 wrapper omitted the shared outer pacing reservation. It was corrected; the study does not claim pacing held throughout.

Cancelling an SSH client left an old remote loop with disconnected stdout. It could claim a brief, then fail before transport. Recovery was restricted to individually audited pre-transport abandonment, checked against both wrapper and driver receipts and exact frozen briefs. Possible actual Sends stayed quarantined. The replacement finite unit uses stable journal output and group-bound shutdown.

DeepSeek long user messages span multiple accessibility nodes, so an old single-bubble check produced unconfirmed receipts even when a later full tagged answer was available. Repeated prompt-verification scrolling was stopped. Exact pre-send prompt hashes plus the reply's unique first line avoid that redundant pass when the required evidence exists.

At the committed snapshot cutoff, an S22 recovery timeout had been localized to an outer UI lock held by another workflow, not proved to be a dead automation server. Other agents' locks were not bypassed or killed; only this run's orphan waiters were removed. The holder later yielded and the canonical launcher resumed. The committed counts remain those at `observed_at`, not a live view of that continuation.

The S25 grant ended at `2026-10-29T05:00:00Z`. Its finite unit stopped without extension. Unsent tasks remain queued for an authorized later window; observers may continue collecting server-side GitHub results without touching the phone.

## Publication and limits

Run `python3 scripts/build_sustained_chat_status.py` before `scripts/build_posts.py`; CI and Pages use that sequence. The committed aggregate snapshot is SHA256-pinned in `manifest.yaml`, not a live public endpoint into private telemetry.

App, hardware, provider, task content, account state, time, admission faults, and the mid-run protocol amendment are confounded. Repository bases and recorded file hashes are not proof of an immutable live runner release. The run cannot establish a causal performance delta, device optimum, or validated answer-quality rate.

[Earlier Android phone-control measurements](https://kvnloo.github.io/z0evals/z0live-phone-control/) are separate and are never mixed into these 100 requested tasks.
