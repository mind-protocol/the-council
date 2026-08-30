# -*- coding: utf-8 -*-
"""etat_du_plan.py — l'etat du plan, toutes affaires confondues.

    python scripts/etat_du_plan.py                 le rapport entier
    python scripts/etat_du_plan.py --du            ce qui est du, et les chaines
    python scripts/etat_du_plan.py --tout          toutes les chaines, meme dormantes
    python scripts/etat_du_plan.py --affaire "port-real"
    python scripts/etat_du_plan.py --office O03
    python scripts/etat_du_plan.py --grille          une ligne par cahier
    python scripts/etat_du_plan.py --qui             les trous par homme
    python scripts/etat_du_plan.py --pour gerardys   ses affaires, a lui seul
    python scripts/etat_du_plan.py --vue-de marlo-vasse
    python scripts/etat_du_plan.py --comparer        l'ecart avec la route /echiquier
    python scripts/etat_du_plan.py --jour-entree "30e de la 4e lune"

Lecture seule : rien n'est ecrit. L'aide complete : --aide.

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container plan/etat_du_plan/ — page, echeances, missions, sections, cli. Le
chemin et la CLI de cette commande sont geles ; les reexports ci-dessous
gardent les anciens noms `etat_du_plan.*` vivants pour les importeurs
historiques (depecher, la porte plan/expose.py).
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from plan.expose import missions_de, phrase  # noqa: E402,F401
from plan.expose import etat_du_plan as _edp  # noqa: E402
from plan.expose import etat_du_plan_main as _main  # noqa: E402

AIDE = _edp.AIDE
aujourdhui = _edp.aujourdhui
echelle = _edp.echelle
registre = _edp.registre
statut_de = _edp.statut_de
echeance_de = _edp.echeance_de

if __name__ == "__main__":
    _main()
