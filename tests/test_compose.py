from ph_music.verify import analyze_song
from ph_music.compose import compose_stream

SONG = "J-Sanghyeondodeuri_Geomungo_part"

def test_d1_has_more_notes_than_d2():
    res = analyze_song(SONG)
    n1 = len(compose_stream(res, "d1").notes)
    n2 = len(compose_stream(res, "d2").notes)
    assert n1 > n2 > 0     # d1 (7 cycles) sonifies more than d2 (3 cycles)

def test_notes_valid():
    res = analyze_song(SONG)
    s = compose_stream(res, "d3")
    for n in s.notes:
        assert n.pitch is not None and n.duration.quarterLength > 0
