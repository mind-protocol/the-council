# -*- coding: utf-8 -*-
"""CALCUL — le score contrefactuel (calculer, raison_du_zero), et la
charge servie a qui depeche un homme (charge_de).
"""
import sys

import plan_modele as PM

from plan.expose import nu
from plan.criticite.page import faite
from plan.criticite.graphe import (CONJONCTIF, DISJONCTIF, amonts,
                                   atteignables, cercles)
from plan.criticite.note import masse, amplitude, poids_des_etats, portee
from plan.criticite.hommes import (charge_des_hommes, gens, porte_des_hommes,
                                   _id)

def _pertes(pieces, tous, un, base, poids, optimiste):
    """Le contrefactuel seul, sans portée ni mise en forme : c'est la passe
    qu'on refait à notes égales pour mesurer l'amplitude du graphe."""
    m0 = masse(base, poids)
    out = []
    for n, p in sorted(pieces.items()):
        if p["genre"] not in ("action", "clef", "verrou"):
            continue
        sans = atteignables(pieces, tous, un, retire=n, optimiste=optimiste)
        out.append((m0 - masse(sans, poids), 0, n, p))
    return out


# ─────────────────────────────────────────────── le calcul
# ────────────────────────────── pourquoi un pas vaut zéro
#
# UN ZERO N'EST PAS UN FAIT, C'EST QUATRE FAITS QU'ON A CONFONDUS. La colonne ne
# disait qu'une chose — « n'ajoute aucune perte mesurable » — et l'écran la
# lisait « ne pèse rien », ce qui n'est pas la même phrase. Sur le plan de la
# reine au 24 août : 53 pas portés, 76 accomplis, 0 redondants, 10 sans portée
# et 1283 à l'amont bloqué — c'est-à-dire quatre-vingt-quinze pour cent du plan
# rangés sous le même zéro que « c'est déjà fait ».
#
# LES DEUX DERNIERS NE SE CONFONDENT PAS NON PLUS, et c'est pourquoi il y en a
# deux et non un « hors-portée » :
#   sans-portee   — le pas ne sert AUCUN état cible. Une pièce écrite qui ne
#                   mène nulle part : un défaut de saisie du cahier.
#   amont-bloque  — le pas sert des états, et aucun n'est atteignable. Ce n'est
#                   pas une branche sans importance : c'est le signe qu'en amont
#                   quelque chose ne se dérive pas — un cycle, une exigence
#                   jamais satisfaite. Un seul arc en trop en produit un
#                   millier, et le zéro le taisait.
GENRES_MESURES = ("action", "clef", "verrou")


def raison_du_zero(p, c, pt_atteignable, portee_brute, attendu=0):
    """Pourquoi ce pas ne pèse rien — ou qu'il pèse, et alors c'est `porte`.

    Une seule règle de lecture : `porte` est le seul cas où le chiffre veut
    dire quelque chose. Les quatre autres disent pourquoi il n'en veut pas, et
    ils ne se remplacent pas les uns les autres."""
    if (c or 0) + (attendu or 0) > 0:
        return u"porte"
    if faite(p):
        return u"accompli"
    if not portee_brute:
        return u"sans-portee"
    if not pt_atteignable:
        return u"amont-bloque"
    return u"redondant"


