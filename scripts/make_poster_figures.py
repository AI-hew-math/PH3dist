import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from ph_music.verify import analyze_song
from ph_music.figures import (plot_distance_matrices, plot_barcodes,
                              plot_persistence_diagram, plot_network)
from ph_music.signature import make_signature

OUT = os.path.join(ROOT, "poster", "figures")
os.makedirs(OUT, exist_ok=True)
SHOW = "J-Sanghyeondodeuri_Geomungo_part"
res = analyze_song(SHOW)
plot_distance_matrices(res, os.path.join(OUT, "fig_distance_matrices.pdf"))
plot_barcodes(res, os.path.join(OUT, "fig_barcodes.pdf"))
plot_persistence_diagram(res, os.path.join(OUT, "fig_persistence_diagram.pdf"))
plot_network(res, os.path.join(OUT, "fig_network.pdf"))
make_signature(SHOW, outdir=OUT)  # writes signature.pdf (+ pngs) into poster/figures
print("figures ->", OUT, "| H1 d1/d3/d2 =", len(res["d1"]), len(res["d3"]), len(res["d2"]))
