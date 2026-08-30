# -*- coding: utf-8 -*-
# CRITICITE — ce qu'on perd si ce pas-la rate.
#
# POURQUOI PAS « CE QUE CA DEBLOQUE ». La mesure naturelle est la portee : la
# masse d'etats cibles qu'un pas sert en aval. Elle repond « c'est gros
# derriere », ce qui n'est pas la question du matin. Trois actions qui
# realisent la meme clef ont chacune une portee enorme et ne valent rien
# separement : on peut en perdre deux. La question du matin est CONTREFACTUELLE
# — combien de poids d'etats cesse d'etre atteignable si ce pas-la n'arrive
# pas ? Un pas substituable tombe alors a zero, tout seul, sans qu'on ait a
# diviser par le nombre de freres. Les deux nombres sont imprimes cote a cote :
# l'ecart entre eux EST la redondance.
#
# LE ET / OU NE SE SAISIT PAS, IL SE LIT SUR LE GENRE. C'est la seule chose que
# ce script suppose, et elle est structurelle :
#   * un VERROU bloque, un ETAT qui en sert un autre le precede
#       -> conjonctif : il les faut TOUS
#   * une CLEF est un mecanisme pour lever un verrou, une ACTION realise une clef
#       -> disjonctif : il en suffit D'UNE
# Aucune colonne a creer. Si un jour une clef exige toutes ses actions, c'est la
# seule exception qu'il faudra ecrire quelque part — pas les 1316 autres cas.
#
# UN SEUL POIDS SE SAISIT : celui des etats cibles, dans etat/poids-etats.json,
# {"23000": 5}. Absent, tout vaut 1 et le script LE DIT. C'est le seul endroit
# ou un jugement humain sur ce qui compte a sa place ; tout le reste se derive,
# donc ne peut pas mentir plus longtemps que le graphe.
#
# CE QUI N'EST PAS DEDANS, ET POURQUOI. Le prix : la colonne « 💰 Ce qu'elle
# coute et ce qu'elle ferme » est de la prose, sur la CLEF, et l'on ne divise
# pas par de la prose. Elle est imprimee telle quelle sous les premieres lignes.
# L'echeance non plus : deux nombres mous multiplies font une fausse precision.
# `etat_du_plan.py --du` tient les dates ; on lit les deux colonnes et l'oeil
# tranche.
#
# Usage :
#     python scripts/criticite.py                  le classement, tous genres
#     python scripts/criticite.py --combien 30
#     python scripts/criticite.py --affaire "Prise de Port-Real"
#     python scripts/criticite.py --restant        sans ce qui est deja fait
#     python scripts/criticite.py --strict         un verrou sans clef bloque
#     python scripts/criticite.py --sans-dep       ignorer « ⛓️ Depend de »
#     python scripts/criticite.py --etats          le poids par etat cible
#     python scripts/criticite.py --acteurs        ce que chaque homme porte
#     python scripts/criticite.py --charge         ce qu il voit / ne voit pas
#     python scripts/criticite.py --charge gerardys
#     python scripts/criticite.py --decisions      l arbre des fourches
#     python scripts/criticite.py --decisions 43011
#     python scripts/criticite.py --pourquoi 8201  la chaine qui empeche une piece
import argparse
import io

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import rapporteurs
import re
import unicodedata
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from plan.expose import nu, sans_emoji, NOM_GENRE  # noqa: E402
from plan.expose import FINI, premier_mot  # noqa: E402
import plan_modele as PM  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

POIDS = os.path.join(RACINE, "etat", "poids-etats.json")
LARGEUR = 100

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


# ─────────────────────────────────────────────── ce que chaque homme porte
def gens(livres):
    """{O##: (office, titulaire)} et {M##: (moyen, qui le tient)}.

    LE NOM SE COUPE A LA PREMIERE VIRGULE, et c'est une approximation assumee :
    « Ser Robert Quince, onze ans en charge » et « Dame Aurore Inchauspe, de La
    Noiseraie » portent leur glose dans la meme cellule. Le point-virgule separe
    deux hommes (« Tobb, de la Claie ; Nesse, du Marais du sud ») — les deux
    comptent, et chacun porte alors la charge entiere de l'office : on ne
    partage pas une charge en deux parce que deux hommes la tiennent."""
    from plan.expose import MO as _MO, registre_de as _ns
    offices, moyens = {}, {}
    for b in livres:
        # LE CASIER M/O, COMME DANS `charger()` — et l'oublier ici a coûté un
        # castellan. La Nera et le grand plan tiennent chacun leur registre sans
        # s'etre concertes : O01 vaut « Castellan de Peyredragon » d'un cote et
        # « Le chantier » de l'autre. Sans prefixe, le dernier livre lu ecrasait
        # l'autre — les vingt-cinq pas de ser Robert Quince etaient attribues a
        # Hann Bourbe, et le castellan ne figurait NULLE PART au tableau des
        # hommes. `couverture.py` a reparé exactement cette faute pour son
        # inventaire (l. 74-92) ; elle n'avait pas ete reportee ici.
        ns = _ns(b.get("id"))
        i = None
        for t in [b] + list(b.get("tables") or []):
            cols = t.get("colonnes") or []
            if not cols:
                continue
            from plan.expose import col as _col
            i_t = _col(cols, u"titulaire")
            i_q = _col(cols, u"qui le tient")
            if i_t is None and i_q is None:
                continue
            cible, i = (offices, i_t) if i_t is not None else (moyens, i_q)
            for l in (t.get("lignes") or []):
                c = [nu(x) for x in ((l if isinstance(l, list) else l.get("cellules")) or [])]
                if len(c) <= max(1, i):
                    continue
                m = _MO.search(c[0])
                if not m:
                    continue
                qui = [x.split(u",")[0].strip() for x in c[i].split(u";") if x.strip()]
                cible[ns + m.group(1)] = (c[1], [q for q in qui if q and q != u"—"])
    return offices, moyens


TITRES = re.compile(u"^(ser|dame|lord|lady|le prince|la princesse|mestre|maitre|maître"
                    u"|septon|celui qu'on appelle) ", re.I)
MOI = re.compile(u"^(moi|moi seule|moi-même|moi meme)$", re.I)
# LA GLOSE AU TIRET CADRATIN COUPE UN HOMME EN DEUX. « SER STEFFON DARKLYN —
# DÉMIS PAR SA PROPRE BORNE » (O16) et « Ser Steffon Darklyn » (O12) faisaient
# deux porteurs, sur le premier goulot de la maison : sa charge se lisait en deux
# moities dont aucune n'etait la sienne. On coupe donc au tiret comme a la
# virgule — c'est la meme chose, une glose derriere le nom.
GLOSE = re.compile(u"\\s+[—–]\\s+.*$")
# UNE CASE VACANTE N'EST PAS UN HOMME. Les registres disent le vide en prose
# (« CASE BLANCHE », « VIDE. Ligne ouverte le 27e », « un trou ne se voit pas »),
# et cette prose se rangeait au classement des porteurs comme un titulaire.
VACANT = re.compile(u"^(vide|case blanche|néant|neant|à désigner|a designer|vacant"
                    u"|personne|personne encore|un trou|une case)\\b", re.I)
# « Elle-même », « Lui », « Eux-mêmes » : le moyen qui se tient tout seul. Ce
# n'est pas un porteur de plus, c'est l'absence de tiers.
SOI = re.compile(u"^(lui|elle|lui-même|elle-même|eux-mêmes|elles-mêmes"
                 u"|lui meme|elle meme|eux memes)$", re.I)


def cle_homme(nom):
    """DEUX REGISTRES, DEUX ORTHOGRAPHES DU MEME HOMME. Les offices ecrivent
    « Dame Aurore Inchauspe », les moyens « Aurore Inchauspe » : sans cette
    normalisation, elle porte 30 de criticite dans une colonne et 21 dans
    l'autre sans que les deux se rejoignent — et l'on conclut qu'on ne lui tire
    rien, alors qu'elle est le second goulot de la maison.

    « Moi » est la reine : les moyens sont ecrits de sa main, a la premiere
    personne. C'est une jointure devinee, et elle est dite en clair sous la
    table plutot que cachee dans un dictionnaire."""
    t = u" ".join(nu(nom).split())
    if MOI.match(t):
        return u"la reine"
    if SOI.match(t):
        return u"— lui-même —"
    if VACANT.match(t):
        return u"— personne, la case est vide —"
    t = TITRES.sub(u"", GLOSE.sub(u"", t)).strip()
    return t.lower()


