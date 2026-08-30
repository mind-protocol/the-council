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

import os

from temps.lecture import ETAT
from etat.expose import tables  # LA PORTE de etat/

STAGING = ETAT

TABLES_MUTABLES = ("intentions", "evenements", "personnages", "monde",
                   "info", "actes", "paroles", "jetons", "annales",
                   "mains", "plis", "lieux")

# Les tables qui appartiennent a UN JOUEUR (voir scripts/appliquer.py).
CROYANCES = ("jetons", "vues", "objectifs")


def chemin_scelle(nom, joueur=None):
    if nom in CROYANCES and joueur:
        p = os.path.join(ETAT, "joueurs", joueur, nom + ".json")
        if os.path.isfile(p):
            return p
    return os.path.join(ETAT, nom + ".json")


def empreintes_etat(joueur=None):
    """Empreinte des tables au moment du calcul.

    Sert de garde a scripts/appliquer.py : si une table a bouge depuis, c'est
    qu'un autre ecrivain est passe et la proposition est perimee.
    """
    empreintes = {}
    for nom in TABLES_MUTABLES:
        chemin = chemin_scelle(nom, joueur)
        if not os.path.isfile(chemin):
            continue
        with io.open(chemin, "rb") as f:
            empreintes[nom] = hashlib.sha1(f.read()).hexdigest()
    return empreintes


def ecrire_proposition(nom_fichier, donnees):
    """SEULE ecriture du script. Refuse tout chemin hors etat/, puis la porte."""
    cible = os.path.abspath(os.path.join(STAGING, nom_fichier))
    permis = os.path.abspath(STAGING) + os.sep
    if not cible.startswith(permis):
        raise RuntimeError(
            "ecriture refusee hors etat/ : {}".format(cible))
    return tables.ecrire(cible, donnees)
