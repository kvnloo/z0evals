---
title: "100 Android chats: a send is not a captured reply"
subtitle: "An operational run of the reusable uiautomator2 workflow, with dispatch, result capture, and verification kept separate."
study: android-sustained-chat-100-v0
status: draft
author: "zer0 research"
date: "october 29, 2026"
published: '2026-10-29'
area: speed-ux
kind: study
tags: [android, cua, throughput]
featured: false
mock_data: false
toc:
  - id: status
    label: current snapshot
  - id: baseline
    label: the baseline workflow
  - id: amendment
    label: the connector correction
  - id: deviations
    label: faults stay in the record
  - id: measurement
    label: what the timings mean
  - id: limits
    label: what this cannot prove
---

## current snapshot {#status}

The allocation is **100 tasks**: 50 ChatGPT/S25 Ultra and 50 DeepSeek/S22+. This is an incomplete operational run with protocol corrections, not a completed comparative benchmark. The page shows a committed snapshot, not a live connection to the phones.

<!-- generated:sustained-chat-100 -->
Dispatch, full result capture, and independent verification are recorded separately in the aggregate snapshot. Missing results are not counted as successes.
<!-- /generated:sustained-chat-100 -->

The [aggregate artifact](https://github.com/kvnloo/z0evals/blob/main/studies/android-sustained-chat-100-v0/data/progress.json) and [study protocol](https://github.com/kvnloo/z0evals/blob/main/studies/android-sustained-chat-100-v0/README.md) preserve the definitions. Full answers go to their authorized consumers; no answer is automatically applied to a repository.

## the baseline workflow {#baseline}

The baseline is the existing **`launch_queue.py` / `burst.py` / `cgdrv.py` uiautomator2 workflow**, not a new model-driven phone controller. Phone-worker admission, UI flock locks, provider quota pauses, and the shared account budget remain the required admission path.

For ChatGPT, the established workflow uses the **GitHub connector**. A worker reads the real repository, writes requested changes on the named feature branch, opens at most one draft PR where needed, and posts one tagged tracking-issue comment. It uses **Extra High or Pro**, finishes in one turn, and never merges. The existing chat-poller collects comments and observed draft PRs; it does not scroll the phone to retrieve results.

DeepSeek uses deterministic dispatch and intentional per-message Copy. A full reply is joined to exact prompt provenance and its unique first-line tag. Re-reading the entire original prompt by repeatedly scrolling is unnecessary when the exact pre-send hash and verification receipt already exist.

The S25 grant ended at **05:00 UTC on October 29**. Its finite unit stopped without extending that grant. Unsent tasks remain queued; collecting server-side GitHub comments can continue without touching the phone. No settings, permission changes, or phone installs are part of this run.

## the connector correction {#amendment}

The original manifest incorrectly gave ChatGPT no-repo-access instructions and an app-response result plan. The owner paused admission and supplied an explicit correction. **26 task records were amended, 16 obsolete access statements were corrected, and 74 records remained unchanged.** Original bytes and old/new hashes were preserved.

Every amended message was independently re-rendered and hashed. All 26 passed live LAWSv2 admission with no unresolved placeholders or truncation. The largest prepared message is 8,090 characters, above the former editorial 8,000-character budget. That brief remains quarantined without a dispatch receipt: its delivery is **not proven**, even though the driver code imposes no corresponding character ceiling.

New ChatGPT results come from tagged comments and optional draft PRs on [Dash #614](https://github.com/kvnloo/dash/issues/614), [.files #124](https://github.com/kvnloo/.files/issues/124), [z0evals #153](https://github.com/kvnloo/z0evals/issues/153), and [z0intelligence #288](https://github.com/kvnloo/z0intelligence/issues/288). **No ChatGPT clipboard harvesting is used after the correction.** Already-sent and ambiguous tasks were not replayed to make the revised manifest look complete.

One proposed amendment was subsequently identified as already dispatched under the original revision and was not resent. Historical receipts remain attributed to the payload revision actually in effect; the new manifest does not retroactively change what an earlier chat received.

## faults stay in the record {#deviations}

- One fx canary completed its controller job while the ChatGPT app still showed Thinking. It is an unpaired setup deviation, not a valid comparison arm or proof of a captured answer.
- Initial native launches could not find the host `uv` executable. The execution path was corrected without installing anything on a phone; uncertain claims were not blindly retried.
- The first native S25 wrapper omitted the outer shared pacing reservation. It was stopped and corrected. Earlier observations remain in the record; this run does not claim pacing held throughout.
- Cancelling an SSH client left an old remote loop with disconnected stdout. It could claim a brief, then fail before transport. Recovery was limited to individually audited pre-transport abandonment. Possible actual Sends stayed quarantined.
- DeepSeek's long messages span multiple accessibility nodes. Some sends emptied the composer but failed the old single-bubble receipt check. Their dispatch status stays unconfirmed even when a later exact-identity full answer is captured.
- Repeated drawer/thread scrolling was stopped. A later apparent recovery timeout was localized to another workflow holding the S22 UI locks, not proved to be a dead automation server. Those locks were not bypassed.

These are reasons **not to publish a performance delta** from this run, not details to remove from the denominator.

## what the timings mean {#measurement}

Dispatch wall time comes from canonical launch receipts; transport time comes from the transport's reported seconds. Dispatch end to full-result observation includes provider work, poller cadence, and harvest scheduling. It is **not model inference latency**.

Control paths and result channels are separate cohorts. Missing observations remain null, not zero. Available failed and unconfirmed timings are retained. Task counts and receipt counts differ when a task has a recorded pre-send failure or recovery.

Phone-worker temperatures, thermal status, battery, load, memory, and storage are sampled roughly every five minutes. These observations cannot rule out throttling between samples. The collector obtains them without extra phone input.

## what this cannot prove {#limits}

CG1-CG5 require new methods to start from the best reusable workflow and include a same-task, same-device baseline arm. This run did not start cleanly and is **not eligible for comparative speedup claims**. Future method comparisons need a fresh paired design; this run does not silently resend tasks to manufacture one.

App, hardware, provider, task content, account state, time, admission faults, and the prompt amendment are confounded. This is neither a randomized device/provider comparison nor an on-device HobbyLM inference benchmark.

A send is not a response. A response is not correct code. A verifier pass needs independent consumer evidence bound to the exact result digest. Model self-reports are not grades.

The public artifact excludes prompts, answers, task identifiers, device serials, local paths, screenshots, and raw traces. It is SHA256-pinned in the study manifest. Recorded repository bases and file hashes are not proof of an immutable live runner release.

[Earlier Android evals](https://kvnloo.github.io/z0evals/z0live-phone-control/) remain separate and are never counted as chats in this run.
