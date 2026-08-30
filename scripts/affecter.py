# -*- coding: utf-8 -*-
"""AFFECTER — donner une adresse physique a une chose de la fiction.

    python scripts/affecter.py                          l etat des affectations
    python scripts/affecter.py --bati 1554              la fiche d un batiment
    python scripts/affecter.py --chercher --usage taverne --pres-de 1772,2789
    python scripts/affecter.py --affecter lieu:la-gaffe 1554 --vraiment
    python scripts/affecter.py --ou lieu:la-gaffe
    python scripts/affecter.py --entre lieu:la-gaffe personnage:marlo-vasse
    python scripts/affecter.py --defaire lieu:la-gaffe --vraiment
    python scripts/affecter.py --verifier

Rien ne s ecrit sans --vraiment. La doctrine complete (la forme d une
affectation, les genres, la paire (monde, bat)) est en tete du paquet
agents/affectation/.

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container agents/affectation/ — lecture, controle, cli. Le chemin et la CLI
de cette commande sont geles ; les reexports ci-dessous gardent les anciens
noms `affecter.*` vivants pour les importeurs historiques (marche.py,
depecher.py, temps/gardes/sieges.py).
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
from agents.expose import affecter as _affectation  # noqa: E402
from agents.expose import affecter_main as main  # noqa: E402,F401

adresse = _affectation.adresse
position = _affectation.position
charger_liens = _affectation.charger_liens
charger_bati = _affectation.charger_bati
verifier = _affectation.verifier
reancrer = _affectation.reancrer
DEFAUT_MONDE = _affectation.DEFAUT_MONDE
GENRES = _affectation.GENRES

if __name__ == "__main__":
    main()
