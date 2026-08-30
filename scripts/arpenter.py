# -*- coding: utf-8 -*-
"""ARPENTER — lever une carte comme un homme qui marche : au pas et a l'oeil.

    python scripts/arpenter.py --de "La porte de Fer" --a "Le Donjon Rouge"
    python scripts/arpenter.py --de "La porte de la Gadoue" --a "Le Donjon Rouge" \
        --livre leve-de-la-gadoue --titre "Ce que j'ai compte de la Gadoue au Donjon"

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — le leve en
pas, maisons, pentes a quatre degres, le brouillard (on ne leve que ce qu'on a
marche) — vit dans monde/arpentage.py, avec tout son POURQUOI en tete. Le
chemin et la CLI de cette commande sont geles ; les reexports ci-dessous
gardent les anciens noms `arpenter.*` vivants.
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from monde.expose import arpentage as _arpentage  # noqa: E402 — LA PORTE de monde/

# Tout ce que l'ancien module offrait reste accessible sous les memes noms.
globals().update({n: getattr(_arpentage, n) for n in dir(_arpentage)
                  if not n.startswith("_")})
main = _arpentage.main

if __name__ == "__main__":
    main()
