import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib import font_manager
from ph_music.verify import analyze_song
from ph_music import palette

_CMSS = os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "cmss10.ttf")
font_manager.fontManager.addfont(_CMSS)
matplotlib.rcParams.update({
    "font.family": font_manager.FontProperties(fname=_CMSS).get_name(),
    "mathtext.fontset": "cm",
})

def _cycle_birth_edges(res, key):
    return {b["birth_edge"]: b["cycle"] for b in res[key]}

def _draw(ax, G, pos, surviving, color, title, alpha_base=0.16):
    nx.draw_networkx_edges(ax=ax, G=G, pos=pos, edge_color=palette.INK, alpha=alpha_base, width=1.2)
    nx.draw_networkx_nodes(ax=ax, G=G, pos=pos, node_size=45,
                           node_color=palette.INK, alpha=0.55)
    for cyc in surviving:
        cyc_edges = list(zip(cyc, cyc[1:] + cyc[:1]))
        nx.draw_networkx_edges(ax=ax, G=G, pos=pos, edgelist=cyc_edges,
                               edge_color=color, width=5.0, alpha=0.95)
    ax.set_title(title, fontsize=38, color=color, pad=10)
    ax.axis("off")

def make_signature(song, outdir="out"):
    os.makedirs(outdir, exist_ok=True)
    res = analyze_song(song)
    G = res["graph"]
    pos = nx.spring_layout(G, seed=7, k=None)
    cyc = {k: list(_cycle_birth_edges(res, k).values()) for k in ("d1", "d3", "d2")}
    panels = [("d1", cyc["d1"], palette.D1), ("d3", cyc["d3"], palette.D3), ("d2", cyc["d2"], palette.D2)]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.8))
    fig.patch.set_facecolor(palette.PAPER)
    for ax, (key, cycles, color) in zip(axes, panels):
        _draw(ax, G, pos, cycles, color, f"${{{key[0]}}}_{{{key[1]}}}$:  {len(cycles)} cycles")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.90, bottom=0.01, wspace=0.04)
    poster_pdf = os.path.join(outdir, "signature.pdf")
    fig.savefig(poster_pdf, bbox_inches="tight", facecolor=palette.PAPER); plt.close(fig)

    frames = []
    for key, cycles, color in panels:
        f, a = plt.subplots(figsize=(5, 5.2)); f.patch.set_facecolor(palette.PAPER)
        _draw(a, G, pos, cycles, color, f"{key.upper()}: {len(cycles)} cycles")
        fp = os.path.join(outdir, f"signature_{key}.png")
        f.savefig(fp, dpi=160, bbox_inches="tight", facecolor=palette.PAPER); plt.close(f)
        frames.append(fp)
    return {"poster_pdf": poster_pdf, "frames": frames}
