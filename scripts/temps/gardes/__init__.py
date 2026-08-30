# -*- coding: utf-8 -*-
"""GARDES — l'audit de coherence de etat/ : `python scripts/tick.py --verifier`.

CE QUE CE PAQUET POSSEDE : le Rapport (trois gravites, une gravite mal
orthographiee PLANTE au lieu de se perdre), les dix-neuf verificateurs
repartis par famille de tables, et `verifier()` qui les assemble dans l'ordre.

    plan.py    : intentions, mains, couts chiffres, etats du plan, rapporteurs
    ecrits.py  : pensees, books, boites, croyances sans porteur
    social.py  : evenements, personnages, plis, rumeurs
    sieges.py  : occupation, sieges, audiences, affectations, registres,
                 activations

TENSION ACTEE : conceptuellement du banc (lit tout, n'ecrit rien) — reexamen
vers bancs/ apres le lot 2. On ne le deplace pas avant.

CE QU'IL REFUSE : la moindre ecriture, et la moindre reparation — un audit
signale, il ne repare jamais.

CONSOMMATEURS : la facade scripts/tick.py (--verifier), /admin/sante via
--verifier --json, scripts/tests/essai_occupation.py (verifier_occupation).
"""

GRAVITES = ("grave", "avertissement", "note")


class Rapport(object):
    """Collecte les anomalies et les imprime, en texte ou en JSON."""

    def __init__(self):
        raise NotImplementedError("implem : passe 2")

    def dire(self, gravite, sujet, texte):
        """Ajoute une anomalie ; refuse bruyamment une gravite inconnue."""
        raise NotImplementedError("implem : passe 2")

    def imprimer_json(self):
        """Le meme audit en JSON, pour /admin/sante (--verifier --json)."""
        raise NotImplementedError("implem : passe 2")

    def imprimer(self):
        """L'audit a l'ecran, groupe par gravite."""
        raise NotImplementedError("implem : passe 2")


def verifier(e, en_json=False):
    """Tout l'audit, dans l'ordre. Code 1 si anomalie hors 'note', 0 sinon."""
    raise NotImplementedError("implem : passe 2")
