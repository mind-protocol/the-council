# -*- coding: utf-8 -*-
u"""RECONCILIER — le journal des affaires ecrites a la main.

    python scripts/reconcilier.py              ce qui serait emis
    python scripts/reconcilier.py --vraiment   emet et pose l'empreinte
    python scripts/reconcilier.py --amorcer    pose l'empreinte SANS emettre

Les affaires ont deux maisons : `etat/books/`, dont la porte emet le journal
toute seule, et `chambres/<qui>/books/`, qui n'a AUCUNE porte — on y ecrit par
Write et Edit. Ce script est le seul moyen de savoir ce qui y a bouge.

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container agents/, module reconcilier.py.
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from agents.expose import reconcilier as _reconcilier  # noqa: E402
from agents.expose import reconcilier_main as main  # noqa: E402,F401

maisons = _reconcilier.maisons
passer = _reconcilier.passer

if __name__ == "__main__":
    main()
