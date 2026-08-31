# -*- coding: utf-8 -*-
u"""RENDRE LES CELLULES — remettre ce qu'une reecriture a efface, SANS ecraser.

    python scripts/rendre_cellules.py chambre:mj              a sec
    python scripts/rendre_cellules.py chambre:mj --vraiment   l'ecriture

ON NE REMPLIT QUE DU VIDE : une cellule occupee n'est jamais touchee, donc la
fusion ne peut rien detruire — meme pendant qu'une autre session ecrit.

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container agents/, module rendre_cellules.py.
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from agents.expose import rendre_cellules as _r  # noqa: E402
from agents.expose import rendre_cellules_main as main  # noqa: E402,F401

fusionner = _r.fusionner
passer = _r.passer

if __name__ == "__main__":
    main()
