import os, json, math, re
import networkx as nx
from ph_music.verify import analyze_song

def _fin(x):
    return None if math.isinf(x) else round(x, 5)

def _slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def export_song(name, outdir="web/data"):
    os.makedirs(outdir, exist_ok=True)
    res = analyze_song(name)
    G = res["graph"]
    pos = nx.spring_layout(G, seed=7)
    data = {
        "name": name,
        "nodes": [list(G.nodes[i]["label"]) for i in range(G.number_of_nodes())],
        "positions": [[round(float(pos[i][0]), 4), round(float(pos[i][1]), 4)]
                      for i in range(G.number_of_nodes())],
        "edges": [[int(u), int(v), round(float(G[u][v]["weight"]), 5)]
                  for u, v in G.edges()],
        "matrices": {k: [[round(float(x), 5) for x in row] for row in res["matrices"][k]]
                     for k in ("d1", "d2", "d3")},
        "persistence": {k: [{"birth": round(b["birth"], 5), "death": _fin(b["death"]),
                             "birth_edge": list(b["birth_edge"]), "cycle": b["cycle"]}
                            for b in res[k]] for k in ("d1", "d2", "d3")},
    }
    path = os.path.join(outdir, f"{_slug(name)}.json")
    with open(path, "w") as fh:
        json.dump(data, fh, ensure_ascii=False)
    return path

def export_all(names, outdir="web/data"):
    return [export_song(n, outdir) for n in names]
