# -*- coding: utf-8 -*-
"""L'outil du MJ de Corneille — retrouver un moment dans le fil.

    python scripts/regie.py --chercher "steffon arrive"
    python scripts/regie.py --chercher "les prisonniers" --max 20
    python scripts/regie.py --autour 7412            # ce qu'il y a autour

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — la
recherche dans le fil, la fenetre autour d'un index, le POURQUOI (le script
donne les candidats, le MJ tranche) — vit dans scene/regie.py. Le chemin et
la CLI de cette commande sont geles. Lecture seule de bout en bout.
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from scene.expose import regie as _regie  # noqa: E402 — LA PORTE de scene/

lire_flux = _regie.lire_flux
chercher = _regie.chercher
autour = _regie.autour
main = _regie.main

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main(sys.argv[1:])
