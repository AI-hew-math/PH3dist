import sys, os, pickle
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "vendor", "ktaic"))
import data_processing as dp  # noqa: E402

NAME = "J-Sanghyeondodeuri_Geomungo_part"
SRC = os.path.join(ROOT, "data", NAME + ".musicxml")
dp.Adjust_criterion[NAME] = ["C1", 1.5]  # Yeongsanhoesang dodeuri group ratio
pit, octv, dur = dp.music_to_tokens(SRC)
song = {"Song_name": NAME, "Song_pitch": pit, "Song_octave": octv, "Song_duration": dur}
out = os.path.join(ROOT, "data", "showcase_song_information.pkl")
with open(out, "wb") as f:
    pickle.dump([song], f)
print("wrote", out, "| tokens:", len(pit))
