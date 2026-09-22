import sys, json; sys.path.insert(0,'/tmp')
import cdp
Q = r"""
(() => {
  const out={};
  const al=document.querySelector('.title-accent-line');
  if(al){const c=getComputedStyle(al);const r=al.getBoundingClientRect();
    out.accent={display:c.display,w:Math.round(r.width),h:Math.round(r.height),bg:c.backgroundColor,mb:c.marginBottom};}
  out.forecastPair=(()=>{const e=document.querySelector('[class*="forecastPair"]');if(!e)return null;
    const c=getComputedStyle(e);return {display:c.display,cols:c.gridTemplateColumns,gap:c.gap};})();
  out.forecast=(()=>{const e=document.querySelector('[class*="forecastCurve"]');if(!e)return null;
    const r=e.getBoundingClientRect();return {w:Math.round(r.width),h:Math.round(r.height)};})();
  out.errors=[...document.querySelectorAll('[class*="errorPlot"]')].map(e=>{const r=e.getBoundingClientRect();
    return {w:Math.round(r.width),h:Math.round(r.height),vb:e.getAttribute('viewBox')};});
  out.figures=[...document.querySelectorAll('[class*="study-module"][class*="figure"]')].slice(0,3).map(e=>{
    const c=getComputedStyle(e);const r=e.getBoundingClientRect();
    return {w:Math.round(r.width),bt:c.borderTopWidth,bb:c.borderBottomWidth,pad:c.padding,fs:c.fontSize,ff:c.fontFamily.split(',')[0]};});
  const fig=e=>{const c=getComputedStyle(e);return {t:e.tagName,cls:(e.getAttribute('class')||'').slice(0,50),fs:c.fontSize,mt:c.marginTop,mb:c.marginBottom,ff:c.fontFamily.split(',')[0]};};
  out.caption=(()=>{const e=document.querySelector('[class*="errorCaption"],[class*="microCaption"],[class*="warningFootnote"]');return e?fig(e):null;})();
  const pr=document.querySelector('[class*="progressRow"]');
  if(pr){const c=getComputedStyle(pr);out.progressRow={cols:c.gridTemplateColumns,gap:c.gap};}
  out.quote=[...document.querySelectorAll('blockquote,.callout')].slice(0,2).map(fig);
  return JSON.stringify(out);
})()
"""
async def main():
    pg=await cdp._open(); await pg.goto("http://127.0.0.1:8917/index.html")
    print(json.dumps(json.loads(await pg.eval(Q)),indent=1))
    await pg.send("Browser.close")
cdp.run(main)
