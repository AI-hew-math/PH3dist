import os, sys, json, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from ph_music.export_json import export_all, _slug
from ph_music.signature import make_signature
from ph_music.verify import analyze_song
from ph_music.figures import plot_distance_matrices, plot_barcodes, plot_persistence_diagram

SONGS = [
    "J-Sanghyeondodeuri_Geomungo_part",
    "01 J-Sangnyeongsan_Geomungo_part(0719)",
    "02 J-Jungnyeongsan_Geomungo_part(0722)",
    "03 J-Seryeongsan_Geomungo_part(0722)",
    "04 J-Garakdeori_Geomungo_part(0722)",
]

def label(name):
    s = re.sub(r"\(.*?\)", "", name).replace("_", " ").replace("J-", "").strip()
    return re.sub(r"\s+", " ", s)

export_all(SONGS, outdir=os.path.join(ROOT, "web", "data"))
index = [{"slug": _slug(n), "name": n, "label": label(n)} for n in SONGS]
with open(os.path.join(ROOT, "web", "data", "index.json"), "w") as f:
    json.dump(index, f, ensure_ascii=False, indent=0)

ASSETS = os.path.join(ROOT, "web", "assets")
os.makedirs(ASSETS, exist_ok=True)
make_signature("J-Sanghyeondodeuri_Geomungo_part", outdir=ASSETS)  # signature_d{1,2,3}.png
res = analyze_song("J-Sanghyeondodeuri_Geomungo_part")
plot_distance_matrices(res, os.path.join(ASSETS, "fig_distance_matrices.png"))
plot_barcodes(res, os.path.join(ASSETS, "fig_barcodes.png"))
plot_persistence_diagram(res, os.path.join(ASSETS, "fig_persistence_diagram.png"))
print("web data + index + signature frames + figure PNGs ready")
