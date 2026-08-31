# -*- coding: utf-8 -*-
"""La regence — ce qu'un siege vacant a le droit de faire, et ce qu'il rend.

    python scripts/regence.py                          # l'etat des sieges en regence
    python scripts/regence.py --clause rhaenyra        # la clause a poser dans sa tete
    python scripts/regence.py --poser rhaenyra --vraiment
    python scripts/regence.py --compte-rendu rhaenyra  # ce qu'on herite en se rasseyant

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — les sept
lignes rouges et le crible lexical (temps/regence.py), la clause, le registre
de passation et le main (temps/regence_passation.py) — vit dans le container
temps/, avec tout son POURQUOI en tete. Le chemin et la CLI de cette commande
sont geles ; les reexports ci-dessous gardent les anciens noms `regence.*`
vivants (sieges passe deja par la porte temps/expose,
qui rend le meme module).
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from temps.expose import regence as _regence  # noqa: E402 — LA PORTE de temps/

# Tout ce que l'ancien module offrait reste accessible sous les memes noms.
globals().update({n: getattr(_regence, n) for n in dir(_regence)
                  if not n.startswith("_")})
main = _regence.main

if __name__ == "__main__":
    main()