# ─────────────────────────────────────────────── les idées, et leur prix
#
# CE QUE ÇA RÉPARE. `missions_de()` sait déjà proposer, par affaire, ce qu'il
# faudrait écrire pour que la chaîne tienne — « afin d'atteindre X, faire Y
# aurait effet Z ». Il les range par `force()`, un barème à la main (0, 1, 1+N,
# 20, 20+N, 60) qui mélange deux axes et ne sait rien du plan hors du cahier
# qu'il regarde. Résultat : trente-six listes d'une dizaine d'idées chacune, et
# aucun moyen de savoir laquelle des trois cent cinquante ouvre le plus.
#
# Ici on ne réécrit pas les détecteurs — une seconde définition du trou, et les
# deux divergeraient. On prend les idées telles qu'elles sortent, et l'on colle
# à chacune la CRITICITÉ DE LA PIÈCE QU'ELLE VISE. Une idée ne vaut pas par la
# gravité de son défaut : elle vaut par ce que la pièce qu'elle débloque tient.
#
# LE NUMÉRO SE LIT SUR LA CLEF DE L'ACTE, qui l'y a déjà mis (`clef/28017`,
# `office/220`, `genre/44001/23000`). C'est laid et c'est juste : cette clef est
# la seule chose que `missions_de` promet de garder stable, et la reconstruire
# en rapprochant des libellés serait inventer un appariement là où il y a une
# adresse.
CHIFFRES = re.compile(r"\d{3,6}")


def idees(pieces, crit, poids, base):
    from plan.expose import missions_de, phrase   # noqa: E402
    out = []
    for aff in sorted({p["affaire"] for p in pieces.values() if p["affaire"]}):
        for m in missions_de(aff, pieces):
            ns = CHIFFRES.findall(m.get("acte") or u"")
            # LA PREMIÈRE EST CELLE QU'ON VISE. « genre/44001/23000 » parle de la
            # colonne de 44001, pas de 23000 qu'elle désigne à tort ; et
            # « retrouver/21020 » vise une pièce qui n'existe pas — score nul,
            # ce qui est la vérité : on ne peut pas chiffrer ce qui manque.
            n = ns[0] if ns else None
            c = crit.get(n) or {}
            score = c.get("perte", 0) + c.get("attendu", 0)
            if not c and n in poids:
                # un état cible n'a pas de perte : il a son poids, et le fait
                # qu'on puisse l'atteindre ou non
                score = poids[n] if not base.get(n) else 0
            out.append({
                "acte": m.get("acte"), "affaire": aff, "nature": m.get("nature", "pas"),
                "texte": phrase(m), "piece": n,
                "genre": (pieces.get(n) or {}).get("genre") if n else None,
                "perte": c.get("perte", 0), "attendu": c.get("attendu", 0),
                "score": score,
            })
    out.sort(key=lambda x: (-x["score"], x["acte"] or u""))
    return out


# ─────────────────────────────────────────── ce qu'un homme NE VOIT PAS
#
# LE ROUTAGE DU PLAN TIENT SUR UN SEUL CHAMP, `tenu_par`, ecrit en tete du
# cahier. Un homme depeche recoit les trous DE SES CAHIERS, et rien d'autre.
# C'est propre, et c'est trop etroit : une action dont il repond par son office
# — c'est ecrit noir sur blanc dans la colonne `🪶 Office` de la ligne — ne lui
# parvient jamais si le cahier appartient a un autre. Personne ne la lui cache :
# simplement, aucun chemin ne la lui porte.
#
# CE SCRIPT NE CHANGE RIEN, IL COMPTE. Avant d'ouvrir la reserve d'un homme aux
# affaires qu'il ne tient pas — ce qui redefinit ce qu'est un cahier —, on
# regarde ce que ca representerait. Trois colonnes, et la troisieme est la
# question : ce qu'il voit, ce qui tombe sur son office ailleurs, et ce qui tire
# sur un moyen qu'il tient sans que son nom soit sur la ligne.
#
# LA JOINTURE ENTRE `tenu_par` ET LE REGISTRE DES OFFICES EST DEVINEE, et elle
# est dite : l'un ecrit des identifiants (`aurore-inchauspe`), l'autre des noms
# avec leurs titres (`Dame Aurore Inchauspe`). On normalise des deux cotes et
# l'on IMPRIME les titulaires qu'on n'a pas su rattacher, plutot que de les
# perdre en silence.
def _id(s):
    t = unicodedata.normalize("NFD", cle_homme(s))
    t = u"".join(c for c in t if unicodedata.category(c) != "Mn")
    return u"-".join(re.sub(u"[^a-z0-9]+", u" ", t.lower()).split())


def rapprocher(ids):
    """UN PRENOM SEUL EST LE MEME HOMME QU'UN PRENOM SUIVI D'UN NOM. Les cahiers
    ecrivent `tenu_par: "jacaerys"`, le registre des offices « Le prince Jacaerys
    Velaryon » : deux clefs, deux hommes, et le prince ressortait a 100 %
    d'aveugle alors qu'il tient DEUX cahiers. C'est la faute la plus couteuse de
    ce tableau, parce qu'elle fabrique exactement le symptome qu'on cherche.

    On replie donc le plus court sur le plus long quand l'un prefixe l'autre, et
    JAMAIS autrement : « nesse » et « nesse-du-marais » sont le meme homme, « rulf
    corne » et « rulf-le-jeune » ne le sont pas. Une inclusion au milieu du mot
    marierait des inconnus."""
    canon = {}
    longs = sorted(ids, key=len, reverse=True)
    for i in ids:
        canon[i] = next((L for L in longs
                         if L == i or L.startswith(i + u"-")), i)
    return canon


def porte_des_hommes(lignes, offices, moyens):
    """Par homme : la criticite des pas dont SON office repond, et celle des pas
    qui tirent sur un moyen qu'il tient. C'est la mesure de la table
    `--acteurs`, et il n'y en a qu'une : la table l'imprime, le JSON la sert,
    l'ecran fait varier ses ronds dessus.

    DEUX FACONS DE PESER SUR LE PLAN, ET IL FAUT LES DEUX. Un homme porte ce
    qu'on lui a confie (son office est ecrit sur l'action) ; il TIENT aussi des
    choses dont d'autres ont besoin (son nom est dans « qui le tient » d'un
    moyen que l'action engage). Le second est invisible aux tableaux de charge —
    et c'est par la qu'on est bloque par quelqu'un qui ne sait meme pas qu'on
    l'attend.

    LA CLEF EST CELLE DE `charge_des_hommes` — un slug replie par
    `rapprocher()` —, et non le nom nu d'autrefois. Un chiffre que l'ecran ne
    sait pas poser sur un visage ne sert a personne, et les deux tableaux du
    meme script ne peuvent pas nommer le meme homme de deux facons.

    Retourne (hommes, sans_office, office_en_clair)."""
    bruts = ({_id(q) for o, (nom, qui) in offices.items() for q in qui}
             | {_id(q) for m, (nom, qui) in moyens.items() for q in qui})
    canon = rapprocher(bruts)
    out, sans, en_clair = {}, [0.0, 0], [0.0, 0]

    def chez(q0):
        i = _id(q0)
        h = out.setdefault(canon.get(i, i),
                           {"nom": u"", "offices": set(), "moyens": set(),
                            "porte": 0.0, "pas": 0, "goulots": 0,
                            "tire": 0.0, "tire_pas": 0})
        # LE PLUS LONG N'EST PAS LE PLUS CLAIR. « Lord Corlys Velaryon —
        # PROPOSE le 27e a neuf heures » est un nom plus une nouvelle ; au
        # classement des hommes, on veut le nom.
        h["nom"] = affiche(cle_homme(q0), q0, h["nom"])
        return h

    for c, pt, n, p in lignes:
        o = p.get("office")
        if o in offices:
            for q0 in (offices[o][1] or [u"— titulaire non écrit —"]):
                h = chez(q0)
                h["porte"] += c
                h["pas"] += 1
                h["goulots"] += 1 if c > 0 else 0
                h["offices"].add(o)
        elif o == u"SANS OFFICE":
            sans[0] += c
            sans[1] += 1
        elif o:
            en_clair[0] += c
            en_clair[1] += 1
        for m in p.get("moyens") or []:
            for q0 in (moyens.get(m) or (u"", []))[1]:
                h = chez(q0)
                h["tire"] += c
                h["tire_pas"] += 1
                h["moyens"].add(m)

    for h in out.values():
        h["offices"] = sorted(h["offices"])
        h["moyens"] = sorted(h["moyens"])
        h["porte"] = round(h["porte"], 3)
        h["tire"] = round(h["tire"], 3)
    return out, sans, en_clair


