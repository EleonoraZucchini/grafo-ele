#!/usr/bin/env python3
"""Trova i gruppi (comunità) nella popolazione e li disegna in gruppi.png.

Legge persone.tsv e archi.tsv (prodotto da genera_grafo.py), rileva le
comunità con Louvain sui pesi degli archi e produce:
  - una tabella testuale con la composizione di ogni comunità
  - gruppi.png: a sinistra le persone raggruppate in bolle per comunità,
    a destra la matrice dei pesi ordinata per comunità.

Uso: python3 trova_gruppi.py [persone.tsv] [archi.tsv] [gruppi.png] [risoluzione]
  risoluzione: più alta = più comunità, più piccole (default 1.5)
Richiede: networkx, matplotlib.
"""
import csv
import math
import sys
from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle

SFONDO = "#fafaf7"
PALETTE = ["#4e79a7", "#e8833a", "#59a14f", "#b07aa1", "#e15759", "#76b7b2"]
ALIAS = {"classe": "sezione", "annata": "anno"}


def leggi(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [
            {ALIAS.get(k.strip().lower(), k.strip().lower()): v.strip()
             for k, v in r.items()}
            for r in csv.DictReader(f, delimiter="\t")
        ]


def etichetta(membri, P):
    """Descrive una comunità con i valori più frequenti di gruppo/scuola/anno."""
    def top(campo):
        v, n = Counter(P[m][campo] for m in membri).most_common(1)[0]
        return v, n

    parti = []
    for campo, nome in (("gruppo", "gruppo"), ("scuola", "scuola"), ("anno", "anno")):
        v, n = top(campo)
        parti.append(f"{nome} {v}" if n == len(membri) else f"{nome} {v} ({n}/{len(membri)})")
    return " · ".join(parti)


def main():
    persone = leggi(sys.argv[1] if len(sys.argv) > 1 else "persone.tsv")
    archi = leggi(sys.argv[2] if len(sys.argv) > 2 else "archi.tsv")
    out = sys.argv[3] if len(sys.argv) > 3 else "gruppi.png"
    risoluzione = float(sys.argv[4]) if len(sys.argv) > 4 else 1.5

    P = {p["nome"]: p for p in persone}
    G = nx.Graph()
    G.add_nodes_from(P)
    for a in archi:
        G.add_edge(a["sorgente"], a["destinazione"], weight=int(a["peso"]))

    comunita = nx.community.louvain_communities(
        G, weight="weight", resolution=risoluzione, seed=1
    )
    comunita = sorted((sorted(c) for c in comunita), key=len, reverse=True)
    mod = nx.community.modularity(G, comunita, weight="weight")

    print(f"{len(comunita)} comunità (risoluzione {risoluzione}, modularità {mod:.2f})\n")
    for i, c in enumerate(comunita, 1):
        print(f"Comunità {i}: {len(c)} persone — {etichetta(c, P)}")
        comp = Counter((P[m]["gruppo"], P[m]["scuola"], P[m]["sezione"], P[m]["anno"]) for m in c)
        for (g, s, sez, an), n in comp.most_common():
            print(f"    {n:>2} × gruppo {g}, scuola {s}, classe {sez}, annata {an}")
        print(f"    persone: {', '.join(c)}\n")

    # ---------- figura ----------
    fig, (ax, axm) = plt.subplots(
        1, 2, figsize=(17, 8.5), facecolor=SFONDO, gridspec_kw={"width_ratios": [1.25, 1]}
    )
    ax.set_facecolor(SFONDO)

    gruppi = sorted({p["gruppo"] for p in persone})
    col_gruppo = {g: PALETTE[i % len(PALETTE)] for i, g in enumerate(gruppi)}
    col_com = ["#dbe4f0", "#fbe3d0", "#dcebd6", "#ecdbe8", "#f6d6d7", "#d6ebe9"]

    # layout: centri delle bolle su un cerchio, persone su un cerchietto interno
    n_c = len(comunita)
    pos, centri, raggi = {}, [], []
    R = 0 if n_c == 1 else 3.2
    for i, c in enumerate(comunita):
        ang = 2 * math.pi * i / n_c + math.pi / 2
        cx, cy = R * math.cos(ang), R * math.sin(ang)
        r = 0.6 + 0.25 * math.sqrt(len(c))
        centri.append((cx, cy))
        raggi.append(r)
        # ordina per gruppo/scuola così persone simili stanno vicine
        ordine = sorted(c, key=lambda m: (P[m]["gruppo"], P[m]["scuola"], P[m]["anno"], P[m]["sezione"]))
        for j, m in enumerate(ordine):
            a = 2 * math.pi * j / len(ordine)
            rr = r * 0.62 if len(ordine) > 1 else 0
            pos[m] = (cx + rr * math.cos(a), cy + rr * math.sin(a))

    appart = {m: i for i, c in enumerate(comunita) for m in c}

    # bolle
    for i, ((cx, cy), r) in enumerate(zip(centri, raggi)):
        ax.add_patch(Circle((cx, cy), r, facecolor=col_com[i % len(col_com)],
                            edgecolor="white", linewidth=3, zorder=0))
        # etichetta centrata sopra (bolle in alto) o sotto (bolle in basso)
        sopra = cy >= 0
        ax.text(cx, cy + (r + 0.12) * (1 if sopra else -1),
                f"Comunità {i + 1} — {len(comunita[i])} persone\n{etichetta(comunita[i], P)}",
                ha="center", va="bottom" if sopra else "top",
                fontsize=9.5, color="#222", fontweight="bold", zorder=5)

    # legami tra bolle: spessore = peso medio tra le due comunità
    for i in range(n_c):
        for j in range(i + 1, n_c):
            ws = [G[u][v]["weight"] if G.has_edge(u, v) else 0
                  for u in comunita[i] for v in comunita[j]]
            media = sum(ws) / len(ws)
            if media > 0:
                (x1, y1), (x2, y2) = centri[i], centri[j]
                d = math.hypot(x2 - x1, y2 - y1)
                ux, uy = (x2 - x1) / d, (y2 - y1) / d
                x1, y1 = x1 + ux * raggi[i], y1 + uy * raggi[i]
                x2, y2 = x2 - ux * raggi[j], y2 - uy * raggi[j]
                ax.plot([x1, x2], [y1, y2], color="#44475a", lw=1 + 6 * media,
                        alpha=0.35, solid_capstyle="round", zorder=1)
                ax.text((x1 + x2) / 2, (y1 + y2) / 2, f"peso medio {media:.1f}",
                        ha="center", va="center", fontsize=8.5, color="#44475a",
                        bbox=dict(boxstyle="round,pad=0.2", fc=SFONDO, ec="none"), zorder=2)

    # persone: riempimento bianco, anello = gruppo originale
    nx.draw_networkx_nodes(
        G, pos, ax=ax, node_size=700, node_color="white",
        edgecolors=[col_gruppo[P[n]["gruppo"]] for n in G], linewidths=3.5,
    ).set_zorder(3)
    for t in nx.draw_networkx_labels(G, pos, ax=ax, font_size=6.5, font_color="#222").values():
        t.set_zorder(4)

    handles = [Line2D([], [], marker="o", ls="", markersize=11, markerfacecolor="white",
                      markeredgecolor=c, markeredgewidth=3, label=f"gruppo {g}")
               for g, c in col_gruppo.items()]
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=10,
              title="Anello = gruppo di origine", title_fontsize=10)
    ax.set_title(f"Comunità trovate dai pesi ({n_c})", fontsize=14, fontweight="bold", pad=12)
    ax.set_aspect("equal")
    ax.margins(0.12)
    ax.set_axis_off()

    # matrice dei pesi ordinata per comunità
    ordine = [m for c in comunita for m in c]
    idx = {m: i for i, m in enumerate(ordine)}
    M = np.zeros((len(ordine), len(ordine)))
    for u, v, d in G.edges(data=True):
        M[idx[u], idx[v]] = M[idx[v], idx[u]] = d["weight"]
    im = axm.imshow(M, cmap="Blues", vmin=0, vmax=max(M.max(), 1))
    taglio = 0
    for c in comunita[:-1]:
        taglio += len(c)
        axm.axhline(taglio - 0.5, color="#c0392b", lw=1.5)
        axm.axvline(taglio - 0.5, color="#c0392b", lw=1.5)
    axm.set_xticks(range(len(ordine)))
    axm.set_yticks(range(len(ordine)))
    axm.set_xticklabels(ordine, rotation=90, fontsize=6.5)
    axm.set_yticklabels(ordine, fontsize=6.5)
    axm.set_title("Matrice dei pesi (ordinata per comunità)", fontsize=14,
                  fontweight="bold", pad=12)
    cb = fig.colorbar(im, ax=axm, fraction=0.046, pad=0.03)
    cb.set_label("peso dell'arco")
    cb.set_ticks(sorted({int(x) for x in M.flatten()}))

    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=SFONDO)
    print(f"salvato {out}")


if __name__ == "__main__":
    main()
