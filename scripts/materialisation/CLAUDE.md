# `materialisation/` — Peyredragon en volume

Donner un corps à Peyredragon : le site, le château, les salles, et de quoi le
regarder. À la différence de `../monde/` qui engendre une ville entière par la
circulation, on est ici sur un lieu unique et dessiné.

| Fichier | Ce qu'il tient |
|---|---|
| `peyredragon.py` | le site : l'île, le relief, la silhouette |
| `salles.py` | les salles et leurs volumes |
| `lieux.py` | les lieux nommés et leur ancrage |
| `circulation.py` | ce qui relie — escaliers, couloirs, cours |
| `formes.py`, `palette.py` | le vocabulaire de dessin |
| `programme.py` | le programme du bâti : quoi, où, combien |
| `exporter.py` | sortir vers Blender : un OBJ, son MTL, et rien d'autre |
| `blender_batir.py` | bâtir DANS Blender — pas d'export, pas d'intermédiaire |
| `blender_ouvrir.py` | ouvrir la scène |
| `vues.py` | où l'on se place pour regarder, et ce qu'on en tire |
| `rendu.py` | le rendu des vues |

```bash
python scripts/materialisation/exporter.py            # l'île entière
python scripts/materialisation/exporter.py --pres     # le château de près
blender --python scripts/materialisation/blender_batir.py
```

**Aucune caméra n'est posée en coordonnées.** Chaque vue se DÉDUIT du site — le
château, le quai, le sommet — si bien qu'un changement de relief la déplace toute
seule. Ne pas revenir à des coordonnées en dur : c'est ce qui fait qu'une vue reste
juste après une régénération.

Le lien avec la fiction se fait par `../affecter.py`, qui donne une adresse
physique à ce qu'un lieu ou une salle nomme, et par `../arpenter.py` et
`../marche.py`, qui rendent des mètres et des minutes de marche.