def charge_des_hommes(pieces, affaires, lignes, attendu, offices, moyens):
    """Par homme : ce qu'il voit, ce qu'il porte sans le voir, ce qu'on lui tire."""
    tenu = {nu(b.get("titre")): (b.get("tenu_par") or u"") for b in affaires}
    score = {n: c + attendu.get(n, 0) for c, pt, n, p in lignes}
    # On rassemble d'abord TOUS les noms des trois sources, puis on les replie :
    # sans ce passage, la meme personne existe une fois par registre.
    bruts = ({_id(q) for o, (nom, qui) in offices.items() for q in qui}
             | {_id(q) for m, (nom, qui) in moyens.items() for q in qui}
             | {_id(v) for v in tenu.values() if v})
    canon = rapprocher(bruts)
    par_off = {}
    for o, (nom, qui) in offices.items():
        for q in qui:
            par_off.setdefault(canon[_id(q)], set()).add(o)
    par_moyen = {}
    for m, (nom, qui) in moyens.items():
        for q in qui:
            par_moyen.setdefault(canon[_id(q)], set()).add(m)

    hommes = {}
    for q in set(list(par_off) + list(par_moyen) + [canon[_id(v)] for v in tenu.values() if v]):
        hommes[q] = {"qui": q, "offices": sorted(par_off.get(q, [])),
                     "moyens": sorted(par_moyen.get(q, [])),
                     "cahiers": sorted({a for a, t in tenu.items()
                                        if t and canon[_id(t)] == q}),
                     "vu": [], "sien_ailleurs": [], "tire": []}

    for c, pt, n, p in lignes:
        s = score.get(n, 0)
        if not s:
            continue
        chez = canon.get(_id(tenu.get(p["affaire"], u"")), u"")
        porteur = None
        for q, os_ in par_off.items():
            if p.get("office") in os_:
                porteur = q
                break
        if chez and chez in hommes:
            hommes[chez]["vu"].append((s, n, p))
        if porteur and porteur in hommes and porteur != chez:
            hommes[porteur]["sien_ailleurs"].append((s, n, p))
        for m in (p.get("moyens") or []):
            for q, ms in par_moyen.items():
                if m in ms and q in hommes and q != chez and q != porteur:
                    hommes[q]["tire"].append((s, n, p))
                    break
    for h in hommes.values():
        for k in ("vu", "sien_ailleurs", "tire"):
            h[k].sort(key=lambda x: (-x[0], x[1]))
    return hommes


def section_charge(hommes, combien, qui=None):
    somme = lambda L: sum(x[0] for x in L)          # noqa: E731
    if not qui:
        titre(u"🪶 CE QU'UN HOMME VOIT, ET CE QU'IL NE VOIT PAS")
        sys.stdout.write(
            u"  « vu » = les cahiers dont il est `tenu_par` — la seule chose qui lui parvienne\n"
            u"  aujourd'hui. « sien ailleurs » = des pas dont SON office répond, dans le cahier\n"
            u"  d'un autre. « on lui tire » = des pas qui engagent un moyen qu'il tient.\n\n")
        sys.stdout.write(u"  %s%s%s%s%s\n" % (
            cale(u"vu", 7), cale(u"sien", 7), cale(u"tiré", 7),
            cale(u"aveugle", 9), u"l'homme"))
        for h in sorted(hommes.values(), key=lambda x: -(somme(x["sien_ailleurs"])
                                                         + somme(x["tire"]))):
            v, s, t = somme(h["vu"]), somme(h["sien_ailleurs"]), somme(h["tire"])
            if not (v or s or t):
                continue
            # LE CHIFFRE QUI DECIDE : la part de ce qui le concerne qu'aucun
            # chemin ne lui porte. Un homme a 100 % d'aveugle est un homme dont
            # le plan attend quelque chose sans avoir aucun moyen de le lui dire.
            aveugle = (100 * (s + t) / (v + s + t)) if (v + s + t) else 0
            sys.stdout.write(u"  %s%s%s%s%s\n" % (
                cale(u"%g" % v, 7), cale(u"%g" % s, 7), cale(u"%g" % t, 7),
                cale(u"%d %%" % aveugle, 9),
                cale(h["qui"] + u"  · " + u" ".join(h["offices"] + h["moyens"]), 56)))
        return

    h = hommes.get(_id(qui)) or next(
        (v for k, v in hommes.items() if k.startswith(_id(qui) + u"-")), None)
    if not h:
        titre(u"🪶 " + qui)
        sys.stdout.write(u"  Personne de ce nom ne tient d'office, de moyen ni de cahier.\n"
                         u"  Connus : " + u" · ".join(sorted(hommes)) + u"\n")
        return
    titre(u"🪶 " + h["qui"].upper() + u" — " + (u" ".join(h["offices"]) or u"sans office")
          + (u" · moyens " + u" ".join(h["moyens"]) if h["moyens"] else u""))
    sys.stdout.write(u"  %d cahier(s) : %s\n"
                     % (len(h["cahiers"]), u" · ".join(h["cahiers"]) or u"aucun"))
    for k, t in ((u"vu", u"📘 CE QU'IL VOIT DÉJÀ — ses cahiers, ce que la dépêche lui porte"),
                 (u"sien_ailleurs", u"🪶 SA CHARGE AILLEURS — son office répond, "
                                    u"le cahier est à un autre"),
                 (u"tire", u"🪝 CE QU'ON LUI TIRE — un moyen qu'il tient, "
                           u"et son nom n'est pas sur la ligne")):
        L = h[k]
        sys.stdout.write(u"\n  %s  (%g sur %d pas)\n" % (t, somme(L), len(L)))
        for s, n, p in L[:combien]:
            sys.stdout.write(u"    %s%s%s%s\n" % (
                cale(u"%g" % s, 6), cale(NOM_GENRE.get(p["genre"], u"") + u" " + n, 10),
                cale(p["nom"], 46), cale(p["affaire"], 32)))
        if len(L) > combien:
            sys.stdout.write(u"    … et %d autres\n" % (len(L) - combien))


# ─────────────────────────────────────────── le total d'une affaire, et sa veille
#
# LA SEULE CHOSE QUE CE DISPOSITIF AIT LE DROIT D'ECRIRE. Tout le reste se
# recalcule : c'est meme sa regle, et c'est pour ca qu'aucun score ne vit dans
# `books.json`. Le PASSE, lui, ne se recalcule pas. Le plan d'hier n'existe plus
# nulle part une fois `books.json` reecrit, et sans trace on ne peut jamais
# repondre a la seule question qui vaille au conseil du matin : est-ce que ca
# monte ou est-ce que ca descend ?
#
# UNE LIGNE PAR CHANGEMENT, ET NON UNE PAR JOUR. La page demande `/criticite` a
# chaque ouverture de volume ; un instantane par appel remplirait le fichier de
# milliers de lignes IDENTIQUES. C'est ce risque-la, et lui seul, qui avait fait
# poser un garde-fou de vingt heures — un garde-fou de TEMPS contre un mal de
# CONTENU. Il coutait ce qu'il protegeait : un plan remanie trois fois dans la
# journee ne laissait qu'une trace, et l'on ne pouvait plus dire laquelle des
# trois ecritures avait fait bouger le score. On garde donc la ligne quand les
# scores different de la derniere posee, et jamais autrement — un fichier ou
# chaque ligne dit un changement reel n'a pas besoin d'etre rationne.
#
# CE QUE CA NE COUTE PAS. Le calcul, lui, ne tourne pas plus souvent : le
# serveur le cache sur la taille et la date de `books.json` et de
# `poids-etats.json`, donc il retombe deja exactement une fois par ecriture. Et
# une ligne pese deux kilo-octets : cent remaniements dans une journee font deux
# cents kilo-octets, ce qui n'est pas un sujet.
#
# L'ECART NE SE PREND PAS CONTRE LA LIGNE PRECEDENTE, et c'est ce qui rend la
# densite inoffensive : il se prend contre la plus recente ligne d'au moins
# vingt heures — « depuis hier », et non « depuis la derniere fois que quelqu'un
# a touche au plan ». Des lignes plus serrees rendent cette base plus juste, pas
# plus bruyante.
#
# APPEND-ONLY, UNE LIGNE PAR JOUR, JAMAIS DE RELECTURE COMPLETE. C'est un
# `.jsonl` comme le flux : on ajoute a la fin, et l'on ne lit que la queue.
HISTOIRE = os.path.join(RACINE, "etat", "criticite-histoire.jsonl")
HEURES = 20 * 3600


def totaux_par_affaire(lignes, attendu, pieces, affaires):
    """{affaire: {score, pas, goulots, restant, tenu_par}}."""
    tenu = {nu(b.get("titre")): (b.get("tenu_par") or u"") for b in affaires}
    out = {}
    for c, pt, n, p in lignes:
        a = p["affaire"] or u"— sans affaire —"
        o = out.setdefault(a, {"score": 0.0, "pas": 0, "goulots": 0, "restant": 0,
                               "tenu_par": tenu.get(a, u"")})
        o["score"] += c + attendu.get(n, 0)
        o["pas"] += 1
        if c > 0:
            o["goulots"] += 1
        if not faite(p):
            o["restant"] += 1
    for o in out.values():
        o["score"] = round(o["score"], 1)
    return out


def _quand():
    """L'horodatage reel, et pas la date du monde : on compare des MESURES,
    et deux mesures d'un meme jour de jeu peuvent etre separees d'une semaine
    de travail. La date du monde est notee a cote, pour la lecture."""
    import time
    return time.time()


def _regime():
    """L'empreinte du bareme en vigueur : les notes, et rien d'autre. Deux
    mesures prises sous deux baremes ne se soustraient pas — c'est la meme
    raison qui interdit de comparer un compte en muids a un compte en tonneaux."""
    try:
        d = json.load(io.open(POIDS, encoding="utf-8"))
        notes = d.get("notes") if isinstance(d.get("notes"), dict) else d
        cle = json.dumps(notes, sort_keys=True, ensure_ascii=False)
    except Exception:
        cle = u"tout-a-un"
    import hashlib
    return hashlib.sha1(cle.encode("utf-8")).hexdigest()[:8]


