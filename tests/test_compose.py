from ph_music.verify import analyze_song
from ph_music.compose import compose_stream, _base_notes

SONG = "J-Sanghyeondodeuri_Geomungo_part"

def test_base_d1_richer_than_d2():
    res = analyze_song(SONG)
    assert len(_base_notes(res, "d1")) > len(_base_notes(res, "d2")) > 0

def test_clips_comparable_length():
    res = analyze_song(SONG)
    def total(k):
        return sum(float(n.duration.quarterLength) for n in compose_stream(res, k).notesAndRests)
    ts = [total(k) for k in ("d1", "d3", "d2")]
    assert max(ts) / min(ts) < 1.4     # all three looped to a similar duration

def test_notes_valid():
    res = analyze_song(SONG)
    notes = list(compose_stream(res, "d3").notes)
    assert len(notes) > 0
    for n in notes:
        assert n.pitch is not None and n.duration.quarterLength > 0
