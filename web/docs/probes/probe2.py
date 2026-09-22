import sys, json; sys.path.insert(0,'/tmp')
import cdp

Q = r"""
(() => {
  const cs=getComputedStyle(document.documentElement);
  const vars={};
  for (const n of ['--content-width','--full-width','--text-base','--leading-relaxed','--text-sm','--text-lg','--text-xl','--text-2xl','--text-3xl','--text-4xl','--sb-*']) {
    if(n.endsWith('*')) { for (const p of ['--sb-background','--sb-text','--sb-primary','--sb-secondary','--sb-highlight','--sb-border','--sb-bg-subtle','--sb-text-muted','--sb-text-light']) vars[p]=cs.getPropertyValue(p).trim(); }
    else vars[n]=cs.getPropertyValue(n).trim();
  }
  const art=document.querySelector('article');
  const env=[];
  const walk=(el,d)=>{
    if(d>3) return;
    const r=el.getBoundingClientRect();
    const c=getComputedStyle(el);
    env.push({d,tag:el.tagName.toLowerCase(),cls:(el.getAttribute('class')||'').slice(0,80),
      w:Math.round(r.width),x:Math.round(r.x),mt:c.marginTop,mb:c.marginBottom,
      fs:c.fontSize,lh:c.lineHeight,ff:c.fontFamily.split(',')[0]});
    [...el.children].forEach(k=>walk(k,d+1));
  };
  walk(art,0);
  return JSON.stringify({vars, env: env.slice(0,34)});
})()
"""

async def main():
    pg = await cdp._open()
    await pg.goto("http://127.0.0.1:8917/index.html")
    d = json.loads(await pg.eval(Q))
    print("=== CSS vars ===")
    for k,v in d['vars'].items(): print(f"  {k:22} = {v}")
    print("\n=== article inner ===")
    for e in d['env']:
        print(f"{'  '*e['d']}{e['tag']:8} x={e['x']:5} w={e['w']:5} mt={e['mt']:8} mb={e['mb']:8} fs={e['fs']:7} lh={e['lh']:8} {e['ff'][:16]:18} .{e['cls']}")
    await pg.send("Browser.close")

cdp.run(main)
