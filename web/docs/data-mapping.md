# Data → component mapping

Every figure on the page is backed by a measured field. This is the whole
chain, one row per component:

**reference component → our component → input artifact → measured fields →
transformation → what happens when the field is missing.**

Nothing on the page is modelled, extrapolated, interpolated, jittered in the
browser, or copied from a vendor claim. The only non-measured values on the page
are **axis furniture** (gridline positions, tick label text, viewBox
coordinates) and **overplotting offsets**, and the offsets are derived
deterministically — see the last section.

Provenance of the input artifact: `p1b-20260921T1430Z/observations.jsonl`,
1,102 rows, produced by the local `z0int cognition serve` supervisor. See
`docs/provenance.md` for why that artifact is currently local-only.

---

## Generation path

```
results/phase1b/p1b-20260921T1430Z/observations.jsonl      (1,102 receipts)
        │
        ├─ scripts/build_matrix.py ──→ studies/…/phase1b-matrix.json
        │
        └─ scripts/build_component_data.py
                 │  (also imports the committed transcription when the raw
                 │   receipts are absent, so CI builds a complete site)
                 ▼
        studies/…/phase1b-components.json   ← the frozen component inputs
                 │
                 └─ scripts/build_site_data.py ──→ web/data/study.json
                          │
                          └─ web/components/figures/*.tsx   (no computation)
```

The React components do **no** arithmetic on measurements. They read a frozen
JSON block and lay it out. Every rate, interval, median, count and offset is
computed once, in Python, at build time, and committed.

---

## Components

### 1. Corpus histogram — `CorpusGrowth`

| | |
|---|---|
| **Reference** | `study-module__corpusPlot` + `corpusTitle` + `corpusHeadline` + `corpusLegend`, viewBox `0 0 500 254`, 17.3px bar pitch |
| **Ours** | `web/components/figures/CorpusGrowth.tsx` |
| **Input** | `components.corpus` |
| **Measured fields** | `decision_ms` (every one of the 1,102 rows), `state_family`, `dangerous_selected`, `deterministic_solution`, `correct`, `arm_kind` |
| **Transform** | `log10(decision_ms)` bucketed 3 bins per decade over the measured range; bar height = bucket count; dots = rows where `dangerous_selected == true`, placed at their own `decision_ms` |
| **Omission** | Rows with `arm_kind == "deterministic"` (84 receipts) are excluded from the histogram because the rules engine's 0.006 ms decision would pull the axis three decades left and flatten the distribution. **Stated in the caption, not hidden.** The flag series is unaffected — no deterministic row ever selected a dangerous action. |

The axis range is `[floor(log10(min)), ceil(log10(max))]` of the actual data,
not a hard-coded 1…100k. There are empty buckets; they are real emptiness, and
the caption says so.

### 2. Model board — `ModelBoard`

| | |
|---|---|
| **Reference** | `modelBoard` / `modelHead` / `modelRow` / `modelName` / `modelCell` / `modelTrack` (8px chamfered track, `clip-path` notch) / `modelReadings` |
| **Ours** | `web/components/figures/ModelBoard.tsx` |
| **Input** | `components.modelBoard`, `components.coverage` |
| **Measured fields** | `arm`, `correct`, `cold_or_warm`, `decision_ms`, `dangerous_selected`, `state_id`, `repetition` |
| **Transform** | success rate = `correct / n` per arm; median response = `median(decision_ms)` over rows with `cold_or_warm == "warm_invocation"`, rounded; dangerous = count of `dangerous_selected`; bar width = value / max(value) across arms |
| **Omission** | The six `arm_kind == "cold_probe"` arms are excluded from every comparison. They are single-state probes (`one_obvious_tool`, n=3) that measure cold-start latency, not accuracy — ranking a 1.000 on three draws beside 84-decision arms would be arithmetically false. Their count, state and row total are printed in the caption and carried in `components.coverage`. |

The median definition is pinned to the headline numbers: `warm_invocation` only.
Verified against `phase1b-summary.json` — 194.8 → 195, 1993.3 → 1993,
3602.8 → 3603 ms.

`compiler+jev` never calls a model (NanoJev decides in process), so it has no
`warm_invocation` rows. Its cell falls back to the `no_model_call` decision time
and the row's readings line says **"in-process decision, no model call"** rather
than passing it off as a warm model latency.

### 3. Progress trajectories — `ProgressRows`

| | |
|---|---|
| **Reference** | `progressRow` (grid `138px minmax(0,1fr) 7ch`), `progressLabel`, `progressPlot` (viewBox `0 0 564 96`, `preserveAspectRatio="none"`), `progressScale`, `progressValue` |
| **Ours** | `web/components/figures/ProgressRows.tsx` |
| **Input** | `components.progress` |
| **Measured fields** | `correct`, `state_id`, `repetition` per arm |
| **Transform** | walk the 28 states in sorted order; a state counts as solved when `sum(correct) * 2 > len(votes)` (strict majority of three). The polyline is the running count. |
| **Omission** | None. Every comparison arm appears. Cold probes do not (they cover one state). |

Majority-of-three, not best-of-three. Best-of-three would flatten the
disagreement the arms actually exhibit.

### 4. Forecast pair — `ForecastPair`

