from ph_music.verify import analyze_song, birth_edge_sets

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
