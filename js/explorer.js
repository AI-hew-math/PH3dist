const DCOL = {d1:"#3E8E7E", d3:"#E0A526", d2:"#C8443B"};
const ORDER = ["d1","d3","d2"];   // d1 -> d3 -> d2 (distill 7->4->3), consistent with the rest of the page
const SUB = {d1:"₁", d3:"₃", d2:"₂"};            // |bcd₁(d_i)| barcode-cardinality label
const bcd = (k) => "|bcd₁(d" + SUB[k] + ")|";
const INK = "#1A2238";

function heatColor(t){ // blue (low) -> hanji -> vermilion (high)
  const lerp=(a,b,u)=>a+(b-a)*u;
  const A=[43,74,139], B=[250,247,240], C=[200,68,59];
  let r,g,b;
  if(t<0.5){const u=t/0.5; r=lerp(A[0],B[0],u);g=lerp(A[1],B[1],u);b=lerp(A[2],B[2],u);}
  else{const u=(t-0.5)/0.5; r=lerp(B[0],C[0],u);g=lerp(B[1],C[1],u);b=lerp(B[2],C[2],u);}
  return `rgb(${r|0},${g|0},${b|0})`;
}

function panel(titleText, node){
  const d=document.createElement("div"); d.className="panel";
  const h=document.createElement("h4"); h.textContent=titleText;
  d.appendChild(h); d.appendChild(node); return d;
}

function renderHeatmap(M, title, gmax){
  const n=M.length, cell=Math.max(4, Math.floor(300/n)), size=n*cell;
  const c=document.createElement("canvas"); c.width=size; c.height=size;
  const ctx=c.getContext("2d");
  for(let i=0;i<n;i++) for(let j=0;j<n;j++){
    ctx.fillStyle = i===j ? "#2B4A8B" : heatColor(gmax?M[i][j]/gmax:0);
    ctx.fillRect(j*cell,i*cell,cell,cell);
  }
  return panel(title, c);
}

function barcodeSVG(bars, key){
  const NS="http://www.w3.org/2000/svg", W=320, H=Math.max(60,bars.length*16+20), pad=8;
  let max=0; bars.forEach(x=>{if(x.death>max)max=x.death;}); max=max||1;
  const svg=document.createElementNS(NS,"svg"); svg.setAttribute("viewBox",`0 0 ${W} ${H}`);
  bars.slice().sort((a,b)=>a.birth-b.birth).forEach((bar,y)=>{
    const x1=pad+(W-2*pad)*bar.birth/max, x2=pad+(W-2*pad)*bar.death/max, yy=12+y*16;
    const ln=document.createElementNS(NS,"line");
    ln.setAttribute("x1",x1);ln.setAttribute("x2",x2);ln.setAttribute("y1",yy);ln.setAttribute("y2",yy);
    ln.setAttribute("stroke",DCOL[key]);ln.setAttribute("stroke-width","5");ln.setAttribute("stroke-linecap","round");
    svg.appendChild(ln);
  });
  return svg;
}

function renderNetwork(data, key){
  const NS="http://www.w3.org/2000/svg", W=320, H=320, pad=18;
  const pos=data.positions;
  const xs=pos.map(p=>p[0]), ys=pos.map(p=>p[1]);
  const minx=Math.min(...xs),maxx=Math.max(...xs),miny=Math.min(...ys),maxy=Math.max(...ys);
  const sx=v=>pad+(W-2*pad)*((v-minx)/((maxx-minx)||1));
  const sy=v=>pad+(H-2*pad)*(1-(v-miny)/((maxy-miny)||1));
  const svg=document.createElementNS(NS,"svg"); svg.setAttribute("viewBox",`0 0 ${W} ${H}`);
  data.edges.forEach(([u,v])=>{
    const e=document.createElementNS(NS,"line");
    e.setAttribute("x1",sx(pos[u][0]));e.setAttribute("y1",sy(pos[u][1]));
    e.setAttribute("x2",sx(pos[v][0]));e.setAttribute("y2",sy(pos[v][1]));
    e.setAttribute("stroke",INK);e.setAttribute("stroke-opacity","0.12");e.setAttribute("stroke-width","1");
    svg.appendChild(e);
  });
  data.persistence[key].forEach(bar=>{
    const cyc=bar.cycle;
    for(let i=0;i<cyc.length;i++){
      const a=cyc[i], b=cyc[(i+1)%cyc.length];
      const e=document.createElementNS(NS,"line");
      e.setAttribute("x1",sx(pos[a][0]));e.setAttribute("y1",sy(pos[a][1]));
      e.setAttribute("x2",sx(pos[b][0]));e.setAttribute("y2",sy(pos[b][1]));
      e.setAttribute("stroke",DCOL[key]);e.setAttribute("stroke-width","3");e.setAttribute("stroke-opacity","0.95");
      svg.appendChild(e);
    }
  });
  pos.forEach(p=>{const c=document.createElementNS(NS,"circle");
    c.setAttribute("cx",sx(p[0]));c.setAttribute("cy",sy(p[1]));c.setAttribute("r","2.5");
    c.setAttribute("fill",INK);c.setAttribute("fill-opacity","0.5");svg.appendChild(c);});
  return panel(`${bcd(key)} = ${data.persistence[key].length}`, svg);
}

function render(data){
  const cont=id=>{const e=document.getElementById(id); e.innerHTML=""; return e;};
  const m=cont("viz-matrices"), b=cont("viz-barcodes"), nw=cont("viz-networks");
  let gmax=0; ORDER.forEach(k=> data.matrices[k].forEach(row=> row.forEach(v=>{ if(v>gmax) gmax=v; })) );
  ORDER.forEach(k=> m.appendChild(renderHeatmap(data.matrices[k], k.toUpperCase(), gmax)) );
  ORDER.forEach(k=> b.appendChild(panel(`${bcd(k)} = ${data.persistence[k].length}`, barcodeSVG(data.persistence[k], k))) );
  ORDER.forEach(k=> nw.appendChild(renderNetwork(data, k)) );
  document.getElementById("counts").textContent =
    `${bcd("d1")}=${data.persistence.d1.length},  ${bcd("d3")}=${data.persistence.d3.length},  ${bcd("d2")}=${data.persistence.d2.length}`;
}

async function load(slug){ const r=await fetch(`data/${slug}.json`); render(await r.json()); }

async function init(){
  const idx=await (await fetch("data/index.json")).json();
  const sel=document.getElementById("song");
  idx.forEach(s=>{const o=document.createElement("option");o.value=s.slug;o.textContent=s.label;sel.appendChild(o);});
  sel.addEventListener("change",()=>load(sel.value));
  if(idx.length) load(idx[0].slug);
}
document.addEventListener("DOMContentLoaded", init);
