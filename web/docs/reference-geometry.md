# Reference geometry and behaviour contract

Extracted from the Southbridge JEV reference **at source level and at computed
level** — cascaded rules from the built stylesheets plus values read back from a
real headless Chromium via the DevTools Protocol at 1440×1200. Nothing here is
eyeballed from a screenshot.

* Source: `/tmp/sb-ref/css/*.css` (2 built stylesheets), `/tmp/sb-ref/ref.html` (server-rendered DOM).
* Computed: `Page.navigate` → `Runtime.evaluate` → `getComputedStyle` / `getBoundingClientRect`.
* The extraction scripts live in `web/docs/` alongside this file's rationale; the
  probe driver is a ~90-line CDP client (launch, `Emulation.setDeviceMetricsOverride`,
  `Runtime.evaluate`, `Page.captureScreenshot`).

Fonts: the reference self-hosts HK Grotesk (sans), Departure Mono (mono),
Parastoo (display), Bitstream Iowan Old Style BT (body). We substitute
Hanken Grotesk / JetBrains Mono / system Iowan Old Style. This is the only
intentional typographic difference; every *metric* below is matched.

## Design tokens

```
--content-width  680px          --full-width  1200px
--text-xs   .75rem  (12px)      --leading-none    1
--text-sm   .875rem (14px)      --leading-tight   1.2
--text-base 1.0625rem (17px)    --leading-snug    1.4
--text-lg   1.1875rem (19px)    --leading-normal  1.5
--text-xl   1.3125rem (21px)    --leading-relaxed 1.65
--text-2xl  1.5rem  (24px)      --leading-loose   1.8
--text-3xl  1.875rem (30px)
--text-4xl  2.25rem  (36px)     --radius-sm 2px   --radius-md 4px
--text-5xl  2.75rem  (44px)     --radius-lg 6px   --radius-xl 8px
--text-6xl  3.5rem   (56px)     --radius-full 9999px

--space-1  4px   --space-2  8px   --space-3 12px   --space-4 16px
--space-5 20px   --space-6 24px   --space-8 32px   --space-10 40px
--space-12 48px  --space-16 64px  --space-20 80px  --space-24 96px
```

Palette (identical to reference): `--sb-text #3c3836`, `--sb-background #fff`,
`--sb-primary #1a3029`, `--sb-secondary #29916e`, `--sb-highlight #20ffaf`
(+ `-soft #20ffaf26`, `-medium #20ffaf4d`), `--sb-border #d9d9d9`,
`--sb-bg-subtle #fafafa`, `--sb-bg-muted #f0f0f0`, `--sb-text-muted #676767`,
`--sb-text-light #888`, `--sb-code-bg #f3f3f2`, `--sb-success #2e7d32`,
`--sb-error #c62828`, `--sb-subshade: var(--sb-secondary)`.

Callout variants: info `#64748b` border / `#64748b0f` bg / icon `#475569` /
title `#334155`; idea `#b45309` / `#b453090d` / `#92400e` / `#78350f`;
warning `#c2410c` / `#c2410c0d` / `#9a3412` / `#7c2d12`; danger `#b91c1c` / …
Notepad `#fef9e7 → #fdf5dc`, margin rule `#e8b4b4`.

## Page architecture (measured boxes at 1440 wide)

```
header.blog-page-header      1440×82    pt-8 pb-4 px-12; nav max-width 1200
main                         py-12 md:py-16 (64px top)
  header.article-header      1440×116   px-12, text-center, mb-14 (56px)
    div max-w-[680px] mx-auto  680 wide
  div.relative
    aside.toc-desktop-sidebar  192 wide  POSITION:FIXED, top-36 (144px)
    article                    1440 wide px-12 (48px) → content 1344
      div.max-w-[680px] mx-auto  680 wide
        div.prose              680 wide
footer.hw-footer             1440×93
```

The rail is **`position: fixed`, not sticky**, and the article is **not** a grid
track — it is full-bleed with 48px inline padding, and the readable column is a
centred 680px box inside it. The rail sits at

