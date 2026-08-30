#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fils.py — ce qui court, et qui tient la plume dessus.

Un fil est une affaire en cours qui porte un nom d homme et une echeance. Il
vit dans etat/joueurs/<siege>/fils.json, donc PAR SIEGE. Doctrine et format :
docs/fils.md — l aide complete : python scripts/fils.py --help.

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container plan/, module affaires.py — le nom leve l homonymie fils.py /
ecrans/modules/fils.js notee dans scripts/CLAUDE.md. Le chemin et la CLI de
cette commande sont geles.
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from plan.expose import affaires as _affaires  # noqa: E402
from plan.expose import fils_main as main  # noqa: E402,F401

lire = _affaires.lire
ecrire = _affaires.ecrire
sieges = _affaires.sieges
chemin = _affaires.chemin
CONDITIONS = _affaires.CONDITIONS

if __name__ == "__main__":
    main()
