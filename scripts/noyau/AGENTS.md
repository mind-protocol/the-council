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
| `partie_greffe.py` | une partie (mj-partie.md) : le repli du jsonl, le grand livre, l'application d'un coup, le passage d'un tour — rien qui se montre | `partie.py`, `partie_lecture`, `partie_validite` |
| `partie_tour.py` | ce qui tombe au PASSAGE DU TOUR d'une partie : la ligne `tour` (`ligne`) et son application (`appliquer`), lues sur la même position — arrivées, dégels, atterrissages, parades qui tiennent un tour, états constatables, camps muets, branches mortes. Sorti du greffe le 3.9 | `partie_greffe` |
| `partie_validite.py` | la recevabilité d'un coup et ses refus motivés (§3, règles de validité) — coupé du greffe au cliquet des 500 lignes : dire si l'on a le droit, sans rien changer à la position | `partie_greffe` |
| `partie_lecture.py` | ce qui se lit d'une partie : chaîne, pièce, grand livre, état, relecture — séparé du greffe parce que rien ici ne change la position | `partie.py` |
| `partie_cartes.py` | la vue JOUEUR d'une partie, en cartes (fronts, piles, deck, desseins) : le brouillard appliqué, l'apparence de chaque carte, aucun id nu — `partie.py --cartes`, servi par `/partie` | `partie.py` |
| `partie_gestes.py` | ce que le joueur FAIT à l'écran traduit en coup : une carte posée sur une carte, et c'est la CIBLE qui dit lequel — refus rhabillés de leurs titres, `partie.py --geste`, servi par `POST /partie/geste` | `partie.py`, `partie_cartes`, `partie_greffe` |

**`bibliotheque.py` est stricte sur chaque manifeste de maison** : volume absent,
identifiant dupliqué ou fichier dont l'id ne correspond pas à son nom font
échouer la lecture. Ne pas assouplir : c'est ce qui empêche deux maisons de faire
foi sous le même identifiant.

`couverture.py` et `criticite.py` sont restés à la RACINE bien qu'ils soient
largement importés : ce sont aussi des commandes qu'on tape, et leurs chemins sont
écrits dans `docs/` et dans `rapporteurs.py`. L'amorce les rend visibles de la même
façon — la racine et `noyau/` sont sur le même chemin.
