# -*- coding: utf-8 -*-
"""Façade publique : extraire le graphe causal amont des événements."""
import os as _os, sys as _sys

_d = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from plan.expose import graphe_causal as _graphe  # noqa: E402
from plan.expose import graphe_causal_main as main  # noqa: E402,F401

extraire = _graphe.extraire
extraire_tous = _graphe.extraire_tous
normaliser = _graphe.normaliser
proposer_complements = _graphe.proposer_complements
ecrire_complements = _graphe.ecrire_complements


if __name__ == "__main__":
    raise SystemExit(main())
