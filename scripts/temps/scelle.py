# -*- coding: utf-8 -*-
"""SCELLE — la garde d'ecriture : empreintes des tables, seule ecriture du tick.

CE QUE CE MODULE POSSEDE : la liste des tables mutables, le chemin scelle
d'une table (par joueur pour les croyances), l'empreinte de l'etat au moment
du calcul (la garde de scripts/appliquer.py contre les propositions perimees),
et l'UNIQUE ecriture du tick — refusee hors etat/.

TENSION ACTEE : ce module est du vocabulaire d'etat (staging) — candidat a
etat/ le jour ou un second ecrivain apparait. On ne le deplace pas avant.

CE QU'IL REFUSE : ecrire ailleurs que sous etat/, et decider quoi que ce soit
du contenu — il scelle et depose, le MJ arbitre.

CONSOMMATEURS : fenetre.py (tick() ecrit sa proposition), et appliquer.py /
migrer_plis via la porte temps/expose.py (empreintes_etat, ecrire_proposition).
"""
import hashlib
import io
import json
import os

from temps.lecture import ETAT

STAGING = ETAT

TABLES_MUTABLES = ("intentions", "evenements", "personnages", "monde",
                   "info", "actes", "paroles", "jetons", "annales",
                   "mains", "plis", "lieux")

# Les tables qui appartiennent a UN JOUEUR (voir scripts/appliquer.py).
CROYANCES = ("jetons", "vues", "objectifs")


def chemin_scelle(nom, joueur=None):
    """Le fichier que appliquer.py ecrira reellement pour cette table."""
    raise NotImplementedError("implem : passe 2")


def empreintes_etat(joueur=None):
    """Empreinte sha1 des tables au moment du calcul — garde d'appliquer.py."""
    raise NotImplementedError("implem : passe 2")


def ecrire_proposition(nom_fichier, donnees):
    """SEULE ecriture du script. Refuse tout chemin hors etat/."""
    raise NotImplementedError("implem : passe 2")
