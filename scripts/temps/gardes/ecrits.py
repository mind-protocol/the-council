# -*- coding: utf-8 -*-
"""GARDES DES ECRITS — pensees, livres, coffrets, croyances sans porteur.

CE QUE CE MODULE POSSEDE : les verificateurs de ce qui S'ECRIT et se lit dans
le monde — les pensees (pas de source, pas de pensee), les livres et coffrets
de docs/books.md (cles hors format, prive qui ne ferme rien, emblemes qui se
confondent), la garde de fond de la refonte (« aucune croyance sans
porteur »), et ses deux aides : les sources possibles d'un savoir, et qui a
du temps aujourd'hui (la feuille de route d'evaluer.py, lue par le tick).

CE QU'IL REFUSE : comprendre le francais — le recoupement de mots rares est
une heuristique, assumee comme telle.

CONSOMMATEURS : gardes/__init__.py (verifier()), et fenetre.py
(qui_a_du_temps, l'entree de la salle).
"""

# Les cles connues du format docs/books.md — implem : passe 2 (elles voyagent
# entieres, avec leurs pourquoi).
CLES_BOOK = frozenset()
CLES_BOITE = frozenset()
TYPES_BOOK = frozenset()


def verifier_pensees(e, r):
    """PAS DE SOURCE, PAS DE PENSEE — et le quartier doit etre calculable."""
    raise NotImplementedError("implem : passe 2")


def qui_a_du_temps(e):
    """QUI DOIT UNE JOURNEE — la feuille de route d'evaluer.py, pour le tick."""
    raise NotImplementedError("implem : passe 2")


def verifier_books(e, r):
    """Les livres : ce qui les empeche de s'afficher, ou les fait doubler."""
    raise NotImplementedError("implem : passe 2")


def verifier_boites(e, r):
    """Les coffrets : ce qui les rend vides, doubles, ou ouverts a tous."""
    raise NotImplementedError("implem : passe 2")


def sources_possibles(e, pid):
    """Tout ce qui a PU apprendre quelque chose a ce personnage (heuristique)."""
    raise NotImplementedError("implem : passe 2")


def verifier_croyances_sans_porteur(e, r):
    """« Aucune croyance sans porteur » — en gravite 'note', jamais bloquante."""
    raise NotImplementedError("implem : passe 2")
