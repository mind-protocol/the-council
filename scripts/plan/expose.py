# -*- coding: utf-8 -*-
"""LA PORTE du container 📋 plan — cahiers, couverture, criticite, mesures.

La regle (docs/organisation.md §2) : on n'entre dans un container que par sa
porte — `from plan.expose import ...`, jamais `from couverture import ...`.
Ce fichier REEXPORTE ce que les importeurs consomment reellement aujourd'hui,
rien de plus : une API revee ici serait un mensonge sur ce qui est servi.

Tant que le lot 2 n'a pas vide les commandes, importer cette porte execute
`couverture`, `etat_du_plan`, `criticite`, `mesures` et `tisser` — comme les
importeurs actuels le font deja en les important directement.

L'ORDRE DES IMPORTS EST UNE CONTRAINTE : `etat_du_plan` et `criticite`,
basculees sur cette porte, relisent `plan.expose` PENDANT son chargement ;
les noms de `couverture` doivent donc etre lies avant elles.
"""

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# couverture d'abord : ses noms servent aux deux suivantes pendant leur import.
# Descendue au lot 2 : le paquet plan/couverture/, plus la commande racine.
from plan import couverture  # noqa: E402,F401 — le module entier, pour `import couverture as C`
from plan.couverture import (nu, sans_emoji, marque, blocs, NUM, MO, NOM_GENRE,  # noqa: E402,F401
                             EST_MO, NERA, etiquette, genre_de, ATTENDU, RANG,
                             FINI, premier_mot, tete_ornee, numero_de,
                             registre_de, col)
from plan.couverture import main as couverture_main  # noqa: E402,F401 — l'entree CLI de la facade
# Descendue au lot 2 : le paquet plan/etat_du_plan/, plus la commande racine.
from plan import etat_du_plan  # noqa: E402,F401
from plan.etat_du_plan import missions_de, phrase  # noqa: E402,F401
from plan.etat_du_plan import main as etat_du_plan_main  # noqa: E402,F401 — l'entree CLI de la facade
# Descendue au lot 2 : le paquet plan/criticite/, plus la commande racine.
from plan import criticite  # noqa: E402,F401 — le module entier, pour `criticite.calculer` etc.
from plan.criticite import entree as criticite_main  # noqa: E402,F401 — l'entree CLI de la facade
# Descendue au lot 2 : le paquet plan/mesures/, plus la commande racine.
from plan import mesures  # noqa: E402,F401
from plan.mesures import main as mesures_main  # noqa: E402,F401 — l'entree CLI de la facade
# Descendue au lot 2 : le paquet plan/tisser/, plus la commande racine.
from plan import tisser  # noqa: E402,F401
from plan.tisser import main as tisser_main  # noqa: E402,F401 — l'entree CLI de la facade
# Descendue au lot 2 : scripts/fils.py -> plan/affaires.py (l'homonymie
# fils.py / ecrans/modules/fils.js est levee, la facade fils.py reste).
from plan import affaires  # noqa: E402,F401
from plan.affaires import main as fils_main  # noqa: E402,F401 — l'entree CLI de la facade
# Descendue au lot 2 : scripts/verser_cahier.py -> plan/verser_cahier.py.
from plan import verser_cahier  # noqa: E402,F401
from plan.verser_cahier import main as verser_cahier_main  # noqa: E402,F401 — l'entree CLI de la facade
