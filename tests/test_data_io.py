from ph_music.data_io import list_songs, load_song_nodes

def test_list_songs_includes_geomungo_verification_set():
    songs = list_songs()
    assert "01 J-Sangnyeongsan_Geomungo_part(0719)" in songs
    assert "05 G-Samhyeondodeuri_Haegeum_part(0807)" in songs  # showcase

def test_load_song_nodes_returns_pitch_duration_tuples():
    nodes = load_song_nodes("01 J-Sangnyeongsan_Geomungo_part(0719)")
    assert isinstance(nodes, list) and len(nodes) > 50
    p, d = nodes[0]
    assert isinstance(p, str) and isinstance(d, str)
    assert "<SOS>" not in [n[0] for n in nodes]
    assert "<EOS>" not in [n[0] for n in nodes]
