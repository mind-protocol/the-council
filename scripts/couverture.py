# -*- coding: utf-8 -*-
"""La couverture d'une affaire — calculee, jamais saisie.

Usage :
    python scripts/couverture.py              toutes les affaires
    python scripts/couverture.py --affaire "L'entree sans bataille"
    python scripts/couverture.py --verifier   dit ce qui bougerait, n'ecrit rien
    python scripts/couverture.py --registres  refait les quatre index derives

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container plan/couverture/ — lecture, blocs, registres, ecrire. Le chemin et
la CLI de cette commande sont geles ; les reexports ci-dessous gardent les
anciens noms `couverture.*` vivants pour les importeurs historiques.
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from plan.expose import (  # noqa: E402,F401
    nu, sans_emoji, marque, blocs, NUM, MO, NOM_GENRE, EST_MO, NERA,
    etiquette, genre_de, ATTENDU, RANG, FINI, premier_mot, tete_ornee,
    numero_de, registre_de, col)
from plan.expose import couverture as _couverture  # noqa: E402
from plan.expose import couverture_main as main  # noqa: E402

charger = _couverture.charger
deriver = _couverture.deriver
ecart_registres = _couverture.ecart_registres
refaire = _couverture.refaire
refaire_registres = _couverture.refaire_registres
verser = _couverture.verser
RIEN = _couverture.RIEN

if __name__ == "__main__":
    sys.exit(main())
