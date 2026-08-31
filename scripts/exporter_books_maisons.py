# -*- coding: utf-8 -*-
"""Exporte en texte les books des maisons Targaryen noire et verte.

Usage :
    python scripts/exporter_books_maisons.py
    python scripts/exporter_books_maisons.py --sortie export/files

Cette commande est une facade : la matiere vit dans plan/.
"""
import os as _os, sys as _sys

_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from plan.expose import exporter_books_maisons_main as main  # noqa: E402


if __name__ == "__main__":
    main()
