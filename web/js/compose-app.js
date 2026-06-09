/* "Compose from your own piece" — fully client-side.
   Parse MIDI/MusicXML -> TDA pipeline (web/js/tda.js) -> Algorithm A (instant) and
   Algorithm B (TensorFlow.js, trained in-browser) -> play on real geomungo (Web Audio). */
(function () {
  "use strict";
  const ORDER = ["d1", "d3", "d2"];
  const SAMPLE_MIDIS = [39, 41, 44, 46, 48, 49, 51, 53, 55, 56, 58, 60, 62, 63, 65, 67];
  const CAP = 200;            // cap input length (keeps PH + ANN fast)
  const EXCERPT = 56;         // playback excerpt length (notes)
  const $ = (id) => document.getElementById(id);
  const status = (m) => { const e = $("tryStatus"); if (e) e.textContent = m; };

  // node label -> [midi, quarterLength]; labels are either [midi, ql] (uploads)
  // or [pitch-string, "n/12"] (presets, the paper's exact node representation).
  const STEP_S = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
  function pitchToMidi(s) {
    if (typeof s === "number") return s;
    const m = String(s).match(/^([A-G])([#-]*)(-?\d+)$/); if (!m) return 60;
    let semi = STEP_S[m[1]]; for (const c of m[2]) semi += (c === "#" ? 1 : -1);
    return 12 * (parseInt(m[3]) + 1) + semi;
  }
  function noteMidiQL(label) {
    const midi = pitchToMidi(label[0]);
    let ql = label[1];
    if (typeof ql !== "number") { const p = String(ql).split("/"); ql = p.length === 2 ? (+p[0]) / (+p[1]) : parseFloat(ql); }
    return [midi, ql || 1];
  }

  let ctx = null, buffers = {}, presets = {}, song = null, res = null;
  let comps = { A: {}, B: {} }, sources = [];

  // ---------- audio ----------
  async function ensureAudio() {
    if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (ctx.state === "suspended") await ctx.resume();
    const missing = SAMPLE_MIDIS.filter((m) => !buffers[m]);
    if (missing.length) {
      status("loading geomungo samples…");
      for (const m of missing) {
        const r = await fetch("audio/geomungo/geo_" + m + ".wav");
        buffers[m] = await ctx.decodeAudioData(await r.arrayBuffer());
      }
      status("");
    }
  }
  // play/pause player over Web Audio (scheduled buffer sources, pausable by offset)
  const nearest = (m) => SAMPLE_MIDIS.reduce((a, b) => Math.abs(b - m) < Math.abs(a - m) ? b : a);
  const player = { key: null, btn: null, sched: null, total: 0, offset: 0, startAt: 0, playing: false, timer: null };
  function killSources() { sources.forEach((s) => { try { s.stop(); } catch (e) {} }); sources = []; if (player.timer) { clearTimeout(player.timer); player.timer = null; } }
  function setBtn(btn, playing) {
    if (!btn) return;
    if (!btn.dataset.base) btn.dataset.base = btn.textContent;
    btn.textContent = playing ? "⏸ Pause" : btn.dataset.base;
    btn.classList.toggle("playing", playing);
  }
  function buildSchedule(notes, tempo) {
    const qps = (tempo || 96) / 60; let t = 0; const sch = [];
    for (const label of notes) { const [midi, ql] = noteMidiQL(label); const dur = Math.max(0.12, ql / qps); sch.push({ s: t, midi, dur }); t += dur; }
    return { sch, total: t };
  }
  function resume() {
    player.playing = true; setBtn(player.btn, true);
    player.startAt = ctx.currentTime - player.offset + 0.05; sources = [];
    for (const n of player.sched) {
      if (n.s < player.offset - 1e-3) continue;
      const when = player.startAt + n.s, nb = nearest(n.midi);
      const src = ctx.createBufferSource(); src.buffer = buffers[nb]; src.playbackRate.value = Math.pow(2, (n.midi - nb) / 12);
      const g = ctx.createGain(); src.connect(g); g.connect(ctx.destination);
      g.gain.setValueAtTime(0.9, when); g.gain.setValueAtTime(0.9, when + n.dur + 0.32); g.gain.linearRampToValueAtTime(0, when + n.dur + 0.5);
      src.start(when); src.stop(when + n.dur + 0.55); sources.push(src);
    }
    player.timer = setTimeout(finishPlayback, (player.total - player.offset) * 1000 + 700);
  }
  function pausePlayback() { if (!player.playing) return; player.offset += ctx.currentTime - player.startAt; if (player.offset < 0) player.offset = 0; player.playing = false; killSources(); setBtn(player.btn, false); }
  function finishPlayback() { killSources(); if (player.btn) setBtn(player.btn, false); player.key = null; player.btn = null; player.offset = 0; player.playing = false; }
  function stopPlayback() { killSources(); if (player.btn) setBtn(player.btn, false); player.key = null; player.btn = null; player.offset = 0; player.playing = false; player.sched = null; }
  async function toggle(key, notes, btn) {
    if (!notes) return;
    await ensureAudio();
    if (player.key === key) { if (player.playing) pausePlayback(); else { player.btn = btn; resume(); } return; }
    stopPlayback();
    player.key = key; player.btn = btn; const b = buildSchedule(notes, 96); player.sched = b.sch; player.total = b.total; player.offset = 0;
    resume();
  }

  // ---------- parsing ----------
  const quantQL = (ql) => Math.max(0.25, Math.round(Math.max(0.125, ql) / 0.25) * 0.25);
  async function parseMidi(buf) {
    const M = window.Midi && (window.Midi.Midi || window.Midi);
    if (!M) throw new Error("MIDI library not loaded");
    const midi = new M(buf), ppq = (midi.header && midi.header.ppq) || 480;
    let ns = [];
    midi.tracks.forEach((tr) => tr.notes.forEach((n) => ns.push({ t: n.ticks, midi: n.midi, dt: n.durationTicks })));
    if (!ns.length) throw new Error("no notes in MIDI");
    ns.sort((a, b) => a.t - b.t || b.midi - a.midi);
    const seq = []; let last = -1;
    for (const n of ns) if (n.t !== last) { seq.push([n.midi, quantQL(n.dt / ppq)]); last = n.t; }  // melody: top note per onset
    return seq;
  }
  function parseMusicXML(text) {
    const doc = new DOMParser().parseFromString(text, "application/xml");
    if (doc.querySelector("parsererror")) throw new Error("invalid XML");
    const part = doc.querySelector("part"); if (!part) throw new Error("no <part> in MusicXML");
    const STEP = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
    const seq = []; let div = 1;
    part.querySelectorAll("measure").forEach((meas) => {
      const d = meas.querySelector("attributes > divisions"); if (d) div = parseInt(d.textContent) || div;
      meas.querySelectorAll("note").forEach((note) => {
        if (note.querySelector("chord")) return;
        const durEl = note.querySelector("duration"); const ql = durEl ? parseInt(durEl.textContent) / div : 0;
        if (note.querySelector("rest")) return;
        const p = note.querySelector("pitch"); if (!p) return;
        const step = p.querySelector("step").textContent.trim();
        const oct = parseInt(p.querySelector("octave").textContent);
        const alt = p.querySelector("alter") ? parseInt(p.querySelector("alter").textContent) : 0;
        seq.push([12 * (oct + 1) + STEP[step] + alt, quantQL(ql)]);
      });
    });
    if (!seq.length) throw new Error("no notes in MusicXML");
    return seq;
  }

  // ---------- Algorithm B (TensorFlow.js) ----------
  async function algorithmB(dk, s, seed, epochs) {
    const G = res.G, tl = TDA.timelineIndices(song, G), d = tl.length, q = G.n;
    const ov = TDA.overlap(res, dk, tl, s), cyc = ov.cycSets, surv = ov.surv, k = cyc.length;
    if (k === 0) return TDA.algorithmA(res, dk, song, s, seed);
    const Mint = surv.map((row, i) => row.map((b, j) => (b ? tl[j] : -1)));
    const L = tl.slice();
    const ntr = Math.max(1, Math.floor(0.7 * d));
    const Xarr = [], Yarr = [];
    for (let i = 0; i < ntr; i++) {
      const xv = new Array(k * d);
      for (let a = 0; a < k; a++) for (let j = 0; j < d; j++) xv[a * d + j] = (Mint[a][(i + j) % d] + 1) / q;
      const yv = new Array(d); for (let j = 0; j < d; j++) yv[j] = L[(i + j) % d];
      Xarr.push(xv); Yarr.push(yv);
    }
    const xs = tf.tensor2d(Xarr), ys = tf.tensor2d(Yarr, [ntr, d], "int32");
    const model = tf.sequential();
    model.add(tf.layers.dense({ inputShape: [k * d], units: 128, activation: "relu" }));
    model.add(tf.layers.dense({ units: 128, activation: "relu" }));
    model.add(tf.layers.dense({ units: d * q }));
    const opt = tf.train.adam(0.005);
    for (let e = 0; e < epochs; e++) {
      tf.tidy(() => opt.minimize(() => {
        const logits = model.apply(xs).reshape([ntr, d, q]);
        return tf.losses.softmaxCrossEntropy(tf.oneHot(ys, q), logits);
      }));
      if (e % 25 === 0) await tf.nextFrame();
    }
    const r = TDA.rng(seed + 7), sv = new Float32Array(k * d);
    for (let i = 0; i < k; i++) {
      const nodes = [...cyc[i]].sort((a, b) => a - b);
      for (let j = 0; j < d; j++) { const val = surv[i][j] ? nodes[Math.floor(r() * nodes.length)] : -1; sv[i * d + j] = (val + 1) / q; }
    }
    const out = tf.tidy(() => model.apply(tf.tensor2d([Array.from(sv)])).reshape([d, q]).argMax(1).arraySync());
    xs.dispose(); ys.dispose(); model.dispose();
    return out;
  }

  // ---------- pipeline + UI ----------
  function loadSong(notes, name) {
    stopPlayback();
    if (notes.length > CAP) notes = notes.slice(0, CAP);
    song = notes; comps = { A: {}, B: {} };
    status("analyzing " + notes.length + " notes…");
    setTimeout(() => {
      try {
        res = TDA.analyze(song);
        const N = Math.min(EXCERPT, song.length);
        for (const k of ORDER) comps.A[k] = TDA.indicesToNotes(res, TDA.algorithmA(res, k, song, 2, 0)).slice(0, N);
        render(name);
        status("done — cycles " + ORDER.map((k) => res[k].length).join("→") + "  (click ▶, then train Algorithm B)");
      } catch (e) { status("error: " + e.message); }
    }, 15);
  }

  function render(name) {
    const box = $("tryResult"); box.innerHTML = "";
    const h = document.createElement("h3");
    h.textContent = (name || "your piece") + " — surviving cycles " + ORDER.map((k) => res[k].length).join(" → ");
    box.appendChild(h);
    const rows = document.createElement("div"); rows.className = "tryrows";
    const SUB = { d1: "₁", d3: "₃", d2: "₂" };
    for (const k of ORDER) {
      const row = document.createElement("div"); row.className = "tryrow";
      const lab = document.createElement("span"); lab.className = "lab " + k;
      lab.textContent = "d" + SUB[k] + " — " + res[k].length + " cycles"; row.appendChild(lab);
      const a = document.createElement("button"); a.className = "btn small"; a.textContent = "▶ Algorithm A";
      a.onclick = () => toggle("A:" + k, comps.A[k], a); row.appendChild(a);
      const b = document.createElement("button"); b.className = "btn small ghost"; b.id = "bbtn_" + k;
      b.textContent = "▶ Algorithm B"; b.disabled = true;
      b.onclick = () => { if (comps.B[k]) toggle("B:" + k, comps.B[k], b); }; row.appendChild(b);
      rows.appendChild(row);
    }
    box.appendChild(rows);
    const bar = document.createElement("div"); bar.style.cssText = "display:flex;gap:10px;flex-wrap:wrap;margin-top:6px";
    const train = document.createElement("button");
    train.className = "btn"; train.textContent = "Train Algorithm B (ANN, in-browser)";
    train.onclick = () => trainB(train); bar.appendChild(train);
    const reset = document.createElement("button");
    reset.className = "btn ghost"; reset.textContent = "↺ Reset";
    reset.onclick = () => { stopPlayback(); song = null; res = null; comps = { A: {}, B: {} }; box.innerHTML = ""; status("cleared — pick a preset or upload a file"); };
    bar.appendChild(reset);
    box.appendChild(bar);
  }

  async function trainB(btn) {
    if (typeof tf === "undefined") { status("TensorFlow.js not loaded"); return; }
    btn.disabled = true; const N = Math.min(EXCERPT, song.length);
    for (const k of ORDER) {
      status("training Algorithm B for " + k.toUpperCase() + " (ANN)…");
      try {
        const seq = await algorithmB(k, 2, 0, 200);
        comps.B[k] = TDA.indicesToNotes(res, seq).slice(0, N);
        const bb = $("bbtn_" + k); if (bb) bb.disabled = false;
      } catch (e) { status("Algorithm B error: " + e.message); btn.disabled = false; return; }
      await new Promise((r) => setTimeout(r, 5));
    }
    status("Algorithm B ready — ▶ to compare with A");
    btn.disabled = false;
  }

  // ---------- init ----------
  function init() {
    if (!$("tryResult")) return;
    fetch("data/preset_songs.json").then((r) => r.json()).then((p) => {
      presets = p; const sel = $("presetSel");
      Object.keys(p).forEach((n) => { const o = document.createElement("option"); o.value = n; o.textContent = n; sel.appendChild(o); });
    }).catch(() => {});
    $("loadPreset").onclick = () => { const n = $("presetSel").value; if (presets[n]) loadSong(presets[n].slice(), n); };
    $("fileInput").addEventListener("change", async (e) => {
      const f = e.target.files[0]; if (!f) return;
      try {
        const notes = /\.(mid|midi)$/i.test(f.name) ? await parseMidi(await f.arrayBuffer()) : parseMusicXML(await f.text());
        if (notes.length < 8) { status("piece too short (need ≥ 8 notes)"); return; }
        loadSong(notes, f.name);
      } catch (err) { status("parse error: " + err.message); }
    });
  }
  if (document.readyState !== "loading") init(); else document.addEventListener("DOMContentLoaded", init);
})();
