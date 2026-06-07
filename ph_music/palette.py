# Dancheong palette; distance -> color encodes the ordering (d2 = hot core).
D1 = "#3E8E7E"   # jade green  (all cycles, diffuse)
D3 = "#E0A526"   # amber/gold  (intermediate)
D2 = "#C8443B"   # vermilion   (core skeleton, glow)
INK = "#1A2238"  # deep navy text
PAPER = "#FAF7F0" # hanji off-white background
ACCENT = "#7A1F2B" # POSTECH-ish maroon
DIST_COLOR = {"d1": D1, "d3": D3, "d2": D2}

def heat_cmap():
    """Blue(low)->red(high) for distance matrices (matches paper Fig 12)."""
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("dist", ["#2B4A8B", PAPER, D2])
