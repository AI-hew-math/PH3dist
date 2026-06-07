import os
from ph_music.signature import make_signature

def test_signature_outputs(tmp_path):
    paths = make_signature("05 G-Samhyeondodeuri_Haegeum_part(0807)", outdir=str(tmp_path))
    assert os.path.exists(paths["poster_pdf"]) and os.path.getsize(paths["poster_pdf"]) > 0
    assert len(paths["frames"]) == 3 and all(os.path.exists(p) for p in paths["frames"])