```
left: max(2rem, calc((100vw - 1200px)/2 - 220px));  top: 9rem;  width: 12rem;
```

so at 1440 it resolves to x=32, and it scrolls with the viewport independently of
the column.

## Typography

| element | family | size | weight | line-height | margin |
|---|---|---|---|---|---|
| `.article-title` (h1) | display | `clamp(3.25rem,5vw,3.75rem)` → 60px | 400 | 1.2 (72px) | `0 0 20px` |
| `.title-accent-line` | — | 60×3px, `--sb-highlight`, radius 2px | | | `0 auto 20px` |
| byline | sans | 0.9rem | | | `·` sep, `mx-2 opacity-30` |
| `.prose h1` | display | 44px | 500 | 1.15 | `3rem 0 .75rem` |
| `.prose h2` | display | 36px | 500 | 1.2 | `2.75rem 0 .625rem` |
| `.prose h3` | display | 30px | 500 | 1.25 | `2.25rem 0 .5rem` |
| `.prose p` | body (serif) | 17px | 400 | 1.65 (28.05px) | `0 0 1.5rem` |
| `.prose hr` | — | | | | `3.5rem 0 2.5rem` |
| `.prose ol` | | | | | `1.25rem 0`, `padding-left 1.75em` |
| `.prose ul` | | | | | `1.25rem 0`, `padding-left 1.5em`, square markers |
| `.prose strong` | | | 600 | | |
| `.prose code` | mono | `.875em` | | | |
| `.prose pre` | mono | | | | pad `--space-4`, radius `--radius-sm` |
| `.prose img` | | | | | `1.5rem 0`, radius 4px |

## Heading frogs

Every `h2`/`h3` is wrapped in `.heading-with-frog { position: relative }` and
carries a `button.heading-frog-link[aria-label="Copy link to this section"]`
holding the frog glyph.

```
.heading-frog-link { opacity:0; position:absolute; display:flex;
  align-items:center; justify-content:center; padding:0; border:none;
  color:var(--sb-text-muted);
  transition: opacity .15s ease-out, color .15s ease-out; }
.heading-with-frog:hover .heading-frog-link,
.heading-frog-link:focus-visible { opacity:.5 }
.heading-frog-link:hover          { color:var(--sb-text); opacity:.8 }
.heading-frog-link.copied         { color:var(--sb-subshade); opacity:1 }
.heading-frog-link.copied::after  { content:"Copied Link"; font:500 10px var(--font-sans);
  color:#fff; background:var(--sb-text); border-radius:4px; padding:3px 8px;
  white-space:nowrap; position:absolute; bottom:calc(100% + 4px); left:50%;
  transform:translate(-50%); animation:1.5s ease-out forwards tooltipFade }
```

Per-level anchors: h1 `top:1rem left:-3rem` svg 30×20 · h2 `top:.85rem
left:-2.75rem` svg 24×18 · h3 `top:.75rem left:-2.5rem` svg 20×15 · h4
`top:.65rem left:-2.25rem` svg 15×10. Hidden at ≤768px.

## Contents rail

```
aside.toc-desktop-sidebar   fixed left-[max(2rem,…)] top-36 w-48
  nav.toc-sidebar.toc-scrollable-container > div.toc-scrollable-inner > ul.space-y-1
    li[style="padding-left:0.75rem"]           (indent per level)
      a.toc-link-frog  flex items-start gap-1.5 text-sm leading-snug py-1
                       transition-colors duration-150 text-sb-text-light
                       hover:text-sb-text
        span.toc-frog-container > svg.toc-frog[viewBox="0 0 200 135"][14×10]
```

Computed: 14px HK Grotesk (sans), colour `#888`, one-line item 28px tall
(`py-1` 4px + `leading-snug` 20px), wraps to 47px on two lines. The frog is
rendered at 7×5px via CSS scale.

Mobile (≤890px) replaces the rail with a floating action button and a bottom
sheet:

