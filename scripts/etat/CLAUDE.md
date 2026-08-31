# `etat/` — 🗄️ les tables et leurs outils

**L'intention.** Les habitants ont accès au dépôt et peuvent modifier directement
`etat/`. Ce paquet conserve seulement les petits outils encore consommés par les
commandes existantes.

**L'exposition Python** : [`expose.py`](expose.py) réexporte les aides communes
pour les consommateurs qui en ont besoin ; ce n'est pas une porte obligatoire.

## Les modules (les commandes descendues, lot 2)

| module | ce qu'il possède | commande façade |
|---|---|---|
| `entree.py` | une entrée à la fois dans les tables d'empilement — la fenêtre étroite qui réduit la course à rien | `scripts/ajouter.py` |
| `empreintes.py` | le détecteur de fumée : sha1 de chaque table, « qu'est-ce qui a bougé depuis mon dernier tour ? » | `scripts/veille.py` |
| `purge.py` | ce qui a été écrit dans une fenêtre de temps — cherche par DATE, montre d'abord, ne supprime que sur `--vraiment` | `scripts/purger.py` |

Les commandes racine sont des **façades** : docstring, amorce, imports par la
porte, entrée CLI. Leurs chemins et leurs CLI sont gelés.

## Frontières

- Le tick ne fait que calculer. Les habitants écrivent directement leurs
  changements dans `etat/`.
- Les croyances (`jetons`, `vues`, `objectifs`) appartiennent à UN JOUEUR :
  elles vivent dans `etat/joueurs/<personnage_id>/`, et l'écriture sans
  `--joueur` refuse bruyamment une fois la racine archivée.
  dans `etat/` sans passer par `tables`.

## Reste à faire (lot 3)

- `noyau/tables.py` → `etat/tables.py` (24+ importeurs à rebasculer).
- `bibliotheque` (les books) est servi à `mutations/cli.py` par la porte de
  `plan/` — paresseusement, dans `main()` : `etat` est rang 0, il ne charge le
  container plan qu'au moment d'appliquer.
