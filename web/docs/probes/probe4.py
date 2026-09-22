import sys, json; sys.path.insert(0,'/tmp')
import cdp
Q = r"""
(() => {
  const svgs=[...document.querySelectorAll('svg')].filter(s=>!s.classList.contains('toc-frog'));
  const list=svgs.map(s=>{const r=s.getBoundingClientRect();
    return {w:Math.round(r.width),h:Math.round(r.height),vb:s.getAttribute('viewBox'),
      aW:s.getAttribute('width'),aH:s.getAttribute('height'),st:s.getAttribute('style'),
      cls:(s.getAttribute('class')||'').slice(0,60),pres:s.getAttribute('preserveAspectRatio'),
      par:(s.closest('.diagram-wrapper')?'diagram':'other'),
      title:(s.closest('figure')?.querySelector('figcaption')?.textContent||'').slice(0,60)};});
  const toc=document.querySelector('.toc-desktop-sidebar');
  const tocItems=[...document.querySelectorAll('.toc-desktop-sidebar a, .toc-desktop-sidebar [role=link]')].slice(0,4).map(a=>{
    const c=getComputedStyle(a);const r=a.getBoundingClientRect();
    return {txt:a.textContent.trim().slice(0,44),cls:(a.getAttribute('class')||'').slice(0,80),
      fs:c.fontSize,h:Math.round(r.height),color:c.color,ff:c.fontFamily.split(',')[0]};});
  const tocHTML=toc?toc.outerHTML.slice(0,1100):null;
  const ctr=[...document.querySelectorAll('select,input,button')].slice(0,10).map(e=>{
    const c=getComputedStyle(e);const r=e.getBoundingClientRect();
    return {tag:e.tagName.toLowerCase(),type:e.getAttribute('type'),label:e.getAttribute('aria-label'),
      h:Math.round(r.height),w:Math.round(r.width),fs:c.fontSize,pad:c.padding,br:c.borderRadius,
      bd:c.border,ff:c.fontFamily.split(',')[0].replace(/"/g,''),cls:(e.getAttribute('class')||'').slice(0,70)};});
  return JSON.stringify({n:svgs.length,svgs:list.slice(0,16),tocItems,tocHTML,ctr});
})()
"""
async def main():
    pg=await cdp._open(); await pg.goto("http://127.0.0.1:8917/index.html")
    d=json.loads(await pg.eval(Q))
    print("non-frog svg count:",d['n'])
    for s in d['svgs']: print("  ",json.dumps(s))
    print("\n--- toc items ---")
    for t in d['tocItems']: print("  ",json.dumps(t))
    print("\n--- toc html ---"); print(d['tocHTML'])
    print("\n--- controls ---")
    for c in d['ctr']: print("  ",json.dumps(c))
    await pg.send("Browser.close")
cdp.run(main)
