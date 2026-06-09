"""Compose distance-varied pieces with the two TDA algorithms of Tran-Lee-Jung (2024)
and render each as a real-geomungo mp3 excerpt for the web page.

Algorithm A (direct) and Algorithm B (ANN) are each run for d1, d3, d2 -> 6 clips:
web/audio/compA_d{1,3,2}.mp3 and compB_d{1,3,2}.mp3.
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from ph_music.verify import analyze_song
from ph_music.tda_compose import algorithm_a, algorithm_b, indices_to_notes
from ph_music.render_geomungo import render_sequence_mp3

SAMPLES = os.path.join(ROOT, "assets", "geomungo_samples")
OUT = os.path.join(ROOT, "web", "audio")
os.makedirs(OUT, exist_ok=True)
SONG = "J-Sanghyeondodeuri_Geomungo_part"
S = 2            # s-scale for the Overlap matrix (proportionate to the paper's 4 at d=440)
N = 56           # demo excerpt length in notes (~1 min)
SEED = 0
TEMP_B = 6.0     # Algorithm B free-position softmax temperature (cycle-anchored steps stay fixed)

res = analyze_song(SONG)
for dk in ["d1", "d3", "d2"]:
    a = indices_to_notes(res, algorithm_a(res, dk, SONG, s=S, seed=SEED))[:N]
    render_sequence_mp3(a, SAMPLES, os.path.join(OUT, f"compA_{dk}.mp3"))
    b = indices_to_notes(res, algorithm_b(res, dk, SONG, s=S, seed=SEED, epochs=500, temperature=TEMP_B))[:N]
    render_sequence_mp3(b, SAMPLES, os.path.join(OUT, f"compB_{dk}.mp3"))
    print("composed + rendered", dk)
