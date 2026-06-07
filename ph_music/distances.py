import heapq
import numpy as np
import networkx as nx
from collections import deque


def _min_edge_path(G, src, dst):
    """Return the unique minimal-edge path from src to dst by vertex ordering.

    BFS from src, tracking distance. Among equal-distance predecessors,
    always pick the smallest-index one to form a canonical path.
    """
    dist = {src: 0}
    q = deque([src])
    while q:
        u = q.popleft()
        for v in sorted(G.neighbors(u)):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    if dst not in dist:
        raise nx.NetworkXNoPath(f"{src}->{dst}")
    path = [dst]
    cur = dst
    while cur != src:
        preds = sorted(p for p in G.neighbors(cur) if dist.get(p, 1e18) == dist[cur] - 1)
        cur = preds[0]
        path.append(cur)
    path.reverse()
    return path


def d1_pair(G, u, v):
    """d1: sum of weights along the minimal-edge-count path (vertex-ordering tie-break)."""
    if u == v:
        return 0.0
    path = _min_edge_path(G, u, v)
    return float(sum(G[a][b]["weight"] for a, b in zip(path, path[1:])))


def d2_pair(G, u, v):
    """d2: minimum total weight path (weighted Dijkstra)."""
    if u == v:
        return 0.0
    return float(nx.dijkstra_path_length(G, u, v, weight="weight"))


def d3_pair(G, u, v):
    """d3: minimum weight among all minimum-edge-count paths.

    Uses lexicographic (hops, weight) Dijkstra so it naturally selects
    the path with fewest hops first, then minimum weight among those.
    """
    if u == v:
        return 0.0
    best = {}
    pq = [(0, 0.0, u)]
    while pq:
        hops, w, x = heapq.heappop(pq)
        if x in best and best[x] <= (hops, w):
            continue
        best[x] = (hops, w)
        if x == v:
            return float(w)
        for y in G.neighbors(x):
            cand = (hops + 1, w + G[x][y]["weight"])
            if y not in best or cand < best[y]:
                heapq.heappush(pq, (cand[0], cand[1], y))
    raise nx.NetworkXNoPath(f"{u}->{v}")


def distance_matrices(G):
    """Compute all three n×n distance matrices for graph G.

    Returns (M1, M2, M3) as numpy arrays where:
      M1[i,j] = d1_pair(G, i, j)
      M2[i,j] = d2_pair(G, i, j)
      M3[i,j] = d3_pair(G, i, j)
    """
    n = G.number_of_nodes()
    M1, M2, M3 = (np.zeros((n, n)) for _ in range(3))
    for i in range(n):
        for j in range(i + 1, n):
            a, b, c = d1_pair(G, i, j), d2_pair(G, i, j), d3_pair(G, i, j)
            M1[i, j] = M1[j, i] = a
            M2[i, j] = M2[j, i] = b
            M3[i, j] = M3[j, i] = c
    return M1, M2, M3
