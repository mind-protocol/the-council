# -*- coding: utf-8 -*-
"""GRAPHE — le plan dans le bon sens : amonts, atteignabilite, cercles,
et la chaine qui empeche une piece (--pourquoi).

LE ET / OU NE SE SAISIT PAS, IL SE LIT SUR LE GENRE (structurel) :
  * un VERROU bloque, un ETAT qui en sert un autre le precede
      -> conjonctif : il les faut TOUS
  * une CLEF est un mecanisme pour lever un verrou, une ACTION realise une clef
      -> disjonctif : il en suffit D'UNE
"""
import os
import sys

from plan.expose import nu, sans_emoji, NOM_GENRE  # noqa: F401
from plan.criticite.page import LARGEUR, cale  # noqa: F401

# Trois etages de plus qu'a la racine : scripts/plan/criticite/.
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

POIDS = os.path.join(RACINE, "etat", "poids-etats.json")

# Qui exige tout le monde, qui se contente d'un seul.
CONJONCTIF = ("verrou", "etat")
DISJONCTIF = ("clef", "action")


# ─────────────────────────────────────────────── le graphe, dans le bon sens
def amonts(pieces, mode_dep="interne", actions_ou=False):
    """Pour chaque piece, ce dont elle depend — separe en « tous » et « un seul ».

    Les aretes `vers` montent (une action designe sa clef) ; on les retourne.
    Le genre de la SOURCE tranche le mode, jamais celui de la cible : un etat
    qui porte deux verrous et une action en raccourci exige ses deux verrous, et
    l'action ne coute rien de plus."""
    disj = DISJONCTIF if actions_ou else ("clef",)
    tous, un = {n: [] for n in pieces}, {n: [] for n in pieces}
    dehors = {n: [] for n in pieces}
    for n, p in pieces.items():
        for v in p["vers"]:
            if v not in pieces:
                continue
            (un if p["genre"] in disj else tous)[v].append(n)
        for d in p["dep"]:
            if d not in pieces or d == n:
                continue
            # UN « DEPEND DE » QUI TRAVERSE N'EST PAS UN PREREQUIS, C'EST UN
            # SIGNAL — et les confondre coutait la moitie du plan. Mesure : 427
            # dependances internes, 73 qui traversent. Ces 73 suffisaient a
            # nouer QUATRE-VINGT-DIX pieces de dix-neuf cahiers en une seule
            # grappe circulaire, et a rendre 64 etats cibles sur 139
            # inatteignables — parce qu'une dependance entre affaires rend
            # dependante toute l'affaire, de proche en proche, jusqu'a boucler.
            #
            # Ce n'est pas ce que la colonne veut dire. A l'interieur d'un
            # cahier, « depend de » ordonne un travail : on ne charge pas avant
            # d'avoir affrete. D'un cahier a l'autre, il dit « l'autre nous doit
            # ca » — une coordination, pas une horloge. `couverture.py` en tire
            # deja le bloc « ⛓️ ce qui pend » : c'est son vrai usage.
            #
            # Requalifie, donc : dedans il bloque, dehors il se COMPTE. Ce qui
            # traverse ressort en colonne `on l'attend` — le poids de ce qui,
            # ailleurs, se casse la figure sans cette piece.
            if pieces[d]["affaire"] == p["affaire"] or mode_dep == "toutes":
                if mode_dep != "aucune":
                    tous[n].append(d)
            else:
                dehors[d].append(n)
    return tous, un, dehors


