# -*- coding: utf-8 -*-
"""LA PORTE du container ⏱️ temps — horloges, echeances, occupation, presence.

La regle (docs/organisation.md §2) : on n'entre dans un container que par sa
porte — `from temps.expose import ...`, jamais `from tick import ...`.
Ce fichier REEXPORTE ce que les importeurs consomment reellement aujourd'hui,
rien de plus.

Tant que le lot 2 n'a pas vide les commandes, importer cette porte execute
`occupation`, `presence`, `regence`, `evaluer` et `tick` (3 200 lignes) —
comme les importeurs actuels le font deja en les important directement.

L'ORDRE DES IMPORTS EST UNE CONTRAINTE : `regence` et `tick`, basculees sur
cette porte, relisent `temps.expose` PENDANT son chargement ; `occupation`
(et `regence` pour `tick`) doivent donc etre lies avant elles.
"""

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import occupation  # noqa: E402,F401 — qui est ASSIS ; lu par regence, sieges, tick
import presence  # noqa: E402,F401 — qui est a portee ; lu par tick, evaluer, append_flux
import regence  # noqa: E402,F401 — relit cette porte : occupation deja lie
import evaluer  # noqa: E402,F401 — qui a du temps ; presence lu paresseusement
import tick  # noqa: E402,F401 — relit cette porte : occupation et regence deja lies
from tick import (BUDGETS, CANAUX_PLI, Etat, date_de, ecrire_proposition,  # noqa: E402,F401
                  empreintes_etat, fmt, jour_absolu, jours_de_route)