```
.mobile-toc-fab-wrapper  fixed bottom-1.5rem right-1.5rem  64×64  z-1000
.mobile-toc-backdrop     fixed inset-0  z-1001  background transparent → #0000004d, transition .25s
.mobile-toc-drawer       fixed bottom-0 left-0 right-0  z-1002  max-height:60vh
                         border-radius 16px 16px 0 0; transform:translateY(100%);
                         transition: transform .3s cubic-bezier(.32,.72,0,1), opacity .25s;
                         box-shadow 0 -8px 32px #1a30291f, 0 -2px 8px #1a30290f
.mobile-toc-drawer-open  transform: translateY(0)
.mobile-toc-fab:hover    transform:translate(-50%,-50%) scale(1.05)
```

## Figures

```
figure / .figure {
  color: var(--sb-text); font-family: var(--font-sans);
  font-size: var(--text-sm);            /* 14px, sans — not serif */
  line-height: var(--leading-normal);
  border-top: 1px solid var(--sb-border);
  border-bottom: 1px solid var(--sb-border);
  padding: var(--space-3) 0;            /* 12px 0 */
  margin: var(--space-3) 0;             /* 12px 0 */
  min-width: 0;
  position: relative;
}
```

**Figures are separated by top and bottom hairlines**, not a rounded card with a
full border. `.diagram-wrapper` in prose carries `margin: 1.5rem 0 2rem`.

Figure eyebrow/title/caption slots, in order:
`--text-lg` fw-500 title → `--text-xs` `--sb-secondary` eyebrow → `--text-xs`
`--sb-text-muted` caption.

A `.wide` figure breaks the 680px column out to the full measure:

```
.wide { width: min(var(--full-width), calc(100vw - var(--space-12)));
        margin-inline: calc((100% - min(var(--full-width), calc(100vw - var(--space-12))))/2);
        padding-inline: var(--space-4); }
```

### Chart canvases (viewBox and rendered height)

| class | viewBox | height | preserveAspectRatio |
|---|---|---|---|
| `.corpusPlot` | `0 0 500 254` | 254px | default |
| `.progressPlot` | `0 0 564 96` | `--space-24` 96px | **none** |
| `.replayPlot` | `0 0 640 244` | 244px | **none** |
| `.forecastCurve` | `0 0 300 200` | 200px | **none** |
| `.matrixPlot` | — | 136px | — |

`preserveAspectRatio="none"` on the wide plots means the drawing is deliberately
stretched to the container width — the viewBox is a coordinate system, not an
aspect contract. Text inside them is therefore counter-scaled or placed in
sibling HTML, not in the stretched SVG.

SVG chart text: `.corpusNumber { font: 10px var(--font-mono); fill: var(--sb-text-muted) }`,
`.corpusLabel { font: 10px var(--font-sans); fill: var(--sb-text-muted) }`.

`.corpusLegend` — centred flex, `gap: --space-4`, 10px, `--sb-text-muted`; entries
are a 7×7 dot (filled `--sb-secondary` / hollow `--sb-background` with
`--sb-text-light` border).

`.plotMeta` — flex space-between, `--text-xs`, `--sb-text-muted`, `margin-bottom: --space-3`.
`.progressScale` — flex space-between, uppercase, `letter-spacing:.04em`, 10px, `--sb-text-light`, `margin-bottom: --space-2`.

`.progressRow { display:grid; grid-template-columns: 138px minmax(0,1fr) 7ch;
  gap: var(--space-4); align-items:center }` collapsing at the mobile breakpoint to
`minmax(0,1fr) 7ch` with the plot on row 2 spanning all columns.
`.progressValue { font-family: var(--font-mono); font-size: var(--text-xs);
  color: var(--sb-text-muted); text-align:right }`
`.replayAxisY { height:212px; margin-top:2px; text-align:right; font-size:var(--text-xs);
  color:var(--sb-text-muted); display:flex; flex-direction:column; justify-content:space-between; line-height:1 }`
