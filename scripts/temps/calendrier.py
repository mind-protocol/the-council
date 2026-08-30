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
    """{annee, lune, jour} -> entier de jours. 12 lunes de 30 jours."""
    if not isinstance(date, dict):
        return None
    try:
        a = int(date.get("annee"))
        l = int(date.get("lune"))
        j = int(date.get("jour"))
    except (TypeError, ValueError):
        return None
    return (a * LUNES_PAR_AN + (l - 1)) * JOURS_PAR_LUNE + (j - 1)


def date_de(n):
    """Entier de jours -> {annee, lune, jour}."""
    jour = n % JOURS_PAR_LUNE
    lunes = n // JOURS_PAR_LUNE
    return {"annee": lunes // LUNES_PAR_AN,
            "lune": (lunes % LUNES_PAR_AN) + 1,
            "jour": jour + 1}


def fmt(date):
    """{annee, lune, jour} -> '129.3.17'."""
    if not isinstance(date, dict):
        return "?"
    return "{}.{}.{}".format(date.get("annee", "?"), date.get("lune", "?"),
                             date.get("jour", "?"))


def lire_date(texte):
    """'129.3.20' -> {annee, lune, jour}."""
    morceaux = texte.replace("/", ".").replace("-", ".").split(".")
    if len(morceaux) != 3:
        sys.exit("date illisible : {} (attendu 129.3.20)".format(texte))
    try:
        a, l, j = (int(m) for m in morceaux)
    except ValueError:
        sys.exit("date illisible : {} (attendu 129.3.20)".format(texte))
    if not 1 <= l <= LUNES_PAR_AN or not 1 <= j <= JOURS_PAR_LUNE:
        sys.exit("date hors calendrier : {} (12 lunes de 30 jours)".format(texte))
    return {"annee": a, "lune": l, "jour": j}
