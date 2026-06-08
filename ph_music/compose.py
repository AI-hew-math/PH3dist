from fractions import Fraction
from music21 import stream, note, tempo

def _ql(dur_str, scale=1.5):
    """junggan 'n/12' duration string -> quarterLength (musical, >= 0.25)."""
    try:
        return max(0.25, float(Fraction(dur_str)) * scale)
    except Exception:
        return 0.5

def compose_stream(res, distance_key):
    """Sonify a distance's surviving cycles: each cycle's notes, in birth order."""
    G = res["graph"]
    bars = sorted(res[distance_key], key=lambda b: (b["birth"], b["death"]))
    s = stream.Stream()
    s.append(tempo.MetronomeMark(number=92))
    for bar in bars:
        for idx in bar["cycle"]:
            pit, dur = G.nodes[idx]["label"]
            if pit == "rest":
                continue
            n = note.Note(pit)
            n.duration.quarterLength = _ql(dur)
            s.append(n)
    return s

def compose_midi(song, distance_key, out_path):
    from ph_music.verify import analyze_song
    s = compose_stream(analyze_song(song), distance_key)
    s.write("midi", fp=out_path)
    return out_path, len(s.notes)
