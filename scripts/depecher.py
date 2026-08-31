# -*- coding: utf-8 -*-
"""DEPECHER — envoyer un homme vivre sa journee (la Regle Zero).

Usage :
    python scripts/depecher.py --qui le-sanglier
    python scripts/depecher.py --tous
    python scripts/depecher.py --qui sara --sec      montre tout, n'appelle pas
    python scripts/depecher.py --qui sara --mission "..."   consigne du jour

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container agents/depeche/ — brief, manuel, narrateur, trous, mission, retour,
cli. Le chemin et la CLI de cette commande sont geles ; les reexports
ci-dessous gardent les anciens noms `depecher.*` vivants pour les importeurs
historiques (boucle_activation).
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
from agents.expose import depeche as _depeche  # noqa: E402
from agents.expose import depecher_main as main  # noqa: E402,F401

OUTILS = _depeche.OUTILS
livre = _depeche.livre
date_du_monde = _depeche.date_du_monde
travaux_ouverts_de = _depeche.travaux_ouverts_de
brief_de = _depeche.brief_de
manuel_de = _depeche.manuel_de
manuel_narrateur_local = _depeche.manuel_narrateur_local
message_tentative = _depeche.message_tentative
contrat_rapport_narrateur = _depeche.contrat_rapport_narrateur
poser_letagere = _depeche.poser_letagere
poser_la_memoire = _depeche.poser_la_memoire
extraire_json = _depeche.extraire_json
depecher = _depeche.depecher
appeler = _depeche.appeler

if __name__ == "__main__":
    main()
