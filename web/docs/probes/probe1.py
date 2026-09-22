import sys, json; sys.path.insert(0,'/tmp')
import cdp, asyncio

OUTLINE = r"""
(() => {
  const out=[];
  const walk=(el,d)=>{
    if(d>4) return;
    const r=el.getBoundingClientRect();
    if(r.width<40||r.height<8) return;
    const cs=getComputedStyle(el);
    const cn=(el.getAttribute('class')||'').toString();
    out.push({d, tag:el.tagName.toLowerCase(), cls:cn.slice(0,95),
      w:Math.round(r.width), h:Math.round(r.height), x:Math.round(r.x), y:Math.round(r.y+scrollY),
      pos:cs.position});
    [...el.children].forEach(c=>walk(c,d+1));
  };
  walk(document.body,0);
  return JSON.stringify(out.slice(0,140));
})()
"""

async def main():
    pg = await cdp._open()
    await pg.goto("http://127.0.0.1:8917/index.html")
    data = json.loads(await pg.eval(OUTLINE))
    for e in data:
        print(f"{'  '*e['d']}{e['tag']:6} x={e['x']:5} y={e['y']:6} {e['w']:5}x{e['h']:<5} {e['pos']:8} .{e['cls']}")
    await cdp.asyncio.sleep(0)

cdp.run(main)
