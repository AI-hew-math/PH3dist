/* Mini piano-roll: draw a note sequence ([ [midi, quarterLength], ... ]) as an SVG
   so the d1/d3/d2 melodic differences are visible at a glance. Also auto-inserts a
   roll under every pre-rendered <audio data-roll="..."> using data/clip_notes.json. */
(function () {
  "use strict";
  const DCOL = { d1: "#3E8E7E", d3: "#E0A526", d2: "#C8443B" };
  function rollColor(key) {
    if (/d1/.test(key)) return DCOL.d1;
    if (/d3/.test(key)) return DCOL.d3;
    if (/d2/.test(key)) return DCOL.d2;
    return "#1A2238";
  }
  function pianoRoll(notes, color, maxNotes) {
    const NS = "http://www.w3.org/2000/svg", W = 600, H = 56, pad = 4;
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("preserveAspectRatio", "none");
    svg.setAttribute("class", "roll");
    notes = (notes || []).slice(0, maxNotes || 28).filter((n) => n && isFinite(n[0]));
    if (!notes.length) return svg;
    let t = 0; const ev = notes.map(([m, ql]) => { const o = { x: t, m, d: Math.max(0.25, ql || 0.5) }; t += o.d; return o; });
    const total = t || 1;
    const mids = notes.map((n) => n[0]); let lo = Math.min(...mids), hi = Math.max(...mids);
    if (hi === lo) { hi += 2; lo -= 2; }
    const rows = hi - lo + 1, rh = (H - 2 * pad) / rows;
    const X = (v) => pad + (v / total) * (W - 2 * pad), Y = (m) => pad + (hi - m) * rh;
    for (const e of ev) {
      const r = document.createElementNS(NS, "rect");
      r.setAttribute("x", X(e.x).toFixed(1)); r.setAttribute("y", Y(e.m).toFixed(1));
      r.setAttribute("width", Math.max(2, (e.d / total) * (W - 2 * pad) - 1).toFixed(1));
      r.setAttribute("height", Math.max(2.5, rh - 1).toFixed(1));
      r.setAttribute("rx", "1.5"); r.setAttribute("fill", color);
      svg.appendChild(r);
    }
    return svg;
  }
  async function init() {
    const holders = document.querySelectorAll("audio[data-roll]");
    if (!holders.length) return;
    let notes; try { notes = await (await fetch("data/clip_notes.json")).json(); } catch (e) { return; }
    holders.forEach((au) => {
      const key = au.getAttribute("data-roll"), seq = notes[key];
      if (seq) au.insertAdjacentElement("afterend", pianoRoll(seq, rollColor(key)));
    });
  }
  window.pianoRoll = pianoRoll; window.rollColor = rollColor;
  if (document.readyState !== "loading") init(); else document.addEventListener("DOMContentLoaded", init);
})();
