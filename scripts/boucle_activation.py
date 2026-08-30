# -*- coding: utf-8 -*-
"""Boucle d'activation narrative pilotee par le graphe miroir.

Usage :
    python scripts/boucle_activation.py --sec --une-fois
    python scripts/boucle_activation.py --une-fois
    python scripts/boucle_activation.py

``--sec`` ne lance aucun modele et n'ecrit aucun etat d'ordonnancement.

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container agents/activation/ — socle, horloges, graphe, taches, missions,
dossier, mutations, rapport, continuite, appels, cycle, cli. Le chemin et la
CLI de cette commande sont geles ; les reexports ci-dessous gardent les
anciens noms `boucle_activation.*` vivants pour les importeurs historiques
(les bancs d'analyse/, plan/lacunes.py — via la porte).
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from agents.expose import boucle_activation as _activation  # noqa: E402
from agents.expose import boucle_activation_main as main  # noqa: E402,F401

cycle = _activation.cycle
VerrouBoucle = _activation.VerrouBoucle
prevoir_activations = _activation.prevoir_activations
GENRES_RELAIS = _activation.GENRES_RELAIS
ETAT_BOUCLE = _activation.ETAT_BOUCLE
charger_tissu = _activation.charger_tissu
adjacence = _activation.adjacence
diffuser = _activation.diffuser
importance = _activation.importance

if __name__ == "__main__":
    raise SystemExit(main())