def veille(totaux, date_monde):
    """Ajoute `avant` et `ecart` a chaque affaire, et pose l'instantane du jour.

    Ne leve JAMAIS : une trace indisponible ne doit pas empecher un calcul. Le
    tableau sort alors sans ecart, ce qui se voit."""
    maintenant = _quand()
    lu = []
    try:
        if os.path.exists(HISTOIRE):
            with io.open(HISTOIRE, encoding="utf-8") as f:
                for l in f:
                    l = l.strip()
                    if l:
                        try:
                            lu.append(json.loads(l))
                        except ValueError:
                            pass
    except Exception:
        lu = []
    # ON NE COMPARE PAS DEUX MESURES PRISES A DES ECHELLES DIFFERENTES, et c'est
    # la faute que cette trace a failli commettre le premier jour. Ce matin le
    # plan pesait 4417 tous etats a 1 ; ce soir 2008 avec les notes posees sur
    # les objectifs finaux. L'ecart de 2409 n'est PAS du travail : c'est un
    # changement de regle. Affiche en « −2409 depuis hier », il aurait fait
    # croire a un effondrement le jour meme ou l'on venait de recoller le plan.
    #
    # Chaque instantane porte donc l'empreinte de son bareme. Un ecart ne se
    # calcule qu'entre deux lignes de meme empreinte ; sinon on ne dit rien —
    # « pas d'ecart » est une reponse honnete, « −2409 » ne l'est pas.
    reg = _regime()
    passees = [x for x in lu
               if maintenant - (x.get("quand") or 0) >= HEURES
               and x.get("regime", reg) == reg]
    avant = passees[-1] if passees else None
    for a, o in totaux.items():
        v = ((avant or {}).get("affaires") or {}).get(a)
        o["avant"] = v
        o["ecart"] = None if v is None else round(o["score"] - v, 1)
    # On pose la ligne quand les scores ont BOUGE, pas quand l'horloge a tourne.
    # Une affaire qui apparait ou disparait compte comme un changement : c'est
    # une comparaison de dictionnaires entiers, pas de valeurs une a une.
    scores = {a: o["score"] for a, o in totaux.items()}
    if not lu or (lu[-1].get("affaires") or {}) != scores:
        try:
            with io.open(HISTOIRE, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps({
                    "quand": maintenant, "date": date_monde,
                    "regime": _regime(), "affaires": scores,
                }, ensure_ascii=False) + u"\n")
        except Exception as e:
            sys.stderr.write(u"  (trace non posee : %s)\n" % e)
    return totaux


# ─────────────────────────────────────── l'arbre des decisions
#
# CE QU'ON CHERCHE ICI, ET POURQUOI CE N'EST PAS LA CRITICITE. Dans un plan
# conjonctif entierement connexe, 95 % des pas portent la meme perte — et c'est
# JUSTE : ils sont tous obligatoires. Le relief n'est donc pas sur les pas, il
# est sur les FOURCHES. Une decision qui en commande sept ne vaut pas une
# decision qui n'en commande aucune, et ca, aucune mesure de pas ne le dira.
#
# UNE DECISION EST DEVINEE, PAS DECLAREE — et c'est la seule hypothese de tout
# ce module. On appelle decision un verrou dont PLUSIEURS clefs sont retenues :
# plusieurs mecanismes gardes pour une meme serrure, donc un choix que personne
# n'a fait. Ca peut se tromper : trois clefs retenues peuvent etre trois
# mecanismes COMPLEMENTAIRES qu'on veut tous les trois. Le remede tient en une
# colonne sur le verrou — « ⚖️ Il en faut : une | toutes », 47 cellules — et
# tant qu'elle n'existe pas, ce rendu est une PROPOSITION de lecture. Il le dit.
#
# L'ARBRE NE S'AFFICHE JAMAIS EN ENTIER : 38 decisions ouvertes font 6,26 x 10^12
# combinaisons. On ne montre donc qu'un saut — une decision, ses branches, et les
# decisions que chacune commande —, exactement comme la colonne `attendu`.
#
# CE QU'UNE BRANCHE COUTE, ET CE QU'ELLE LIBERE. Choisir n'est pas seulement
# engager : c'est ECARTER. Retenir une clef sur trois retire du plan les actions
# des deux autres, et c'est le vrai gain d'une decision — le plan retrecit. Les
# deux nombres se posent donc cote a cote : ce que la voie engage, ce que le
# choix libere.
# ─────────────────────────────────────── ce qu'une voie coûte, en clair
#
# ON NE CRÉE PAS UN FORMAT, ON LIT CELUI QUI EXISTE. Les hommes écrivent déjà
# leurs prix dans une forme presque uniforme, sans que personne le leur ait
# demandé : « 6 bras-jours + 1 coque marchande 2 jours · une fois · engagé J−22 ».
# Mesure sur les 909 prix écrits du plan : 49 % portent une date d'engagement,
# 56 % une cadence, 9 % des dragons, 7 % des bras-jours. La convention est bonne,
# l'adoption est à 7 % — il n'y a donc rien à concevoir, seulement à lire et à
# demander le reste.
#
# CE QU'ON NE DEVINE PAS. « Un homme entier, 30 jours » vaut probablement trente
# bras-jours, et « une matinée » un demi. On ne le convertit PAS : une somme
# obtenue en devinant la moitié de ses termes est plus dangereuse qu'une absence
# de somme, parce qu'elle a l'air d'un compte. Ce qui n'est pas écrit en clair
# est compté comme ILLISIBLE, et le nombre d'illisibles s'affiche à côté du
# total. Un total de douze sur trois prix dont deux sont illisibles n'est pas
# douze : c'est « au moins douze, et l'on ne sait pas ».
#
# POURQUOI ÇA VAUT LE DÉTOUR — la fourche du débarquement, 20101 :
#   au compte des pièces   5 contre 1        (la première a l'air cinq fois plus lourde)
#   au prix                12 bj contre 12   (elles coûtent exactement la même chose)
# Un conseil qui choisit sur le compte des lignes choisit à l'envers.
BRAS = re.compile(u"(\\d+(?:[.,]\\d+)?)\\s*(?:bras[-\\s]jours?|journ[ée]es?\\s+d.homme|j-h\\b)", re.I)
DRAGONS = re.compile(u"(\\d+(?:[.,]\\d+)?)\\s*dragons?\\b", re.I)
ENGAGE = re.compile(u"engag[ée]e?\\s*([JD][−\\-]\\s*\\d+)", re.I)


def cout(prose):
    """{bj, or, engage, lisible} — ce qu'une cellule de prix dit VRAIMENT."""
    t = nu(prose or u"")
    b = BRAS.search(t)
    d = DRAGONS.search(t)
    e = ENGAGE.search(t)
    return {"bj": float(b.group(1).replace(u",", u".")) if b else None,
            "or": float(d.group(1).replace(u",", u".")) if d else None,
            "engage": e.group(1).replace(u" ", u"") if e else None,
            "lisible": bool(b or d)}


def cout_du_plan(pieces_du_plan, prix_de):
    """Le prix d'une voie : la somme de ce qui est lisible, et le compte de ce
    qui ne l'est pas. Les deux ensemble, jamais l'un sans l'autre."""
    bj = 0.0
    orr = 0.0
    flou = 0
    quand = []
    for a in pieces_du_plan:
        c = cout(prix_de.get(a))
        if c["bj"]:
            bj += c["bj"]
        if c["or"]:
            orr += c["or"]
        if not c["lisible"]:
            flou += 1
        if c["engage"]:
            quand.append(c["engage"])
    # LE PLUS TÔT COMMANDE : une voie est due le jour de son premier engagement,
    # pas le jour de son dernier. « J−22 » vient avant « J−6 ».
    def rang(x):
        try:
            return -int(re.sub(u"[^0-9]", u"", x))
        except Exception:
            return 0
    return {"bj": bj, "or": orr, "flou": flou,
            "quand": sorted(quand, key=rang)[0] if quand else None}


def dire_cout(c, n):
    """« 12 bj · 8 dragons · dû J−22 · 1 prix illisible sur 3 »."""
    bouts = []
    if c["bj"]:
        bouts.append(u"%g bras-jours" % c["bj"])
    if c["or"]:
        bouts.append(u"%g dragons" % c["or"])
    if c["quand"]:
        bouts.append(u"dû %s" % c["quand"])
    if c["flou"]:
        bouts.append(u"%d prix illisible%s sur %d"
                     % (c["flou"], u"s" if c["flou"] > 1 else u"", n))
    return u" · ".join(bouts) if bouts else u"aucun prix lisible"


