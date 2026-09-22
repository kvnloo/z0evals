import sys, json; sys.path.insert(0,'/tmp')
import cdp
Q = r"""
(() => {
  const pick=(part)=>[...document.querySelectorAll('[class*="study-module"][class*="'+part+'"]')];
  const out={};
  const svgSummary=(root)=>{ if(!root) return null;
    const svg=root.tagName==='svg'?root:root.querySelector('svg');
    if(!svg) return {none:true};
    const kids={};
    [...svg.children].forEach(c=>{const k=c.tagName+ (c.getAttribute('class')?('.'+c.getAttribute('class')):'');
      kids[k]=(kids[k]||0)+1;});
    const txt=[...svg.querySelectorAll('text')].slice(0,6).map(t=>t.textContent);
    const paths=[...svg.querySelectorAll('path')].slice(0,3).map(p=>({d:(p.getAttribute('d')||'').slice(0,90),sw:p.getAttribute('stroke-width'),st:p.getAttribute('stroke'),fill:p.getAttribute('fill'),op:p.getAttribute('opacity')}));
    const lines=[...svg.querySelectorAll('line')].slice(0,3).map(l=>({x1:l.getAttribute('x1'),y1:l.getAttribute('y1'),x2:l.getAttribute('x2'),y2:l.getAttribute('y2'),sw:l.getAttribute('stroke-width'),st:l.getAttribute('stroke')}));
    const rects=[...svg.querySelectorAll('rect')].slice(0,3).map(r=>({w:r.getAttribute('width'),h:r.getAttribute('height'),fill:r.getAttribute('fill'),rx:r.getAttribute('rx')}));
    const circles=[...svg.querySelectorAll('circle')].slice(0,3).map(r=>({r:r.getAttribute('r'),fill:r.getAttribute('fill'),stroke:r.getAttribute('stroke'),sw:r.getAttribute('stroke-width')}));
    return {viewBox:svg.getAttribute('viewBox'),par:svg.getAttribute('preserveAspectRatio'),childTags:kids,texts:txt,paths,lines,rects,circles,
      svgCount:svg.querySelectorAll('svg').length};
  };
  for (const part of ['corpusPlot','errorPlot','forecastCurve','matrixPlot','replayPlot','progressPlot']) {
    const els=pick(part);
    out[part]={count:els.length, summary: els[0]?svgSummary(els[0]):null};
  }
  const mb=pick('modelBoard')[0];
  out.modelBoard = mb? {html: mb.outerHTML.slice(0,2600)} : null;
  const pb=pick('profileBoard')[0];
  out.profileBoard = pb? {html: pb.outerHTML.slice(0,1800)} : null;
  const hc=pick('holdoutControl')[0];
  out.holdout = hc? {html: hc.outerHTML.slice(0,1200)} : null;
  return JSON.stringify(out);
})()
"""
async def main():
    pg=await cdp._open(); await pg.goto("http://127.0.0.1:8917/index.html")
    d=json.loads(await pg.eval(Q))
    for k,v in d.items():
        if k in ('modelBoard','profileBoard','holdout'):
            print(f"\n===== {k} =====");print((v or {}).get('html','<none>') if v else '<none>')
        else:
            print(f"\n===== {k}  (n={v['count']}) =====")
            print(json.dumps(v['summary'],indent=1)[:1500] if v['summary'] else '  <none>')
    await pg.send("Browser.close")
cdp.run(main)
