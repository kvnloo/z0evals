# z0evals site

A port of the Southbridge **"Models watching models"** article template onto our
Phase 1B experiment.

Reference: <https://www.southbridge.ai/blog/jev-watching-the-agents>

## What is copied, and what is ours

**Copied from the reference** (by inspecting its built output, not by guessing):

| Reference | Here |
|---|---|
| Next.js + React + Tailwind v4, static | same stack, `output: "export"` |
| hand-rolled SVG charts, no chart library | same — `components/charts/*` use raw `<svg>` |
| CSS keyframes + `IntersectionObserver` + `requestAnimationFrame`, no animation library | same — `useReveal`, `RouteProgress` |
| sticky left contents rail | `.rail` in `app/globals.css` |
| serif centred title, centred byline | `.article-header` |
| `--sb-*` design tokens | reproduced verbatim in `@theme` |
| inset metric headline | `.metric-row` |
| inline bar tables, filter chips, expandable family rows | `.data-table`, `.chart-tabs`, `FamilyStack` |
| replayable curve + playhead slider | `ReplayChart` |
| observation scrubber with `aria-valuetext` readout | `ObservationScrubber` |
| family / metric selectors | `ResultsExplorer`, `Heatmap` |
| outcome heatmap across states × observers | `Heatmap` |
| appendix methodology table | `app/page.tsx` § Appendix |

## Font substitution

The reference self-hosts **HK Grotesk** and **Bitstream Iowan Old Style BT**,
both commercial, plus **Departure Mono**. We load the closest open equivalents
rather than copying licensed files:

| Reference | Here | Why |
|---|---|---|
| HK Grotesk (sans) | **Hanken Grotesk** (Google, OFL) | same designer lineage, near-identical metrics |
| Departure Mono (mono) | **JetBrains Mono** (Google, OFL) | technical mono covers the label/number/code role |
| Iowan Old Style (serif) | system stack `Iowan Old Style, Georgia, serif` | the reference's own fallback chain |

Swap in the real faces by dropping woff2 files into `public/fonts/` and pointing
`next/font/local` at them.

## Data

`data/study.json` is **generated** by `../scripts/build_site_data.py` from the
real Phase 1B run. Nothing is hand-typed; if a dimension was not measured it is
`null` and the component omits it. The per-state matrix
(`studies/slm-router-v0/data/phase1b-matrix.json`) is derived from
`observations.jsonl` when the local-only source is present.

```bash
python3 ../scripts/build_site_data.py     # regenerate data/study.json
npm run build                             # static export to out/
Z0_BASE_PATH=/z0evals/next/ npm run build # build for a channel path
```
