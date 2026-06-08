import os
import matplotlib
matplotlib.use("Agg")
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import font_manager
from ph_music import palette

# Unify typography with the poster: Computer Modern Sans (= Latin Modern Sans,
# the poster's body font) for words, Computer Modern for math (d_1, epsilon, ...).
_CMSS = os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "cmss10.ttf")
font_manager.fontManager.addfont(_CMSS)
_CMSS_NAME = font_manager.FontProperties(fname=_CMSS).get_name()
matplotlib.rcParams.update({
    "font.family": _CMSS_NAME,
    "mathtext.fontset": "cm",
    "font.size": 22,
    "axes.titlesize": 30,
    "axes.labelsize": 26,
    "xtick.labelsize": 20,
    "ytick.labelsize": 20,
    "legend.fontsize": 24,
    "savefig.dpi": 200,
})


def plot_distance_matrices(res, path):
    """Three heatmaps d2/d3/d1 on ONE shared color scale (so d2<=d3<=d1 is visible)."""
    cmap = palette.heat_cmap()
    M = res["matrices"]
    gmax = max(float(np.max(M[k])) for k in ("d1", "d2", "d3")) or 1.0
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.4))
    im = None
    for ax, key, lbl in zip(axes, ["d2", "d3", "d1"], ["$d_2$", "$d_3$", "$d_1$"]):
        im = ax.imshow(M[key], cmap=cmap, vmin=0, vmax=gmax)
        ax.set_title(lbl, fontsize=38, color=palette.DIST_COLOR[key], pad=12)
        ax.set_xticks([]); ax.set_yticks([])
    cb = fig.colorbar(im, ax=axes, fraction=0.045, pad=0.02)
    cb.ax.tick_params(labelsize=18)
    fig.savefig(path, bbox_inches="tight", transparent=True); plt.close(fig)
    return str(path)


def plot_barcodes(res, path):
    """Three H1 barcodes; thick bars, large per-panel labels, shared x-range."""
    keys = ["d2", "d3", "d1"]
    xmax = max([b["death"] for k in keys for b in res[k]] + [1.0])
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.0))
    for ax, key, lbl in zip(axes, keys, ["$d_2$", "$d_3$", "$d_1$"]):
        bars = sorted(res[key], key=lambda b: b["birth"])
        for y, b in enumerate(bars):
            ax.plot([b["birth"], b["death"]], [y, y], lw=10,
                    color=palette.DIST_COLOR[key], solid_capstyle="round")
        ax.set_title(f"{lbl}:  {len(bars)} bars", fontsize=32,
                     color=palette.DIST_COLOR[key])
        ax.set_yticks([]); ax.set_xlabel(r"filtration $\epsilon$", fontsize=24)
        ax.set_xlim(0, xmax * 1.05)
        ax.tick_params(axis="x", labelsize=18)
        ax.margins(y=0.18)
    fig.tight_layout(); fig.savefig(path, bbox_inches="tight", transparent=True); plt.close(fig)
    return str(path)


def plot_persistence_diagram(res, path):
    """Overlay d1/d3/d2 birth-death points; large labels, legend, markers."""
    fig, ax = plt.subplots(figsize=(7.2, 6.6))
    lim = 0.0
    for key in ["d1", "d3", "d2"]:
        xs = [b["birth"] for b in res[key]]; ys = [b["death"] for b in res[key]]
        ax.scatter(xs, ys, s=220, label=f"${{{key[0]}}}_{{{key[1]}}}$",
                   color=palette.DIST_COLOR[key], edgecolors=palette.INK,
                   linewidths=1.6, zorder=3, alpha=0.9)
        lim = max([lim] + xs + ys)
    ax.plot([0, lim * 1.05], [0, lim * 1.05], "--", color=palette.INK, lw=1.6)
    ax.set_xlabel("Birth", fontsize=26); ax.set_ylabel("Death", fontsize=26)
    ax.tick_params(labelsize=18)
    ax.legend(fontsize=24, markerscale=1.1, loc="lower right")
    fig.tight_layout(); fig.savefig(path, bbox_inches="tight", transparent=True); plt.close(fig)
    return str(path)


def plot_network(res, path):
    """The bare music network (nodes + edges) — used in the 'music to graph' panel."""
    G = res["graph"]
    pos = nx.spring_layout(G, seed=7)
    fig, ax = plt.subplots(figsize=(6.2, 6.2)); fig.patch.set_facecolor(palette.PAPER)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=palette.INK, alpha=0.30, width=1.6)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=130, node_color=palette.D2,
                           edgecolors=palette.INK, linewidths=0.8)
    ax.axis("off")
    fig.savefig(path, bbox_inches="tight", transparent=True); plt.close(fig)
    return str(path)