def plan_de(k, pieces, sous):
    """LE PLAN PROPRE D'UNE OPTION — ce qu'on juge, au lieu de la phrase qui la
    nomme. Ses actions, plus tout ce qui ne dépend QUE d'elles. Mesuré sur les
    quatre-vingt-quatre options du plan : médiane 3 pièces, moyenne 4,2, jamais
    plus de 20. Deux plans de cette taille se posent côte à côte et se comparent
    à l'œil — ce n'était pas gagné d'avance, et c'est ce qui rend l'idée tenable
    ici. Sept options n'ont AUCUN plan propre : une clef retenue qui n'engage
    aucune action est une phrase, pas une voie, et ça doit se voir."""
    base = set(sous.get(k, []))
    bouge = True
    while bouge:
        bouge = False
        for n, p in pieces.items():
            if n in base:
                continue
            ds = [d for d in p["dep"] if d in pieces]
            if ds and all(d in base for d in ds):
                base.add(n)
                bouge = True
    return base


def declaree(ks, pieces):
    """Une fourche est DÉCLARÉE quand deux de ses options s'excluent l'une
    l'autre par le lien, SUPPOSÉE quand on ne l'infère que du nombre de clefs
    retenues. La différence n'est pas cosmétique : dans le second cas, trois
    clefs gardées peuvent être trois compléments qu'on veut tous les trois, et
    l'appeler « choix » est une lecture de plus qu'on prête au cahier."""
    return any(j in (pieces[k].get("exclut") or []) for k in ks for j in ks if j != k)


def decisions_ouvertes(pieces):
    """{verrou: [clefs retenues]} pour les verrous qui en ont plus d'une."""
    par = {}
    for n, p in pieces.items():
        if p["genre"] != "clef":
            continue
        for v in p["vers"]:
            if v in pieces and pieces[v]["genre"] == "verrou":
                par.setdefault(v, []).append(n)
    retenue = lambda k: u"retenue" in (pieces[k].get("etat") or u"").lower()  # noqa: E731
    out = {}
    for v, ks in par.items():
        gardees = sorted(k for k in ks if retenue(k))
        if len(gardees) > 1:
            out[v] = gardees
    return out


def arbre_des_decisions(pieces):
    """(decisions, aval, racines). `aval[v]` = les decisions que v commande."""
    dec = decisions_ouvertes(pieces)
    memo = {}

    def amont(n):
        """Tout ce qu'on atteint en remontant : les etats que n sert, de proche
        en proche jusqu'aux objectifs."""
        if n in memo:
            return memo[n]
        memo[n] = set()
        vu = {n}
        pile = [n]
        while pile:
            x = pile.pop()
            for v in pieces.get(x, {}).get("vers", []):
                if v in pieces and v not in vu:
                    vu.add(v)
                    pile.append(v)
        memo[n] = vu
        return vu

    # UNE DECISION EST EN AVAL D'UNE AUTRE quand elle bloque un etat que la
    # premiere sert. On ne la « rencontre » jamais en remontant — un verrou
    # pointe vers un etat, aucun etat ne pointe vers un verrou —, et c'est la
    # faute que j'ai faite en premier : elle rendait zero partout et faisait
    # conclure que les decisions etaient independantes. Elles ne le sont pas.
    aval = {}
    for v in dec:
        ets = amont(v) - {v}
        aval[v] = sorted(w for w in dec
                         if w != v and any(e in ets for e in pieces[w]["vers"]))
    commandees = {w for L in aval.values() for w in L}
    racines = sorted(v for v in dec if v not in commandees)
    return dec, aval, racines


def descendance(v, aval, vu=None):
    vu = vu if vu is not None else set()
    for w in aval.get(v, []):
        if w not in vu:
            vu.add(w)
            descendance(w, aval, vu)
    return vu


def section_decisions(pieces, lignes, attendu, prix_de, combien, une_seule=None):
    dec, aval, racines = arbre_des_decisions(pieces)
    score = {n: c + attendu.get(n, 0) for c, pt, n, p in lignes}
    sous = {}
    for n, p in pieces.items():
        if p["genre"] == "action":
            for k in p["vers"]:
                if k in pieces and pieces[k]["genre"] == "clef":
                    sous.setdefault(k, []).append(n)

    titre(u"🌳 L'ARBRE DES DÉCISIONS — %d fourches ouvertes, %d de premier rang"
          % (len(dec), len(racines)))
    dites = sum(1 for x, ks in dec.items() if declaree(ks, pieces))
    sys.stdout.write(
        u"  %d déclarée%s par le lien ⛔ Exclut · %d encore supposée%s\n\n"
        u"  Une fourche SUPPOSÉE est un verrou dont plusieurs clefs sont retenues — plusieurs\n"
        u"  mécanismes gardés pour une même serrure. C'est une LECTURE : trois clefs retenues\n"
        u"  peuvent aussi être trois compléments qu'on veut tous les trois. Une fourche DÉCLARÉE\n"
        u"  porte le lien ⛔ Exclut entre ses options, et là on ne suppose plus rien.\n\n"
        u"  On juge des PLANS, pas des phrases : chaque voie montre ce qu'elle engage — ses\n"
        u"  pièces, l'office sur qui elles tombent, leur jour — et ce qu'elle tue chez la voisine.\n"
        % (dites, u"s" if dites > 1 else u"", len(dec) - dites,
           u"s" if len(dec) - dites > 1 else u""))

    liste = [une_seule] if une_seule else racines
    for v in sorted(liste, key=lambda x: -len(descendance(x, aval))):
        if v not in dec:
            sys.stdout.write(u"\n  %s n'est pas une décision ouverte.\n" % v)
            continue
        p = pieces[v]
        d = descendance(v, aval)
        dit = declaree(dec[v], pieces)
        sys.stdout.write(u"\n  🔒 %s  %s   %s\n" % (
            v, p["nom"], u"[FOURCHE DÉCLARÉE]" if dit else u"[fourche supposée]"))
        sys.stdout.write(u"      %s · commande %d décision%s en aval\n"
                         % (p["affaire"][:52], len(d), u"s" if len(d) > 1 else u""))
        bloque = [e for e in p["vers"] if e in pieces]
        if bloque:
            sys.stdout.write(u"      bloque : %s\n" % u" · ".join(
                u"🎯 %s %s" % (e, pieces[e]["nom"][:40]) for e in bloque[:2]))
        toutes = dec[v]
        couts = {}
        for k in toutes:
            mien = plan_de(k, pieces, sous)
            # CE QU'ON TUE EN CHOISISSANT. Déclarée, l'exclusion dit exactement
            # quelles voies tombent ; supposée, on prend les autres options de la
            # serrure et l'on assume la lecture. Les deux nombres ne sont pas de
            # même nature, et le rendu ne les mélange pas.
            tuees = ([j for j in toutes if j in (pieces[k].get("exclut") or [])]
                     if dit else [j for j in toutes if j != k])
            perdu = set()
            for j in tuees:
                perdu |= plan_de(j, pieces, sous)
            af = sum(1 for a in mien if not faite(pieces[a]))
            c = cout_du_plan(mien, prix_de)
            couts[k] = c
            sys.stdout.write(u"\n      ├ 🗝️ %-6s %s\n" % (k, pieces[k]["nom"][:58]))
            sys.stdout.write(u"      │    LE PLAN : %d pièce%s, %d à faire%s\n"
                             % (len(mien), u"s" if len(mien) > 1 else u"", af,
                                u"   ⚠️ aucune action : c'est une phrase, pas une voie"
                                if not mien else u""))
            sys.stdout.write(u"      │    LE PRIX : %s\n" % dire_cout(c, len(mien)))
            for a in sorted(mien)[:6]:
                q = pieces[a]
                sys.stdout.write(u"      │      %s %-6s %-42s %-9s %s\n" % (
                    NOM_GENRE.get(q["genre"], u""), a, q["nom"][:42],
                    (q.get("office") or u"—")[:9],
                    sans_emoji(q.get("jour") or q.get("etat") or u"")[:18]))
            if len(mien) > 6:
                sys.stdout.write(u"      │      … et %d autres\n" % (len(mien) - 6))
            if tuees:
                sys.stdout.write(u"      │    %s : %s — %d pièce(s) retirée(s) du plan\n"
                                 % (u"tue" if dit else u"écarterait",
                                    u" ".join(tuees), len(perdu)))
            px = prix_de.get(k)
            if px:
                sys.stdout.write(u"      │    prix : %s\n" % nu(px)[:88])
        # L'ÉGALITÉ DÉGUISÉE EN ÉVIDENCE. C'est le cas qui a justifié tout ce
        # bloc : au compte des pièces, la fourche du débarquement se lit cinq
        # contre un ; au prix, douze bras-jours contre douze. On le DIT, parce
        # qu'un lecteur pressé s'arrête au premier nombre qu'il voit.
        lus = [(k, c) for k, c in couts.items() if c["bj"]]
        if len(lus) > 1:
            bas, haut = min(c["bj"] for _, c in lus), max(c["bj"] for _, c in lus)
            flou = sum(c["flou"] for _, c in lus)
            if haut and (haut - bas) / haut <= 0.15:
                sys.stdout.write(
                    u"      ⚖️ ÉGALITÉ DE PRIX : %s — le compte des pièces trompe ici.%s\n"
                    % (u" contre ".join(u"%g bj" % c["bj"] for _, c in lus),
                       u"" if not flou else u"  (%d prix illisible(s))" % flou))
        if aval[v]:
            sys.stdout.write(u"      └ ouvre ensuite : %s\n" % u" · ".join(
                u"🔒 %s %s" % (w, pieces[w]["nom"][:30]) for w in aval[v][:3]))
    if not une_seule:
        sys.stdout.write(
            u"\n  Les %d autres décisions sont PRÉMATURÉES : chacune dépend d'une fourche\n"
            u"  d'amont non tranchée. Les prendre aujourd'hui, c'est trancher sans savoir.\n"
            u"  `--decisions <n°>` déroule une fourche seule.\n" % (len(dec) - len(racines)))


