# -*- coding: utf-8 -*-
"""GARDES DU SOCIAL — evenements, personnages, courrier, rumeurs.

CE QUE CE MODULE POSSEDE : les verificateurs de ce qui CIRCULE entre les gens
— les evenements (echeances passees, diffusion en retard, lieux inconnus),
les personnages (lieux qui existent), les plis (ce qui traine, ce qui vole
sans oiseau, ce qui n'a pas de main) et les roukeries, les rumeurs (une chose
ne devient jamais plus vraie en passant de bouche en bouche).

CE QU'IL REFUSE : ecrire, et proposer — la propagation vit dans rumeur.py, ici
on ne fait que constater ce qui cloche.

CONSOMMATEURS : gardes/__init__.py (verifier() les appelle dans l'ordre).
"""


def verifier_evenements(e, r):
    """Echeances passees, diffusion en retard, lieux inconnus."""
    raise NotImplementedError("implem : passe 2")


def verifier_personnages(e, r):
    """Chaque personnage est dans un lieu que lieux.json connait."""
    raise NotImplementedError("implem : passe 2")


def verifier_plis(e, r):
    """Le courrier : ce qui traine, vole sans oiseau, ou n'a pas de main."""
    raise NotImplementedError("implem : passe 2")


def verifier_rumeurs(e, r):
    """Les incidents qui servent de rumeurs. En gravite 'note', jamais bloquant."""
    raise NotImplementedError("implem : passe 2")
