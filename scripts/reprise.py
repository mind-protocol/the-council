# -*- coding: utf-8 -*-
"""La feuille de reprise : ce qu'il faut avoir en tete pour se rasseoir, et RIEN d'autre.

Usage :
    python scripts/reprise.py                    (le siege courant, 3 jours devant)
    python scripts/reprise.py --jours 6
    python scripts/reprise.py --qui aurore-inchauspe
    python scripts/reprise.py --large            (les textes entiers, pas les entames)

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — les cinq
questions d'un homme qui ouvre les yeux, les plafonds par section — vit dans
temps/reprise.py. Le chemin et la CLI de cette commande sont geles. Lecture
seule : il n'ecrit nulle part.
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from temps.expose import reprise as _reprise  # noqa: E402 — LA PORTE de temps/

main = _reprise.main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
