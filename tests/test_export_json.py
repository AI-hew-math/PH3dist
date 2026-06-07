import json, os, math
import networkx as nx
from ph_music import export_json
from ph_music.export_json import export_song

def test_export_song_json(tmp_path):
    p = export_song("01 J-Sangnyeongsan_Geomungo_part(0719)", outdir=str(tmp_path))
    data = json.load(open(p))
    assert {"name","nodes","positions","matrices","persistence"} <= set(data)
    assert set(data["matrices"]) == {"d1","d2","d3"}
    assert set(data["persistence"]) == {"d1","d2","d3"}
    assert len(data["nodes"]) == len(data["positions"])

def test_infinite_death_serializes_to_null(tmp_path, monkeypatch):
    g = nx.Graph()
    g.add_node(0, label=("A", "1"))
    g.add_node(1, label=("B", "1"))
    g.add_edge(0, 1)
    fake = {
        "graph": g,
        "matrices": {"d1": [[0, 1], [1, 0]], "d2": [[0, 1], [1, 0]], "d3": [[0, 1], [1, 0]]},
        "d1": [{"birth": 0.5, "death": float("inf"), "birth_edge": [0, 1], "cycle": [0, 1]}],
        "d2": [], "d3": [],
    }
    monkeypatch.setattr(export_json, "analyze_song", lambda name: fake)
    p = export_json.export_song("fake", outdir=str(tmp_path))
    data = json.load(open(p))
    assert data["persistence"]["d1"][0]["death"] is None
