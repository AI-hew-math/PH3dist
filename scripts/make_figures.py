import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ph_music.verify import analyze_song
from ph_music.figures import plot_distance_matrices, plot_barcodes, plot_persistence_diagram
os.makedirs("out", exist_ok=True)
SHOW = "J-Sanghyeondodeuri_Geomungo_part"  # showcase
res = analyze_song(SHOW)
plot_distance_matrices(res, "out/fig_distance_matrices.pdf")
plot_barcodes(res, "out/fig_barcodes.pdf")
plot_persistence_diagram(res, "out/fig_persistence_diagram.pdf")
print("wrote out/fig_*.pdf for", SHOW, "| H1 d1/d3/d2 =",
      len(res["d1"]), len(res["d3"]), len(res["d2"]))
