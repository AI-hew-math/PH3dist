import os, pickle, functools

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_PKLS = ["group1_song_information.pkl", "group2_song_information.pkl", "group3_song_information.pkl",
         "showcase_song_information.pkl"]
_SPECIAL = {"<SOS>", "<EOS>", "<PAD>"}

@functools.lru_cache(maxsize=1)
def _load_all():
    songs = {}
    for fn in _PKLS:
        with open(os.path.join(_DATA_DIR, fn), "rb") as f:
            for d in pickle.load(f):
                songs[d["Song_name"]] = d
    return songs

def list_songs():
    return sorted(_load_all().keys())

def load_song_nodes(name):
    """Return [(pitch_label, duration_str), ...] for pitched notes only.

    Paper node definition: a node is a (pitch, duration) pair where pitch is a
    sounding pitch.  Rest tokens are not pitches and are therefore excluded;
    notes on either side of a rest become consecutive in the sequence.
    Special tokens (<SOS>/<EOS>/<PAD>) are also excluded."""
    d = _load_all()[name]
    pit, octv, dur = d["Song_pitch"], d["Song_octave"], d["Song_duration"]
    nodes = []
    for p, o, t in zip(pit, octv, dur):
        if p in _SPECIAL or p == "rest":
            continue
        nodes.append((f"{p}{o}", str(t)))
    return nodes
