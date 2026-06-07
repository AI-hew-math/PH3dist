import os
from ph_music.verify import analyze_song
from ph_music.figures import plot_distance_matrices, plot_barcodes, plot_persistence_diagram

def test_figures_write_files(tmp_path):
    res = analyze_song("01 J-Sangnyeongsan_Geomungo_part(0719)")
    p1 = plot_distance_matrices(res, tmp_path / "dm.pdf")
    p2 = plot_barcodes(res, tmp_path / "bc.pdf")
    p3 = plot_persistence_diagram(res, tmp_path / "pd.pdf")
    for p in (p1, p2, p3):
        assert os.path.exists(p) and os.path.getsize(p) > 0
