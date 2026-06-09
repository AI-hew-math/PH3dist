from ph_music.verify import analyze_song
from ph_music.tda_compose import algorithm_b, overlap_matrices, timeline_indices

SONG = "J-Sanghyeondodeuri_Geomungo_part"

def test_algorithm_b_length_and_distance_varies():
    res = analyze_song(SONG)
    d = len(timeline_indices(SONG, res["graph"]))
    b1 = algorithm_b(res, "d1", SONG, s=2, seed=0, epochs=60, temperature=6.0)
    b2 = algorithm_b(res, "d2", SONG, s=2, seed=0, epochs=60, temperature=6.0)
    assert len(b1) == len(b2) == d > 0
    assert sum(x != y for x, y in zip(b1, b2)) > 0.05 * d   # distance changes the composition

def test_overlap_coverage_ordering():
    res = analyze_song(SONG)
    tl = timeline_indices(SONG, res["graph"])
    cov = {}
    for dk in ("d1", "d2"):
        _, _, m_bin, _ = overlap_matrices(res, dk, tl, s=2)
        cov[dk] = (m_bin.sum(0) > 0).mean()
    assert cov["d1"] >= cov["d2"]   # d1 retains more cycles, so more of the timeline is covered
