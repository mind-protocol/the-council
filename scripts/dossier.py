# -*- coding: utf-8 -*-
"""Le dossier d'un sujet : tout ce que l'etat sait deja de lui, avant d'ecrire.

Usage :
    python scripts/dossier.py --sur wat
    python scripts/dossier.py --sur caves --sur roon --depuis 16
    python scripts/dossier.py --sur rosby --large        (tout le texte, pas d'extrait)

Ce script ne verifie rien et n'arbitre rien : il RASSEMBLE, dans l'ordre
d'autorite. A lire avant d'ouvrir une scene, et avant de faire parler
quelqu'un.

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container agents/, module matiere.py (§7 : dossier.py -> agents/matiere.py).
Le chemin et la CLI de cette commande sont geles.
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from agents.expose import dossier_main as main  # noqa: E402

if __name__ == "__main__":
    main(sys.argv[1:])