def affiche(cle, brut, deja=None):
    """Le nom qu'on montre pour une clef d'homme. Les clefs sentinelles se
    disent en clair — « la reine » n'est pas un nom qu'on a lu quelque part,
    c'est une deduction, et le lecteur doit pouvoir la contester."""
    if cle == u"la reine":
        return u"La reine (« moi » aux registres)"
    if cle.startswith(u"—"):
        return cle
    n = GLOSE.sub(u"", u" ".join(nu(brut).split())).strip()
    return max(deja or u"", n, key=len)


# ─────────────────────────────────────── la note, et l'echelle qui s'y regle
#
# ON NE SAISIT PAS UN POIDS, ON DONNE UNE NOTE SUR DIX. Un poids est un nombre
# de machine : personne ne sait dire si le Trone « vaut 12 » ou « vaut 40 », et
# celui qui l'ecrirait le prendrait au hasard puis n'oserait plus y toucher. Une
# note sur dix est un jugement d'homme, et elle se defend en une phrase.
#
# L'ECHELLE SE REGLE SUR LE GRAPHE, ET C'EST TOUT LE POINT. Une note portee en
# poids lineaire (1 a 10) ne pese RIEN contre la topologie : une chaine qui sert
# huit etats bat un objectif note 10 tout seul, et l'on aurait donne au joueur un
# volant qui ne tourne pas. On mesure donc d'abord ce que le graphe amplifie
# deja — l'ecart entre le cahier le plus lourd et le cahier median, a notes
# egales — et l'on cale l'echelle dessus :
#
#     note 5  ->  1          la neutralite, ce que valent les choses aujourd'hui
#     note 10 ->  A          A = amplitude structurelle du plan
#     note 0  ->  1/A        poids(note) = A ** ((note - 5) / 5)
#
# Autrement dit : passer un objectif de 5 a 10 lui donne exactement le poids que
# la topologie donne, a elle seule, au plus gros cahier contre un cahier moyen.
# Une main d'homme pese alors autant qu'une position dans le graphe, ni plus ni
# moins. Et quand le plan change de forme, l'echelle suit — d'ou « adaptative ».
#
# SEULS LES OBJECTIFS FINAUX PORTENT UNE NOTE, et les autres etats valent ZERO.
# Ce n'est pas une economie de saisie : un etat intermediaire n'a pas de valeur
# propre, il vaut ce qu'il sert. Lui laisser 1 revenait a payer deux fois la meme
# chose, et c'est ce qui faisait remonter la plomberie au-dessus du but.
NOTE_NEUTRE = 5.0
AMPLITUDE_MIN, AMPLITUDE_MAX = 3.0, 20.0


def objectifs_finaux(pieces):
    """Les etats cibles qui ne servent aucun autre etat : le bout des chaines."""
    et = {n for n, p in pieces.items() if p["genre"] == "etat"}
    return sorted(n for n in et
                  if not [v for v in pieces[n]["vers"] if v in et])


