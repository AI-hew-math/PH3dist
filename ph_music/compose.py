from fractions import Fraction
from music21 import stream, note, tempo, instrument

KOTO_GM = 107  # General-MIDI "Koto": a plucked zither — the closest GM voice to the geomungo

def _ql(dur_str, scale=1.5):
    """junggan 'n/12' duration string -> quarterLength (musical, >= 0.25)."""
    try:
        return max(0.25, float(Fraction(dur_str)) * scale)
    except Exception:
        return 0.5

def _base_notes(res, distance_key):
    """Surviving-cycle notes (pitch_label, duration_str), in birth order."""
    G = res["graph"]
    bars = sorted(res[distance_key], key=lambda b: (b["birth"], b["death"]))
    out = []
    for bar in bars:
        for idx in bar["cycle"]:
            pit, dur = G.nodes[idx]["label"]
            if pit != "rest":
                out.append((pit, dur))
    return out

def _base_ql(res, distance_key):
    return sum(_ql(d) for _, d in _base_notes(res, distance_key))

def compose_stream(res, distance_key, tempo_bpm=96, program=KOTO_GM):
    """Sonify a distance by looping its surviving cycles to the SAME length for all
    three distances (the longest distance, d1, sets the target; shorter ones repeat).
    On a koto-like (geomungo-style) plucked timbre. Same length, but d2 is the core
    motif repeated (sparser, insistent) while d1 is a more varied melody."""
    target_ql = max(_base_ql(res, k) for k in ("d1", "d3", "d2")) or 12.0
    base = _base_notes(res, distance_key) or [("C4", "12/12")]
    s = stream.Stream()
    inst = instrument.Instrument(); inst.midiProgram = program
    s.insert(0, inst)
    s.append(tempo.MetronomeMark(number=tempo_bpm))
    acc = 0.0
    i = 0
    nb = len(base)
    while acc < target_ql or i < nb:          # at least one full pass, then loop to target
        pit, dur = base[i % nb]
        n = note.Note(pit); n.duration.quarterLength = _ql(dur)
        s.append(n); acc += n.duration.quarterLength; i += 1
    return s

def compose_midi(song, distance_key, out_path):
    from ph_music.verify import analyze_song
    s = compose_stream(analyze_song(song), distance_key)
    s.write("midi", fp=out_path)
    return out_path, len(s.notes)
