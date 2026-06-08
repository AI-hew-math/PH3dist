import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from ph_music.verify import analyze_song
from ph_music.render_geomungo import render_mp3

SAMPLES = os.path.join(ROOT, "assets", "geomungo_samples")
OUT = os.path.join(ROOT, "web", "audio")
os.makedirs(OUT, exist_ok=True)
SONG = "J-Sanghyeondodeuri_Geomungo_part"
res = analyze_song(SONG)
for k in ["d1", "d3", "d2"]:
    render_mp3(res, k, SAMPLES, os.path.join(OUT, f"{k}.mp3"))
    print("rendered geomungo", k)
