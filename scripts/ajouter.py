# -*- coding: utf-8 -*-
"""Ajoute UN enregistrement a une table d'empilement, sans jamais reecrire
ce qu'on n'a pas lu a l'instant meme.

Usage :
    python scripts/ajouter.py actes '{"id":"acte-042", ...}'
    python scripts/ajouter.py vues --fichier v.json
    python scripts/ajouter.py paroles '<json>' '<json>' ...

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — le
POURQUOI de la fenetre etroite et les tables d'empilement — vit dans
etat/entree.py. Le chemin et la CLI de cette commande
sont geles ; les reexports ci-dessous gardent les anciens noms `ajouter.*`
vivants pour les importeurs historiques.
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from etat.expose import entree as _entree  # noqa: E402 — LA PORTE de etat/

TABLES = _entree.TABLES
chemin = _entree.chemin
ajouter = _entree.ajouter
main = _entree.main

if __name__ == "__main__":
    main(sys.argv[1:])
