# -*- coding: utf-8 -*-
"""PASSER — un livre change de main, ou se pose sur une table.

    python scripts/passer.py                             # ce que chacun porte
    python scripts/passer.py carnet-marlo                # ou est ce volume
    python scripts/passer.py carnet-marlo --a rhaenyra --vraiment
    python scripts/passer.py leve-de-la-gadoue --pose table-peinte --vraiment
    python scripts/passer.py carnet-marlo --a rhaenyra --ouvert --vraiment

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container plan/, module passer.py. Le chemin et la CLI de cette commande
sont geles.
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
from plan.expose import passer_main as main  # noqa: E402

if __name__ == "__main__":
    main(sys.argv[1:])
