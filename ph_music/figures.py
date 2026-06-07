import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ph_music import palette

def plot_distance_matrices(res, path):
    cmap = palette.heat_cmap()
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, key, title in zip(axes, ["d2", "d3", "d1"], ["$d_2$", "$d_3$", "$d_1$"]):
        im = ax.imshow(res["matrices"][key], cmap=cmap)
        ax.set_title(title); ax.set_xticks([]); ax.set_yticks([])
        fig.colorbar(im, ax=ax, fraction=0.046)
    fig.suptitle("Distance matrices  $d_2 \\leq d_3 \\leq d_1$")
    fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    return str(path)

def plot_barcodes(res, path):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, key, title in zip(axes, ["d2", "d3", "d1"], ["$d_2$", "$d_3$", "$d_1$"]):
        bars = res[key]
        for y, b in enumerate(bars):
            ax.plot([b["birth"], b["death"]], [y, y], lw=4,
                    color=palette.DIST_COLOR[key], solid_capstyle="round")
        ax.set_title(f"{title}  ($H_1$: {len(bars)})")
        ax.set_yticks([]); ax.set_xlabel("$\\epsilon$")
    fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    return str(path)

def plot_persistence_diagram(res, path):
    fig, ax = plt.subplots(figsize=(5, 5))
    lim = 0
    for key in ["d1", "d3", "d2"]:
        xs = [b["birth"] for b in res[key]]; ys = [b["death"] for b in res[key]]
        ax.scatter(xs, ys, s=60, label=key, color=palette.DIST_COLOR[key],
                   edgecolors=palette.INK, zorder=3)
        lim = max([lim] + xs + ys)
    ax.plot([0, lim*1.05], [0, lim*1.05], "--", color=palette.INK, lw=1)
    ax.set_xlabel("Birth"); ax.set_ylabel("Death"); ax.legend()
    ax.set_title("Persistence diagram")
    fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    return str(path)
