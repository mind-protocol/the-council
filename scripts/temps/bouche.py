# -*- coding: utf-8 -*-
"""LA BOUCHE — le rapprochement de textes, et l'echelle mesuree sur le quartier.

CE QUE CE MODULE POSSEDE : l'heuristique des mots rares (on ne comprend pas le
francais, on compare des mots distinctifs — assumee comme telle), les lectures
de tete (croyances, etapes au format objet), et l'ECHELLE d'un acteur —
mesuree sur le quartier (docs/boucle-acteurs.md), jamais declaree. Les budgets
par echelle (BUDGETS, TOLERANCE_MAJ, FENETRE_ROYAUME) vivent ici, a cote de
`echelle_de` qui est leur clef d'entree.

CE QU'IL REFUSE : la detection des arrivees (detecter_bouches vit dans
rumeur.py, avec la propagation dont elle partage les entrees), et tout
jugement — il mesure, gardes/ juge.

CONSOMMATEURS : rumeur.py, gardes/, fenetre.py, resume.py, et appliquer.py via
la porte temps/expose.py (BUDGETS).
"""

# L'ECHELLE A DISPARU, et le QUARTIER la remplace (docs/boucle-acteurs.md) :
# un acteur est dans le quartier d'un siege occupe, ou il est au loin.
ECHELLES = ("quartier", "au loin")

BUDGETS = {
    "quartier": {"acteurs": None, "croyances": 6, "etapes": 5,
                 "declencheurs": 3},
    "au loin":  {"acteurs": None, "croyances": 3, "etapes": 2,
                 "declencheurs": 1},
}

TOLERANCE_MAJ = {"quartier": 1, "au loin": 15}
FENETRE_ROYAUME = 5

MOTS_COMMUNS = frozenset()          # implem : passe 2 (la liste voyage entiere)
MOTS_PARTAGES_MINIMUM = 2


def mots_rares(texte):
    """Les mots distinctifs d'un texte : sans accents, longs, hors banalites."""
    raise NotImplementedError("implem : passe 2")


def se_recoupent(texte, autre, minimum=MOTS_PARTAGES_MINIMUM):
    """Deux textes parlent-ils vraisemblablement de la meme chose ?"""
    raise NotImplementedError("implem : passe 2")


def croyances_de(tete):
    """Les croyances d'une tete qui sont des chaines, et rien d'autre."""
    raise NotImplementedError("implem : passe 2")


def _dans_le_quartier():
    """Les ids que le joueur peut atteindre a pied, calcules une fois par run."""
    raise NotImplementedError("implem : passe 2")


def echelle_de(tete):
    """Ou se tient cette tete par rapport au joueur — mesure, jamais declaree."""
    raise NotImplementedError("implem : passe 2")


def etapes_de(tete):
    """Les etapes de plan au format objet ; les chaines sont ignorees ici."""
    raise NotImplementedError("implem : passe 2")
