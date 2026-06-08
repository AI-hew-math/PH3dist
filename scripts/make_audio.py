import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from ph_music.compose import compose_midi

OUT = os.path.join(ROOT, "web", "audio")
os.makedirs(OUT, exist_ok=True)
SONG = "J-Sanghyeondodeuri_Geomungo_part"
for k in ["d1", "d3", "d2"]:
    p, n = compose_midi(SONG, k, os.path.join(OUT, f"{k}.mid"))
    print(f"{k}: {n} notes -> {p}")
