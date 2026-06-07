from ph_music.data_io import load_song_nodes, list_songs
from ph_music.verify import analyze_song, intervals

NAME = "J-Sanghyeondodeuri_Geomungo_part"

def test_showcase_song_loads():
    assert NAME in list_songs()
    assert len(load_song_nodes(NAME)) > 100
    assert all(p != "rest" for p, _ in load_song_nodes(NAME))

def test_showcase_counts_7_4_3():
    res = analyze_song(NAME)
    assert (len(res["d1"]), len(res["d3"]), len(res["d2"])) == (7, 4, 3)

def test_showcase_c1_interval_matches_paper():
    # Paper Table 1 #5 J-Sanghyeondodeuri geomungo C1 = [1/3, 2/3]
    res = analyze_song(NAME)
    d1 = intervals(res, "d1")
    assert any(abs(b - 1/3) < 1e-3 and abs(d - 2/3) < 1e-3 for b, d in d1)
