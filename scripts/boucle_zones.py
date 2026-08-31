# -*- coding: utf-8 -*-
"""BOUCLE DES ZONES — la veille de focus des narrateurs.

Usage :
    python scripts/boucle_zones.py                      # a blanc : montre tout
    python scripts/boucle_zones.py --vraiment           # une passe, reveils en cast
    python scripts/boucle_zones.py --vraiment --intervalle 60   # boucle, 60 min

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans
agents/focus.py — le classement des etats cibles par energie, le routage
par le tissu, le mot du reveil, la cadence par narrateur.
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from agents.expose import focus_main as main  # noqa: E402

if __name__ == "__main__":
    import sys
    sys.exit(main())
