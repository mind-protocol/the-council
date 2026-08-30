# -*- coding: utf-8 -*-
"""CORPS — la ville a deja les corps ; on les regarde, on les lie, on les promeut.

    python scripts/corps.py --autour "La porte de la Gadoue" --rayon 120
    python scripts/corps.py --lier <personnage_id> <corps>
    python scripts/corps.py --promouvoir <corps> --vraiment

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — l'annuaire
des corps, l'appariement par metier et quartier (corps_metiers), le logement,
la promotion — vit dans monde/corps.py et monde/corps_metiers.py. Le chemin
et la CLI de cette commande sont geles ; les reexports ci-dessous gardent les
anciens noms `corps.*` vivants.
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from monde.expose import corps as _corps  # noqa: E402 — LA PORTE de monde/

# Tout ce que l'ancien module offrait reste accessible sous les memes noms.
globals().update({n: getattr(_corps, n) for n in dir(_corps)
                  if not n.startswith("_")})
main = _corps.main

if __name__ == "__main__":
    main()
