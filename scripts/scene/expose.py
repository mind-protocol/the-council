# -*- coding: utf-8 -*-
"""LA PORTE du container 📜 scene — le flux, l'inbox, la montre, les sieges.

La regle (docs/organisation.md §2) : on n'entre dans un container que par sa
porte — `from scene.expose import ...`, jamais `import tunnel`.
Ce fichier REEXPORTE ce que les importeurs consomment reellement aujourd'hui,
rien de plus : seul `tunnel` est lu (par `append_flux`, du meme container).

`append_flux.py` reste la seule plume du flux ; personne ne l'importe, et la
scene est LA PEAU : les autres containers ne doivent jamais lire cette porte.
"""

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import tunnel  # noqa: E402,F401 — le compteur du flux ; lu par append_flux
from scene import seed_flux  # noqa: E402,F401 — le beat d'ouverture ; import inerte, l'ecriture ne part que par main()
