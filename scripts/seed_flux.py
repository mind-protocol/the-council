# -*- coding: utf-8 -*-
"""(Re)initialise etat/flux.jsonl — beat d'ouverture : le conseil noir.

    python scripts/seed_flux.py     # DESTRUCTIF : reecrit le fil entier

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — les items
du beat d'ouverture et l'ecriture du fil — vit dans scene/seed_flux.py, ou
elle ne part que par main() (l'import est inerte). Le chemin et la CLI de
cette commande sont geles.
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from scene.expose import seed_flux as _seed_flux  # noqa: E402 — LA PORTE de scene/

main = _seed_flux.main

if __name__ == "__main__":
    main()
