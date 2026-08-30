# -*- coding: utf-8 -*-
"""LA PORTE du container 🎨 peinture — ce qui appelle une API payante.

La regle (docs/organisation.md §2) : on n'entre dans un container que par sa
porte — `from peinture.expose import ...`, jamais un module interne.

`composer` est descendu ici au lot 2 (facade scripts/composer.py) ; son
import est inerte (des defs, pas d'appel). ATTENTION pour la suite : ce
container appelle des API payantes — aucun reexport ne doit declencher un
appel au chargement.
"""

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from peinture import composer  # noqa: E402,F401 — poser une chanson en .md ; import inerte, aucun appel d'API
