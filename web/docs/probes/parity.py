"""Measure the same properties on the reference and on our build, then diff them.

This is the acceptance test for visual/interaction parity: identical probes,
identical viewport, values printed side by side with the delta called out.
"""
import asyncio
import json
import sys

sys.path.insert(0, "/tmp")
import cdp

REF = "http://127.0.0.1:8917/index.html"
OURS = "http://127.0.0.1:8921/"

PROBE = r"""
(() => {
  const g = (sel, props) => {
    const el = typeof sel === 'string' ? document.querySelector(sel) : sel;
    if (!el) return null;
    const c = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const o = {__w: Math.round(r.width), __h: Math.round(r.height), __x: Math.round(r.x)};
    (props||[]).forEach(p => o[p] = c.getPropertyValue(p));
    return o;
  };
  const out = {};
  const rootC = getComputedStyle(document.documentElement);
  ['--content-width','--full-width','--text-base','--leading-relaxed','--text-sm','--text-3xl','--text-4xl','--space-3','--space-24','--radius-sm']
    .forEach(v => out['var'+v] = rootC.getPropertyValue(v).trim());

  // title
  out.title = g('.article-title', ['font-size','line-height','font-weight','margin-bottom','letter-spacing']);
  const hd = document.querySelector('.article-header');
  out.header = hd ? {h: Math.round(hd.getBoundingClientRect().height), mb: getComputedStyle(hd).marginBottom} : null;
  // first heading after body copy
  const h2 = [...document.querySelectorAll('h2')].find(e => e.closest('.prose, .article-body, article') && !e.closest('figure'));
  out.h2 = g(h2, ['font-size','line-height','font-weight','margin-top','margin-bottom','font-family']);
  const h3 = [...document.querySelectorAll('h3')].find(e => e.closest('.prose, .article-body, article') && !e.closest('figure'));
  out.h3 = g(h3, ['font-size','line-height','font-weight','margin-top','margin-bottom']);
  const p = [...document.querySelectorAll('.prose p, article p, .article-body p')].filter(e=>!e.classList.contains('lede') && !e.closest('figure') && !e.closest('.figure')).find(e => (e.textContent||'').length > 120);
  out.p = g(p, ['font-size','line-height','margin-bottom','font-family']);
  // rail
  const rail = document.querySelector('.rail, .toc-desktop-sidebar');
  out.rail = rail ? g(rail, ['position','top','width']) : null;
  out.railLeft = rail ? Math.round(rail.getBoundingClientRect().x) : null;
  // rail link
  const rl = document.querySelector('.toc-link-frog, .toc a');
  out.tocLink = g(rl, ['font-size','line-height','padding-top','color','font-family','text-decoration-line']);
  // figure
  const fig = document.querySelector('figure, .figure');
  out.figure = fig ? {__h: Math.round(fig.getBoundingClientRect().height),
                      borderTop: getComputedStyle(fig).borderTopWidth,
                      borderBottom: getComputedStyle(fig).borderBottomWidth,
                      fs: getComputedStyle(fig).fontSize,
                      ff: getComputedStyle(fig).fontFamily.split(',')[0].replace(/"/g,''),
                      pt: getComputedStyle(fig).paddingTop} : null;
  // captions
  const cap = document.querySelector('figcaption');
  out.figcaption = g(cap, ['font-size','color','line-height','margin-top']);
  // range + buttons
  const range = document.querySelector('input[type=range]');
  out.range = g(range, ['width','height','accent-color']);
  out.rangeLabel = range ? range.getAttribute('aria-label') : null;
  const btn = document.querySelector('button');
  out.button = g(btn, ['font-size','border-radius','border-width','padding-left']);
  // counts of the reference's own control surface
  out.counts = {
    headingFrogLink: document.querySelectorAll('.heading-frog-link').length,
    headingWithFrog: document.querySelectorAll('.heading-with-frog').length,
    titleAccent: document.querySelectorAll('.title-accent-line').length,
    fab: document.querySelectorAll('.mobile-toc-fab-wrapper').length,
    drawer: document.querySelectorAll('.mobile-toc-drawer').length,
    tocFrog: document.querySelectorAll('.toc-frog').length,
    figures: document.querySelectorAll('figure, .figure').length,
    svgs: document.querySelectorAll('svg').length,
    modelTrack: document.querySelectorAll('.modelTrack').length,
    progressRow: document.querySelectorAll('.progressRow').length,
    corpusPlot: document.querySelectorAll('.corpusPlot').length,
    corpusLegend: document.querySelectorAll('.corpusLegend').length,
    forecastCurve: document.querySelectorAll('.forecastCurve').length,
    errorPlot: document.querySelectorAll('.errorPlot').length,
  };
  // svg geometry of our named plots
  out.plots = {};
  ['.corpusPlot','.progressPlot','.forecastCurve','.errorPlot','.replayPlot','.matrixPlot'].forEach(sel => {
    const s = document.querySelector(sel);
    if (s) { const r = s.getBoundingClientRect();
      out.plots[sel] = {w: Math.round(r.width), h: Math.round(r.height), vb: s.getAttribute('viewBox'), par: s.getAttribute('preserveAspectRatio')}; }
  });
  return JSON.stringify(out);
})()
"""


async def measure(pg, url):
    await pg.goto(url)
    return json.loads(await pg.eval(PROBE))


def flat(d, prefix=""):
    o = {}
    for k, v in d.items():
        if isinstance(v, dict):
            o.update(flat(v, f"{prefix}{k}."))
        else:
            o[prefix + k] = v
    return o


async def main():
    pg = await cdp._open()
    await pg.set_viewport(1440, 1200)
    ref = await measure(pg, REF)
    ours = await measure(pg, OURS)
    fr, fo = flat(ref), flat(ours)

    keys = sorted(set(fr) | set(fo))
    same = diff = 0
    print(f"{'property':44} {'REFERENCE':28} {'OURS':28}")
    print("-" * 104)
    for k in keys:
        a, b = fr.get(k), fo.get(k)
        if a == b:
            same += 1
            continue
        diff += 1
        print(f"{k:44} {str(a)[:27]:28} {str(b)[:27]:28}  <-- DIFF")
    print("-" * 104)
    print(f"identical: {same}/{len(keys)}   differing: {diff}")
    await pg.send("Browser.close")


cdp.run(main)
