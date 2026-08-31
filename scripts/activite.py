# -*- coding: utf-8 -*-
"""ACTIVITE — la loupe de debug des sessions de dev : qui a fait quoi.

    python scripts/activite.py                  tout, sur 24 h reelles
    python scripts/activite.py --heures 3       la fenetre reelle
    python scripts/activite.py --monde 12       la fenetre en heures de JEU
    python scripts/activite.py --tout           sans fenetre
    python scripts/activite.py --qui otto       un seul homme
    python scripts/activite.py --appels --refus telle ou telle section
    python scripts/activite.py --json           pour la regie ou un tableur

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container agents/, module activite.py.
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from agents.expose import activite as _activite  # noqa: E402
from agents.expose import activite_main as main  # noqa: E402,F401

activations = _activite.activations
canaux = _activite.canaux
matrice = _activite.matrice

if __name__ == "__main__":
    main()
