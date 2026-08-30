# -*- coding: utf-8 -*-
"""Applique une proposition de etat/ a etat/*.json.

Usage :
    python scripts/appliquer.py tick-20260806-024652.json              -> blanc
    python scripts/appliquer.py tick-20260806-024652.json --vraiment   -> ecrit
    python scripts/appliquer.py <fichier> --vraiment --forcer          -> passe outre
                                                                          les gardes

Le pendant de scripts/tick.py. Le tick CALCULE et propose ; celui-ci APPLIQUE
ce que le MJ a valide, sous trois gardes : empreintes, validation, atomicite.

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
paquet etat/mutations/ — vocabulaire, lecture, validation (val_plan,
val_registres, val_courrier, val_social), application, cli. Le vocabulaire
FERME des mutations est documente dans etat/mutations/__init__.py ; la
reference normative reste docs/schema.md. Le chemin et la CLI de cette
commande sont geles ; les reexports ci-dessous gardent les anciens noms
`appliquer.*` vivants pour les importeurs historiques (boucle_activation
passe deja par la porte etat/expose, qui rend le meme paquet).
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from etat.expose import mutations as _mutations  # noqa: E402 — LA PORTE de etat/

# Tout ce que l'ancien module offrait reste accessible sous les memes noms.
_publics = [n for n in dir(_mutations) if not n.startswith("_")]
globals().update({n: getattr(_mutations, n) for n in _publics})
main = _mutations.main

if __name__ == "__main__":
    sys.exit(main())
