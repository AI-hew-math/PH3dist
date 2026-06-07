from ph_music.data_io import load_song_nodes
from ph_music.music_graph import build_graph
from ph_music.distances import distance_matrices
from ph_music.ph import h1_persistence

def analyze_song(name):
    G = build_graph(load_song_nodes(name))
    M1, M2, M3 = distance_matrices(G)
    return {
        "graph": G,
        "d1": h1_persistence(M1),
        "d2": h1_persistence(M2),
        "d3": h1_persistence(M3),
        "matrices": {"d1": M1, "d2": M2, "d3": M3},
    }

def birth_edge_sets(res):
    """Return (B1, B2, B3): the sets of birth edges for d1, d2, d3.
    Paper Prop 4.2 guarantees B2 ⊆ B3 ⊆ B1."""
    B1 = {b["birth_edge"] for b in res["d1"]}
    B2 = {b["birth_edge"] for b in res["d2"]}
    B3 = {b["birth_edge"] for b in res["d3"]}
    return B1, B2, B3

def intervals(res, key, ndigits=6):
    return sorted((round(b["birth"], ndigits), round(b["death"], ndigits))
                  for b in res[key])
