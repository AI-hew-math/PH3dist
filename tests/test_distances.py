import itertools, networkx as nx, numpy as np
from ph_music.distances import d1_pair, d2_pair, d3_pair, distance_matrices

def _triangle():
    # Example 3.11: a-b=1, a-c=1, b-c=10
    G = nx.Graph()
    G.add_edge(0, 1, weight=1.0)   # a-b
    G.add_edge(0, 2, weight=1.0)   # a-c
    G.add_edge(1, 2, weight=10.0)  # b-c
    return G

def test_example_3_11_triangle():
    G = _triangle()
    assert d1_pair(G, 1, 2) == 10.0
    assert d3_pair(G, 1, 2) == 10.0
    assert d2_pair(G, 1, 2) == 2.0

def test_prop_3_12_ordering_random():
    rng = np.random.default_rng(0)
    for _ in range(20):
        G = nx.gnp_random_graph(7, 0.5, seed=int(rng.integers(1e6)))
        if not nx.is_connected(G):
            continue
        for (u, v) in G.edges():
            G[u][v]["weight"] = float(rng.integers(1, 9))
        for u, v in itertools.combinations(G.nodes(), 2):
            d1, d2, d3 = d1_pair(G,u,v), d2_pair(G,u,v), d3_pair(G,u,v)
            assert d2 <= d3 + 1e-9 <= d1 + 1e-9

def test_distance_matrices_shape_symmetry():
    G = _triangle()
    M1, M2, M3 = distance_matrices(G)
    for M in (M1, M2, M3):
        assert M.shape == (3, 3)
        assert np.allclose(M, M.T)
        assert np.allclose(np.diag(M), 0)
