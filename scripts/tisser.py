# -*- coding: utf-8 -*-
"""TISSER — projeter tous les mecanismes de lien dans UNE SEULE table d'aretes.

Usage :
    python scripts/tisser.py                 le rapport
    python scripts/tisser.py --pendantes     ce qui ne resout pas, en clair
    python scripts/tisser.py --ecrire        depose le tissu dans etat/tissu

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container plan/tisser/ — lecture, tissage. Le chemin et la CLI de cette
commande sont geles ; les reexports ci-dessous gardent les anciens noms
`tisser.*` vivants pour les importeurs historiques (plan/normaliser.py lit
CANON et INVERSES par la porte).
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from plan.expose import tisser as _tisser  # noqa: E402
from plan.expose import tisser_main as main  # noqa: E402,F401

CANON = _tisser.CANON
INVERSES = _tisser.INVERSES
indexer = _tisser.indexer
tisser = _tisser.tisser
charger = _tisser.charger

if __name__ == "__main__":
    import sys
    sys.exit(main())
