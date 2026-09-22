import sys, json, asyncio; sys.path.insert(0,'/tmp')
import cdp

REF="http://127.0.0.1:8917/index.html"
OURS="http://127.0.0.1:8921/"
VIEWS=[(1440,1200,"1440x1200"),(1024,1200,"1024x1200"),(390,844,"390x844")]

MEASURE = r"""
(() => {
  const q=(s)=>document.querySelector(s);
  const box=(el)=>{if(!el)return null;const r=el.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y+scrollY),w:Math.round(r.width),h:Math.round(r.height)};};
  const rail=q('.rail, .toc-desktop-sidebar');
  const fab=q('.mobile-toc-fab-wrapper');
  const vis=(el)=>{if(!el)return false;const c=getComputedStyle(el);const r=el.getBoundingClientRect();
    return c.display!=='none'&&c.visibility!=='hidden'&&r.width>0&&r.height>0;};
  // heading frog
  const hf=q('.heading-frog-link');
  return JSON.stringify({
    docH: document.documentElement.scrollHeight,
    railVisible: vis(rail), railBox: box(rail),
    fabVisible: vis(fab), fabBox: box(fab),
    frogVisible: vis(hf),
    titleBox: box(q('.article-title')),
    headerBox: box(q('.article-header')),
    firstFigBox: box(q('figure, .figure')),
    proseW: (()=>{const p=[...document.querySelectorAll('.article-body p, .prose p')]
      .find(e=>(e.textContent||'').length>200 && !e.classList.contains('lede'));return p?Math.round(p.getBoundingClientRect().width):null;})(),
    proseFs: (()=>{const p=[...document.querySelectorAll('.article-body p, .prose p')]
      .find(e=>(e.textContent||'').length>200 && !e.classList.contains('lede'));
      return p?getComputedStyle(p).fontSize:null;})(),
    h2Fs: (()=>{const e=[...document.querySelectorAll('.article-body h2, .prose h2')][0];
      return e?getComputedStyle(e).fontSize:null;})(),
    rangeW: (()=>{const e=q('input[type=range]');return e?Math.round(e.getBoundingClientRect().width):null;})(),
    figures: document.querySelectorAll('figure, .figure').length,
    svgs: document.querySelectorAll('svg').length,
    showMore: document.querySelectorAll('select').length,
    buttons: document.querySelectorAll('button').length,
  });
})()
"""

async def one(pg, url, w, h, name):
    await pg.set_viewport(w, h, mobile=(w < 500))
    await pg.goto(url)
    m = json.loads(await pg.eval(MEASURE))
    await pg.shot(f"/tmp/vr/{name}.png", full=True)
    return m

async def main():
    pg = await cdp._open()
    out = {}
    for (w,h,label) in VIEWS:
        r = await one(pg, REF, w, h, f"ref-{label}")
        o = await one(pg, OURS, w, h, f"ours-{label}")
        out[label] = {"reference": r, "ours": o}
        print(f"\n===== {label} =====")
        for k in sorted(set(r) | set(o)):
            a, b = r.get(k), o.get(k)
            flag = "" if a == b else "   <-- DIFF"
            print(f"  {k:16} ref={str(a)[:44]:46} ours={str(b)[:44]}{flag}")
    open("/tmp/vr/measure.json","w").write(json.dumps(out, indent=2))
    await pg.send("Browser.close")

cdp.run(main)
