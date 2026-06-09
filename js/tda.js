/* Client-side port of the PH-music pipeline (graph -> d1/d2/d3 distances -> H1
   persistence with representative cycles -> Overlap matrix -> Algorithm A).
   Verified against the Python implementation (ph_music/*) on the showcase piece.
   Algorithm B (ANN) lives in compose-app.js using TensorFlow.js. */
(function (root) {
  "use strict";

  // ---- seeded RNG (mulberry32) ----
  function rng(seed) {
    let a = (seed >>> 0) || 1;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const pick = (r, arr) => arr[Math.floor(r() * arr.length)];

  // ---- graph (music_graph.build_graph) ----
  function buildGraph(noteSeq) {
    const index = new Map(), labels = [];
    const key = (x) => JSON.stringify(x);
    for (const node of noteSeq) {
      const k = key(node);
      if (!index.has(k)) { index.set(k, labels.length); labels.push(node); }
    }
    const n = labels.length;
    const counts = new Map();
    for (let t = 0; t < noteSeq.length - 1; t++) {
      const a = index.get(key(noteSeq[t])), b = index.get(key(noteSeq[t + 1]));
      if (a === b) continue;
      const i = Math.min(a, b), j = Math.max(a, b), kk = i + "," + j;
      counts.set(kk, (counts.get(kk) || 0) + 1);
    }
    const nbrs = Array.from({ length: n }, () => []);
    const wt = Array.from({ length: n }, () => Object.create(null));
    for (const [kk, c] of counts) {
      const [i, j] = kk.split(",").map(Number), w = 1.0 / c;
      nbrs[i].push(j); nbrs[j].push(i); wt[i][j] = w; wt[j][i] = w;
    }
    for (const nb of nbrs) nb.sort((a, b) => a - b);
    return { n, labels, nbrs, wt, index, key };
  }

  // ---- distances (distances.py) ----
  function minEdgePath(G, src, dst) {
    const dist = new Map([[src, 0]]), q = [src];
    for (let h = 0; h < q.length; h++) {
      const u = q[h];
      for (const v of G.nbrs[u]) if (!dist.has(v)) { dist.set(v, dist.get(u) + 1); q.push(v); }
    }
    if (!dist.has(dst)) return null;
    const path = [dst]; let cur = dst;
    while (cur !== src) {
      const preds = G.nbrs[cur].filter(p => dist.has(p) && dist.get(p) === dist.get(cur) - 1);
      cur = preds[0]; path.push(cur);   // nbrs already ascending -> smallest index
    }
    path.reverse(); return path;
  }
  function d1pair(G, u, v) {
    if (u === v) return 0;
    const p = minEdgePath(G, u, v); let s = 0;
    for (let k = 0; k < p.length - 1; k++) s += G.wt[p[k]][p[k + 1]];
    return s;
  }
  function d2pair(G, u, v) {
    if (u === v) return 0;
    const dist = new Array(G.n).fill(Infinity), done = new Array(G.n).fill(false);
    dist[u] = 0;
    for (let it = 0; it < G.n; it++) {
      let x = -1, best = Infinity;
      for (let i = 0; i < G.n; i++) if (!done[i] && dist[i] < best) { best = dist[i]; x = i; }
      if (x < 0) break; done[x] = true; if (x === v) return dist[v];
      for (const y of G.nbrs[x]) { const nd = dist[x] + G.wt[x][y]; if (nd < dist[y]) dist[y] = nd; }
    }
    return dist[v];
  }
  const lex = (a, b) => (a[0] !== b[0]) ? a[0] - b[0] : a[1] - b[1];
  function d3pair(G, u, v) {
    if (u === v) return 0;
    const best = new Array(G.n).fill(null), done = new Array(G.n).fill(false);
    best[u] = [0, 0];
    for (let it = 0; it < G.n; it++) {
      let x = -1, bk = null;
      for (let i = 0; i < G.n; i++) if (!done[i] && best[i] && (bk === null || lex(best[i], bk) < 0)) { bk = best[i]; x = i; }
      if (x < 0) break; done[x] = true; if (x === v) return best[v][1];
      for (const y of G.nbrs[x]) {
        const cand = [best[x][0] + 1, best[x][1] + G.wt[x][y]];
        if (best[y] === null || lex(cand, best[y]) < 0) best[y] = cand;
      }
    }
    return best[v] ? best[v][1] : Infinity;
  }
  function distMatrix(G, fn) {
    const M = Array.from({ length: G.n }, () => new Array(G.n).fill(0));
    for (let i = 0; i < G.n; i++) for (let j = i + 1; j < G.n; j++) { const d = fn(G, i, j); M[i][j] = d; M[j][i] = d; }
    return M;
  }

  // ---- H1 persistence with representative cycles (ph.py) ----
  function forestPath(adj, src, dst) {
    const prev = new Map([[src, -1]]), q = [src];
    for (let h = 0; h < q.length; h++) {
      const u = q[h]; if (u === dst) break;
      for (const v of adj[u]) if (!prev.has(v)) { prev.set(v, u); q.push(v); }
    }
    const path = []; let cur = dst;
    while (cur !== -1) { path.push(cur); cur = prev.get(cur); }
    path.reverse(); return path;
  }
  function h1(D, tol) {
    tol = tol || 1e-9;
    const n = D.length, edges = [];
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) edges.push([i, j]);
    edges.sort((e, f) => (D[e[0]][e[1]] - D[f[0]][f[1]]) || (e[0] - f[0]) || (e[1] - f[1]));
    const edgeIndex = new Map();
    edges.forEach((e, k) => edgeIndex.set(e[0] + "," + e[1], k));
    const parent = Array.from({ length: n }, (_, i) => i);
    const find = (x) => { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; };
    const fAdj = Array.from({ length: n }, () => []);
    const births = [];
    for (const [i, j] of edges) {
      const ri = find(i), rj = find(j);
      if (ri !== rj) { parent[ri] = rj; fAdj[i].push(j); fAdj[j].push(i); }
      else births.push({ edge: [i, j], birth: D[i][j], cycle: forestPath(fAdj, i, j) });
    }
    const tris = [];
    for (let a = 0; a < n; a++) for (let b = a + 1; b < n; b++) for (let c = b + 1; c < n; c++)
      tris.push([Math.max(D[a][b], D[a][c], D[b][c]), a, b, c]);
    tris.sort((x, y) => (x[0] - y[0]) || (x[1] - y[1]) || (x[2] - y[2]) || (x[3] - y[3]));
    const lowToCol = new Map(), deathOf = new Map();
    for (const [f, a, b, c] of tris) {
      let col = new Set([edgeIndex.get(a + "," + b), edgeIndex.get(a + "," + c), edgeIndex.get(b + "," + c)]);
      while (col.size) {
        let low = -1; for (const x of col) if (x > low) low = x;
        if (lowToCol.has(low)) { const o = lowToCol.get(low); for (const x of o) { if (col.has(x)) col.delete(x); else col.add(x); } }
        else { lowToCol.set(low, col); if (!deathOf.has(low)) deathOf.set(low, f); break; }
      }
    }
    const bars = [];
    for (const b of births) {
      const rank = edgeIndex.get(b.edge[0] + "," + b.edge[1]);
      const death = deathOf.has(rank) ? deathOf.get(rank) : Infinity;
      if (death - b.birth > tol) bars.push({ birth: b.birth, death, birth_edge: b.edge, cycle: b.cycle });
    }
    bars.sort((x, y) => (x.birth - y.birth) || (x.death - y.death));
    return bars;
  }

  // ---- analyze: graph + 3 distance PH ----
  function analyze(noteSeq) {
    const G = buildGraph(noteSeq);
    const M = { d1: distMatrix(G, d1pair), d2: distMatrix(G, d2pair), d3: distMatrix(G, d3pair) };
    return { G, matrices: M, d1: h1(M.d1), d2: h1(M.d2), d3: h1(M.d3) };
  }

  // ---- Overlap matrix + Algorithm A (tda_compose.py) ----
  function timelineIndices(noteSeq, G) {
    return noteSeq.map(nd => G.index.get(G.key(nd)));
  }
  function survival(timeline, cycSet, s) {
    const n = timeline.length, surv = new Array(n).fill(false);
    let j = 0;
    while (j < n) {
      if (cycSet.has(timeline[j])) {
        let k = j; while (k < n && cycSet.has(timeline[k])) k++;
        if (k - j >= s) for (let t = j; t < k; t++) surv[t] = true;
        j = k;
      } else j++;
    }
    return surv;
  }
  function overlap(res, dk, timeline, s) {
    const cycSets = res[dk].map(b => new Set(b.cycle));
    const surv = cycSets.map(c => survival(timeline, c, s));   // k x d bool
    return { cycSets, surv };
  }
  function algorithmA(res, dk, noteSeq, s, seed) {
    const G = res.G, tl = timelineIndices(noteSeq, G), d = tl.length;
    const { cycSets, surv } = overlap(res, dk, tl, s);
    const S = [], I = [];
    for (let j = 0; j < d; j++) {
      const sj = []; for (let i = 0; i < cycSets.length; i++) if (surv[i][j]) sj.push(i);
      S.push(sj);
      if (sj.length) {
        let inter = new Set(cycSets[sj[0]]);
        for (let m = 1; m < sj.length; m++) inter = new Set([...inter].filter(x => cycSets[sj[m]].has(x)));
        if (!inter.size) for (const i of sj) for (const x of cycSets[i]) inter.add(x);
        I.push(inter);
      } else I.push(new Set());
    }
    const pool = tl.slice(), r = rng(seed || 0), out = [];
    for (let j = 0; j < d; j++) {
      if (S[j].length) out.push(pick(r, [...I[j]].sort((a, b) => a - b)));
      else {
        const forbidden = new Set();
        if (j > 0 && S[j - 1].length) for (const x of I[j - 1]) forbidden.add(x);
        if (j < d - 1 && S[j + 1].length) for (const x of I[j + 1]) forbidden.add(x);
        let choices = pool.filter(p => !forbidden.has(p)); if (!choices.length) choices = pool;
        out.push(pick(r, choices));
      }
    }
    return out;  // node-index sequence
  }
  const indicesToNotes = (res, idx) => idx.map(i => res.G.labels[i]);

  root.TDA = {
    rng, buildGraph, d1pair, d2pair, d3pair, distMatrix, h1, analyze,
    timelineIndices, survival, overlap, algorithmA, indicesToNotes,
  };
})(typeof module !== "undefined" && module.exports ? module.exports : (this.window = this.window || this));
if (typeof module !== "undefined" && module.exports) module.exports = module.exports.TDA;
