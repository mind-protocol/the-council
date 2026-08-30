# -*- coding: utf-8 -*-
"""EVALUER — les questions qu'on ne pouvait pas poser au tissu.

Usage :
    python scripts/evaluer.py                tout, en resume
    python scripts/evaluer.py --goulots --desequilibres --critique
    python scripts/evaluer.py --orphelins --murs --sourds --portees
    python scripts/evaluer.py --json        la feuille que la regie relit

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans
temps/disponibilite.py (les questions 1-7 : goulots, desequilibres, chemin
critique, orphelins, murs, sourds, portees) et temps/disponibilite_regie.py
(la force narrative, la feuille de la regie, le main). Le chemin et la CLI de
cette commande sont geles ; les reexports ci-dessous gardent les anciens noms
`evaluer.*` vivants (depecher et les gardes passent deja par la porte
temps/expose, qui rend le meme module sous le nom `evaluer`).
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from temps.expose import evaluer as _evaluer  # noqa: E402 — LA PORTE de temps/

# Tout ce que l'ancien module offrait reste accessible sous les memes noms.
globals().update({n: getattr(_evaluer, n) for n in dir(_evaluer)
                  if not n.startswith("_")})
main = _evaluer.main

if __name__ == "__main__":
    main()
