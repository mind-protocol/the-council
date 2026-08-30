# -*- coding: utf-8 -*-
"""ETAT DU PLAN — l'etat du plan, toutes affaires confondues. Lecture seule.

DEUX ECHELLES. Le plan se date a rebours du jour d'entree, qui n'est arrete
nulle part (verrou 11001). Sans jour d'entree, les J−N sont comptes et tries
entre eux ; avec --jour-entree, ils sont convertis sous une hypothese
annoncee en tete de rapport. Les derivations viennent du chargeur de
couverture ; si un cahier dit autre chose, relancer couverture.

CE QUE CE PAQUET POSSEDE, decoupe sous le plafond de 500 lignes :
    page.py      : la mise en page (largeur, titres, lignes, cales)
    echeances.py : le jour, les statuts, l'echelle J−N, les registres annexes
    missions.py  : la coupe par personne (missions_de, phrase, --pour, --qui)
    sections.py  : les sections du rapport (--du, chaines, grille, comparer)
    cli.py       : main() et l'AIDE — la CLI gelee de scripts/etat_du_plan.py

La commande gelee `scripts/etat_du_plan.py` est une FACADE qui appelle main()
par la porte plan/expose.py.
"""
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from plan.etat_du_plan.page import LARGEUR, titre, ligne, cale  # noqa: F401
from plan.etat_du_plan.echeances import (  # noqa: F401
    RACINE, DATE_LUNE, DATE_JOUR, DEPEND, FINI_ETAT, STATUTS, aujourdhui,
    rang, statut_de, echeance_de, relatives, echelle, amont_de, colonne,
    registre)
from plan.etat_du_plan.missions import (  # noqa: F401
    etats_bloques, verrous_de, clefs_de, actions_de, nom_de, adresse,
    suffisance, force, missions_de, phrase, section_pour, section_emblemes,
    section_qui)
from plan.etat_du_plan.sections import (  # noqa: F401
    PLAFOND, section_jour, section_portee, section_synthese,
    section_brouillons, section_du, section_chaines, section_arrache,
    section_charge, section_muettes, section_trous, section_grille,
    section_comparer)
from plan.etat_du_plan.cli import AIDE, main  # noqa: F401
