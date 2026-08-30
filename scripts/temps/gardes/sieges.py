# -*- coding: utf-8 -*-
"""GARDES DES SIEGES — l'occupation mesuree, la regence, et les derives.

CE QUE CE MODULE POSSEDE : les verificateurs de ce qui tient au DEHORS du jeu
— l'occupation des sieges confrontee a la mesure (un drapeau qui ne ment pas
tout seul), les sieges vacants qui doivent une tete et la clause de regence,
les audiences du flux a plusieurs, les affectations au monde engendre, les
registres derives (un index ecrit a la main est un index qui va mentir), et
les activations (un taux de perte est une panne, pas une statistique).

CE QU'IL REFUSE : rafraichir quoi que ce soit — il renvoie aux commandes
(sieges.py --rafraichir, regence.py --poser, couverture.py --registres).

CONSOMMATEURS : gardes/__init__.py (verifier()), et
scripts/tests/essai_occupation.py (verifier_occupation, via la facade tick).
"""


def verifier_occupation(e, r):
    """L'IMPOSSIBLE QUE PERSONNE NE VOYAIT : le cache confronte a la mesure."""
    raise NotImplementedError("implem : passe 2")


def siege_par_id(e, pid):
    """L'entree de joueurs.json de ce personnage, ou {}."""
    raise NotImplementedError("implem : passe 2")


def verifier_sieges(e, r):
    """Le siege vacant doit avoir une tete ; l'occupe ne doit pas en avoir."""
    raise NotImplementedError("implem : passe 2")


def verifier_audiences(e, r):
    """A plusieurs, aucun item du flux ne doit etre sans audience."""
    raise NotImplementedError("implem : passe 2")


def verifier_affectations(e, r):
    """Les adresses physiques donnees en jeu tiennent-elles encore ?"""
    raise NotImplementedError("implem : passe 2")


def verifier_registres_derives(e, r):
    """Un index ecrit a la main est un index qui va mentir."""
    raise NotImplementedError("implem : passe 2")


def verifier_activations(e, r):
    """Ce que la boucle d'activation a produit, et ce qui a ete jete."""
    raise NotImplementedError("implem : passe 2")
