# Visual and interaction parity

Reference: the Southbridge JEV article. Ours: the Phase 1B article.

Two independent checks:

1. **Source level** — cascaded rules read out of the reference's built
   stylesheets (`docs/reference-geometry.md`).
2. **Computed level** — values read back from a real headless Chromium over the
   DevTools Protocol, at the same viewport, with the *same probe*, on both
   pages. Screenshots alone were not used to decide anything.

Reproduce with the scripts in `docs/probes/`:

```
python3 docs/probes/probe1.py … probe7.py    # reference geometry extraction
python3 docs/probes/parity.py                # reference vs ours, property diff
python3 docs/probes/shots.py                 # 3-viewport capture + measurement
python3 docs/probes/confirm.py               # focused assertions on our build
```

## Exact matches (1440×1200, confirmed on both pages)

| property | reference | ours |
|---|---|---|
| `.article-title` font / size / weight / line-height | display / 60px / 400 / 72px | identical |
| `.article-title` box | x 380, w 680, h 72 | x 380, w 680, h 72 |
| `.article-header` height | 116px | 117px |
| article header margin-bottom | 56px | 56px |
| prose `p` | 17px / 28.05px / mb 24px | 17px / 28.05px / mb 24px |
| prose `p` box | x 380, w 680 | x 380, w 680 |
| prose `h2` | 36px / 43.2px / fw 500 / mt 44px / mb 10px | identical |
| prose `h3` | 30px / 37.5px / fw 500 / mt 36px / mb 8px | identical |
| `hr` | mt 56px / mb 40px | identical |
| readable column | 680px | 680px |
| contents rail | `fixed`, top 144px, w 192px, x 32 | identical |
| rail link | 14px / 19.6px / x 44 / w 180 | identical |
| range scrubber | 104×32px, accent `rgb(41,145,110)` | identical |
| titles accent line | `display: none` | `display: none` |
| frog glyph | 7 paths, viewBox `0 0 200 135` | 7 paths, viewBox `0 0 200 135` |
| `.figure` | 14px sans, 1px top+bottom hairline, pad 12px 0 | identical |
| `figcaption` | 12px, `--sb-text-muted`, mt 8px | identical |
| `--content-width` / `--full-width` | 680px / 1200px | identical |
| `--space-*`, `--radius-*`, `--text-*`, `--leading-*` | 40 tokens | identical |

## Charts: viewBox, rendered height, aspect handling

| plot | reference | ours |
|---|---|---|
| `corpusPlot` | `0 0 500 254`, h 254 | `0 0 500 254`, h 254 |
| `progressPlot` | `0 0 564 96`, h 96, `preserveAspectRatio="none"` | identical |
| `forecastCurve` | `0 0 300 200`, h 200, `par="none"` | identical |
| `errorSpread` | `0 0 300 68`, `par="none"` | identical |
| `forecastPair` grid | `328px 328px`, gap 24px | `328px 328px`, gap 24px |
| bar pitch (`corpusPlot`) | 17.3px | 17.9px |

## Breakpoint behaviour (measured at each viewport)

| | 1440×1200 | 1024×1200 | 390×844 |
|---|---|---|---|
| rail visible — reference | yes, x 32 | no | no |
| rail visible — ours | yes, x 32 | no | no |
| mobile FAB visible — reference | — | yes, 64×64 @ (936, 1112) | yes, 64×64 @ (302, 756) |
| mobile FAB visible — ours | — | yes, 64×64 @ (936, 1112) | yes, 64×64 @ (302, 756) |
| heading frog visible — reference | yes | yes | **no** |
| heading frog visible — ours | yes | yes | **no** |
| range width | 104 | 104 | 104 |
| `h2` size | 36px | 36px | 36px |
| layout viewport | 1440 | 1024 | 390 |

The rail→sheet swap is at **1199px** and the frog is hidden at **768px**, both
as in the reference. The mobile FAB position is byte-identical at all three
viewports, which it was not before the containment fix described below.

## Motion

Keyframes are transcribed exactly (`fadeIn` 10px rise, `slideIn` 20px from the
left, `packetPulse` .2→.7, `tooltipFade` with its ±4px and 15%/85% hold,
`loading-pulse` .1→.25 with scale 1.05). Entrance animation is
`fadeIn .8s ease-out both`; the copy-link pill is
`tooltipFade 1.5s ease-out forwards`.

