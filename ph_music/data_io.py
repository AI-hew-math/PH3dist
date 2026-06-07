import os, pickle, functools

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_PKLS = ["group1_song_information.pkl", "group2_song_information.pkl", "group3_song_information.pkl"]
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
    """Return [(pitch_label, duration_str), ...] with SOS/EOS removed.
    pitch_label = 'rest' for rests else f'{pitch}{octave}'."""
    d = _load_all()[name]
    pit, octv, dur = d["Song_pitch"], d["Song_octave"], d["Song_duration"]
    nodes = []
    for p, o, t in zip(pit, octv, dur):
        if p in _SPECIAL:
            continue
        label = "rest" if p == "rest" else f"{p}{o}"
        nodes.append((label, str(t)))
    return nodes
