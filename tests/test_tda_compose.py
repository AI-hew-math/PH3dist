from ph_music.verify import analyze_song
from ph_music.tda_compose import algorithm_a, overlap_matrices, timeline_indices

SONG = "J-Sanghyeondodeuri_Geomungo_part"

def test_algorithm_a_length_and_distance_varies():
    res = analyze_song(SONG)
    d = len(timeline_indices(SONG, res["graph"]))
    a1 = algorithm_a(res, "d1", SONG, s=2, seed=0)
    a2 = algorithm_a(res, "d2", SONG, s=2, seed=0)
    assert len(a1) == len(a2) == d > 0
    assert sum(x != y for x, y in zip(a1, a2)) > 0.2 * d   # distance changes the composition

def test_overlap_coverage_ordering():
    res = analyze_song(SONG)
    tl = timeline_indices(SONG, res["graph"])
    cov = {}
    for dk in ("d1", "d2"):
        _, _, m_bin, _ = overlap_matrices(res, dk, tl, s=2)
        cov[dk] = (m_bin.sum(0) > 0).mean()
    assert cov["d1"] >= cov["d2"]   # d1 retains more cycles, so more of the timeline is covered
