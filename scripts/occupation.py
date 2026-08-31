# -*- coding: utf-8 -*-
"""Qui est ASSIS — mesure, et non declaration.

    python scripts/occupation.py               # la mesure, siege par siege
    python scripts/occupation.py --rafraichir --vraiment

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — la
definition arretee (« occupe » = actif recemment : veille fraiche OU inbox),
la regle des veilles qui comptent, les deux marques de main (assis_a,
quitte_a), le refus de rendre vacant un siege sans tete — vit dans
temps/occupation.py, avec tout son POURQUOI en tete. Le chemin et la CLI de
cette commande sont geles ; les reexports ci-dessous gardent les anciens noms
`occupation.*` vivants (regence, sieges et les tests
passent deja par la porte temps/expose, qui rend le meme module).
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from temps.expose import occupation as _occupation  # noqa: E402 — LA PORTE de temps/

# Tout ce que l'ancien module offrait reste accessible sous les memes noms.
globals().update({n: getattr(_occupation, n) for n in dir(_occupation)
                  if not n.startswith("_")})
main = _occupation.main

if __name__ == "__main__":
    main()
