# -*- coding: utf-8 -*-
"""LA PORTE du container 🗄️ etat — les tables, l'ecriture gardee, l'entree.

La regle (docs/organisation.md §2) : on n'entre dans un container que par sa
porte — `from etat.expose import ...`, jamais `import appliquer`.
Ce fichier REEXPORTE ce que les importeurs consomment reellement aujourd'hui,
rien de plus.

`noyau/tables.py` est DEJA la porte de fait de `etat/` (la porte unique des
ecritures) : cette porte la reexporte aussi, sans rien changer a son role —
ses importeurs directs basculeront quand `tables` aura demenage ici (lot 3).
"""

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import tables  # noqa: E402,F401 — la porte unique des ecritures dans etat/
import appliquer  # noqa: E402,F401 — le vocabulaire ferme des mutations ; lu par boucle_activation
import ajouter  # noqa: E402,F401 — une entree a la fois, ecriture atomique ; lu par passer
