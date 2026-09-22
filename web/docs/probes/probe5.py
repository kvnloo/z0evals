import sys, json; sys.path.insert(0,'/tmp')
import cdp
Q = r"""
(() => {
  const cs=getComputedStyle(document.documentElement);
  const names=[];
  for (const sh of document.styleSheets) { try{ for(const r of sh.cssRules){ if(r.style){ for(const p of r.style){ if(p.startsWith('--')) names.push(p);} } } }catch(e){} }
  const uniq=[...new Set(names)];
  const out={};
  for(const n of uniq) out[n]=cs.getPropertyValue(n).trim();
  const keys=Object.keys(out).filter(k=>/^--(space|radius|text|leading|font-weight|tracking|full-width|content-width)/.test(k));
  return JSON.stringify(keys.sort().map(k=>[k,out[k]]));
})()
"""
async def main():
    pg=await cdp._open(); await pg.goto("http://127.0.0.1:8917/index.html")
    for k,v in json.loads(await pg.eval(Q)): print(f"  {k:22} = {v}")
    await pg.send("Browser.close")
cdp.run(main)
