"""Export the note sequences behind each audio clip (as [midi, quarterLength]) so the
web page can draw a mini piano-roll under each player. -> web/data/clip_notes.json."""
import os, sys, json
from fractions import Fraction
from music21 import pitch as P
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from ph_music.verify import analyze_song
from ph_music.compose import compose_stream
from ph_music.tda_compose import algorithm_a, algorithm_b, indices_to_notes

SONG = "J-Sanghyeondodeuri_Geomungo_part"
N = 28
res = analyze_song(SONG)

def to_midiql(label_notes):
    out = []
    for pit, dur in label_notes[:N]:
        try:
            out.append([int(round(P.Pitch(pit).midi)), round(float(Fraction(dur)), 3)])
        except Exception:
            pass
    return out

clips = {}
for k in ["d1", "d3", "d2"]:                              # Listen: cycle sonification
    s = compose_stream(res, k)
    clips[k] = [[int(round(n.pitch.midi)), round(float(n.duration.quarterLength), 3)] for n in s.notes][:N]
for k in ["d1", "d3", "d2"]:                              # composed pieces
    clips["compA_" + k] = to_midiql(indices_to_notes(res, algorithm_a(res, k, SONG, s=2, seed=0)))
    clips["compB_" + k] = to_midiql(indices_to_notes(res, algorithm_b(res, k, SONG, s=2, seed=0, epochs=500)))

json.dump(clips, open(os.path.join(ROOT, "web", "data", "clip_notes.json"), "w"))
print("clip_notes:", {k: len(v) for k, v in clips.items()})