def atteignables(pieces, tous, un, retire=None, optimiste=True):
    """Le plus petit point fixe : qui peut etre obtenu, en partant de rien.

    On itere au lieu de descendre en recursion, parce que le graphe porte des
    cycles de dependance (221 attend 222 qui attend 221) et qu'une recursion y
    repond selon l'ordre de visite. Un point fixe croissant, lui, tranche
    toujours pareil : ce qui est circulaire n'est pas atteignable, et c'est la
    bonne reponse.

    optimiste : un verrou dont aucune clef n'est ecrite se leve quand meme. Ce
    n'est pas de la complaisance — 63 verrous sur 288 n'ont pas de clef, et en
    mode strict ils rendent la moitie du plan inatteignable, ce qui met tous les
    scores a zero et ne dit plus rien. Le mode strict existe pour compter ces
    trous, pas pour classer."""
    ok = {n: False for n in pieces}
    if retire is not None:
        pieces_actives = lambda n: n != retire  # noqa: E731
    else:
        pieces_actives = lambda n: True  # noqa: E731
    change = True
    while change:
        change = False
        for n in pieces:
            if ok[n] or not pieces_actives(n):
                continue
            # ON NE FILTRE PAS LE RETIRÉ DE SES LISTES — on le laisse a `False`.
            # L'en retirer, c'est le rendre inutile au lieu de le rendre
            # manquant : une exigence conjonctive disparaissait alors du ET, et
            # « Nommer l'executant de ce cahier » sortait substituable.
            if not all(ok[s] for s in tous[n]):
                continue
            if un[n]:
                # UN MOYEN ECRIT PUIS RETIRE N'EST PAS UN MOYEN JAMAIS ECRIT, et
                # les confondre vidait la mesure de tout son sens : l'optimisme
                # rattrapait le retrait de la derniere clef d'un verrou, donc
                # aucun retrait ne coutait plus rien — quatre goulots sur
                # huit cent quatre-vingt-neuf pas, ce qui aurait du alerter.
                if not any(ok[s] for s in un[n]):
                    continue
            elif not optimiste and pieces[n]["genre"] in ("verrou", "clef"):
                # rien n'a jamais ete ecrit pour l'ouvrir
                continue
            ok[n] = True
            change = True
    return ok


def cercles(pieces, tous, un):
    """Les composantes fortement connexes du graphe de prerequis, taille > 1.

    CE N'EST PAS UN SOUS-PRODUIT, C'EST LA TROUVAILLE. Une action qui depend du
    verrou qu'elle est censee lever ne se levera jamais, et rien dans les six
    detecteurs de `couverture.py` ne le voit : chaque ligne, prise seule, est
    bien formee. Ca ne se voit qu'en essayant d'ATTEINDRE quelque chose — le
    point fixe s'arrete, et l'on cherche pourquoi. C'est aussi pourquoi le
    script imprime les cercles AVANT le classement : tant qu'un cercle tient,
    tout ce qui pend derriere est a zero, et le classement ment par omission.

    Tarjan, en iteratif : le graphe porte des chaines de plus de mille pieces et
    la recursion Python casse a mille."""
    graphe = {n: list(tous[n]) + list(un[n]) for n in pieces}
    index, bas, sur, pile, out = {}, {}, set(), [], []
    compteur = [0]
    for depart in pieces:
        if depart in index:
            continue
        travaux = [(depart, iter(graphe[depart]))]
        index[depart] = bas[depart] = compteur[0]
        compteur[0] += 1
        pile.append(depart)
        sur.add(depart)
        while travaux:
            n, it = travaux[-1]
            avance = False
            for s in it:
                if s not in index:
                    index[s] = bas[s] = compteur[0]
                    compteur[0] += 1
                    pile.append(s)
                    sur.add(s)
                    travaux.append((s, iter(graphe[s])))
                    avance = True
                    break
                if s in sur:
                    bas[n] = min(bas[n], index[s])
            if avance:
                continue
            travaux.pop()
            if travaux:
                bas[travaux[-1][0]] = min(bas[travaux[-1][0]], bas[n])
            if bas[n] == index[n]:
                grappe = []
                while True:
                    m = pile.pop()
                    sur.discard(m)
                    grappe.append(m)
                    if m == n:
                        break
                if len(grappe) > 1:
                    out.append(sorted(grappe))
    return sorted(out, key=lambda g: (-len(g), g[0]))


def pourquoi(n, pieces, tous, un, ok, prof=0, chemin=None):
    """La chaine qui empeche une piece d'etre atteignable, jusqu'a la boucle."""
    chemin = chemin or []
    p = pieces.get(n)
    if not p:
        return
    boucle = n in chemin
    sys.stdout.write(u"  %s%s %s %s%s\n" % (
        u"  " * prof, u"✅" if ok.get(n) else u"🚫",
        NOM_GENRE.get(p["genre"], u"") + u" " + n, cale(p["nom"], 58),
        u"  ↩ LA BOUCLE SE REFERME ICI" if boucle else u""))
    if ok.get(n) or boucle or prof > 6:
        return
    for s in tous[n]:
        if not ok.get(s):
            pourquoi(s, pieces, tous, un, ok, prof + 1, chemin + [n])
    if un[n] and not any(ok.get(s) for s in un[n]):
        for s in un[n]:
            pourquoi(s, pieces, tous, un, ok, prof + 1, chemin + [n])