`.axisY { height:192px; margin-top:4px }`

## Controls

```
button (primary)  padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm);
                  border:1px solid var(--sb-border); background: var(--sb-text);
                  color: var(--sb-background); font: inherit
button.quiet      padding: var(--space-1) var(--space-3); display:inline-flex;
                  align-items:center; gap:var(--space-2); border:1px solid var(--sb-border);
                  color:var(--sb-text-muted); font-size:var(--text-xs)
focus-visible     outline: 2px solid var(--sb-secondary); outline-offset: 2–3px
```

Range scrubber (`aria-label="Replay position"`, `aria-label="Inspect one
recorded event"`):

```
input[type=range]  width:104px; height:var(--space-8) → 32px; appearance:none;
                   background:0 0; border:0; border-radius:0; flex:0 0 104px
::-webkit-slider-runnable-track  background: var(--sb-border); height:2px
::-webkit-slider-thumb           appearance:none; width:var(--space-3); height:var(--space-3);
                                 background:var(--sb-text-muted); border:1px solid var(--sb-background);
                                 border-radius:50%; margin-top:-5px
accent-color: var(--sb-secondary)
```

Compact row controls measured live: row-expand `button.warningSelect` 74×18px,
12px; `button.quietButton` 38×26px, 12px, `padding:4px 0`. Table rows use
`--text-sm`/`--text-xs` with `--space-2` vertical padding.

## Motion

Exact keyframes, transcribed:

```
@keyframes fadeIn      { 0% {opacity:0; transform:translateY(10px)} to {opacity:1; transform:translateY(0)} }
@keyframes slideIn     { 0% {opacity:0; transform:translate(-20px)} to {opacity:1; transform:translate(0)} }
@keyframes packetPulse { 0%,to {opacity:.2} 50% {opacity:.7} }
@keyframes tooltipFade { 0% {opacity:0; transform:translate(-50%) translateY(4px)}
                         15% {opacity:1; transform:translate(-50%) translateY(0)}
                         85% {opacity:1; transform:translate(-50%) translateY(0)}
                         to {opacity:0; transform:translate(-50%) translateY(-4px)} }
@keyframes loading-pulse { 0%,to {opacity:.1; transform:scale(1)} 50% {opacity:.25; transform:scale(1.05)} }
```

Durations and delays observed: entrance `fadeIn .8s ease-out both` with `.1s` and
`.2s` stagger; quick `fadeIn .6s ease-out forwards`; `slideIn .5s ease-out
forwards`; tooltips `tooltipFade 1.5s ease-out forwards`; `packetPulse 2s
ease-in-out infinite`; `loading-pulse 1.8s ease-in-out infinite`.

`prefers-reduced-motion` neutralises animation and transition duration.

### Scroll behaviour

Scroll spy on the rail:

```
new IntersectionObserver(cb, { rootMargin: "-100px 0px -66% 0px" })
```

Reveal-on-scroll uses **rootMargin, not threshold** — `rootMargin: "300px"` (and
`"200px"` for a second group), so elements are revealed before they enter the
viewport rather than when they cross a percentage line.

No animation library is present: no `framer-motion`, no `useMotion`. Motion is
CSS keyframes driven by `IntersectionObserver` and `requestAnimationFrame`.

## Breakpoints

`@media (max-width: 1199px)`, `1100px`, `900px`, **`890px`**, **`768px`**,
`720px`, `680px`, `640px`, `600px`, `540px`, `480px`. The two that matter for the
article shell are **890px** (rail → mobile FAB) and **768px** (heading frogs
hidden; `.heading-frog-link { display:none }`).

## Print / resolution mode

`body:has(#jev-resolution)` hides the rail, both mobile TOC layers, the page
header, the footer and every heading frog:
`:is(.mobile-toc-fab-wrapper, .mobile-toc-backdrop, .mobile-toc-drawer,
.toc-desktop-sidebar, .blog-page-header, footer, nextjs-portal,
.heading-frog-link) { display:none !important }`.
