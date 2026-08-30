# -*- coding: utf-8 -*-
"""Les sieges — s'asseoir dans un personnage, en quitter un.

    python scripts/sieges.py                          # l'etat des sieges
    python scripts/sieges.py --quitter rhaenyra --vraiment
    python scripts/sieges.py --asseoir marlo-vasse --vraiment

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — la regle
(siege occupe -> pas de tete ; siege vacant -> une tete obligatoirement), la
bascule, l'archive des tetes — vit dans scene/sieges.py, avec tout son
POURQUOI en tete. Le chemin de cette commande est ULTRA-GELE (les books de
etat/ le citent) et sa CLI aussi ; les reexports ci-dessous gardent les
anciens noms `sieges.*` vivants pour les importeurs historiques.
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from scene.expose import sieges as _sieges  # noqa: E402 — LA PORTE de scene/

# Tout ce que l'ancien module offrait reste accessible sous les memes noms.
globals().update({n: getattr(_sieges, n) for n in dir(_sieges)
                  if not n.startswith("_")})
main = _sieges.main

if __name__ == "__main__":
    main()
