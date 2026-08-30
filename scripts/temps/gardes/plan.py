# -*- coding: utf-8 -*-
"""GARDES DU PLAN — les tetes, les mains, les couts, et les producteurs.

CE QUE CE MODULE POSSEDE : les verificateurs de ce qui FAIT AVANCER le jeu —
les intentions (une tete par actif, budgets, retards, dependances), les mains
(l'arithmetique doit pouvoir etre juste), les couts chiffres, la colonne
d'etat du plan (six mots, pas un de plus), et les rapporteurs (un producteur
muet depuis sa cadence est une panne, jamais une statistique).

CE QU'IL REFUSE : ecrire, reparer, ou juger le contenu narratif.

CONSOMMATEURS : gardes/__init__.py (verifier() les appelle dans l'ordre).
"""


def verifier_intentions(e, r):
    """Une tete par actif, une seule, dans les budgets, a jour."""
    raise NotImplementedError("implem : passe 2")


def verifier_mains(e, r):
    """Les mains : ce qui empeche l'arithmetique d'etre juste."""
    raise NotImplementedError("implem : passe 2")


def verifier_couts_chiffres(e, r):
    """Un cout d'etape qui cite une mesure doit citer une mesure qui existe."""
    raise NotImplementedError("implem : passe 2")


def verifier_etats_du_plan(e, r):
    """La colonne d'etat d'une action ne porte QU'UN MOT, pris dans six."""
    raise NotImplementedError("implem : passe 2")


def verifier_rapporteurs(e, r):
    """Le seul verificateur qui ne regarde pas l'etat : il regarde LES AUTRES."""
    raise NotImplementedError("implem : passe 2")
