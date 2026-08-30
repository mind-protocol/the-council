# -*- coding: utf-8 -*-
"""Ajoute des items au flux de jeu (append-only) ET tient l'horloge du monde.

Usage : python scripts/append_flux.py '<json item>' '<json item>' ...
   ou : python scripts/append_flux.py --fichier chemin.json   (liste d'items)
Un item {"type": "effacer"} vide l'ecran (changement de scene).

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans
scene/flux.py (le script : audience, barriere des deux jours, presence,
horloges), scene/flux_scribe.py (portraits, montre d'un livre, l'heure) et
scene/flux_ecrits.py (les avis renvois et ecrits). flux.py est un SCRIPT qui
refuse l'import — la facade demande a la porte de le LANCER (pousser_flux),
argv tels quels : le chemin et la CLI de cette commande sont geles (le
serveur et le manuel l'appellent en sous-processus).
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from scene.expose import pousser_flux  # noqa: E402 — LA PORTE de scene/

if __name__ == "__main__":
    pousser_flux()
else:
    raise ImportError(
        "append_flux.py s'execute, il ne s'importe pas : l'importer pousserait "
        "le flux et avancerait l'horloge. Lancez-le en sous-processus.")
