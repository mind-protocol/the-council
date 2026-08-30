# -*- coding: utf-8 -*-
"""LECTURE — tout l'etat charge une fois, et les jours de route.

CE QUE CE MODULE POSSEDE : le chargement de etat/*.json (lecture seule,
toujours), la classe Etat avec ses index (lieux, personnages, mesures,
intentions, sieges mesures par occupation), et l'estimation des jours de route
entre deux lieux. Il possede aussi les constantes du COURRIER (canaux, etats
de pli, tolerances) : elles vivent a cote de `jours_de_route` et des methodes
plis d'Etat (roukerie, destinataire_naturel, depart_de), qui sont leurs seuls
lecteurs arithmetiques.

CE QU'IL REFUSE : toute ecriture (c'est scelle.py), toute interpretation
(gardes/ et fenetre.py jugent, lui charge).

CONSOMMATEURS : gardes/, fenetre.py, rumeur.py, resume.py, la facade tick.py,
et migrer_plis via la porte temps/expose.py (Etat, jours_de_route, CANAUX_PLI).
"""
import io
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ETAT = os.path.join(RACINE, "etat")

# Les plis (docs/plis.md). Un pli est un OBJET : la rumeur et le temoin n'en
# sont pas, et restent a evenements.diffusion.
CANAUX_PLI = ("corbeau", "cavalier", "barque")
ETATS_PLI = ("en-route", "remis", "ouvert", "retenu", "perdu", "intercepte")
ETATS_PLI_EN_MAIN = ("remis", "ouvert", "retenu")
TOLERANCE_PLI = 3
DIVISEUR_CORBEAU = 3


def charger(nom, defaut):
    """Lit etat/<nom>.json. Lecture seule, toujours."""
    raise NotImplementedError("implem : passe 2")


class Etat(object):
    """Tout l'etat charge une fois, avec les index dont on se sert partout."""

    def __init__(self):
        raise NotImplementedError("implem : passe 2")

    def lieu(self, lid):
        """Id de lieu -> id canonique, ou None si inconnu."""
        raise NotImplementedError("implem : passe 2")

    def nom(self, pid):
        """Id de personnage -> son nom, ou l'id lui-meme."""
        raise NotImplementedError("implem : passe 2")

    def actifs_en(self, lid):
        """Personnages actifs presents dans ce lieu (alias compris)."""
        raise NotImplementedError("implem : passe 2")

    def roukerie(self, lid):
        """Stock de corbeaux d'un lieu : {lieu d'origine: nombre}."""
        raise NotImplementedError("implem : passe 2")

    def destinataire_naturel(self, lid):
        """A qui un pli est REMIS en arrivant la — jamais au 'pour'."""
        raise NotImplementedError("implem : passe 2")

    def depart_de(self, pli):
        """Lieu de depart d'un pli : `depuis`, sinon le lieu de l'expediteur."""
        raise NotImplementedError("implem : passe 2")


def jours_de_route(e, depuis, vers, canal):
    """Estimation en jours depuis les jours_de_pr. None si on ne sait pas."""
    raise NotImplementedError("implem : passe 2")
