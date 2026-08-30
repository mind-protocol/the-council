# -*- coding: utf-8 -*-
"""CALENDRIER — l'arithmetique des dates absolues {annee, lune, jour}.

CE QUE CE MODULE POSSEDE : le calendrier du jeu (12 lunes de 30 jours), la
conversion date <-> entier de jours, le format d'affichage, la lecture d'une
date tapee en ligne de commande.

CE QU'IL REFUSE : les dates RELATIVES (l'echelle J-N du plan). Elles vivent
dans scripts/noyau/jours_relatifs.py, et la fusion n'a PAS eu lieu : son
`rang(a, l, j)` vaut ((a*12)+l)*30+j — sans le decalage -1 sur la lune et le
jour que `jour_absolu` applique. Deux arithmetiques du meme calendrier,
decalees d'une constante (31) ; fusionner changerait les rangs que les cahiers
citent deja. C'est note, pas tranche.

CONSOMMATEURS : tous les modules de temps/ (lecture, rumeur, gardes, fenetre,
resume), et migrer_plis / appliquer via la porte temps/expose.py.
"""
import sys

JOURS_PAR_LUNE = 30
LUNES_PAR_AN = 12


def jour_absolu(date):
    """{annee, lune, jour} -> entier de jours ; None si illisible."""
    raise NotImplementedError("implem : passe 2")


def date_de(n):
    """Entier de jours -> {annee, lune, jour}."""
    raise NotImplementedError("implem : passe 2")


def fmt(date):
    """{annee, lune, jour} -> '129.3.17' ; '?' si illisible."""
    raise NotImplementedError("implem : passe 2")


def lire_date(texte):
    """'129.3.20' -> {annee, lune, jour} ; sys.exit si hors calendrier."""
    raise NotImplementedError("implem : passe 2")
