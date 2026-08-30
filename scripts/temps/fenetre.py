# -*- coding: utf-8 -*-
"""FENETRE — ce qui tombe entre monde.date et la cible. Aucune decision.

CE QUE CE MODULE POSSEDE : le calcul de la fenetre, eclate en PHASES nommees
d'apres les sections de l'ancien calculer() — les commentaires de section sont
devenus leurs docstrings, on n'a pas perdu une ligne de pourquoi. calculer()
n'est plus qu'un sommaire qui les appelle dans l'ordre :

    les mains d'abord, acteurs simules, evenements a resoudre, nouvelles a
    livrer, le courrier, etapes, la bouche, la rumeur, declencheurs, tetes en
    retard, mutations proposees, les pensees.

Et tick() : la cible n'avance que dans un sens, la proposition s'ecrit dans
etat/tick-<horodatage>.json, le resume s'imprime.

CE QU'IL REFUSE : decider. Il lit etat/ et n'ecrit qu'une PROPOSITION sous
etat/ : le MJ seul relit, arbitre et applique (scripts/appliquer.py).

CONSOMMATEURS : la facade scripts/tick.py (--jours / --jusqu-a).
"""


def _phase_mains(e, jours, cible):
    """LES MAINS D'ABORD : leur sortie est l'entree des couts d'etapes."""
    raise NotImplementedError("implem : passe 2")


def _phase_acteurs(e, restriction, jours):
    """Quels acteurs on simule ; les 'royaume' sautent les fenetres courtes."""
    raise NotImplementedError("implem : passe 2")


def _phase_evenements(e, fin):
    """Les evenements a resoudre dans la fenetre, en retard compris."""
    raise NotImplementedError("implem : passe 2")


def _phase_nouvelles(e, fin):
    """Les nouvelles a livrer : resolu -> livrable, a-venir -> conditionnel."""
    raise NotImplementedError("implem : passe 2")


def _phase_courrier(e, fin):
    """LE COURRIER : un pli echu est REMIS au destinataire naturel du lieu."""
    raise NotImplementedError("implem : passe 2")


def _phase_etapes(e, simules, sautes, jours, mesures_apres):
    """Les etapes : tombent, avancent, ou attendent — les echeances jamais perdues."""
    raise NotImplementedError("implem : passe 2")


def _phase_declencheurs(simules):
    """Les declencheurs a evaluer — le MJ seul juge."""
    raise NotImplementedError("implem : passe 2")


def _phase_retards(simules, fin):
    """Les tetes en retard une fois la fenetre franchie."""
    raise NotImplementedError("implem : passe 2")


def _phase_mutations(mains, franchissements, avancent, plis_remis, rumeurs,
                     nouvelles, jours, cible):
    """Les mutations proposees : STRICTEMENT ce qui est arithmetique."""
    raise NotImplementedError("implem : passe 2")


def calculer(e, cible, restriction, joueur=None):
    """Ce qui tombe entre monde.date et cible. Aucune decision, du calcul."""
    raise NotImplementedError("implem : passe 2")


def tick(e, cible, restriction, joueur=None):
    """Calcule, ecrit la proposition dans etat/, imprime le resume. Rend 0."""
    raise NotImplementedError("implem : passe 2")
