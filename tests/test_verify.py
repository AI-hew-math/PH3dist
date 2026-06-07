import pytest
from ph_music.verify import analyze_song, birth_edge_sets, intervals

def test_inclusion_and_counts_sangnyeongsan():
    res = analyze_song("01 J-Sangnyeongsan_Geomungo_part(0719)")
    n1, n3, n2 = len(res["d1"]), len(res["d3"]), len(res["d2"])
    assert n1 >= n3 >= n2
    B1, B3, B2 = birth_edge_sets(res)
    assert B2 <= B3 <= B1   # Prop 4.2

def test_inclusion_holds_for_all_geomungo_verification_songs():
    for name in [
        "01 J-Sangnyeongsan_Geomungo_part(0719)",
        "02 J-Jungnyeongsan_Geomungo_part(0722)",
        "03 J-Seryeongsan_Geomungo_part(0722)",
        "04 J-Garakdeori_Geomungo_part(0722)",
    ]:
        res = analyze_song(name)
        B1, B3, B2 = birth_edge_sets(res)
        assert B2 <= B3 <= B1, name
        assert len(res["d1"]) >= len(res["d3"]) >= len(res["d2"]), name

def _close(a, b, tol=1e-3):
    return abs(a - b) < tol

def test_sangnyeongsan_matches_table1_exactly():
    res = analyze_song("01 J-Sangnyeongsan_Geomungo_part(0719)")
    d1 = intervals(res, "d1"); d2 = intervals(res, "d2"); d3 = intervals(res, "d3")
    # Paper Table 1: d1 = {[1/11,1/8], [1/5,1/4]}, d2 = d3 = {[1/11,1/8]}
    assert len(d1) == 2 and len(d3) == 1 and len(d2) == 1
    assert _close(d1[0][0], 1/11) and _close(d1[0][1], 1/8)
    assert _close(d1[1][0], 1/5)  and _close(d1[1][1], 1/4)
    assert _close(d2[0][0], 1/11) and _close(d2[0][1], 1/8)
    assert _close(d3[0][0], 1/11) and _close(d3[0][1], 1/8)
