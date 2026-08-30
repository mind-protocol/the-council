# -*- coding: utf-8 -*-
"""Ce qui a ete ecrit dans une fenetre de temps — et, sur ordre, ce qu'on en retire.

Usage :
    python scripts/purger.py --du 25:886 --au 25:1100
    python scripts/purger.py --du 25:886 --au 25:1100 --qui aurore-inchauspe
    python scripts/purger.py --du 25:886 --au 25:1100 --vraiment

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — le POURQUOI
de la recherche par DATE et jamais par mots-cles, le mode montrer-d'abord —
vit dans etat/purge.py. Le chemin et la CLI de cette commande sont geles ;
les reexports ci-dessous gardent les anciens noms `purger.*` vivants.
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from etat.expose import purge as _purge  # noqa: E402 — LA PORTE de etat/

TABLES = _purge.TABLES
PAR_JOUEUR = _purge.PAR_JOUEUR
sans_accents = _purge.sans_accents
borne = _purge.borne
dans = _purge.dans
main = _purge.main

if __name__ == "__main__":
    main(sys.argv[1:])
