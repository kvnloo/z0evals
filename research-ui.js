(function(){
  const mount=document.getElementById("phase1bChart");
  if(!mount)return;

  const source=mount.dataset.source;
  const buttons=[...document.querySelectorAll("[data-phase-metric]")];
  const NS="http://www.w3.org/2000/svg";

  const short={
    "compiler + hammer2.1_3b":"Hammer 3B",
    "compiler + qwen3.5_4b":"Qwen 4B",
    "compiler + qwen3.5_9b":"Qwen 9B",
    "compiler + hammer2.1_7b":"Hammer 7B",
    "compiler + nemotron_8b":"Nemotron",
    "compiler + functiongemma_270m":"FnGemma",
    "compiler + NanoJev 0.6B":"NanoJev 0.6B",
    "unfiltered + hammer2.1_3b":"Unfiltered"
  };

  function metricValue(row,metric){
    if(metric==="success") return row.success_rate*100;
    if(metric==="latency") return row.warm_p50_ms;
    return row.dangerous;
  }

  function metricLabel(metric){
    if(metric==="success") return "Success · %";
    if(metric==="latency") return "Warm p50 · ms";
    return "Dangerous selections";
  }

  function fmt(v,metric){
    if(metric==="success") return v.toFixed(1)+"%";
    if(metric==="latency") return Math.round(v).toLocaleString()+" ms";
    return String(v);
  }

  function svgEl(name,attrs={}){
    const el=document.createElementNS(NS,name);
    for(const [k,v] of Object.entries(attrs)) el.setAttribute(k,String(v));
    return el;
  }

  function render(rows,metric){
    mount.innerHTML="";
    const W=820,H=330,L=54,R=14,T=30,B=66;
    const innerW=W-L-R, innerH=H-T-B;
    const vals=rows.map(r=>metricValue(r,metric));
    let min=0,max=Math.max(...vals);
    if(metric==="success"){min=45;max=100;}
    if(metric==="latency"){max=Math.ceil(max/500)*500;}
    if(metric==="danger"){max=Math.max(6,max);}

    const svg=svgEl("svg",{viewBox:`0 0 ${W} ${H}`,class:"sb-chart",role:"img","aria-label":metricLabel(metric)});
    const title=svgEl("text",{x:L,y:14,class:"sb-axis-title"});
    title.textContent=metricLabel(metric);
    svg.appendChild(title);

    const yTicks=4;
    for(let i=0;i<=yTicks;i++){
      const frac=i/yTicks;
      const y=T+innerH-(innerH*frac);
      const value=min+(max-min)*frac;
      svg.appendChild(svgEl("line",{x1:L,y1:y,x2:W-R,y2:y,class:"sb-grid"}));
      const txt=svgEl("text",{x:L-10,y:y+4,"text-anchor":"end",class:"sb-axis"});
      txt.textContent=metric==="success"?Math.round(value):Math.round(value).toLocaleString();
      svg.appendChild(txt);
    }

    const points=rows.map((row,i)=>{
      const x=L+(rows.length===1?0:innerW*i/(rows.length-1));
      const v=metricValue(row,metric);
      const y=T+innerH-innerH*((v-min)/(max-min||1));
      return {x,y,v,row};
    });

    const line=svgEl("path",{class:"sb-line"});
    line.setAttribute("d",points.map((p,i)=>`${i?"L":"M"} ${p.x} ${p.y}`).join(" "));
    svg.appendChild(line);

    points.forEach((p,i)=>{
      const g=svgEl("g",{class:"sb-point-group"});
      const c=svgEl("circle",{cx:p.x,cy:p.y,r:4,class:p.row.arm.startsWith("unfiltered")?"sb-point sb-point-dark":"sb-point"});
      const tip=document.createElementNS(NS,"title");
      tip.textContent=`${short[p.row.arm]||p.row.arm}: ${fmt(p.v,metric)}`;
      c.appendChild(tip);
      g.appendChild(c);

      const label=svgEl("text",{x:p.x,y:H-34,"text-anchor":"middle",class:"sb-x"});
      label.textContent=short[p.row.arm]||p.row.arm;
      g.appendChild(label);

      if(p.row.arm==="compiler + hammer2.1_3b"){
        const value=svgEl("text",{x:p.x,y:p.y-10,"text-anchor":"middle",class:"sb-value"});
        value.textContent=fmt(p.v,metric);
        g.appendChild(value);
      }
      svg.appendChild(g);
    });

    mount.appendChild(svg);
    const readout=document.createElement("div");
    readout.className="sb-chart-note";
    readout.textContent=metric==="success"
      ? "Compiler-first Hammer3B ties Qwen4B at 75/84 while staying far faster."
      : metric==="latency"
        ? "Warm latency only. Residency costs are discussed separately below."
        : "The unfiltered Hammer3B arm is the only listed arm with dangerous selections.";
    mount.appendChild(readout);
  }

  fetch(source,{cache:"no-store"})
    .then(r=>{if(!r.ok)throw new Error("HTTP "+r.status);return r.json();})
    .then(data=>{
      const rows=data.bounded_choice||[];
      let metric="success";
      render(rows,metric);
      buttons.forEach(btn=>btn.addEventListener("click",()=>{
        buttons.forEach(x=>x.classList.remove("active"));
        btn.classList.add("active");
        metric=btn.dataset.phaseMetric||"success";
        render(rows,metric);
      }));
    })
    .catch(err=>{
      mount.innerHTML='<p class="figure-copy">Could not load published Phase 1B data: '+String(err)+'</p>';
    });
})();