Scroll spy uses `rootMargin: "-100px 0px -66% 0px"` with **no threshold**, and
reveal-on-scroll is `rootMargin`-based (`300px` / `200px`), because that is what
the reference does — it configures reveal by rootMargin rather than by a
percentage crossing.

No animation library is present on either page: no `framer-motion`, no
`useMotion`. Motion is CSS keyframes plus `IntersectionObserver` and
`requestAnimationFrame`.

## Defects this pass found and fixed

1. **Title geometry.** Was `clamp(2.3rem,5vw,3.4rem)`; the reference is
   `clamp(3.25rem,5vw,3.75rem)`, weight 400, line-height 1.2 → 60px/72px.
2. **Layout architecture.** Ours was a 3-track grid with a *sticky* rail. The
   reference is full-bleed with 48px inline padding, a centred 680px column,
   and a *fixed* rail at `left: max(2rem, calc((100vw - 1200px)/2 - 220px))`.
   Rebuilt to match.
3. **Hand-drawn frog.** The contents rail contained an invented frog path. The
   reference's actual seven-path glyph is now used, in `Frog.tsx`, on the rail,
   the heading links and the mobile FAB.
4. **Missing font variables.** The stylesheet referenced `--font-sans` /
   `--font-mono` / `--font-serif` that no longer existed, so type fell back to
   system defaults. Restored, and the display role now loads **Parastoo** — the
   reference's own display face — so that substitution is eliminated entirely.
5. **Unstyled scrubbers.** The two range inputs were forced to `width: 100%`
   by inline styles and rendered 680×16px. They are now the reference's
   104×32px control with a 2px track and a 10px round thumb.
6. **Mobile layout viewport blew out to 573px.** A `.data-table` wider than the
   screen expanded the document, which displaced the mobile FAB to x=485 and
   scaled the whole page. The reference clips at its outer wrapper rather than
   at `body`; ours now does the same, and at 390px the layout viewport is
   **390px** with a FAB at x=302 — identical to the reference.
7. **Contents rail.** Was 8 flat entries with no indent and no nested sub-items.
   Now 20 entries with the reference's `padding-left: 0.75rem` per level, and
   the link metrics (14px, 19.6px, x 44, 180px wide) match exactly.
8. **Figure grammar.** Figures were rounded cards with a full border. The
   reference uses **top and bottom hairlines only**, no radius, sans at 14px,
   and a `.wide` variant that breaks the 680px column out to 1200px. Rebuilt.

## Remaining differences (all intentional, all listed)

| difference | why |
|---|---|
| Typeface family names (Hanken Grotesk, JetBrains Mono) | HK Grotesk is commercial and Departure Mono is not fetchable from CI. Roles and every metric are matched; Parastoo is the reference's own face, used directly. |
| Words, headings, section order | Different study. The visual grammar is the reference's; the prose is ours. |
| Title wraps to 2 lines at 1440, 3 at 390 | Our title is shorter than the reference's; identical type at identical size. |
| Rail is 804px tall vs 595px | 20 contents entries vs 12, from a longer document. Same item metrics. |
| 99 SVGs vs 53; 39 buttons vs 104 | Different number of figures and controls. Every measure of a *shared* figure and control matches. |
| No `<select>` family/run/metric choosers | The reference's three dropdowns are its own study's chooser for a dataset with a different shape. Our explorer uses chip-style `chart-tabs` on the same interaction grammar. |
| Counted dangerous **selections**, not exposures | The reference counts what a draw selected. We report exposures separately and footnote the gate clause that ignores them. |
| Empty histogram buckets | There genuinely are no measured decisions between ~10 ms and ~100 ms. Not smoothed away. |

## Evidence in this directory

* `ours-1440x1200.png`, `ours-1024x1200.png`, `ours-390x844.png` — full-page
  capture of **our** build at the three required viewports, from the same run
  that produced `measure.json`. These are the regression baseline.
* `measure.json` — the raw measurements for both pages at all three viewports.

The reference captures are not stored, because they are third-party content and
are reproducible in one command: serve the saved reference DOM with its own
stylesheets and run `shots.py`. The parallax of numbers in this document is the
comparison.
