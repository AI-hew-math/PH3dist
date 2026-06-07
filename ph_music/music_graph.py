import networkx as nx
from collections import Counter

def build_graph(node_seq):
    """node_seq: list of (pitch,duration) tuples. Returns nx.Graph (Def 3.1-3.3).

    Nodes are indexed by first-appearance order (0..n-1), with a 'label' attribute.
    Edges connect consecutive DISTINCT nodes (self-loops are skipped).
    Edge weight = 1 / co-occurrence count (undirected).
    """
    index = {}
    order = []
    for node in node_seq:
        if node not in index:
            index[node] = len(order)
            order.append(node)

    counts = Counter()
    for a, b in zip(node_seq, node_seq[1:]):
        if a == b:
            continue  # ni != nj
        i, j = index[a], index[b]
        counts[(min(i, j), max(i, j))] += 1

    G = nx.Graph()
    for node, i in index.items():
        G.add_node(i, label=node)
    for (i, j), c in counts.items():
        G.add_edge(i, j, weight=1.0 / c, count=c)
    return G