def amplitude(pieces, lignes):
    """Ce que le graphe amplifie tout seul : le cahier le plus lourd contre le
    median, a notes egales. Bornee, parce qu'un plan de trois cahiers donnerait
    un rapport absurde et qu'un plan tres plat rendrait la note inoperante."""
    par = {}
    for c, pt, n, p in lignes:
        par[p["affaire"]] = par.get(p["affaire"], 0) + c
    v = sorted(x for x in par.values() if x > 0)
    if len(v) < 4:
        return AMPLITUDE_MIN
    med = v[len(v) // 2]
    return max(AMPLITUDE_MIN, min(AMPLITUDE_MAX, (v[-1] / med) if med else AMPLITUDE_MIN))


def poids_des_etats(pieces, ampli=None):
    """(poids par etat, nombre de notes saisies).

    Sans fichier, ou tant qu'aucune note n'est ecrite, TOUT VAUT 1 comme avant :
    on ne change pas la mesure sous les pieds de quelqu'un qui n'a rien demande.
    Des qu'une note existe, on bascule dans le regime des objectifs finaux — les
    notes portent, les etats intermediaires valent zero."""
    brut = {}
    if os.path.exists(POIDS):
        try:
            brut = json.load(io.open(POIDS, encoding="utf-8"))
        except Exception:
            brut = {}
    notes = brut.get("notes") if isinstance(brut.get("notes"), dict) else {}
    # L'ANCIENNE FORME RESTE LISIBLE : un fichier de nombres nus est pris pour des
    # poids directs. On ne casse pas ce que quelqu'un aurait deja ecrit a la main.
    directs = {k: v for k, v in brut.items()
               if not k.startswith(u"_") and isinstance(v, (int, float))}
    etats = [n for n, p in pieces.items() if p["genre"] == "etat"]
    if not notes:
        return {n: float(directs.get(n, 1)) for n in etats}, len(directs)
    a = ampli or AMPLITUDE_MIN
    fins = set(objectifs_finaux(pieces))
    poids = {}
    for n in etats:
        if n not in fins:
            poids[n] = 0.0            # il vaut ce qu'il sert, pas plus
            continue
        note = float(notes.get(n, NOTE_NEUTRE))
        poids[n] = round(a ** ((note - NOTE_NEUTRE) / NOTE_NEUTRE), 3)
    return poids, len([n for n in notes if n in fins])


def masse(ok, poids):
    return sum(w for n, w in poids.items() if ok.get(n))


def portee(n, pieces, poids, cache):
    """Les etats cibles qu'une piece sert, en remontant. Ensemble, pas somme de
    chemins : un losange compterait deux fois le meme etat."""
    if n in cache:
        return cache[n]
    cache[n] = set()          # coupe les cycles
    vus = set()
    p = pieces.get(n)
    if p:
        if p["genre"] == "etat":
            vus.add(n)
        for v in p["vers"]:
            if v in pieces:
                vus |= portee(v, pieces, poids, cache)
    cache[n] = vus
    return vus


# ─────────────────────────────────────────────── mise en page
def titre(t):
    sys.stdout.write(u"\n" + t + u"\n" + u"─" * LARGEUR + u"\n")


def cale(t, n):
    t = nu(t)
    return (t[:n - 1] + u"…") if len(t) > n else t.ljust(n)


def statut(p):
    t = sans_emoji(p["etat"] or u"")
    return cale(t, 14) if t else u"—"


def prix(livres):
    """{numero: la prose du prix}. Elle est portee par la CLEF — « 💰 Ce
    qu'elle coute et ce qu'elle ferme » — et `charger()` ne la remonte pas :
    l'index derive ne la porte pas non plus, a dessein. On la relit ici, pour
    l'imprimer telle quelle. On n'en tire aucun nombre : diviser par de la
    prose ne se fait pas, et lui coller un bareme serait inventer le seul
    chiffre que personne n'a ecrit."""
    out = {}
    from plan.expose import numero_de as _numero_de, col as _col
    for b in livres:
        for t in (b.get("tables") or []):
            cols = t.get("colonnes") or []
            i = _col(cols, u"coûte|coute|le prix")
            if i is None:
                continue
            for l in (t.get("lignes") or []):
                c = [nu(x) for x in ((l if isinstance(l, list) else l.get("cellules")) or [])]
                if len(c) > i and c and c[i]:
                    m = _numero_de(c[0])
                    if m:
                        out.setdefault(m.group(1), c[i])
    return out


def faite(p):
    return bool(FINI.match(premier_mot(p["etat"]) or u""))


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--combien", type=int, default=25)
    ap.add_argument("--affaire")
    ap.add_argument("--restant", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--sans-dep", action="store_true")
    ap.add_argument("--dep", choices=("interne", "toutes", "aucune"), default="interne")
    ap.add_argument("--etats", action="store_true")
    ap.add_argument("--actions-ou", action="store_true")
    ap.add_argument("--pourquoi", metavar=u"N°")
    # POUR L'ÉCRAN, ET SANS RIEN ÉCRIRE SUR LE DISQUE. Une colonne de criticité
    # posée dans `books.json` serait effacée au prochain `couverture.py`, qui
    # regénère les registres à quatre colonnes exprès — et elle mentirait dès la
    # première action cochée. Le serveur appelle donc ce mode et sert le résultat
    # à côté du volume ; les livres restent ce qu'ils sont, l'écran les augmente.
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--acteurs", action="store_true")
    ap.add_argument("--charge", nargs="?", const="", metavar=u"QUI")
    ap.add_argument("--decisions", nargs="?", const="", metavar=u"N°")
    ap.add_argument("--vue-de", default=PM.personnage_par_defaut(),
                    help="siège dont on mesure l'étagère visible")
    a = ap.parse_args()

    modele = PM.charger(a.vue_de)
    livres, pieces, inventaire, affaires = (modele["livres"], modele["pieces"],
                                            modele["inventaire"], modele["affaires"])
    prix_de = prix(livres)
    # La date du monde, notée à côté de chaque instantané : elle ne sert pas à
    # comparer (deux mesures d'un même jour de jeu peuvent être séparées d'une
    # semaine de travail) mais à relire la trace en années de règne.
    date = json.load(io.open(os.path.join(RACINE, "etat", "monde.json"),
                             encoding="utf-8")).get("date") or {}
    mode_dep = u"aucune" if a.sans_dep else a.dep
    lignes, base, poids, saisis, m0, dehors = calculer(
        pieces, mode_dep=mode_dep, optimiste=not a.strict,
        actions_ou=a.actions_ou)
    # CE QUI ATTEND AILLEURS — le signal, une fois requalifie. Un saut, pas une
    # cascade : le poids de ce qui, dans un AUTRE cahier, nomme cette piece dans
    # son « depend de ». On somme leur criticite propre, pas leur nombre : dix
    # pieces sans consequence pesent moins qu'une seule qui tient un etat.
    crit = {n: c for c, pt, n, p in lignes}
    attendu = {n: sum(crit.get(m, 0) for m in ms) for n, ms in dehors.items()}

    if a.json:
        # La portee BRUTE — les etats qu'un pas sert, atteignables ou non. Elle
        # separe « ne sert rien » de « sert ce que le plan ne sait pas
        # atteindre » ; `calculer` la jette apres usage, on la refait ici. Le
        # cache est celui de `portee` : le second passage ne coute rien.
        cache_portee = {}
        grappes = cercles(pieces, *amonts(pieces, mode_dep, a.actions_ou)[:2])
        noue = {m: i for i, g in enumerate(grappes) for m in g}
        offices, moyens = gens(livres)
        # LA PAGE NE DOIT PAS RELIRE `books.json` POUR AFFICHER UN NOM. Le
        # fichier fait 2,4 Mo ; le faire descendre au navigateur pour y
        # rechercher trois cents intitulés serait payer mille fois le prix du
        # calcul lui-meme. On sert donc la ligne entiere, prete a poser.
        # QUI TIENT QUOI, PAR MOYEN. `pas[n].moyens` ne donne que des numeros ;
        # sans cette table, la page ne peut pas dire a qui l'on tire, et sa
        # colonne « on tire » reste a zero sans que rien n'echoue. On sert le
        # nom tel qu'il est ECRIT au registre des moyens : la jointure avec les
        # titulaires d'offices (« Dame Aurore » d'un cote, « Aurore » de
        # l'autre) se refait cote page, qui seule sait sur quoi elle regroupe.
        tenu = {m: list(qui) for m, (_nom, qui) in moyens.items() if qui}
        # LA CHARGE DES HOMMES SE SERT D'ICI, ET NON REFAITE DANS LE NAVIGATEUR.
        # La page a de quoi la recalculer — elle a `pas`, `offices` et `tenu` —
        # et c'est precisement ce qu'il ne faut pas : deux definitions de « ce
        # qu'un homme ne voit pas », dont l'une derive au premier repli de nom
        # qu'on ajoute ici. `charge_des_hommes()` est deja la seule main qui
        # replie « jacaerys » sur « jacaerys-velaryon » ; on sert son resultat.
        #
        # ON SERT DES SOMMES PAR AFFAIRE, PAS UN TOTAL. Le calcul voit les
        # quarante-deux cahiers du depot, cahiers d'un autre siege compris ; un
        # total tout cuit serait donc infiltrable et l'ecran n'aurait aucun
        # moyen de le borner. Rendues par cahier, les sommes se restreignent a
        # l'etagere que ce siege peut ouvrir — c'est la meme borne que le volume
        # « Les pas », appliquee une fois de plus et non reinventee.
        def _par_affaire(L):
            out = {}
            for s, n, p in L:
                c = out.setdefault(p["affaire"] or u"", {"s": 0.0, "pas": 0})
                c["s"] += s
                c["pas"] += 1
            return out
        charge = {q: {"offices": h["offices"], "moyens": h["moyens"],
                      "cahiers": h["cahiers"],
                      "vu": _par_affaire(h["vu"]),
                      "sien_ailleurs": _par_affaire(h["sien_ailleurs"]),
                      "tire": _par_affaire(h["tire"])}
                  for q, h in charge_des_hommes(pieces, affaires, lignes,
                                                attendu, offices, moyens).items()}
        # La table `--acteurs`, servie telle quelle : l'écran fait varier la
        # taille des ronds du plan sur `porte`, et il ne recalcule rien — la
        # jointure office↔homme est devinée, elle se fait ici ou nulle part.
        acteurs, sans_office, office_en_clair = porte_des_hommes(lignes, offices,
                                                                 moyens)
        sys.stdout.write(json.dumps({
            "vue_de": modele["vue_de"],
            "portee": PM.mesures(modele),
            "charge": charge,
            "acteurs": acteurs,
            "hors_acteurs": {"sans_office": {"s": round(sans_office[0], 3),
                                             "pas": sans_office[1]},
                             "office_en_clair": {"s": round(office_en_clair[0], 3),
                                                 "pas": office_en_clair[1]}},
            "tenu": tenu,
            "masse": m0, "saisis": saisis, "mode_dep": mode_dep,
            "date": json.load(io.open(os.path.join(RACINE, "etat", "monde.json"),
                                      encoding="utf-8")).get("date") or {},
            "etats": {n: {"poids": w, "atteignable": bool(base.get(n)),
                          "nom": pieces[n]["nom"], "affaire": pieces[n]["affaire"]}
                      for n, w in poids.items()},
            "cercles": [{"taille": len(g),
                         "pieces": [{"n": m, "genre": pieces[m]["genre"],
                                     "nom": pieces[m]["nom"],
                                     "affaire": pieces[m]["affaire"]} for m in g]}
                        for g in grappes],
            "offices": {o: {"nom": v[0], "qui": v[1]} for o, v in offices.items()},
            "tenu": {m: v[1] for m, v in moyens.items()},
            # Les sommes par cahier, avec l'écart contre la veille. Elles ne
            # sont pas dérivables à l'écran : le passé n'existe plus dans
            # `books.json` une fois qu'il a été réécrit.
            "affaires": veille(totaux_par_affaire(lignes, attendu, pieces, affaires),
                               date),
            "idees": idees(pieces,
                           {n: {"perte": c, "attendu": attendu.get(n, 0)}
                            for c, pt, n, p in lignes},
                           poids, base),
            "pas": {n: {"perte": c, "portee": pt,
                        "attendu": attendu.get(n, 0),
                        # POURQUOI CE CHIFFRE EST CE QU'IL EST. Sans elle, un
                        # zéro d'amont bloqué se lit comme un zéro d'accompli,
                        # et l'écran range sous « rien à faire » ce qui est en
                        # réalité « le plan ne sait pas y arriver ».
                        "raison": raison_du_zero(p, c, pt,
                                                 portee(n, pieces, poids,
                                                        cache_portee),
                                                 attendu.get(n, 0)),
                        "cercle": noue.get(n),
                        "genre": p["genre"], "nom": p["nom"],
                        "affaire": p["affaire"], "etat": p["etat"],
                        "faite": faite(p),
                        "office": p.get("office") or u"",
                        "moyens": p.get("moyens") or [],
                        "prix": prix_de.get(n) or u""}
                    for c, pt, n, p in lignes},
        }, ensure_ascii=False))
        return

    titre(u"⚖️ LA CRITICITÉ — ce que le plan perd si ce pas-là rate")
    sys.stdout.write(
        u"  vue de %s · %d pièces · %d états cibles, dont %d atteignables (masse %g)\n"
        u"  poids saisis à la main : %d — les autres valent 1 (etat/poids-etats.json)\n"
        u"  ET/OU lu sur le genre · « dépend de » %s · verrou sans clef : %s\n"
        % (modele["vue_de"], len(pieces), len(poids),
           sum(1 for e in poids if base.get(e)), m0, saisis,
           {u"interne": u"bloque dans le cahier, compté dehors",
            u"toutes": u"bloque partout", u"aucune": u"ignoré"}[mode_dep],
           u"bloque (strict)" if a.strict else u"se lève quand même"))

    tous, un, _ = amonts(pieces, mode_dep=mode_dep, actions_ou=a.actions_ou)
    if a.pourquoi:
        titre(u"❓ POURQUOI %s N'EST PAS ATTEIGNABLE" % a.pourquoi)
        pourquoi(a.pourquoi, pieces, tous, un, base)
        return

    grappes = cercles(pieces, tous, un)
    if grappes:
        titre(u"🔁 LES CERCLES — %d chaîne%s qui se mord%s la queue, donc ne partira%s jamais"
              % (len(grappes), u"s" if len(grappes) > 1 else u"",
                 u"ent" if len(grappes) > 1 else u"", u"ient" if len(grappes) > 1 else u""))
        for g in grappes[:12]:
            # UNE GRAPPE DE QUATRE-VINGT-NEUF PIECES N'EST PAS UN CERCLE QU'ON
            # LIT : imprimee en chaine, elle occupe six lignes et ne se repare
            # pas. On dit alors sa taille et les cahiers qu'elle traverse, et
            # l'on renvoie a `--pourquoi`. Les petites, elles, se lisent et se
            # coupent d'un trait de plume — ce sont celles qui valent l'impression.
            if len(g) > 8:
                affs = sorted({pieces[m]["affaire"] for m in g if pieces[m]["affaire"]})
                sys.stdout.write(u"  🕸️ %d pièces enchevêtrées, %d cahiers — %s…\n"
                                 % (len(g), len(affs), u" · ".join(affs[:3])))
                sys.stdout.write(u"      commence à %s · `--pourquoi %s` pour dérouler\n"
                                 % (g[0], g[0]))
                continue
            sys.stdout.write(u"  %s\n" % u" → ".join(
                NOM_GENRE.get(pieces[m]["genre"], u"") + u" " + m for m in g))
            sys.stdout.write(u"      %s\n" % cale(pieces[g[0]]["nom"], 88))
        sys.stdout.write(
            u"\n  Aucun des six détecteurs de `couverture.py` ne les voit : chaque ligne,\n"
            u"  prise seule, est bien formée. Tant qu'un cercle tient, tout ce qui pend\n"
            u"  derrière est à zéro — 🕳️ ci-dessous.\n")

    if a.decisions is not None:
        section_decisions(pieces, lignes, attendu, prix_de, a.combien,
                          a.decisions or None)
        return

    if a.charge is not None:
        offices, moyens = gens(livres)
        section_charge(charge_des_hommes(pieces, affaires, lignes, attendu,
                                         offices, moyens),
                       a.combien, a.charge or None)
        return

    if a.acteurs:
        offices, moyens = gens(livres)
        hommes, sans, en_clair = porte_des_hommes(lignes, offices, moyens)
        titre(u"👤 CE QUE CHAQUE HOMME PORTE — criticité de ses pas, et de ce qu'il tient")
        sys.stdout.write(u"  %s%s%s%s%s\n" % (
            cale(u"porte", 8), cale(u"pas", 6), cale(u"goulots", 9),
            cale(u"on tire", 9), u"l'homme, et ses offices"))
        rang = sorted(hommes.items(), key=lambda x: -x[1]["porte"])
        for q, h in [x for x in rang if x[1]["pas"]][:a.combien]:
            sys.stdout.write(u"  %s%s%s%s%s\n" % (
                cale(u"%g" % h["porte"], 8), cale(u"%d" % h["pas"], 6),
                cale(u"%d" % h["goulots"], 9), cale(u"%g" % h["tire"], 9),
                cale(h["nom"] + u"  · " + u" ".join(h["offices"]), 58)))
        titre(u"🪝 CE QU'ON LEUR TIRE — ils tiennent un moyen dont le plan a besoin")
        for q, h in sorted(hommes.items(),
                           key=lambda x: -x[1]["tire"])[:min(10, a.combien)]:
            if h["pas"] or not h["tire_pas"]:
                continue
            sys.stdout.write(u"  %s%s%s\n" % (cale(u"%g" % h["tire"], 8),
                                              cale(u"%d pas" % h["tire_pas"], 9),
                                              h["nom"]))
        sys.stdout.write(
            u"\n  🕳️ sans office écrit : %g de criticité sur %d pas"
            u"  ·  office nommé mais sans numéro : %g sur %d\n"
            u"      Ce premier chiffre est le seul qui n'ait personne pour le porter.\n"
            u"      Jointure devinée entre les deux registres : titres retirés, « moi » = la reine.\n"
            % (sans[0], sans[1], en_clair[0], en_clair[1]))
        return

    if a.etats:
        titre(u"🎯 LES ÉTATS CIBLES — poids, et atteignables ou non")
        for n, w in sorted(poids.items(), key=lambda x: (-x[1], x[0])):
            p = pieces[n]
            if a.affaire and a.affaire.lower() not in sans_emoji(p["affaire"]).lower():
                continue
            sys.stdout.write(u"  %s %-6s %s  %s  %s\n" % (
                u"✅" if base.get(n) else u"🚫", n, cale(u"%g" % w, 4),
                cale(p["nom"], 52), cale(p["affaire"], 30)))
        return

    ret = [l for l in lignes if l[0] > 0]
    red = [l for l in lignes if l[0] == 0 and l[1] > 0]
    mort = [l for l in lignes if l[1] == 0]
    if a.affaire:
        f = lambda L: [l for l in L if a.affaire.lower() in sans_emoji(l[3]["affaire"]).lower()]  # noqa: E731
        ret, red, mort = f(ret), f(red), f(mort)
    if a.restant:
        f = lambda L: [l for l in L if not faite(l[3])]  # noqa: E731
        ret, red, mort = f(ret), f(red), f(mort)

    titre(u"🔺 LES GOULOTS — %d pas dont la perte coûte quelque chose" % len(ret))
    # PERTE PLUS GRANDE QUE PORTEE N'EST PAS UNE INCOHERENCE, c'est le seul
    # endroit ou les `depend de` se voient : la portee ne suit que la remontee
    # de l'affaire, la perte compte aussi ce qui attend la piece AILLEURS.
    sys.stdout.write(
        u"  « attendu » = le poids qui, dans un AUTRE cahier, se casse la figure sans ce pas.\n"
        u"  Un saut, jamais une cascade : c'est un signal de coordination, pas un prérequis.\n")
    sys.stdout.write(u"  %s%s%s%s%s%s\n" % (cale(u"perte", 7), cale(u"portée", 7),
                                            cale(u"attendu", 8), cale(u"n°", 10),
                                            cale(u"le pas", 42), u"état"))
    for c, pt, n, p in sorted(ret, key=lambda x: (-(x[0] + attendu.get(x[2], 0)), x[2]))[:a.combien]:
        sys.stdout.write(u"  %s%s%s%s%s%s\n" % (
            cale(u"%g" % c, 7), cale(u"%g" % pt, 7),
            cale(u"%g" % attendu[n] if attendu.get(n) else u"—", 8),
            cale(NOM_GENRE.get(p["genre"], u"") + u" " + n, 10),
            cale(p["nom"], 42), statut(p)))

    titre(u"➖ LES SUBSTITUABLES — %d pas de grande portée qu'on peut perdre sans rien perdre"
          % len(red))
    for c, pt, n, p in sorted(red, key=lambda x: (-x[1], x[2]))[:min(8, a.combien)]:
        sys.stdout.write(u"  %s%s%s%s\n" % (
            cale(u"%g" % pt, 7), cale(NOM_GENRE.get(p["genre"], u"") + u" " + n, 10),
            cale(p["nom"], 48), statut(p)))

    titre(u"🕳️ LES ORPHELINS — %d pas qui ne servent aucun état atteignable" % len(mort))
    sys.stdout.write(u"  " + u" · ".join(
        NOM_GENRE.get(p["genre"], u"") + u" " + n for _, _, n, p in mort[:40]) + u"\n")

    # Le prix, en prose, pour les premiers seulement — c'est le seul endroit
    # ou il a une chance d'etre lu.
    titre(u"💰 CE QUE COÛTENT LES CINQ PREMIERS — la colonne des clefs, telle quelle")
    for c, pt, n, p in sorted(ret, key=lambda x: (-(x[0] + attendu.get(x[2], 0)), x[2]))[:5]:
        sys.stdout.write(u"  %s %s\n     %s\n" % (
            cale(n, 6), cale(p["nom"], 60), prix_de.get(n) or u"— rien d'écrit —"))

    titre(u"🏰 PAR AFFAIRE — la masse de criticité que chaque cahier porte")
    par = veille(totaux_par_affaire(lignes, attendu, pieces, affaires), date)
    sys.stdout.write(u"  %s%s%s%s\n" % (cale(u"score", 8), cale(u"depuis", 8),
                                        cale(u"pas", 6), u"le cahier"))
    for aff, o in sorted(par.items(), key=lambda x: -x[1]["score"])[:15]:
        e = o.get("ecart")
        sys.stdout.write(u"  %s%s%s%s\n" % (
            cale(u"%g" % o["score"], 8),
            cale(u"—" if e is None else (u"%+g" % e), 8),
            cale(u"%d" % o["pas"], 6), cale(aff, 58)))
    sys.stdout.write(
        u"\n  ⚠️  Un score dérivé de ce qui est ÉCRIT mesure la rédaction autant que\n"
        u"      l'importance : le nombre de pas est là pour que le gonflement se voie.\n")


if __name__ == "__main__":
    main()
    # Le battement se pose APRES main(), donc seulement si elle est allee
    # au bout : un plantage ne bat pas, et c est le mecanisme entier.
    rapporteurs.battre("criticite", u"classement refait")
