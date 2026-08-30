# `etat/` — 🗄️ les tables, la porte unique, les empreintes

**L'intention.** Une seule sémantique de lecture et d'écriture pour `etat/*.json` :
tout ce qui touche les tables passe par une porte unique, avec une sémantique
d'erreur nommée (`TableAbimee`), une écriture atomique, et un vocabulaire FERMÉ
de mutations — pas de chemin JSON arbitraire, sinon n'importe quelle faute de
frappe corrompt l'état en silence.

**La porte** : [`expose.py`](expose.py) — `from etat.expose import ...`, jamais
un module interne (docs/organisation.md §2). `noyau/tables.py` est DÉJÀ la
porte de fait des écritures ; cette porte la réexporte sans changer son rôle
(son déménagement ici est le lot 3).

## Les modules (les commandes descendues, lot 2)

| module | ce qu'il possède | commande façade |
|---|---|---|
| `entree.py` | une entrée à la fois dans les tables d'empilement — la fenêtre étroite qui réduit la course à rien | `scripts/ajouter.py` |
| `empreintes.py` | le détecteur de fumée : sha1 de chaque table, « qu'est-ce qui a bougé depuis mon dernier tour ? » | `scripts/veille.py` |
| `purge.py` | ce qui a été écrit dans une fenêtre de temps — cherche par DATE, montre d'abord, ne supprime que sur `--vraiment` | `scripts/purger.py` |
| `mutations/` | le vocabulaire fermé des mutations et ses trois gardes (empreintes, validation, atomicité) — voir `mutations/__init__.py` | `scripts/appliquer.py` |

`mutations/` est un paquet : `vocabulaire` (enums, champs autorisés,
OPERATIONS), `lecture` (chemins, croyances par joueur, empreintes),
`validation` (le cadre) + `val_plan` / `val_registres` / `val_courrier` /
`val_social` (les branches par famille de tables), `application` (muter puis
écrire), `cli` (résumé et main). Découpe mécanique de l'ancien
`appliquer.py` (1492 l.) : même code, même ordre de refus.

Les commandes racine sont des **façades** : docstring, amorce, imports par la
porte, entrée CLI. Leurs chemins et leurs CLI sont gelés.

## Frontières

- **Un seul écrivain** : le MJ applique ; le tick ne fait que PROPOSER
  (container `temps/`). Toute écriture passe par `tables.ecrire` (atomique).
- Les croyances (`jetons`, `vues`, `objectifs`) appartiennent à UN JOUEUR :
  elles vivent dans `etat/joueurs/<personnage_id>/`, et l'écriture sans
  `--joueur` refuse bruyamment une fois la racine archivée.
- La garde `porte-etat` de `verifier.mjs` vérifie qu'aucun fichier n'écrit
  dans `etat/` sans passer par `tables`.

## Reste à faire (lot 3)

- `noyau/tables.py` → `etat/tables.py` (24+ importeurs à rebasculer).
- `bibliotheque` (les books) est servi à `mutations/cli.py` par la porte de
  `plan/` — paresseusement, dans `main()` : `etat` est rang 0, il ne charge le
  container plan qu'au moment d'appliquer.
