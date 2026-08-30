# -*- coding: utf-8 -*-
"""LA PORTE du container ⚔️ bataille — EN SURSIS : le futur adaptateur vers `batailles`.

La regle (docs/organisation.md §2) : on n'entre dans un container que par sa
porte. D1 est acte : le jour de la bascule vers le depot `batailles`, on
remplace une porte par une porte — `cuire(ordre) -> annales` vivra ici.

Rien de consomme encore : personne n'importe `bataille.py` aujourd'hui.

HOMONYMIE A CONNAITRE : tant que `scripts/bataille.py` existe a la racine, le
module `bataille` masque le paquet `bataille/` — `from bataille.expose import`
echouerait. Sans consommateur ce n'est pas un probleme aujourd'hui ; le jour
ou la porte sert, c'est la commande qui devient facade et le conflit se regle
au lot 2 (docs/organisation.md §8 le sait deja pour `fils`).
"""

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
