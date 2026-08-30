# -*- coding: utf-8 -*-
"""Verse les `cahier2` des rapports dans etat/books.json — les changements de
registre qu'un homme depeche a rapportes de sa journee, en coordonnees.

Usage :
    python scripts/verser_cahier.py                 # a sec — montre tout
    python scripts/verser_cahier.py --qui sara      # un homme, repetable
    python scripts/verser_cahier.py --vraiment      # ecrit

Il ne devine pas : une coordonnee qui ne se resout pas exactement est REFUSEE
et dite en clair, jamais rapprochee au plus proche.

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container plan/, module verser_cahier.py. Le chemin et la CLI de cette
commande sont geles.
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from plan.expose import verser_cahier_main as main  # noqa: E402

if __name__ == "__main__":
    main()
