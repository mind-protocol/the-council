# -*- coding: utf-8 -*-
"""LA PORTE du container 🌍 monde — la ville : masque, plan, bati, gens, relief.

La regle (docs/organisation.md §2) : on n'entre dans un container que par sa
porte — `from monde.expose import ...`, jamais un module interne.

Les commandes du monde sont descendues ici au lot 2 : `marche`->trajets,
`arpenter`->arpentage, `corps`->corps, `carte_geo`->geographie. Personne ne
les importe encore hors leurs facades ; le premier consommateur entre par
cette porte, et n'invente pas un chemin interne.
"""

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from monde import arpentage  # noqa: E402,F401 — lever une carte au pas ; facade scripts/arpenter.py
arpenter = arpentage  # l'ancien nom reste vivant pour la facade
from monde import trajets  # noqa: E402,F401 — marcher par les rues ; facade scripts/marche.py
marche = trajets  # l'ancien nom reste vivant pour la facade
