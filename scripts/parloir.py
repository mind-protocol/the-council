# -*- coding: utf-8 -*-
"""PARLOIR — se parler pendant qu'on travaille.

Le fil qui reste ouvert pendant qu'un homme depeche vit sa journee : le MJ
peut le relancer en cours de route au lieu de le rappeler dans une session
neuve qui a tout oublie. Un hook PostToolUse bat `--ecouter` des deux cotes ;
le silence ne coute rien.

Usage :
    python scripts/parloir.py --dire --de mj --a le-sanglier "Reviens au quai"
    python scripts/parloir.py --dire --de mj --a tous "On ouvre la salle"
    python scripts/parloir.py --ecouter --qui le-sanglier
    python scripts/parloir.py --ecouter --qui mj --hook   (sortie pour hook)
    python scripts/parloir.py --fils                      (l etat des fils)

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container agents/, module parloir.py. Le chemin est gele — les hooks
PostToolUse de .claude/settings.json le tapent tel quel.
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from agents.expose import parloir as _parloir  # noqa: E402
from agents.expose import parloir_main as main  # noqa: E402,F401

ouvrir_instance = _parloir.ouvrir_instance
nom_du_fil = _parloir.nom_du_fil
fils = _parloir.fils
TOUS = _parloir.TOUS

if __name__ == "__main__":
    main()
