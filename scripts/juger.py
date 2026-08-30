# -*- coding: utf-8 -*-
"""JUGER — hook Stop du NARRATEUR, jamais de l'acteur.

Il relit le rapport que le narrateur vient d'etablir sur la tentative. Si
l'acteur est sous le seuil, il bloque la fin du narrateur et lui demande de
rendre un objet `relance_acteur`. Deux relances au plus.

Usage (le hook le fait tout seul ; ces formes servent a l'essayer) :
    python scripts/juger.py --sec --transcript <fichier.jsonl>
    echo '<charge du hook>' | python scripts/juger.py

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container agents/, module jugement.py (§7 : juger.py -> agents/jugement.py).
Le chemin est gele — le hook Stop de .claude/settings.json le tape tel quel.
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from agents.expose import juger_main as main  # noqa: E402

if __name__ == "__main__":
    main()
