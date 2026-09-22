import sys, json; sys.path.insert(0,'/tmp')
import cdp

Q = r"""
(() => {
  const g=(el)=>{const c=getComputedStyle(el);const r=el.getBoundingClientRect();
    return {w:Math.round(r.width),h:Math.round(r.height),x:Math.round(r.x),y:Math.round(r.y+scrollY),
      fs:c.fontSize,lh:c.lineHeight,fw:c.fontWeight,ff:c.fontFamily.split(',')[0].replace(/"/g,''),
      mt:c.marginTop,mb:c.marginBottom,pad:c.padding,ls:c.letterSpacing,color:c.color,bg:c.backgroundColor,
      br:c.borderRadius,bd:c.border,pos:c.position,top:c.top};};
  const out={};
  const t=document.querySelector('.article-title')||document.querySelector('h1');
  out.title={sel:t?(t.className||''):null, ...(t?g(t):{})};
  const sub=document.querySelector('.article-subtitle')||document.querySelector('.article-header p');
  out.subtitle=sub?{cls:sub.className,...g(sub)}:null;
  const byline=document.querySelector('.article-meta')||document.querySelector('.article-byline');
  out.byline=byline?{cls:byline.className,...g(byline)}:null;
  out.headerHTML=document.querySelector('.article-header')?document.querySelector('.article-header').outerHTML.slice(0,1400):null;
  out.svgs=[...document.querySelectorAll('svg')].slice(0,14).map(s=>{const r=s.getBoundingClientRect();
    return {w:Math.round(r.width),h:Math.round(r.height),attrW:s.getAttribute('width'),attrH:s.getAttribute('height'),
      vb:s.getAttribute('viewBox'),cls:(s.getAttribute('class')||'').slice(0,70),
      parent:(s.parentElement.getAttribute('class')||'').slice(0,60)};});
  return JSON.stringify(out);
})()
"""
async def main():
    pg = await cdp._open()
    await pg.goto("http://127.0.0.1:8917/index.html")
    d=json.loads(await pg.eval(Q))
    for k in ['title','subtitle','byline']:
        print(f"--- {k} ---"); print("  ",json.dumps(d[k],indent=None)[:400])
    print("\n--- article-header HTML ---"); print(d['headerHTML'])
    print("\n--- svgs ---")
    for s in d['svgs']: print("  ",json.dumps(s))
    await pg.send("Browser.close")
cdp.run(main)
