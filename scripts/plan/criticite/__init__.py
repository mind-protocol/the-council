# -*- coding: utf-8 -*-
"""CRITICITE — ce qu'on perd si ce pas-la rate.

POURQUOI PAS « CE QUE CA DEBLOQUE ». La mesure naturelle est la portee : la
masse d'etats cibles qu'un pas sert en aval. Elle repond « c'est gros
derriere », ce qui n'est pas la question du matin. La question du matin est
CONTREFACTUELLE — combien de poids d'etats cesse d'etre atteignable si ce
pas-la n'arrive pas ? Un pas substituable tombe alors a zero, tout seul.
Les deux nombres sont imprimes cote a cote : l'ecart entre eux EST la
redondance.

UN SEUL POIDS SE SAISIT : celui des etats cibles, dans etat/poids-etats.json.
Absent, tout vaut 1 et le script LE DIT. Tout le reste se derive, donc ne
peut pas mentir plus longtemps que le graphe.

CE QUE CE PAQUET POSSEDE, decoupe sous le plafond de 500 lignes :
    page.py      : la mise en page (largeur, titres, cales, statuts)
    graphe.py    : amonts, atteignabilite, cercles, --pourquoi
    hommes.py    : ce que chaque homme porte, et ce qu'il NE VOIT PAS
    affaires.py  : le total d'une affaire, et sa veille
    decisions.py : l'arbre des fourches, et ce qu'une voie coute
    note.py      : la note d'un etat cible, et son echelle
    calcul.py    : le score contrefactuel, la charge servie au depeche
    cli.py       : main() — la CLI gelee de scripts/criticite.py

La commande gelee `scripts/criticite.py` est une FACADE qui appelle entree()
par la porte plan/expose.py.
"""
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from plan.criticite.page import (  # noqa: F401
    LARGEUR, titre, cale, statut, prix, faite)
from plan.criticite.graphe import (  # noqa: F401
    RACINE, POIDS, CONJONCTIF, DISJONCTIF, amonts, atteignables, cercles,
    pourquoi)
from plan.criticite.hommes import (  # noqa: F401
    TITRES, MOI, GLOSE, VACANT, SOI, CHIFFRES, gens, cle_homme, idees,
    rapprocher, porte_des_hommes, charge_des_hommes, section_charge, affiche)
from plan.criticite.affaires import (  # noqa: F401
    HISTOIRE, HEURES, totaux_par_affaire, veille)
from plan.criticite.decisions import (  # noqa: F401
    BRAS, DRAGONS, ENGAGE, cout, cout_du_plan, dire_cout, plan_de, declaree,
    decisions_ouvertes, arbre_des_decisions, descendance, section_decisions)
from plan.criticite.note import (  # noqa: F401
    NOTE_NEUTRE, objectifs_finaux, amplitude, poids_des_etats, masse, portee)
from plan.criticite.calcul import (  # noqa: F401
    GENRES_MESURES, raison_du_zero, calculer, charge_de)
from plan.criticite.cli import main, entree  # noqa: F401
