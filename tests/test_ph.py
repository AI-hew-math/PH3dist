import numpy as np, math
from ph_music.ph import h1_persistence

def test_unit_square_one_bar():
    s, r = 1.0, math.sqrt(2)
    D = np.array([
        [0, s, r, s],
        [s, 0, s, r],
        [r, s, 0, s],
        [s, r, s, 0.0],
    ])
    bars = h1_persistence(D)
    assert len(bars) == 1
    b = bars[0]
    assert abs(b["birth"] - 1.0) < 1e-9
    assert abs(b["death"] - r) < 1e-9
    assert set(b["cycle"]) == {0, 1, 2, 3}

def test_filled_triangle_no_h1():
    D = np.array([[0,1,1],[1,0,1],[1,1,0.0]])
    assert h1_persistence(D) == []
