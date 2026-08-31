# -*- coding: utf-8 -*-
"""LA PORTE du container ⏱️ temps — horloges, echeances, occupation, presence.

La regle (docs/organisation.md §2) : on n'entre dans un container que par sa
porte — `from temps.expose import ...`, jamais `from tick import ...`.
Ce fichier REEXPORTE ce que les importeurs consomment reellement aujourd'hui,
rien de plus.

Le tick est decoupe : la matiere vit dans les modules du container
(calendrier, lecture, bouche, mains, rumeur, gardes/,
fenetre, resume) et les symboles ci-dessous en viennent directement.
`scripts/tick.py` n'est plus qu'une facade CLI — reexportee ici uniquement
pour les importeurs historiques du module (tests).

L'ORDRE DES IMPORTS EST UNE CONTRAINTE : les modules du tick relisent
`temps.expose` PENDANT son chargement — `lecture` en lit `occupation`,
`gardes.sieges` en lit `occupation` et `regence`, `bouche` et
`gardes.ecrits` en lisent `presence` et `evaluer` paresseusement ;
`occupation`, `presence`, `regence` et `evaluer` doivent donc etre lies
avant eux.
"""

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from temps import occupation  # noqa: E402,F401 — qui est ASSIS ; lu par regence, sieges, lecture
from temps import presence  # noqa: E402,F401 — qui est a portee ; lu par bouche, evaluer, append_flux
from temps import regence  # noqa: E402,F401 — relit cette porte : occupation deja lie
from temps import disponibilite as evaluer  # noqa: E402,F401 — qui a du temps ; presence lu paresseusement
disponibilite = evaluer  # le nom du lot 2 (docs/organisation.md §7), pour les nouveaux lecteurs
import jours_relatifs  # noqa: E402,F401 — le calendrier relatif (noyau, lot 3 : il demenagera ici) ; lu par dater_plan et les echeances
from temps.calendrier import jour_absolu, date_de, fmt  # noqa: E402,F401
from temps.lecture import CANAUX_PLI, Etat, jours_de_route  # noqa: E402,F401
from temps.bouche import BUDGETS, echelle_de  # noqa: E402,F401 — BUDGETS n'a pas de sens sans sa clef : elle se MESURE (echelle_de), elle ne se declare plus
import tick  # noqa: E402,F401 — la facade CLI, gardee pour les tests qui l'importent
from temps import reprise  # noqa: E402,F401 — la feuille de reprise (lecture seule) ; hors contrainte d'ordre
