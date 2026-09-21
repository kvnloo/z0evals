(function(){
  const chart=document.getElementById("phase1bChart");
  if(!chart)return;

  const source=chart.dataset.source;
  const buttons=[...document.querySelectorAll("[data-phase-metric]")];

  function labelFor(arm){
    return arm
      .replace("compiler + ","")
      .replace("unfiltered + ","unfiltered ")
      .replace("hammer2.1_","Hammer ")
      .replace("qwen3.5_","Qwen ")
      .replace("functiongemma_270m","FunctionGemma")
      .replace("nemotron_8b","Nemotron 8B")
      .replace("JEV","JEV")
      .replace("3b","3B")
      .replace("4b","4B")
      .replace("7b","7B")
      .replace("9b","9B");
  }

  function render(rows,metric){
    let max=1;
    if(metric==="latency") max=Math.max(...rows.map(r=>r.warm_p50_ms));
    if(metric==="danger") max=Math.max(1,...rows.map(r=>r.dangerous));

    chart.innerHTML=rows.map(row=>{
      let value,width,display;
      if(metric==="success"){
        value=row.success_rate*100;
        width=value;
        display=value.toFixed(1)+"%";
      } else if(metric==="latency"){
        value=row.warm_p50_ms;
        width=(value/max)*100;
        display=value.toLocaleString()+" ms";
      } else {
        value=row.dangerous;
        width=(value/max)*100;
        display=String(value);
      }
      const cls=row.arm==="compiler + hammer2.1_3b"?" phase-primary":
        row.arm.startsWith("unfiltered")?" phase-warning":"";
      return '<div class="route-row'+cls+'"><span>'+labelFor(row.arm)+'</span>'+
        '<div class="bar-track"><div class="bar-fill" style="width:'+width.toFixed(1)+'%"></div></div>'+
        '<b>'+display+'</b></div>';
    }).join("");
  }

  fetch(source,{cache:"no-store"})
    .then(r=>{if(!r.ok)throw new Error("HTTP "+r.status);return r.json();})
    .then(data=>{
      const rows=data.bounded_choice||[];
      let metric="success";
      render(rows,metric);
      buttons.forEach(btn=>{
        btn.addEventListener("click",()=>{
          buttons.forEach(x=>x.classList.remove("active"));
          btn.classList.add("active");
          metric=btn.dataset.phaseMetric||"success";
          render(rows,metric);
        });
      });
    })
    .catch(err=>{
      chart.innerHTML='<p class="figure-copy">Could not load published Phase 1B data: '+String(err)+'</p>';
    });
})();