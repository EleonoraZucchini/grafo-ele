# grafo-ele

Costruisce un grafo pesato a partire da `persone.tsv` e trova i gruppi (comunità) nella popolazione.

## Dati di input

`persone.tsv`, separato da tab, con colonne `Nome, Gruppo, Scuola, Classe, Annata`
(le intestazioni sono lette senza distinzione tra maiuscole e minuscole; gli spazi attorno ai valori vengono ignorati).

## Pesi degli archi

Per ogni coppia di persone si sommano due componenti:

| componente | peso 1 | peso 2 |
|---|---|---|
| gruppo | stesso gruppo | stesso gruppo + stessa annata |
| scuola | stessa scuola | stessa scuola + stessa classe + stessa annata |

Il peso totale va da 0 (nessun arco) a 4.

## Uso

```
pip install -r requirements.txt

python3 genera_grafo.py     # persone.tsv -> archi.tsv
python3 plotta_grafo.py     # archi.tsv   -> grafo.png   (un nodo per persona)
python3 trova_gruppi.py     # archi.tsv   -> gruppi.png  (comunità + matrice dei pesi)
```

Eseguire sempre `genera_grafo.py` per primo: gli altri due leggono `archi.tsv`.

## Script

- `genera_grafo.py`: calcola i pesi e scrive `archi.tsv` (`sorgente`, `destinazione`, `peso`). Usa solo la libreria standard.
- `plotta_grafo.py`: disegna il grafo, con spessore degli archi proporzionale al peso. Con molte persone diventa illeggibile.
- `trova_gruppi.py`: rileva le comunità con l'algoritmo di Louvain, stampa la composizione di ognuna e disegna le bolle per comunità accanto alla matrice dei pesi. Il quarto argomento è la risoluzione (default 1.5): più alta dà più comunità, più piccole.
  Esempio: `python3 trova_gruppi.py persone.tsv archi.tsv gruppi.png 2.0`
