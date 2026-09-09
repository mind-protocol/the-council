# -*- coding: utf-8 -*-
"""
regles.py — le livre de règles de la partie et le code qui les applique,
tenus ensemble.

    python scripts/regles.py --verifier   une règle sans marqueur, un marqueur
                                          sans règle, une ligne « où » périmée :
                                          sortie 1 ; les règles « sans code »
                                          sont listées à part et ne barrent rien
    python scripts/regles.py --ecrire     regénère sous chaque règle du livre la
                                          ligne « où : `module` (`fonction`) »,
                                          puis vérifie
    python scripts/regles.py --lister     les règles nommées, dans l'ordre du livre

Façade : la matière vit dans `scripts/noyau/regles_partie.py`. Rien ici ne
touche `etat/`.
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# Console Windows en cp1252 : sans ça, le garde crashe sur ses propres accents.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import regles_partie  # noqa: E402

if __name__ == "__main__":
    args = sys.argv[1:] or ["--verifier"]
    raise SystemExit(regles_partie.main(args))
