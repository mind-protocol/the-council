# -*- coding: utf-8 -*-
"""MESURES — les adresses de mesure : ce qu'un cahier cite, et ce que l'etat
tient vraiment.

POURQUOI. Une colonne « La mesure » qui porte `recrutement-peyredragon.solde-due`
a l'air tenue. Rien ne garantit pourtant que la main existe, ni la mesure.
La faute symetrique est pire : un compte qui avance seul dans mains.json et
qu'aucun office ne cite ne remontera jamais a personne.

Ce paquet ne repare rien, n'arbitre rien, et n'ecrit NULLE PART. Il resout
les adresses citees dans etat/books.json contre etat/mains.json, nomme les
adresses mortes, les mesures orphelines, et les offices sans compte. Avec
--seuils, il confronte les hypotheses du plan aux valeurs du jour.

CE QUE CE PAQUET POSSEDE, decoupe sous le plafond de 500 lignes :
    adresses.py : la lecture de l'etat et la resolution des adresses
    rapport.py  : dire une mesure, et les trois sections
    seuils.py   : les hypotheses du plan, l'AIDE et l'entree CLI main()

La commande gelee `scripts/mesures.py` est une FACADE qui appelle main()
par la porte plan/expose.py.
"""
from plan.mesures.adresses import (  # noqa: F401
    LIVRE_OFFICES, forcer_utf8, dire, nu, sans_emoji, sans_accents, colonne,
    cellules_de, tables_de, charger_livres, charger_mains, index_des_mesures,
    BACKTICK, ADRESSE, adresses_dans, lire_offices, citations_ailleurs)
from plan.mesures.rapport import (  # noqa: F401
    mouvement, valeur_dite, porteur_dit, ligne_de_mesure, avoue_le_trou,
    entete, section_ce_qui_se_mesure, section_ce_qui_ne_resout_pas,
    section_sans_mesure)
from plan.mesures.seuils import (  # noqa: F401
    MOTS_VIDES, radical, mots_clefs, lire_hypotheses, lire_seuil, rapprocher,
    verdict_arithmetique, section_seuils, AIDE, main)
