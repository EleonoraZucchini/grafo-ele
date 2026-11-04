#!/usr/bin/env python3
"""Disegna il grafo da persone.tsv + archi.tsv e lo salva in grafo.png.

Il peso degli archi è rappresentato dallo spessore (e dall'opacità).
Richiede: networkx, matplotlib.
Uso: python3 plotta_grafo.py [persone.tsv] [archi.tsv] [grafo.png]
"""
import csv
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D

SFONDO = "#fafaf7"
PALETTE = ["#4e79a7", "#e8833a", "#59a14f", "#b07aa1", "#e15759", "#76b7b2"]
COLORE_ARCO = "#44475a"
SPESSORE_PER_PESO = 3.5  # px di spessore per unità di peso


def leggi(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [
            {k.strip().lower(): v.strip() for k, v in r.items()}
            for r in csv.DictReader(f, delimiter="\t")
        ]


def main():
    persone = leggi(sys.argv[1] if len(sys.argv) > 1 else "persone.tsv")
    archi = leggi(sys.argv[2] if len(sys.argv) > 2 else "archi.tsv")
    out = sys.argv[3] if len(sys.argv) > 3 else "grafo.png"

    # un colore per ogni gruppo presente nei dati
    gruppi = sorted({p["gruppo"] for p in persone})
    COLORI_GRUPPO = {g: PALETTE[i % len(PALETTE)] for i, g in enumerate(gruppi)}

    G = nx.Graph()
    for p in persone:
        G.add_node(p["nome"], gruppo=p["gruppo"], scuola=p["scuola"])
    for a in archi:
        G.add_edge(a["sorgente"], a["destinazione"], weight=int(a["peso"]))

    # layout calcolato solo sui nodi connessi (gli isolati lo sbilanciano);
    # gli isolati vengono messi in fila sotto il grafo
    isolati = list(nx.isolates(G))
    connessi = G.subgraph(n for n in G if n not in isolati)
    pos = nx.spring_layout(connessi, seed=3, k=2.0, weight="weight", iterations=300)
    if pos:
        ys = [y for _, y in pos.values()]
        xs = [x for x, _ in pos.values()]
        y0 = min(ys) - 0.7 * (max(ys) - min(ys) or 1)
        cx = (min(xs) + max(xs)) / 2
    else:
        y0, cx = 0, 0
    for i, n in enumerate(isolati):
        pos[n] = (cx + (i - (len(isolati) - 1) / 2) * 0.6, y0)

    fig, ax = plt.subplots(figsize=(13, 10), facecolor=SFONDO)
    ax.set_facecolor(SFONDO)

    # archi: spessore e opacità proporzionali al peso, disegnati dal più
    # leggero al più pesante così quelli forti stanno sopra
    pesi_max = max((d["weight"] for *_, d in G.edges(data=True)), default=1)
    for u, v, d in sorted(G.edges(data=True), key=lambda e: e[2]["weight"]):
        w = d["weight"]
        nx.draw_networkx_edges(
            G, pos, edgelist=[(u, v)], ax=ax,
            width=SPESSORE_PER_PESO * w,
            alpha=0.25 + 0.55 * w / pesi_max,
            edge_color=COLORE_ARCO,
            style="solid",
        )

    # nodi
    nx.draw_networkx_nodes(
        G, pos, ax=ax, node_size=1500 if len(G) > 15 else 4200,
        node_color=[COLORI_GRUPPO.get(G.nodes[n]["gruppo"], "#999999") for n in G],
        edgecolors="white", linewidths=3,
    )
    nx.draw_networkx_labels(
        G, pos, ax=ax, font_size=7 if len(G) > 15 else 10, font_weight="bold", font_color="white"
    )

    # legenda: colori = gruppo, spessori = peso
    pesi = sorted({d["weight"] for *_, d in G.edges(data=True)})
    handles = [
        Line2D([], [], marker="o", ls="", markersize=12, color=c,
               markeredgecolor="white", label=f"gruppo {g}")
        for g, c in COLORI_GRUPPO.items()
    ]
    handles += [Line2D([], [], lw=0, label=" ")]
    handles += [
        Line2D([], [], color=COLORE_ARCO, lw=SPESSORE_PER_PESO * w,
               alpha=0.25 + 0.55 * w / pesi_max, label=f"peso {w}")
        for w in pesi
    ]
    ax.legend(handles=handles, loc="lower right", frameon=False,
              fontsize=10, labelspacing=1.1, handlelength=3)

    ax.set_title("Rete di relazioni tra persone", fontsize=15,
                 fontweight="bold", color="#222", pad=14)
    ax.margins(0.15)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(out, dpi=170, facecolor=SFONDO)
    print(f"salvato {out}")


if __name__ == "__main__":
    main()
