# -*- coding: utf-8 -*-
"""REVEILLER — le reveil du MJ du joueur sur le POST (habitant.md pas 5 :
le guetteur meurt, le geste du joueur EST le reveilleur).

    python scripts/reveiller.py --de rhaenyra
    python scripts/reveiller.py --qui mj-portreal --de otto "on force la porte"
    python scripts/reveiller.py --qui mj --de dev --etabli

`--etabli` : la journee-etabli du MJ (habitant.md : le MJ est un travailleur)
— le mot devient son etabli (staging, fils echus, billets non lus), calcule
par le lanceur hors sandbox (zone.etabli_de), verbe ETABLI.

Le serveur la spawn DETACHEE sur POST /action (serveur/routes/action.js) ;
elle appelle zone.appeler_zone — session continue du MJ, verdict sur stdout
(que personne ne lit ici : le MJ ecrit lui-meme au flux, c'est sa montre).

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container agents/, module zone.py.
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from agents.expose import reveiller_main as main  # noqa: E402,F401

if __name__ == "__main__":
    main()
