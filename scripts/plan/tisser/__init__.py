# -*- coding: utf-8 -*-
"""TISSER — projeter tous les mecanismes de lien dans UNE SEULE table d'aretes.

POURQUOI. Le narratif de cette partie n'est pas dans les objets, il est dans
ce qui les relie : ~2 290 aretes ecrites a la main contre ~1 000 objets, sous
TREIZE noms, dans CINQ fichiers, qu'aucune requete ne traverse.

CE PAQUET NE MIGRE RIEN ET N'ECRIT PAS DANS etat/ (sauf --ecrire, qui depose
le tissu derive dans etat/tissu). Il PROJETTE : il relit les formats
existants et rend une vue. Le chiffre qui decide de tout le reste est le taux
de resolution — au-dela de 10% de pendantes, on repare l'adressage d'abord.

CE QUE CE PAQUET POSSEDE, decoupe sous le plafond de 500 lignes :
    lecture.py : le vocabulaire canonique, la lecture de l'etat, indexer()
    tissage.py : tisser() et l'entree CLI main()

La commande gelee `scripts/tisser.py` est une FACADE qui appelle main()
par la porte plan/expose.py.
"""
from plan.tisser.lecture import (  # noqa: F401
    RACINE, ETAT, SORTIE, CANON, INVERSES, PIECE, MOYEN, OFFICE, HYPO,
    A_DESIGNER, charger, grilles, registres_de, sphere_de, resoudre_code,
    nommer, plat_nom, col, nu, indexer)
from plan.tisser.tissage import tisser, main  # noqa: F401
