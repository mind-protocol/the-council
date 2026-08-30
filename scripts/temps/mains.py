# -*- coding: utf-8 -*-
"""MAINS — l'arithmetique des mesures : rythmes, bornes, decomptes, seuils.

CE QUE CE MODULE POSSEDE : tout ce qui fait bouger une mesure de mains.json
en entiers exacts (le reliquat empeche toute derive, quelle que soit la
decoupe des ticks), la lecture des couts chiffres d'une etape de plan, et le
predicat de seuil.

CE QU'IL REFUSE : la boucle qui applique tout ca sur une fenetre (fenetre.py),
et le jugement des mains mal formees (gardes/plan.py).

CONSOMMATEURS : fenetre.py (le decompte de la fenetre), gardes/plan.py
(verifier_mains, verifier_couts_chiffres via couts_chiffres et seuil_franchi).
"""


def rythme_de(mesure):
    """(par, jours) en entiers. Un rythme illisible vaut 'ne bouge pas'."""
    raise NotImplementedError("implem : passe 2")


def borner(valeur, mesure):
    """(valeur bornee, 'plancher'|'plafond'|None)."""
    raise NotImplementedError("implem : passe 2")


def au_plancher(mesure):
    """La mesure est-elle posee sur son plancher ?"""
    raise NotImplementedError("implem : passe 2")


def decompter(mesure, jours):
    """(valeur_apres, reliquat_apres, borne) — entiers seulement, sans derive."""
    raise NotImplementedError("implem : passe 2")


def porteur_absent(e, act):
    """Un porteur mort ou absent ne produit plus, mais l'affaire coute encore."""
    raise NotImplementedError("implem : passe 2")


def couts_chiffres(etape):
    """Les couts qui CITENT une mesure : {mesure: <adresse>, quantite: <int>}."""
    raise NotImplementedError("implem : passe 2")


def chiffrer_cout(etape, mesures_apres):
    """Ce qui manque pour tenir l'etape, adresse par adresse. [] = ca passe."""
    raise NotImplementedError("implem : passe 2")


def seuil_franchi(mesure_valeur, seuil):
    """Le seuil est-il franchi pour cette valeur ('sous' ou 'sur' la borne) ?"""
    raise NotImplementedError("implem : passe 2")
