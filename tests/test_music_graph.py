from ph_music.music_graph import build_graph

def test_build_graph_indices_weights():
    seq = [("A","1"),("B","1"),("A","1"),("B","1"),("C","1")]
    G = build_graph(seq)
    assert G.number_of_nodes() == 3
    assert G.nodes[0]["label"] == ("A","1")
    # A-B occurs 3 times (A->B, B->A, A->B) => weight 1/3
    assert abs(G[0][1]["weight"] - 1/3) < 1e-9
    # B-C occurs once => weight 1
    assert abs(G[1][2]["weight"] - 1.0) < 1e-9

def test_no_self_loops_for_repeated_node():
    seq = [("A","1"),("A","1"),("B","1")]   # A->A is not an edge (ni != nj)
    G = build_graph(seq)
    assert not G.has_edge(0, 0)
    assert G.has_edge(0, 1)
