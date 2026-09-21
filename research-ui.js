(function(){
  const names=["deterministic","tiny specialist","bounded scorer","orchestrator"];
  const slider=document.getElementById("complexity");
  const out=document.getElementById("complexityOut");
  const bars=document.getElementById("routeBars");
  function renderBars(){
    if(!slider||!bars)return;
    const x=+slider.value; if(out) out.textContent=x;
    const vals=[
      Math.max(15,92-x*.65),
      Math.max(24,82-Math.abs(x-38)*.45),
      Math.max(20,76-Math.abs(x-58)*.32),
      Math.min(94,28+x*.62)
    ];
    bars.innerHTML=names.map((n,i)=>
      '<div class="route-row"><span>'+n+'</span><div class="bar-track"><div class="bar-fill" style="width:'+vals[i].toFixed(0)+'%"></div></div><b>'+vals[i].toFixed(0)+'</b></div>'
    ).join("");
  }
  if(slider){slider.addEventListener("input",renderBars);renderBars();}

  const pointSets={
    quality:[[14,80,"tiny",1],[38,88,"bounded",0],[66,91,"orchestrator",0],[86,96,"general",0]],
    latency:[[12,92,"tiny",1],[31,76,"bounded",0],[68,38,"orchestrator",0],[88,20,"general",0]],
    cost:[[10,91,"tiny",1],[30,79,"bounded",0],[65,48,"orchestrator",0],[90,28,"general",0]]
  };
  const scatter=document.getElementById("scatter");
  function plot(metric){
    if(!scatter)return;
    scatter.innerHTML=pointSets[metric].map(p=>
      '<span class="point '+(p[3]?'best':'')+'" data-label="'+p[2]+'" style="left:'+p[0]+'%;bottom:'+p[1]+'%"></span>'
    ).join("");
  }
  document.querySelectorAll(".tab").forEach(btn=>{
    btn.addEventListener("click",()=>{
      document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));
      btn.classList.add("active"); plot(btn.dataset.metric);
    });
  });
  plot("quality");

  const lp=document.getElementById("latencyPlot");
  if(lp){
    const sets=[
      ["#446b48",[12,18,24,33,42],45],
      ["#e4572e",[34,49,66,81,92],110],
      ["#315f82",[25,42,63,78,88],175]
    ];
    lp.innerHTML=sets.map(s=>
      '<div class="latency-line" style="bottom:'+s[2]+'px;background:'+s[0]+'">'+
      s[1].map((x,i)=>'<span style="left:'+x+'%;background:'+s[0]+'" title="mock percentile '+(i+1)+'"></span>').join("")+
      '</div>'
    ).join("");
  }

  const replay=document.getElementById("replayTrace");
  if(replay){
    replay.addEventListener("click",()=>{
      const trace=replay.closest(".trace"), steps=[...trace.querySelectorAll(".trace-step")];
      trace.classList.add("replaying"); steps.forEach(s=>s.classList.remove("on"));
      steps.forEach((step,i)=>setTimeout(()=>step.classList.add("on"),250+i*420));
      setTimeout(()=>trace.classList.remove("replaying"),250+steps.length*420+700);
    });
  }
})();