def calculer(pieces, mode_dep="interne", optimiste=True, actions_ou=False):
    tous, un, dehors = amonts(pieces, mode_dep, actions_ou)
    # L'AMPLITUDE SE MESURE AVANT DE POUVOIR S'APPLIQUER — d'où deux passes, et
    # elles ne sont pas gratuites : on calcule le plan une première fois à notes
    # égales, uniquement pour savoir de combien le graphe étire déjà les
    # cahiers, puis on refait tout avec l'échelle calée dessus. Le raccourci
    # aurait été de figer un facteur au jugé ; il aurait vieilli au premier
    # cahier ouvert.
    poids, saisis = poids_des_etats(pieces)
    base = atteignables(pieces, tous, un, optimiste=optimiste)
    if saisis:
        premieres = _pertes(pieces, tous, un, base,
                            {n: 1.0 for n in poids}, optimiste)
        poids, saisis = poids_des_etats(pieces, amplitude(pieces, premieres))
    m0 = masse(base, poids)

    cache = {}
    lignes = []
    for n, p in sorted(pieces.items()):
        # UN VERROU SE MESURE AUSSI, et le laisser dehors etait une faute de
        # vocabulaire prise pour une regle. « On ne rate pas un verrou » est
        # vrai : on ne le fait pas, on le LEVE. Mais le contrefactuel se pose
        # exactement pareil — s'il ne se leve pas, qu'est-ce qui devient
        # inatteignable ? — et l'arithmetique est la meme au signe pres du
        # recit. Sans lui, le registre des verrous etait le seul des quatre a
        # n'afficher aucun chiffre, alors que c'est LA table ou l'on vient
        # demander « lequel de ces empechements coute le plus cher ».
        #
        # La colonne se lit donc autrement selon le genre, et c'est dit dans
        # l'aide : pour une action ou une clef, « si ce pas rate » ; pour un
        # verrou, « tant qu'il tient ».
        if p["genre"] not in ("action", "clef", "verrou"):
            continue          # un etat cible n'est pas un moyen : il a son poids
        pt = portee(n, pieces, poids, cache)
        pt_atteignable = sum(poids[e] for e in pt if base.get(e))
        if not pt_atteignable:
            lignes.append((0.0, pt_atteignable, n, p))
            continue
        sans = atteignables(pieces, tous, un, retire=n, optimiste=optimiste)
        lignes.append((m0 - masse(sans, poids), pt_atteignable, n, p))
    return lignes, base, poids, saisis, m0, dehors


# ───────────────────────────── ce qu'un homme porte, servi à qui le dépêche
#
# LA MESURE EXISTE DEPUIS `--charge` ; CE QUI MANQUAIT, C'EST UNE PORTE. Compter
# ce qu'un homme ne voit pas et ne pas le lui donner, c'est tenir un registre de
# ce qu'on ne fait pas. `depecher.py` appelle donc ceci, et n'a AUCUNE seconde
# definition de « sa charge ailleurs » — deux definitions divergeraient au
# premier repli de nom qu'on ajoute d'un cote.
#
# ON NE FILTRE PAS L'ETAT ICI. Un pas deja fait ne tire plus rien, mais la
# colonne `--charge` mesure comment un homme PESE sur le plan, pas ce qui lui
# reste a faire : y retirer les pas faits changerait les chiffres du tableau
# « Mon gouvernement » pour une raison qui n'est pas la sienne. Le tri est au
# demandeur, et c'est `depecher.py` qui l'applique — sa reserve, elle, ne parle
# que de ce qui reste.
def charge_de(qui, vue_de=None):
    """(vu, sien_ailleurs, tire) pour un homme — chacun une liste (score, n°,
    pièce), le plus lourd en tête. Listes vides si le nom n'est connu d'aucun
    des trois registres."""
    modele = PM.charger(vue_de or qui)
    livres, pieces, affaires = (modele["livres"], modele["pieces"],
                                modele["affaires"])
    lignes, base, poids, saisis, m0, dehors = calculer(pieces)
    crit = {n: c for c, pt, n, p in lignes}
    attendu = {n: sum(crit.get(m, 0) for m in ms) for n, ms in dehors.items() if ms}
    offices, moyens = gens(livres)
    hommes = charge_des_hommes(pieces, affaires, lignes, attendu, offices, moyens)
    # Le repli des noms est celui de `rapprocher()` : on cherche la clef exacte,
    # puis celle dont le nom donné est le préfixe — « corlys » pour
    # « corlys-velaryon ». Jamais une inclusion au milieu du mot.
    h = hommes.get(_id(qui)) or next(
        (v for k, v in hommes.items() if k.startswith(_id(qui) + u"-")), None)
    if not h:
        return [], [], []
    return h["vu"], h["sien_ailleurs"], h["tire"]

