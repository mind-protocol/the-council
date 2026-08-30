# -*- coding: utf-8 -*-
"""Exporte le Grand Plan en texte brut, un fichier par cahier, dans exports/.

Usage :
    python scripts/exporter_plan.py            # boite-grand-plan + boite-sujets
    python scripts/exporter_plan.py --tout     # tous les livres de type plan
    python scripts/exporter_plan.py --sortie <dossier>

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container plan/, module exporter_plan.py. Le chemin et la CLI de cette
commande sont geles. L'ancien fichier exportait DES L'IMPORT (le piege note
dans scripts/CLAUDE.md) ; la facade n'exporte qu'executee.
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from plan.expose import exporter_plan_main as main  # noqa: E402

if __name__ == "__main__":
    main()
