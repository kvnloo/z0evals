# NOOP × Hermes agent API (no adb, tailnet only)

Status: **draft, one handset run** (owner's Galaxy S25 Ultra, 2026-10-20/21). Source: `kvnloo/noop`
branch `feat/android-hermes-agent-api` (fork-only Experimental feature, default OFF).

## What was tested

Hermes on the owner's host (groot) calling NOOP on the owner's phone through an MCP tool surface the app
serves on its Tailscale address while the owner's time-boxed grant runs. adb was used only to install the
update and to read the phone's own audit log / foreground activity for verification; every agent call
went over the tailnet (`http://100.x:8765/mcp`, WireGuard-encrypted).

Identity reuses the owner's z0live broker pairing: NOOP stores only the token's SHA-256 and re-checks
it against the broker every 5 minutes. Hermes-side, every response passes through Microsoft Presidio
(`presidio-analyzer 2.2.364`, spaCy `en_core_web_sm`) before the model sees it.

## Results

| Check | Result |
| --- | --- |
| No-adb end-to-end script (`e2e_phone.py`), run 1 / run 2 | 12/12, 12/12 |
| Reads: `data_freshness`, `health_snapshot`, `sleep_summary`, `workout_summary`, `metric_series` | all OK, summary-only, no forbidden keys (device ids, notes, routes, stage JSON) |
| Daily values without the `read_detail` tick | refused (`scope_required`) |
| Wrong bearer token / browser `Origin` header | 401 / 403, both written to the phone audit log |
| `open_screen` while NOOP visible (run 2) | `landed: true` in 487 ms; adb confirms `MainActivity` on Sleep |
| `open_screen` while another app is in front | `mode: notification`, `posted: true`, owner's foreground app untouched |
| Real Hermes turn ("how did I sleep this week, what should I do today") | Hermes called 4 read tools, rendered the ephemeral coach dashboard and posted a coach note; all calls in phone audit and Hermes-side receipts |
| Broker revocation | see `data/summary.json` → `revocation` |
| Warm call latency, `data_freshness` (n=20) | p50 10 ms, p95 14 ms; first call ~1.5 s (broker re-check + Presidio load) |
| JVM unit tests (`com.noop.agent.AgentApiTest`) on the installed lineage | 18/18 (incl. an audit-concurrency regression found on the handset) |
| Hermes-side Python tests (Presidio and regex-fallback hosts) | 8/8 on groot, 7/7 on mbp (pre-fix count) |

Two defects surfaced on the handset and were fixed in the same branch. The audit log could lose an entry when the settings screen and the service wrote at once (now a process-wide lock). spaCy tagged the source
kind `oura` as `PERSON`, so Presidio redacted it. Source kinds are now a closed, allow-listed vocabulary.

## Not shown here

No health values, dashboard content or advice text are published. `data/summary.json` holds pass/fail,
latencies, counts of audit entries by kind/tool/outcome, and response key structure only.

## Limits

- One handset, one night, one grant scope combination (summaries + actions; daily values not granted).
- The coach advice quality was not evaluated; only that the flow ran and stayed inside the gates.
- The installed APK is a local integration of the feature onto other in-flight NOOP branches.
- The grant UI taps were made by the test harness via adb on the owner's behalf during this run.
