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

CONSOMMATEURS : rumeur.py, gardes/, fenetre.py et resume.py.
"""


# L'ECHELLE A DISPARU, et le QUARTIER la remplace (docs/boucle-acteurs.md).
#
# Trois systemes reglaient l'importance d'un acteur et se marchaient dessus :
# l'echelle posee a la main, l'excitation comptee, la force narrative calculee
# sur le graphe. En retirant l'echelle des poids, le classement des dix
# premiers ne bougeait quasiment pas — elle recopiait a la main ce que le tissu
# calculait deja, et se contredisait avec lui six fois sur quinze.
#
# Ce qui la remplace ne se declare pas : il se MESURE, a chaque tick, sur la
# topologie. Un acteur est dans le QUARTIER d'un siege occupe (meme composante
# connexe, moins de vingt minutes de marche) ou il est AU LOIN. Aucun plafond
# d'acteurs : ce qui coute, c'est la tete, et une tete au loin coute peu.
ECHELLES = ("quartier", "au loin")

BUDGETS = {
    "quartier": {"acteurs": None, "croyances": 6, "etapes": 5,
                 "declencheurs": 3},
    # un declencheur reste permis : sans lui, un lointain serait sourd au joueur
    "au loin":  {"acteurs": None, "croyances": 3, "etapes": 2,
                 "declencheurs": 1},
}

# Retard tolere de date_maj, en jours, avant qu'une tete soit dite en retard.
TOLERANCE_MAJ = {"quartier": 1, "au loin": 15}

# Les acteurs lointains ne valent pas le calcul sur une fenetre courte.
FENETRE_ROYAUME = 5

# LA BOUCHE — rapprochement de textes. On ne comprend pas le francais, on
# compare des mots rares : deux mots distinctifs partages suffisent a dire
# « ce fait a pu lui venir de la ». C'est une heuristique, assumee comme telle.
MOTS_COMMUNS = frozenset("""
alors apres aussi avait avant avec bien cela cette chose comme contre dans deux
elle encore entre etait etre faire fait fille homme jamais leur leurs mais meme
moins nous parce pour plus pourrait pouvoir quand quelque reine roi sans sera
serait seul sont sous suis tous tout toute toutes trois trop vers veut voir
votre vous celui ceux dont donc dire dit ete leurs pris peut sait savoir
""".split())
MOTS_PARTAGES_MINIMUM = 2


def mots_rares(texte):
    """Les mots distinctifs d'un texte : sans accents, longs, hors banalites."""
    if not isinstance(texte, str):
        return set()
    plat = texte.lower()
    for a, b in (("àâä", "a"), ("éèêë", "e"), ("îï", "i"), ("ôö", "o"),
                 ("ùûü", "u"), ("ç", "c")):
        for lettre in a:
            plat = plat.replace(lettre, b)
    mot, mots = [], set()
    for car in plat:
        if car.isalnum():
            mot.append(car)
            continue
        if mot:
            mots.add("".join(mot))
            mot = []
    if mot:
        mots.add("".join(mot))
    return {m for m in mots if len(m) >= 5 and m not in MOTS_COMMUNS}


def se_recoupent(texte, autre, minimum=MOTS_PARTAGES_MINIMUM):
    """Deux textes parlent-ils vraisemblablement de la meme chose ?"""
    return len(mots_rares(texte) & mots_rares(autre)) >= minimum


def croyances_de(tete):
    return [c for c in (tete.get("croyances") or []) if isinstance(c, str)]


_QUARTIER = {"gens": None}


def _dans_le_quartier():
    """Les ids que le joueur peut atteindre a pied, calcules une fois par run.

    Faute de topologie lisible (fichier absent, aucun siege occupe resolu), on
    rend None et `echelle_de` retombe sur « quartier » pour tout le monde : mieux
    vaut simuler trop que geler le monde entier sur une erreur de lecture.
    """
    if _QUARTIER["gens"] is None:
        try:
            from temps.expose import presence
            _QUARTIER["gens"] = set(presence.quartier().get("dedans") or {})
        except Exception:
            _QUARTIER["gens"] = set()
    return _QUARTIER["gens"] or None


def echelle_de(tete):
    """Ou se tient cette tete par rapport au joueur — mesure, jamais declaree.

    Remplace le champ `echelle` de `intentions.json`, qu'on posait a la main et
    qu'on oubliait de rabaisser quand quelqu'un s'eloignait.
    """
    dedans = _dans_le_quartier()
    if dedans is None:
        return "quartier"
    return "quartier" if tete.get("personnage_id") in dedans else "au loin"


def etapes_de(tete):
    """Les etapes de plan au format objet ; les chaines sont ignorees ici."""
    return [e for e in (tete.get("plan") or []) if isinstance(e, dict)]
