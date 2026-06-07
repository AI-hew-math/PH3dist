import json, os
from ph_music.export_json import export_song

def test_export_song_json(tmp_path):
    p = export_song("01 J-Sangnyeongsan_Geomungo_part(0719)", outdir=str(tmp_path))
    data = json.load(open(p))
    assert {"name","nodes","positions","matrices","persistence"} <= set(data)
    assert set(data["matrices"]) == {"d1","d2","d3"}
    assert set(data["persistence"]) == {"d1","d2","d3"}
    assert len(data["nodes"]) == len(data["positions"])
