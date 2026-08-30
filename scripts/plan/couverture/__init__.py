# -*- coding: utf-8 -*-
"""COUVERTURE — la couverture d'une affaire, calculee, jamais saisie.

POURQUOI. Une couverture ecrite a la main ment en trois jours : on ajoute une
action et l'on oublie de redire, en tete, qu'elle attend une piece d'ailleurs.
Tout ce qui se DEDUIT du graphe se recalcule donc ici, et l'on ne laisse a la
plume que ce qu'aucun calcul ne peut trouver : la conclusion, et fermee quand.

LES LIENS SONT TYPES, ET LA MOITIE SE DERIVE.
  ecrits  : decoupe / decoupee par · contredit · remplace / remplacee par · exclut
  derives : attend / attendue par · sert / servie par · partage
Un lien derive ne se saisit jamais : on le refait, il ne peut pas mentir.

CE QUE CE PAQUET POSSEDE, decoupe sous le plafond de 500 lignes :
    lecture.py   : normalisations, genres, numeros, casiers M/O, charger()
    blocs.py     : ce qui pend, ce qu'on engage, les trous, les liens derives
    registres.py : les quatre index derives et leur garde d'ecart
    ecrire.py    : refaire les couvertures, verser, et l'entree CLI main()

La commande gelee `scripts/couverture.py` est une FACADE qui appelle main()
par la porte plan/expose.py.
"""
import sys

# La console Windows est en cp1252 : une fleche ou un embleme dans un
# message de progression tuait le script APRES qu'il eut ecrit une partie
# de son travail. Le rapport ne doit jamais pouvoir faire tomber le calcul.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from plan.couverture.lecture import (  # noqa: F401
    RACINE, LIVRES, GENRES, NOM_GENRE, ECRITS, VIEUX, NUM, ADRESSE, MO,
    NERA, EST_MO, TETE_NUM, RIEN, nu, sans_emoji, genre_de, numero_de,
    registre_de, etiquette, col, charger)
from plan.couverture.blocs import (  # noqa: F401
    ATTENDU, RANG, FINI, tete_ornee, premier_mot, marque, blocs, remonte)
from plan.couverture.registres import (  # noqa: F401
    REGISTRES, SENS, NUMERO, NOM, AFFAIRE, ALIAS, CALCULE, colonnes_de,
    lire_cahiers, deriver, ecart_registres)
from plan.couverture.ecrire import (  # noqa: F401
    CHAMPS, SIGNE, refaire, verser, refaire_registres, main)
