# -*- coding: utf-8 -*-
"""Les adresses de mesure : ce qu'un cahier cite, et ce que l'etat tient vraiment.

LECTURE SEULE — rien n'est ecrit.

Usage :
    python scripts/mesures.py                                 tout
    python scripts/mesures.py --office O02                    une ligne d'office
    python scripts/mesures.py --main recrutement-peyredragon
    python scripts/mesures.py --seuils                        les hypotheses du plan
    python scripts/mesures.py --aide

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container plan/mesures/ — adresses, rapport, seuils. Le chemin et la CLI de
cette commande sont geles ; les reexports ci-dessous gardent les anciens noms
`mesures.*` vivants pour les importeurs historiques (tests/test_mesures.py).
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
from plan.expose import mesures as _mesures  # noqa: E402
from plan.expose import mesures_main as main  # noqa: E402,F401

adresses_dans = _mesures.adresses_dans
lire_offices = _mesures.lire_offices
citations_ailleurs = _mesures.citations_ailleurs
index_des_mesures = _mesures.index_des_mesures
AIDE = _mesures.AIDE

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
