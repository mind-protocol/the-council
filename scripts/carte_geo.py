# -*- coding: utf-8 -*-
"""Genere la geometrie de la carte de Westeros a partir du mod AGOT.

Usage :
    python scripts/carte_geo.py                 -> ecrans/modules/geo.js
    python scripts/carte_geo.py --hauteur 620   (hauteur du viewBox)
    python scripts/carte_geo.py --tolerance 0.5 (simplification, unites SVG)

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — les
constantes de la carte et le lecteur du mod (monde/geographie.py), les
masques, contours et routes (monde/geographie_traces.py), l'assemblage et
l'ecriture de ecrans/modules/geo.js (monde/geographie_sortie.py) — vit dans
le container monde/. Le chemin et la CLI de cette commande sont geles ; les
reexports ci-dessous gardent les anciens noms `carte_geo.*` vivants.
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from monde.expose import geographie as _geographie  # noqa: E402 — LA PORTE de monde/

# Tout ce que l'ancien module offrait reste accessible sous les memes noms.
globals().update({n: getattr(_geographie, n) for n in dir(_geographie)
                  if not n.startswith("_")})
main = _geographie.main

if __name__ == "__main__":
    main()
