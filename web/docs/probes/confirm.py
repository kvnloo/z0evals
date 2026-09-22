import sys, json; sys.path.insert(0,'/tmp')
import cdp
Q = r"""
(() => {
  const ps=[...document.querySelectorAll('.article-body p')]
    .filter(e=>(e.textContent||'').length>150 && !e.closest('figure') && !e.closest('.callout') && !e.closest('.headline'));
  const p=ps[0]; const c=getComputedStyle(p);
  const h2=[...document.querySelectorAll('.article-body h2')][0];
  const h2c=getComputedStyle(h2);
  const h3=[...document.querySelectorAll('.article-body h3')][0];
  const h3c=getComputedStyle(h3);
  const rail=document.querySelector('.rail');
  const rl=document.querySelector('.toc-link-frog');
  const rlc=getComputedStyle(rl);
  const rng=document.querySelector('input[type=range]');
  const rngc=getComputedStyle(rng);
  const acc=document.querySelector('.title-accent-line');
  return JSON.stringify({
    proseP:{fs:c.fontSize, lh:c.lineHeight, mb:c.marginBottom, ff:c.fontFamily.split(',')[0]},
    proseH2:{fs:h2c.fontSize, lh:h2c.lineHeight, fw:h2c.fontWeight, mt:h2c.marginTop, mb:h2c.marginBottom},
    proseH3:{fs:h3c.fontSize, lh:h3c.lineHeight, fw:h3c.fontWeight, mt:h3c.marginTop, mb:h3c.marginBottom},
    rail:{pos:getComputedStyle(rail).position, top:getComputedStyle(rail).top, w:getComputedStyle(rail).width, x:Math.round(rail.getBoundingClientRect().x)},
    tocLink:{fs:rlc.fontSize, lh:rlc.lineHeight, color:rlc.color, x:Math.round(rl.getBoundingClientRect().x), w:Math.round(rl.getBoundingClientRect().width)},
    range:{w:rngc.width, h:rngc.height, accent:rngc.accentColor, label:rng.getAttribute('aria-label')},
    accentDisplay: acc?getComputedStyle(acc).display:null,
    headingFrogs: document.querySelectorAll('.heading-frog-link').length,
    headingWithFrog: document.querySelectorAll('.heading-with-frog').length,
    frogPaths: document.querySelector('.toc-frog')?document.querySelector('.toc-frog').querySelectorAll('path').length:0,
    fab: !!document.querySelector('.mobile-toc-fab'),
    figures: document.querySelectorAll('figure, .figure').length,
  });
})()
"""
async def main():
    pg=await cdp._open(); await pg.goto("http://127.0.0.1:8921/")
    print(json.dumps(json.loads(await pg.eval(Q)),indent=1))
    await pg.send("Browser.close")
cdp.run(main)
