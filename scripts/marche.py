# -*- coding: utf-8 -*-
"""MARCHE — combien de temps il faut pour aller la-bas, a pied, par les rues.

    python scripts/marche.py salle:cabane-du-peigne lieu:la-gaffe
    python scripts/marche.py "La porte de la Gadoue" "Le Donjon Rouge" --qui marlo-vasse
    python scripts/marche.py --cache          (re)construit le graphe des rues

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — l'allure
tiree de l'identite, le cout des rues, le cache extrait du gros graphe — vit
dans monde/trajets.py, avec tout son POURQUOI en tete. Le chemin et la CLI de
cette commande sont geles ; les reexports ci-dessous gardent les anciens noms
`marche.*` vivants.
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from monde.expose import trajets as _trajets  # noqa: E402 — LA PORTE de monde/

# Tout ce que l'ancien module offrait reste accessible sous les memes noms.
globals().update({n: getattr(_trajets, n) for n in dir(_trajets)
                  if not n.startswith("_")})
main = _trajets.main

if __name__ == "__main__":
    main()