| | |
|---|---|
| **Reference** | `forecastPair` (grid `328px 328px`, gap 24px), `forecastCurve` (viewBox `0 0 300 200`, `preserveAspectRatio="none"`, one shaded polygon + three polylines), `errorPlot` container wrapping an `errorSpread` SVG (viewBox `0 0 300 68`, 12px interval bar, centre marker, vertical reference rule), `plotMeta` |
| **Ours** | `web/components/figures/ForecastPair.tsx` |
| **Input** | `components.forecast` |
| **Measured fields** | `correct`, `arm`, `decision_ms` ordering |
| **Transform** | Wilson 95% score interval (z = 1.96) on `correct / n` per arm; the same estimator recomputed for every prefix of the best arm's receipts, giving the interval-narrowing curve; `singleLo`/`singleHi` is the same estimator restricted to the 3 repetitions of one state |
| **Omission** | None. Arms with different `n` are shown at their own `n`, and `n` is printed on every interval and in the tooltip. The 76-receipt cascade arm is not padded to 84. |

Wilson rather than a normal approximation because several arms sit near 0 or 1
where the normal interval leaves [0, 1]. No bootstrap, no resampling, no
simulation.

### 5. Utility tie — `UtilityTie`

| | |
|---|---|
| **Reference** | the crowded dot layer from `corpusPlot` (r 3, `var(--sb-secondary)`, stroke-width 1.2) and `replayPlot`, in the standard `.figure` shell |
| **Ours** | `web/components/figures/UtilityTie.tsx` |
| **Input** | `components.utility` |
| **Measured fields** | `decision_ms`, `correct`, `arm`, `repetition`, `state_id`, `run_id` |
| **Transform** | one lane per arm; x = `log10(decision_ms)` over the measured range including the 4000 ms budget; y = lane; horizontal/vertical stagger = the sha256 offset below; `utility` is the frozen gate value, constant by construction |
| **Omission** | None — all 39 rows of `tool_fails` are drawn. |

This figure exists to show a **defect**, and the data proves it without any
modelling: `distinctUtilities` is `[-1.0]`, a single value across all 39 draws.
The only correct arms (both Qwen3.5-9B) sit at a 4,727 ms median, past the
frozen 4,000 ms budget; incorrect arms sit well inside it. Correct-but-slow and
wrong-but-fast are indistinguishable to the gate.

### 6. Headline figure — `HeadlineFigure`

| | |
|---|---|
| **Reference** | the dominant-number opening figure |
| **Ours** | `web/components/HeadlineFigure.tsx` + `components/charts/DensityBars.tsx` |
| **Input** | `density` |
| **Measured fields** | `raw_receipts`, `phase1b_measured_cells`, `phase1b_cells_n_ge_3`, `phase1b_cells_n_eq_1` |
| **Transform** | counts as recorded; bar width = count / max |
| **Omission** | None. |

### 7. Reliability curve + beeswarm — `Calibration`

| | |
|---|---|
| **Reference** | the reference's calibration/agreement figure |
| **Ours** | `web/components/charts/Calibration.tsx` |
| **Input** | `matrix.calibration` (186 rows) |
| **Measured fields** | reported `confidence`, `correct`, `arm` |
| **Transform** | decile bins of reported confidence; observed accuracy per bin; beeswarm points at (`confidence`, `correct`) |
| **Omission** | Only **186 of 924** bounded decisions emit a confidence at all, and they skew to NanoJev and Hammer 7B. This is stated in the caption and in footnote 1 — the curve describes the arms that emit confidence, not every arm. |

### 8. Remaining charts

`ArmScatter`, `DangerousBars`, `ResidencyBars`, `CompositionSplit`,
`OrchestrationBars`, `ReplayChart`, `Heatmap`, `FamilyStack`, `ArmTable`,
`ActionTable`, `FamilySparklines`, `ResultsExplorer`, `LadderFlow` all read
aggregates out of `matrix` / `residency` / `composition` / `orchestration` /
`actions`, computed by `scripts/build_site_data.py` from the same receipts.
The only literal arrays in any component are **axis tick positions**
(`[0.5, 0.6, 0.7, 0.8, 0.9]` for a 0–100% axis, `logTicks(...)` for a latency
axis). Those are chart furniture, not data.

---

## Determinism: the only synthetic values on the page

Overplotting offsets are the one place a value is invented. They are **not
random** and they are **not generated in the browser**:

```python
def _jitter(run_id, state_id, arm, rep, spread=0.34):
    key = f"{run_id}|{state_id}|{arm}|{int(rep)}".encode("utf-8")
    h = int.from_bytes(hashlib.sha256(key).digest()[:6], "big")
    return ((h / float(1 << 48)) - 0.5) * 2.0 * spread
```

* Input is the receipt's own identity — run, state, arm, repetition.
* The offset is therefore stable: rebuilding produces byte-identical output,
  and the same receipt lands in the same place every time.
* It is computed once, in `scripts/build_component_data.py`, and shipped inside
  `phase1b-components.json` as the `jitter` field.
* No component imports a random source, and no component reads `Math.random`.

Verification:

```
$ grep -rnE 'Math\.random|faker|mock|synthetic|illustrative|placeholder|lorem' web/components web/app web/lib
(no matches)
```

---

## What is deliberately *not* shown

* **No remote inference.** Every arm ran on the local RTX 3080 Ti; external
  spend is $0.00.
* **No extrapolation to unseen states.** 28 states is 28 states.
* **No ranking on fewer than 76 receipts.** The cold probes are excluded, and
  the reason is printed on the page rather than buried.
* **No claim of reproducibility from this repository alone.** The source
  commits are local-only; the page says the raw receipts are authoritative and
  pending import. It does not say "clone and re-run this".
