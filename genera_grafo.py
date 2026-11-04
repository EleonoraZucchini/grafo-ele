#!/usr/bin/env python3
"""Genera un grafo pesato dalle persone in persone.tsv.

Pesi (per ogni coppia di persone), sommando le due componenti:
  gruppo:  1 se stesso gruppo, 2 se stesso gruppo + stesso anno
  scuola:  1 se stessa scuola, 2 se stessa scuola + sezione + anno
Le coppie con peso totale 0 non hanno arco.

Uso: python3 genera_grafo.py [persone.tsv] [archi.tsv]
"""
import csv
import sys
from itertools import combinations


def peso(a, b):
    p = 0
    if a["gruppo"] == b["gruppo"]:
        p += 2 if a["anno"] == b["anno"] else 1
    if a["scuola"] == b["scuola"]:
        p += 2 if (a["sezione"] == b["sezione"] and a["anno"] == b["anno"]) else 1
    return p


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "persone.tsv"
    dst = sys.argv[2] if len(sys.argv) > 2 else "archi.tsv"

    with open(src, newline="", encoding="utf-8") as f:
        # il file ha spazi di riempimento attorno ai campi: li rimuovo
        # nomi colonna in minuscolo; classe = sezione, annata = anno
        alias = {"classe": "sezione", "annata": "anno"}
        persone = [
            {alias.get(k.strip().lower(), k.strip().lower()): v.strip()
             for k, v in r.items()}
            for r in csv.DictReader(f, delimiter="\t")
        ]

    archi = []
    for a, b in combinations(persone, 2):
        p = peso(a, b)
        if p > 0:
            archi.append((a["nome"], b["nome"], p))

    with open(dst, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["sorgente", "destinazione", "peso"])
        w.writerows(archi)

    for s, d, p in archi:
        print(f"{s} -- {d}: {p}")
    print(f"\n{len(persone)} nodi, {len(archi)} archi -> {dst}")


if __name__ == "__main__":
    main()
