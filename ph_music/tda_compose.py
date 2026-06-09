"""Machine composition from the PH cycle structure, following the ANN method
(Algorithm B) of Tran-Lee-Jung (2024), arXiv:2203.15468 — adapted to the three
distances d1/d2/d3 of this project.

The seed piece's surviving H1 cycles + its note timeline give an "Overlap matrix"
M^s (cycle x time): cycle Ci "survives" at a position when >=s consecutive notes there
all belong to Ci.  An MLP learns p(note-sequence | Overlap matrix) from the one seed
piece (periodic-extension data augmentation), then composes from a generated seed
Overlap matrix (#2 Element-by-Element variant).  Decoding keeps the learned note at
cycle-anchored positions and temperature-samples the free positions, so distances with
fewer surviving cycles (d2 < d3 < d1) improvise more — distance is a tunable knob on
the composition.
"""
import numpy as np
from ph_music import data_io


# ----------------------------- shared structure -----------------------------
def timeline_indices(song, graph):
    """The piece as a sequence of graph node indices (length d), rests excluded."""
    lab2idx = {tuple(graph.nodes[i]["label"]): i for i in graph.nodes}
    return [lab2idx[tuple(e)] for e in data_io.load_song_nodes(song) if tuple(e) in lab2idx]


def _survival(timeline, cyc, s):
    """Boolean length-d mask: positions inside a run of >=s consecutive notes all in cyc."""
    n = len(timeline)
    surv = np.zeros(n, bool)
    inc = [t in cyc for t in timeline]
    j = 0
    while j < n:
        if inc[j]:
            k = j
            while k < n and inc[k]:
                k += 1
            if k - j >= s:
                surv[j:k] = True
            j = k
        else:
            j += 1
    return surv


def overlap_matrices(res, distance_key, timeline, s):
    """Return (cycles, cyc_sets, M_bin, M_int) for one distance.
    M_bin[i,j]=1 where cycle i survives; M_int[i,j]=timeline node there, else -1."""
    cycles = [list(b["cycle"]) for b in res[distance_key]]
    cyc_sets = [set(c) for c in cycles]
    surv = np.array([_survival(timeline, c, s) for c in cyc_sets], dtype=bool)  # k x d
    if surv.size == 0:
        surv = np.zeros((0, len(timeline)), bool)
    M_bin = surv.astype(int)
    tl = np.array(timeline)
    M_int = np.where(surv, tl[None, :], -1)
    return cycles, cyc_sets, M_bin, M_int


# ----------------------------- Algorithm B (ANN) -----------------------------
def _seed_overlap_int(M_bin, M_int, cyc_sets, seed):
    """Element-by-Element seed Overlap matrix (#2): keep the binary pattern, resample the
    node identity in each surviving cell from that cycle's nodes."""
    rng = np.random.default_rng(seed + 7)
    out = np.full(M_int.shape, -1)
    for i in range(M_bin.shape[0]):
        nodes = sorted(cyc_sets[i])
        cols = np.where(M_bin[i] > 0)[0]
        out[i, cols] = rng.choice(nodes, size=len(cols))
    return out


def algorithm_b(res, distance_key, song, s=2, seed=0, epochs=500, hidden=256,
                temperature=1.0):
    """ANN composition (Tran-Lee-Jung Section 5): MLP learns Overlap matrix -> note
    sequence from the one seed piece, then composes from a generated seed matrix.
    Returns node-index list of length d.

    Distance-sensitive decoding: at positions where a cycle survives ("anchored"),
    keep the learned note (argmax); elsewhere ("free") sample from the softmax at
    `temperature`.  Distances with fewer surviving positions (d2 < d3 < d1) therefore
    improvise at more positions, so the three pieces diverge audibly even though the
    network is trained on one seed melody.  temperature<=0 reproduces pure argmax."""
    import torch
    import torch.nn as nn
    torch.manual_seed(seed)

    G = res["graph"]
    tl = timeline_indices(song, G)
    d = len(tl)
    nodes = sorted(G.nodes())
    node2col = {n: c for c, n in enumerate(nodes)}
    q = len(nodes)
    cycles, cyc_sets, M_bin, M_int = overlap_matrices(res, distance_key, tl, s)
    k = M_int.shape[0]
    if k == 0:                              # no cycles survive -> nothing to learn; replay the piece
        return list(tl)

    def encode(mat):                        # k x d int(node idx or -1) -> normalized k*d vector
        v = np.where(mat >= 0, np.vectorize(lambda x: node2col.get(x, -1))(mat), -1).astype(np.float32)
        v = (v + 1.0) / q                   # -1 -> 0 ; node col c -> (c+1)/q
        return v.reshape(-1)

    L = np.array([node2col[t] for t in tl])          # d note columns
    Mc = np.concatenate([M_int, M_int], axis=1)      # periodic extension (cols)
    Lc = np.concatenate([L, L])
    X = np.stack([encode(Mc[:, i:i + d]) for i in range(d)])         # d x (k*d)
    Y = np.stack([Lc[i:i + d] for i in range(d)])                   # d x d (node columns)
    X = torch.tensor(X, dtype=torch.float32)
    Y = torch.tensor(Y, dtype=torch.long)
    ntr = max(1, int(0.7 * d))
    perm = torch.randperm(d)
    tr = perm[:ntr]

    net = nn.Sequential(
        nn.Linear(k * d, hidden), nn.ReLU(),
        nn.Linear(hidden, hidden), nn.ReLU(),
        nn.Linear(hidden, d * q),
    )
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    lossf = nn.CrossEntropyLoss()
    for _ in range(epochs):
        opt.zero_grad()
        logits = net(X[tr]).view(len(tr), d, q)
        loss = lossf(logits.reshape(-1, q), Y[tr].reshape(-1))
        loss.backward()
        opt.step()

    seed_mat = _seed_overlap_int(M_bin, M_int, cyc_sets, seed)
    surv_pos = (seed_mat >= 0).any(axis=0)          # anchored where a cycle survives
    xs = torch.tensor(encode(seed_mat)[None, :], dtype=torch.float32)
    with torch.no_grad():
        logits = net(xs).view(d, q).numpy()
    rng = np.random.default_rng(seed + 13)
    cols = np.empty(d, dtype=int)
    for j in range(d):
        if surv_pos[j] or temperature <= 0:         # cycle-anchored: keep the learned note
            cols[j] = int(np.argmax(logits[j]))
        else:                                       # free position: improvise
            z = logits[j] / temperature
            z = z - z.max()
            p = np.exp(z); p = p / p.sum()
            cols[j] = int(rng.choice(q, p=p))
    return [nodes[int(c)] for c in cols]


# ----------------------------- to renderable notes -----------------------------
def indices_to_notes(res, idx_seq):
    """Node-index list -> list of (pitch, duration) labels for the geomungo renderer."""
    G = res["graph"]
    return [tuple(G.nodes[i]["label"]) for i in idx_seq]
