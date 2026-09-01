# `noyau/` — les modules qu'on importe, jamais ceux qu'on tape

Ici vit ce que plusieurs scripts partagent. Aucun de ces fichiers n'est une
commande du tour de jeu : on les charge, on ne les lance pas.

**C'est le SEUL dossier importable depuis ailleurs.** L'amorce de chemin décrite
dans [`../CLAUDE.md`](../CLAUDE.md) ne rend visibles que la racine de `scripts/` et
ce dossier-ci. Un module de `plan/` ou d'`analyse/` ne s'importe pas — s'il doit
l'être, il descend ici, et c'est la règle qui garde le classement honnête.

| Module | Ce qu'il tient | Importé par |
|---|---|---|
| `bibliotheque.py` | l'agrégat des livres possédés par les maisons, avec écriture optimiste par volume | 24 scripts |
| `plan_modele.py` | le plan visible d'un siège, normalisé avant toute mesure | `criticite`, `etat_du_plan`, `depecher` |
| `rapporteurs.py` | le registre des battements dérivés : qui doit tourner, quand | `tick`, `couverture`, `criticite` |
| `livre.py` | ouvrir UN volume pour quelqu'un de nommé (`books.json` fait 2 Mo) | `depecher`, `plan_modele` |
| `jours_relatifs.py` | l'échelle J−N du plan, lue par une seule main | `dater_plan`, `etat_du_plan` |
| `carte_muette.py` | le compteur : un conseil qui nomme des places sans toucher la table | `append_flux`, `bilan` |
| `chiffrer.py` | ce qui, dans les coûts et les effets, se laisse suivre | `tisser` |
| `git_donnees.py` | sélection, validation et empreinte cohérente de `etat/` + `chambres/`, sans verrous ni caches | `pousser_donnees.py` |

**`bibliotheque.py` est stricte sur chaque manifeste de maison** : volume absent,
identifiant dupliqué ou fichier dont l'id ne correspond pas à son nom font
échouer la lecture. Ne pas assouplir : c'est ce qui empêche deux maisons de faire
foi sous le même identifiant.

`couverture.py` et `criticite.py` sont restés à la RACINE bien qu'ils soient
largement importés : ce sont aussi des commandes qu'on tape, et leurs chemins sont
écrits dans `docs/` et dans `rapporteurs.py`. L'amorce les rend visibles de la même
façon — la racine et `noyau/` sont sur le même chemin.
