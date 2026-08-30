# -*- coding: utf-8 -*-
"""LA PORTE du container 🌍 monde — la ville : masque, plan, bati, gens, relief.

La regle (docs/organisation.md §2) : on n'entre dans un container que par sa
porte — `from monde.expose import ...`, jamais un module interne.

Rien de consomme encore : aucune commande du monde (`carte_geo`, `arpenter`,
`corps`, `marche`) n'est importee par un autre fichier Python aujourd'hui.
La porte est posee vide pour que le premier consommateur entre par elle,
et n'invente pas un chemin interne.
"""

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
