import itertools
import networkx as nx


def _edges_sorted(D):
    n = len(D)
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    edges.sort(key=lambda e: (D[e[0]][e[1]], e))
    return edges


def h1_persistence(D, tol=1e-9):
    n = len(D)
    edges = _edges_sorted(D)
    edge_index = {e: k for k, e in enumerate(edges)}  # filtration rank

    # ---- births + representative cycles via union-find spanning forest ----
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    forest = nx.Graph()
    forest.add_nodes_from(range(n))
    births = {}  # birth_edge (i,j) -> dict(birth, cycle)
    for (i, j) in edges:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj
            forest.add_edge(i, j)          # negative edge (H0)
        else:
            cyc = nx.shortest_path(forest, i, j) + [i]   # close the loop
            births[(i, j)] = {"birth": float(D[i][j]), "cycle": cyc[:-1]}

    # ---- deaths via Z/2 reduction of boundary_2 ----
    tris = []
    for (a, b, c) in itertools.combinations(range(n), 3):
        f = max(D[a][b], D[a][c], D[b][c])
        tris.append((f, (a, b, c)))
    tris.sort(key=lambda t: (t[0], t[1]))

    def tri_boundary(t):
        a, b, c = t
        es = [(a, b), (a, c), (b, c)]
        return set(edge_index[e] for e in es)

    low_to_col = {}  # pivot edge-rank -> reduced column (set)
    death_of = {}    # edge-rank -> death filtration
    for f, t in tris:
        col = tri_boundary(t)
        while col:
            low = max(col)
            if low in low_to_col:
                col ^= low_to_col[low]
            else:
                low_to_col[low] = col
                if low not in death_of:
                    death_of[low] = f
                break

    # ---- assemble bars (finite, positive-persistence H1) ----
    bars = []
    for e, info in births.items():
        rank = edge_index[e]
        death = death_of.get(rank, float("inf"))
        if death - info["birth"] > tol:
            bars.append({"birth": info["birth"], "death": death,
                         "birth_edge": e, "cycle": info["cycle"]})
    bars.sort(key=lambda b: (b["birth"], b["death"]))
    return bars
