/* "Compose from your own piece" — fully client-side.
   Parse MIDI/MusicXML (durations snapped to a musical grid) -> TDA pipeline (web/js/tda.js)
   -> Algorithm B (MLP, TensorFlow.js, trained in-browser) -> play on a selectable gugak instrument (Web Audio). */
(function () {
  "use strict";
  const ORDER = ["d1", "d3", "d2"];
  const DCOL = { d1: "#3E8E7E", d3: "#E0A526", d2: "#C8443B" };
  const PIANO = { label: "Piano (피아노)", full: true, sustained: false, ext: "mp3",   // real samples (Salamander Grand Piano, CC-BY); plays any pitch
    midis: [36, 39, 42, 45, 48, 51, 54, 57, 60, 63, 66, 69, 72, 75, 78, 81, 84, 87, 90, 93, 96],
    pitchClasses: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] };
  const DEFAULT_INSTR = { geomungo: { label: "Geomungo (거문고)", sustained: false, pitchClasses: [0, 1, 2, 3, 4, 5, 7, 8, 10], midis: [39, 41, 44, 46, 48, 49, 51, 53, 55, 56, 58, 60, 62, 63, 65, 67] }, piano: PIANO };
  const RANGE_TOL = 5;        // a note > this many semitones from any sample => "not on this instrument" -> piano
  const CAP = 200;            // cap input length (keeps PH + model fast)
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
  function rollWrap(tag, labelNotes, color) {
    const w = document.createElement("div"); w.className = "rollwrap";
    const t = document.createElement("span"); t.className = "rolltag"; t.textContent = tag; w.appendChild(t);
    if (window.pianoRoll) w.appendChild(window.pianoRoll((labelNotes || []).map(noteMidiQL), color));
    return w;
  }

  let ctx = null, buffers = {}, presets = {}, song = null, res = null;
  let comps = { B: {} }, sources = [];
  let instruments = DEFAULT_INSTR, curInst = "geomungo";     // sample sets per gugak instrument (audio/instruments.json)
  const instMidis = () => (instruments[curInst] && instruments[curInst].midis) || [];
  const isFull = () => !!(instruments[curInst] && instruments[curInst].full);     // piano: plays any pitch
  const effInst = () => (isFull() || songOutOfInstrument()) ? "piano" : curInst;  // instrument actually sounded (piano fallback)
  function noteOnInstrument(m) {                             // is pitch m actually playable on the current instrument?
    if (isFull()) return true;
    const I = instruments[curInst]; if (!I) return false;
    if (I.pitchClasses && I.pitchClasses.indexOf(((m % 12) + 12) % 12) < 0) return false;  // a pitch class the instrument doesn't use
    const ms = I.midis || []; if (!ms.length) return false;
    const nb = ms.reduce((a, b) => Math.abs(b - m) < Math.abs(a - m) ? b : a, ms[0]);      // within playable range?
    return Math.abs(m - nb) <= RANGE_TOL;
  }
  const songOutOfInstrument = () => !isFull() && !!song && song.map(noteMidiQL).some((x) => !noteOnInstrument(x[0]));
  function updateInstrWarning() {
    const el = $("instrWarn"); if (!el) return;
    if (songOutOfInstrument()) {
      const lbl = (instruments[curInst] && instruments[curInst].label) || curInst;
      el.textContent = "⚠ " + lbl + " doesn't have some of these pitches, so the trained melody is played on piano instead.";
      el.style.cssText = "background:#fff7e6;border-left:3px solid var(--d3);padding:8px 12px;border-radius:6px;margin:8px 0";
    } else { el.textContent = ""; el.style.cssText = ""; }
  }

  // ---------- audio ----------
  async function ensureAudio() {
    if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (ctx.state === "suspended") await ctx.resume();
    const eff = effInst(), I = instruments[eff]; if (!I || !(I.midis || []).length) return;
    if (!buffers[eff]) buffers[eff] = {};
    const bset = buffers[eff], ext = I.ext || "wav", missing = I.midis.filter((m) => !bset[m]);
    if (missing.length) {
      status("loading " + (I.label || eff) + " samples…");
      for (const m of missing) {
        const r = await fetch("audio/" + eff + "/" + eff + "_" + m + "." + ext);
        bset[m] = await ctx.decodeAudioData(await r.arrayBuffer());
      }
      status("");
    }
  }
  // play/pause player over Web Audio (scheduled buffer sources, pausable by offset)
  const nearest = (m) => instMidis().reduce((a, b) => Math.abs(b - m) < Math.abs(a - m) ? b : a, instMidis()[0]);
  function pianoVoice(when, midi, dur) {                     // synthesized piano (full range; used for the piano option + out-of-range fallback)
    const freq = 440 * Math.pow(2, (midi - 69) / 12), decay = Math.max(dur, 0.16) + 0.35;
    const g = ctx.createGain(); g.connect(ctx.destination);
    g.gain.setValueAtTime(0.0001, when);
    g.gain.exponentialRampToValueAtTime(0.38, when + 0.006); // sharp attack
    g.gain.exponentialRampToValueAtTime(0.0001, when + decay); // piano-like decay
    for (const spec of [[1, 1.0, "triangle"], [2, 0.25, "sine"], [3, 0.08, "sine"]]) {
      const o = ctx.createOscillator(); o.type = spec[2]; o.frequency.value = freq * spec[0];
      const og = ctx.createGain(); og.gain.value = spec[1]; o.connect(og); og.connect(g);
      o.start(when); o.stop(when + decay + 0.02); sources.push(o);
    }
  }
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
    const eff = effInst(), I = instruments[eff] || {}, ems = I.midis || [], sustained = !!I.sustained, bset = buffers[eff] || {};
    const enear = (m) => ems.length ? ems.reduce((a, b) => Math.abs(b - m) < Math.abs(a - m) ? b : a, ems[0]) : -1;
    for (const n of player.sched) {
      if (n.s < player.offset - 1e-3) continue;
      const when = player.startAt + n.s, nb = enear(n.midi);
      if (nb < 0 || !bset[nb]) { pianoVoice(when, n.midi, n.dur); continue; }   // emergency synth fallback if a sample is missing
      const src = ctx.createBufferSource(); src.buffer = bset[nb]; src.playbackRate.value = Math.pow(2, (n.midi - nb) / 12);
      const g = ctx.createGain(); src.connect(g); g.connect(ctx.destination);
      if (sustained) {                                    // blown/bowed tones don't decay -> gate to ~note length so they don't pile up into a chord
        const end = when + n.dur + 0.06;
        g.gain.setValueAtTime(0.0001, when);
        g.gain.linearRampToValueAtTime(0.85, when + 0.02);
        g.gain.setValueAtTime(0.85, Math.max(when + 0.03, end - 0.07));
        g.gain.linearRampToValueAtTime(0.0001, end);
        src.start(when); src.stop(end + 0.05);
      } else {                                            // plucked: let the pluck ring and decay naturally
        g.gain.setValueAtTime(0.9, when); g.gain.setValueAtTime(0.9, when + n.dur + 0.32); g.gain.linearRampToValueAtTime(0, when + n.dur + 0.5);
        src.start(when); src.stop(when + n.dur + 0.55);
      }
      sources.push(src);
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
  // Snap note durations to a 1/12-beat grid: matches the paper's n/12 duration encoding,
  // preserves triplets/dotted values, and collapses float / micro-timing jitter so two notes
  // a fraction of a beat apart map to ONE (pitch,duration) graph node instead of many.
  const DUR_GRID = 12;
  const quantQL = (ql) => Math.max(1 / DUR_GRID, Math.round((ql || 0) * DUR_GRID) / DUR_GRID);
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
    // Walk each measure with a time cursor — <backup>/<forward> rewind/advance it, so multiple
    // voices/staves (e.g. a piano grand staff) are placed at their true onsets instead of being
    // concatenated. Then keep the TOP pitch at each onset -> one melody line (same as the MIDI path).
    const events = []; let div = 1, base = 0;
    part.querySelectorAll("measure").forEach((meas) => {
      const dv = meas.querySelector("attributes > divisions"); if (dv) div = parseInt(dv.textContent) || div;
      let cursor = 0, lastOnset = 0, measLen = 0;
      Array.from(meas.childNodes).forEach((el) => {
        if (el.nodeType !== 1) return;
        const tag = el.tagName.toLowerCase();
        if (tag === "note") {
          const isChord = !!el.querySelector("chord");
          const durEl = el.querySelector("duration"); const dur = durEl ? parseInt(durEl.textContent) || 0 : 0;
          const onset = isChord ? lastOnset : cursor;
          const p = el.querySelector("pitch");
          if (p && !el.querySelector("rest")) {
            const step = p.querySelector("step").textContent.trim();
            const oct = parseInt(p.querySelector("octave").textContent);
            const alt = p.querySelector("alter") ? parseInt(p.querySelector("alter").textContent) : 0;
            events.push({ onset: base + onset, midi: 12 * (oct + 1) + STEP[step] + alt, ql: quantQL(dur / div) });
          }
          if (!isChord) { lastOnset = cursor; cursor += dur; }
          if (cursor > measLen) measLen = cursor;
        } else if (tag === "backup") {
          const d = el.querySelector("duration"); cursor = Math.max(0, cursor - (d ? parseInt(d.textContent) || 0 : 0));
        } else if (tag === "forward") {
          const d = el.querySelector("duration"); cursor += (d ? parseInt(d.textContent) || 0 : 0);
        }
      });
      base += measLen;
    });
    const byOnset = new Map();
    for (const e of events) { const cur = byOnset.get(e.onset); if (!cur || e.midi > cur.midi) byOnset.set(e.onset, e); }
    const seq = [...byOnset.keys()].sort((a, b) => a - b).map((o) => { const e = byOnset.get(o); return [e.midi, e.ql]; });
    if (!seq.length) throw new Error("no notes in MusicXML");
    return seq;
  }

  // ---------- Algorithm B (TensorFlow.js) ----------
  async function algorithmB(dk, s, seed, epochs) {
    const G = res.G, tl = TDA.timelineIndices(song, G), d = tl.length, q = G.n;
    const ov = TDA.overlap(res, dk, tl, s), cyc = ov.cycSets, surv = ov.surv, k = cyc.length;
    if (k === 0) return tl.slice();             // no cycles -> nothing to learn; replay the piece
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
    const TEMP_B = 6;                                   // free-position softmax temperature
    const logits = tf.tidy(() => model.apply(tf.tensor2d([Array.from(sv)])).reshape([d, q]).arraySync());
    xs.dispose(); ys.dispose(); model.dispose();
    const r2 = TDA.rng(seed + 13);
    const out = new Array(d);
    for (let j = 0; j < d; j++) {
      const row = logits[j];
      const anchored = surv.some((rw) => rw[j]);        // a cycle survives here -> keep the learned note
      if (anchored) {
        let bi = 0, bv = row[0];
        for (let c = 1; c < q; c++) if (row[c] > bv) { bv = row[c]; bi = c; }
        out[j] = bi;
      } else {                                          // free position -> improvise (temperature sampling)
        let mx = row[0];
        for (let c = 1; c < q; c++) if (row[c] > mx) mx = row[c];
        let sum = 0; const p = new Array(q);
        for (let c = 0; c < q; c++) { p[c] = Math.exp((row[c] - mx) / TEMP_B); sum += p[c]; }
        let x = r2() * sum, acc = 0, pick = q - 1;
        for (let c = 0; c < q; c++) { acc += p[c]; if (x <= acc) { pick = c; break; } }
        out[j] = pick;
      }
    }
    return out;
  }

  // ---------- pipeline + UI ----------
  function loadSong(notes, name) {
    stopPlayback();
    if (notes.length > CAP) notes = notes.slice(0, CAP);
    song = notes; comps = { B: {} };
    status("analyzing " + notes.length + " notes…");
    setTimeout(() => {
      try {
        res = TDA.analyze(song);
        render(name);
        status("done — cycles " + ORDER.map((k) => res[k].length).join("→") + "  ·  now train to compose");
      } catch (e) { status("error: " + e.message); }
    }, 15);
  }

  function render(name) {
    const box = $("tryResult"); box.innerHTML = "";
    const h = document.createElement("h3");
    h.textContent = (name || "your piece") + " — surviving cycles " + ORDER.map((k) => res[k].length).join(" → ");
    box.appendChild(h);
    const counts = ORDER.map((k) => res[k].length), maxC = Math.max(...counts);
    let advice = "";
    if (maxC === 0) advice = "No robust cycles were found, so each distance just replays your piece. Persistent homology needs repeated structure — try a longer or more repetitive piece (the method is built for repetitive court music).";
    else if (counts[0] === counts[counts.length - 1]) advice = "Only " + maxC + " cycle" + (maxC > 1 ? "s" : "") + ", and the count doesn't drop across the distances, so the three versions will sound nearly identical. The effect is strongest on long, repetitive pieces.";
    if (advice) { const w = document.createElement("p"); w.className = "cap"; w.style.cssText = "background:#fff7e6;border-left:3px solid var(--d3);padding:8px 12px;border-radius:6px;margin:6px 0"; w.textContent = "⚠ " + advice; box.appendChild(w); }
    const rows = document.createElement("div"); rows.className = "tryrows";
    const SUB = { d1: "₁", d3: "₃", d2: "₂" };
    for (const k of ORDER) {
      const row = document.createElement("div"); row.className = "tryrow";
      const head = document.createElement("div"); head.className = "tryhead";
      const lab = document.createElement("span"); lab.className = "lab " + k;
      lab.textContent = "d" + SUB[k] + " — " + res[k].length + " cycles"; head.appendChild(lab);
      const b = document.createElement("button"); b.className = "btn small"; b.id = "bbtn_" + k;
      b.textContent = "▶ Play"; b.disabled = true;
      b.onclick = () => { if (comps.B[k]) toggle("B:" + k, comps.B[k], b); }; head.appendChild(b);
      row.appendChild(head);
      const bh = document.createElement("div"); bh.id = "rollB_" + k; row.appendChild(bh);
      rows.appendChild(row);
    }
    box.appendChild(rows);
    const bar = document.createElement("div"); bar.style.cssText = "display:flex;gap:10px;flex-wrap:wrap";
    const train = document.createElement("button");
    train.className = "btn"; train.textContent = "Start training now!";
    train.onclick = () => trainB(train); bar.appendChild(train);
    const reset = document.createElement("button");
    reset.className = "btn ghost"; reset.textContent = "↺ Reset";
    reset.onclick = () => { stopPlayback(); song = null; res = null; comps = { B: {} }; box.innerHTML = ""; const a = $("tryActions"); if (a) a.innerHTML = ""; status("cleared — pick a preset or upload a file"); updateInstrWarning(); };
    bar.appendChild(reset);
    const actions = $("tryActions"); if (actions) { actions.innerHTML = ""; actions.appendChild(bar); } else box.appendChild(bar);
    updateInstrWarning();
  }

  async function trainB(btn) {
    if (typeof tf === "undefined") { status("TensorFlow.js not loaded"); return; }
    btn.disabled = true; const N = Math.min(EXCERPT, song.length);
    for (const k of ORDER) {
      status("training for " + k.toUpperCase() + "…");
      try {
        const seq = await algorithmB(k, 2, 0, 200);
        comps.B[k] = TDA.indicesToNotes(res, seq).slice(0, N);
        const bb = $("bbtn_" + k); if (bb) bb.disabled = false;
        const bh = $("rollB_" + k); if (bh) { bh.innerHTML = ""; bh.appendChild(rollWrap("B", comps.B[k], DCOL[k])); }
      } catch (e) { status("Algorithm B error: " + e.message); btn.disabled = false; return; }
      await new Promise((r) => setTimeout(r, 5));
    }
    status("composition ready — ▶ to play");
    btn.disabled = false;
  }

  // ---------- init ----------
  function init() {
    if (!$("tryResult")) return;
    fetch("data/preset_songs.json").then((r) => r.json()).then((p) => {
      presets = p; const sel = $("presetSel");
      Object.keys(p).forEach((n) => { const o = document.createElement("option"); o.value = n; o.textContent = n; sel.appendChild(o); });
    }).catch(() => {});
    const fillInstrSel = () => {
      const isel = $("instrSel"); if (!isel) return;
      isel.innerHTML = "";
      Object.keys(instruments).forEach((k) => { const o = document.createElement("option"); o.value = k; o.textContent = instruments[k].label || k; isel.appendChild(o); });
      if (!instruments[curInst]) curInst = Object.keys(instruments)[0];
      isel.value = curInst;
      isel.onchange = () => { stopPlayback(); curInst = isel.value; updateInstrWarning(); };
    };
    fetch("audio/instruments.json").then((r) => r.json()).then((m) => { instruments = Object.assign({}, m, { piano: PIANO }); })
      .catch(() => {}).then(() => { fillInstrSel(); updateInstrWarning(); });
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
