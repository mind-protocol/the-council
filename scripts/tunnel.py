# -*- coding: utf-8 -*-
"""Le tunnel — un homme qui devide au lieu de distiller.

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — les seuils
(ITEM, TRANCHE, SUITE, VOIX, FILS), le plafond dur (MUR) et l'avis qui refuse
la poussee — vit dans scene/tunnel.py, avec tout son POURQUOI en tete. Pas de
CLI : ce module est le garde-fou d'append_flux, qui l'importe par la porte
scene/expose. Les reexports ci-dessous gardent les anciens noms `tunnel.*`
vivants pour les importeurs historiques.
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from scene.expose import tunnel as _tunnel  # noqa: E402 — LA PORTE de scene/

ITEM = _tunnel.ITEM
TRANCHE = _tunnel.TRANCHE
SUITE = _tunnel.SUITE
VOIX = _tunnel.VOIX
FILS = _tunnel.FILS
MUR = _tunnel.MUR
BAVARDS = _tunnel.BAVARDS
avis = _tunnel.avis
