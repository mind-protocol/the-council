# -*- coding: utf-8 -*-
"""Le detecteur de fumee : qu'est-ce qui a bouge dans etat/ depuis mon dernier tour ?

Usage :
    python scripts/veille.py rhaenyra          -> ce qui a change depuis mon
                                                  dernier passage, puis rearme
    python scripts/veille.py rhaenyra --voir   -> regarde sans rearmer

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — le POURQUOI
de l'alarme, les empreintes sha1, le rearmement — vit dans etat/empreintes.py.
Le chemin et la CLI de cette commande sont geles ; les reexports ci-dessous
gardent les anciens noms `veille.*` vivants pour les importeurs historiques.
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from etat.expose import empreintes as _empreintes  # noqa: E402 — LA PORTE de etat/

IGNORE = _empreintes.IGNORE
empreintes = _empreintes.empreintes
main = _empreintes.main

if __name__ == "__main__":
    main(sys.argv[1:])
