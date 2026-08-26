# -*- coding: utf-8 -*-
"""PLAN_VILLE — cuire le plan 2D de la ville à partir du travail fait en 3D.

    python scripts/monde/plan_ville.py                 (port-real, par défaut)
    python scripts/monde/plan_ville.py --lieu port-real --sortie monde/portreal.plan2d.json

POURQUOI. Le monde en volume existe et il est juste, mais il se regarde mal :
il faut une carte graphique, il met dix secondes à se lever, et LA NUIT ON N'Y
VOIT RIEN — ce qui est fidèle et inutilisable, puisque cette partie se joue le
soir. Or tout ce qu'on lui demande à l'échelle de la ville est plan : où est
la rue des Sœurs, combien de pas jusqu'à la porte de la Gadoue, par où l'on
sort. Un SVG répond à ça mieux qu'un relief, se lit à toute heure, s'imprime,
et pèse ce que pèse un dessin.

ON NE RECALCULE RIEN. La ville a été engendrée une fois par la circulation
(voir `_engendre` de la carte) ; ce script ne fait que la TRADUIRE :

    monde/<x>.terrain.json   la grille d'altitude et le masque d'eau
                             → le trait de côte et les courbes de niveau
    monde/<x>.rues.json      22 840 nœuds, 18 314 arêtes classées
                             → les voies, chaînées par classe
    monde/<x>.bati.json      48 377 bâtiments (x, y, cap, façade, profondeur)
                             → des rectangles orientés, groupés par catégorie

CUIT, ET PAS CALCULÉ AU NAVIGATEUR. Les deux fichiers d'entrée font 7 Mo et
demandent un chaînage de graphe : le faire à chaque ouverture d'onglet, sur la
machine du joueur, c'est payer trois secondes pour un résultat qui ne change
jamais. On le fait ici, une fois, et l'on sert des chaînes `d` de SVG que le
client pose sans y toucher. La ville change ? On relance la commande.

LE GRAIN EST DANS LA SORTIE, pas dans le client. Chaque couche est cuite
séparément pour que la vue en montre plus à mesure qu'on approche : de loin
l'eau, le relief, les artères et les vingt institutions ; de près les ruelles
et les quarante mille maisons. Le client ne fait qu'allumer des couches — il
ne décide jamais quoi simplifier, parce qu'il n'a pas les moyens de bien le
faire.
"""
import argparse
import json
import math
import os
import random
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Le préfixe des fichiers du monde, par lieu. Même table que `LIEUX3D` côté
# serveur ; on ne la lit pas depuis JavaScript, on la redit ici, courte.
PREFIXES = {"port-real": "portreal", "peyredragon": "peyredragon"}

# Le préfixe du monde en cours de cuisson — `cuire` le pose, `monuments` le lit
# pour trouver son fichier d'emprises. Une liste plutôt qu'une chaîne, pour ne
# pas avoir à déclarer `global` dans chaque fonction qui la touche.
PREFIXE = ["portreal"]

# Les altitudes qu'on trace. Port-Réal monte à 106 m (la colline de Rhaenys) :
# huit courbes disent les trois collines sans noircir la carte. Une courbe tous
# les dix mètres en donnerait onze de plus qui ne distinguent rien.
NIVEAUX = [10, 20, 30, 40, 55, 70, 85, 100]

# Ce qui se voit de loin et ce qui n'apparaît qu'au près. L'ordre est celui du
# dessin : ce qui est écrit en premier est dessiné dessous.
COUCHES_VOIES = ["artere", "rue", "ruelle", "escalier", "quai", "abord"]
COUCHES_BATI = ["institution", "culte", "civique", "commerce", "artisanat",
                "plaisir", "service", "nuisance", "habitat"]


def lire(chemin):
    with open(os.path.join(RACINE, chemin), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Marching squares — une seule fois, deux usages
#
# Le trait de côte et les courbes de niveau sont le MÊME problème : où une
# grille de valeurs franchit-elle un seuil. On écrit donc un seul parcours, et
# l'on s'en sert pour l'eau (masque 0/1, seuil 0.5) comme pour l'altitude.
# Les segments sortent en désordre ; on les recoud bout à bout, sinon un SVG
# de dix-huit mille traits de deux points pèse cinq fois son dessin.
# ---------------------------------------------------------------------------
def segments(grille, nx, ny, seuil, pas):
    """Les segments frontière, en mètres. `grille[j][i]`, j en y, i en x."""
    out = []
    for j in range(ny - 1):
        l0, l1 = grille[j], grille[j + 1]
        for i in range(nx - 1):
            a, b, c, d = l0[i], l0[i + 1], l1[i + 1], l1[i]
            code = (1 if a > seuil else 0) | (2 if b > seuil else 0) | \
                   (4 if c > seuil else 0) | (8 if d > seuil else 0)
            if code == 0 or code == 15:
                continue
            x, y = i * pas, j * pas

            def ip(v1, v2):        # où le seuil tombe entre deux sommets
                if v2 == v1:
                    return .5
                t = (seuil - v1) / (v2 - v1)
                return 0. if t < 0 else (1. if t > 1 else t)

            haut = (x + ip(a, b) * pas, y)
            droite = (x + pas, y + ip(b, c) * pas)
            bas = (x + ip(d, c) * pas, y + pas)
            gauche = (x, y + ip(a, d) * pas)
            # Les deux cas ambigus (5 et 10) se tranchent au hasard consistant :
            # une selle mal coupée fait une île de plus, pas une carte fausse.
            table = {1: [(haut, gauche)], 2: [(haut, droite)], 3: [(gauche, droite)],
                     4: [(droite, bas)], 5: [(haut, gauche), (droite, bas)],
                     6: [(haut, bas)], 7: [(gauche, bas)], 8: [(gauche, bas)],
                     9: [(haut, bas)], 10: [(haut, droite), (gauche, bas)],
                     11: [(droite, bas)], 12: [(gauche, droite)], 13: [(haut, droite)],
                     14: [(haut, gauche)]}
            out.extend(table[code])
    return out


def coudre(segs, tol=.51):
    """Recoud des segments en polylignes. Deux bouts à moins de `tol` sont un."""
    clef = lambda p: (round(p[0] / tol), round(p[1] / tol))
    par = {}
    for a, b in segs:
        par.setdefault(clef(a), []).append((a, b))
        par.setdefault(clef(b), []).append((b, a))
    vus = set()
    lignes = []
    for a, b in segs:
        if (a, b) in vus or (b, a) in vus:
            continue
        vus.add((a, b))
        ligne = [a, b]
        # on prolonge par les deux bouts jusqu'à ce que plus rien ne recolle
        for sens in (0, 1):
            while True:
                bout = ligne[-1] if sens == 0 else ligne[0]
                suite = None
                for p, q in par.get(clef(bout), []):
                    if (p, q) in vus or (q, p) in vus:
                        continue
                    suite = (p, q)
                    break
                if not suite:
                    break
                vus.add(suite)
                if sens == 0:
                    ligne.append(suite[1])
                else:
                    ligne.insert(0, suite[1])
        lignes.append(ligne)
    return lignes


def alleger(ligne, eps):
    """Douglas-Peucker, itératif. Une côte relevée au décimètre ne se voit pas.

    UNE BOUCLE FERMÉE EST LE PIÈGE de cet algorithme, et il ne se voit pas : le
    premier et le dernier point sont le même, la corde de référence est donc de
    longueur nulle, toutes les distances valent zéro, et une courbe de niveau
    de 445 points ressort à DEUX — un trait invisible au lieu d'une colline.
    Quand la corde est dégénérée, on mesure donc l'écart au point de départ, ce
    qui rouvre la boucle du bon côté et vaut à tous les étages de la descente.
    """
    if len(ligne) < 3:
        return ligne
    garde = [False] * len(ligne)
    garde[0] = garde[-1] = True
    pile = [(0, len(ligne) - 1)]
    while pile:
        i, j = pile.pop()
        if j <= i + 1:
            continue
        ax, ay = ligne[i]
        bx, by = ligne[j]
        dx, dy = bx - ax, by - ay
        n = math.hypot(dx, dy)
        pire, k = 0., -1
        for m in range(i + 1, j):
            px, py = ligne[m]
            d = (math.hypot(px - ax, py - ay) if n < 1e-9
                 else abs(dy * px - dx * py + bx * ay - by * ax) / n)
            if d > pire:
                pire, k = d, m
        if pire > eps and k > 0:
            garde[k] = True
            pile.append((i, k))
            pile.append((k, j))
    return [p for p, g in zip(ligne, garde) if g]


def chemin(lignes, dec=1, ferme=False):
    """Des polylignes en une seule chaîne `d`."""
    f = "%." + str(dec) + "f"
    bouts = []
    for l in lignes:
        if len(l) < 2:
            continue
        d = "M" + f % l[0][0] + " " + f % l[0][1]
        for x, y in l[1:]:
            d += "L" + f % x + " " + f % y
        bouts.append(d + ("Z" if ferme else ""))
    return "".join(bouts)


# ---------------------------------------------------------------------------
# Les voies — le graphe des rues, chaîné
#
# 18 314 arêtes tracées une par une font 18 314 `M…L…` : le double du dessin
# utile. On les recoud en chemins continus par classe, ce qui divise par cinq
# et donne en prime des courbes lissables.
# ---------------------------------------------------------------------------
def voies(rues):
    noeuds = rues["noeuds"]
    par_classe = {}
    for a in rues["aretes"]:
        p, q = noeuds.get(a["de"]), noeuds.get(a["vers"])
        if not p or not q:
            continue
        par_classe.setdefault(a.get("g") or "rue", []).append(
            ((p[0], p[1]), (q[0], q[1])))
    out = {}
    for g, segs in par_classe.items():
        lignes = coudre(segs, tol=.6)
        out[g] = chemin(lignes)
    return out


# ---------------------------------------------------------------------------
# Le bâti — 48 377 rectangles orientés
#
# Chaque bâtiment a son cap : on tourne la façade, on ne pose pas un carré
# aligné sur le nord. C'est ce qui fait qu'une ville engendrée par ses rues
# RESSEMBLE à une ville et pas à un damier — les maisons suivent la courbe de
# la voie devant elles.
#
# Deux corrections se font ICI, dans le four, et jamais au navigateur : il ne
# sait pas ce qu'est une rue et il n'a pas le temps de le chercher.
#
#   1. LE CAP SE REDRESSE SUR LA VOIE. Le semis a donné à chaque maison un cap
#      approché ; à la relecture, beaucoup de façades regardent de travers la
#      rue qui passe devant leur porte. On cherche donc le segment de voie le
#      plus proche de la PORTE (pas du centre : c'est la porte qui donne sur la
#      rue) et l'on aligne la façade dessus. Passé RAYON_VOIE, on ne touche à
#      rien : mieux vaut une maison telle qu'elle a été semée qu'une maison
#      tournée vers une rue qui n'est pas la sienne.
#
#   2. CE QUI SE CHEVAUCHE NE MONTRE QUE SA SILHOUETTE. Le bâti est semé, et
#      les rectangles se recouvrent par milliers. Tracés un par un, on voit
#      leurs contours intérieurs se croiser : une bouillie de traits au lieu
#      d'un pâté de maisons. On unit donc les rectangles qui se recouvrent —
#      voir `souder`.
# ---------------------------------------------------------------------------

# Au-delà, la voie la plus proche n'est plus « la rue devant chez soi ».
RAYON_VOIE = 25.

# La largeur des voies par classe, en mètres — la même table qu'à la
# génération (`monde/<x>.graph.json`), redite ici parce que `rues.json` ne
# garde que la classe. Sans elle, on ne sait pas où finit la chaussée, et l'on
# pose les maisons dedans.
LARGEUR_VOIE = {"artere": 8.0, "rue": 4.2, "ruelle": 2.3, "escalier": 3.0,
                "quai": 6.0, "abord": 4.0}

# Ce qui reste entre la chaussée et la façade. Une artère a de quoi laisser
# passer un banc et un étal ; une ruelle n'a rien du tout.
TROTTOIR = {"artere": 1.5, "rue": 1.0, "quai": 1.5, "abord": 1.0,
            "ruelle": 0.5, "escalier": 0.4}

# On ne pousse pas une maison à l'autre bout de son îlot : passé ce
# déplacement PERPENDICULAIRE, c'est que la voie trouvée n'est pas la sienne.
# On la laisse alors où elle a été semée, et l'on se contente de la tourner.
RECUL_MAX = 8.0

# LA MITOYENNETÉ SE DÉCLENCHE À LA DENSITÉ, jamais partout. On mesure, par
# tronçon de rue et par côté, ce que les façades occupent de sa longueur. Aux
# deux cinquièmes, on est dans un pâté de maisons : les murs se touchent, et
# c'est ainsi que se bâtit une ville qui n'a plus de place. En dessous, on est
# dans un faubourg : les maisons gardent leur écart, et les serrer serait un
# mensonge sur ce qu'on peut passer entre elles.
#
# LE CHIFFRE A ÉTÉ BALAYÉ, pas choisi. Il valait deux tiers ; on a mesuré, à
# chaque seuil, combien de maisons finissent avec un vrai mur partagé et de
# combien on déplace le semis pour l'obtenir :
#
#     seuil   maisons avec mur   déplacement médian
#      0,62        36 %               3,56 m
#      0,50        38 %               4,49 m
#      0,40        39 %               4,96 m      ← ici
#      0,30        40 %               5,20 m
#      0,10        40 %               5,28 m      (plus rien à gagner)
#
# La courbe se couche à 0,30 : en dessous, on déplace des maisons pour rien.
# On s'arrête juste avant, là où les trois points gagnés valent encore le mètre
# et demi de déplacement qu'ils coûtent.
DENSITE_MITOYENNE = 0.40
MITOYENS_MIN = 3

# JUSQU'OÙ ON RECTIFIE — et ce réglage n'est pas un confort, c'est la ligne de
# partage avec le semis.
#
# Rectifier ici ne corrige QUE le plan 2D. `bati.json` n'est pas touché, et il
# est lu tel quel par la ville en volume (`ecrans/modules/monde/bati.js`,
# `scripts/monde/batir.py`) et surtout par `densifier.py`, qui déduit de
# l'emprise des bâtiments les cours, les porches et les entrées. Déplacer les
# maisons ici et pas là-bas, c'est deux villes au lieu d'une : un front de rue
# continu sur la carte, et des porches qui donnent ailleurs. Le jeu se sert des
# deux vues, donc ça se voit.
#
# Trois crans, du plus au moins interventionniste :
#   "plein"  — sens, recul, ligne de front, mitoyenneté, dégagement. À tenir
#              tant que le semis n'a pas été refait : c'est la seule correction.
#   "filet"  — sens et dégagement seuls. Le bon cran QUAND LE SEMIS EST PROPRE :
#              on ne repose plus rien, on rattrape juste ce qui traîne encore
#              dans la chaussée.
#   "aucun"  — le sens de la façade, et rien d'autre. Les silhouettes par
#              catégorie restent, elles : c'est du rendu, sans équivalent amont.
RECTIFICATION = "plein"

# Ce qui ne se met jamais en rang, quelle que soit la densité : un septuaire ne
# partage pas son mur avec l'échoppe d'à côté.
SANS_MITOYENNETE = {"institution", "culte", "civique"}

# La maille des index spatiaux, en mètres. Assez large pour qu'un bâtiment ou
# une arête tienne dans quelques cases, assez fine pour que les cases ne
# contiennent pas la moitié du quartier.
MAILLE = 40.

# Le pas auquel on colle les bouts de segments avant de les recoudre. Deux
# intersections calculées des deux côtés diffèrent au milliardième ; collées au
# demi-décimètre, elles deviennent le même point et l'anneau se referme.
COLLE = .05

# Combien de bâtiments ont été semés, pour le dire à la fin en regard du nombre
# de silhouettes qu'ils ont fini par faire. Un compteur et pas une clef de la
# sortie : le plan servi au client garde exactement la forme qu'il attend.
COMPTE = [0]

# Où chaque maison a fini par se poser, et lesquelles un monument a avalées.
# `bati()` le sait — il redresse la ville entière contre ses rues — et
# `enseignes()` en a besoin pour poser sa marque sur la porte REDRESSÉE et non
# sur celle du semis, qui est ailleurs de plusieurs mètres. Rectifier deux fois
# coûterait la moitié de la cuisson ; on garde donc le résultat au passage,
# comme COMPTE, et pour la même raison : ce n'est pas une clef de la sortie.
POSES = [None, frozenset()]

# --- la mitoyenneté, telle qu'elle a été RÉSOLUE ---------------------------
# `_mitoyenner` range les façades d'un front bord à bord. Deux choses en
# sortent, dont le dessin a besoin et que les colonnes du semis ne portent pas :
#
#   LARGEURS  la façade EFFECTIVE de chaque maison. Quand un front est plus
#             chargé que long, on ne peut pas y mettre tout le monde à sa
#             largeur : on comprime, au prorata. C'était la seule autre issue —
#             l'ancienne était de les répartir à égalité EN LES LAISSANT SE
#             RECOUVRIR, en comptant sur la soudure pour n'en faire qu'un front.
#             Or `souder` refuse de fondre deux propriétaires (« c'est la
#             mitoyenneté, pas une raison de n'en faire qu'une »), et refuse
#             avec raison. Les deux passes se contredisaient, et le résultat
#             était vingt-trois mille maisons qui se traversaient.
#
#   COLLES    de quel côté chaque maison a un voisin au contact — (gauche,
#             droite) dans son repère local. C'est ce qui permet au dessin de
#             garder le MUR MITOYEN DROIT : un pan coupé, un trapèze ou un
#             pignon de guingois sur un mur qu'on partage, ce n'est pas une
#             maison de plus, c'est un trou entre deux maisons.
LARGEURS = [{}]
COLLES = [{}]

# Les formes qui rongent le flanc : on les interdit du côté d'un mur partagé.
# Les autres (pleine, té, équerre, cour, croix) gardent leurs bords x = ±f
# francs sur tout ou partie de la profondeur — c'est-à-dire un vrai mur mitoyen.
RONGENT_LE_FLANC = ("angle", "trapeze", "biais")


def _index_voies(rues):
    """Les arêtes de rue, en grille, avec leur cap. Pour chercher la plus proche."""
    noeuds = rues["noeuds"]
    segs, grille = [], {}
    for a in rues["aretes"]:
        p, q = noeuds.get(a["de"]), noeuds.get(a["vers"])
        if not p or not q:
            continue
        dx, dy = q[0] - p[0], q[1] - p[1]
        if dx * dx + dy * dy < 1e-9:
            continue
        k = len(segs)
        segs.append((p[0], p[1], q[0], q[1], math.degrees(math.atan2(dy, dx)),
                     a.get("g") or "ruelle", math.hypot(dx, dy)))
        for i in range(int(min(p[0], q[0]) // MAILLE), int(max(p[0], q[0]) // MAILLE) + 1):
            for j in range(int(min(p[1], q[1]) // MAILLE), int(max(p[1], q[1]) // MAILLE) + 1):
                grille.setdefault((i, j), []).append(k)
    return segs, grille


# ---------------------------------------------------------------------------
# LES TRONÇONS SE RECHAÎNENT EN RUES — sans quoi il n'y a pas de front
# ---------------------------------------------------------------------------
# Un front de rue, c'est une RUE, pas un morceau de graphe. Or `rues.json` en
# compte QUARANTE-CINQ MILLE CENT CINQUANTE ET UN pour une ville de cinq
# kilomètres sur trois et demi : `portes.py` coupe chaque arête de surface à
# l'abscisse de chacune de ses portes — c'est ce qu'il doit faire, une porte
# donne sur la rue devant elle — et `coudre.py` en fait autant aux entrées et
# aux porches. Ce qui reste est un confetti par maison.
#
# CE QUE ÇA COÛTAIT, mesuré : groupés par tronçon, 33 049 fronts sur 38 575 ne
# portaient QU'UNE SEULE maison, et 8,4 % du bâti seulement atteignait les trois
# maisons qu'exige `MITOYENS_MIN`. La mitoyenneté ne pouvait donc pas se
# produire : elle n'avait pas de rue où se produire. Ce n'était pas un seuil mal
# réglé, c'était la clef de regroupement.
#
# ON RECHAÎNE DONC AVANT DE GROUPER. Deux tronçons se suivent quand ils se
# touchent à un nœud où RIEN D'AUTRE n'aboutit (un vrai carrefour en a trois),
# qu'ils sont de la même classe, et que la rue ne casse pas d'angle. Une chaîne
# est alors une rue au sens où un passant l'entend : une longueur, un côté, un
# rang de façades.
#
# Ça ne déplace rien tout seul : chaque maison reste posée sur SON tronçon, avec
# le cap de ce tronçon-là — une rue qui tourne garde ses maisons qui tournent.
# Seuls le GROUPEMENT et l'abscisse changent d'échelle.
ANGLE_CHAINE = 30.       # au-delà, ce n'est plus la même rue mais un tournant


def _chainer(segs):
    """Recoud les tronçons en rues. Rend de quoi passer de l'un à l'autre.

    `par_seg[e]` = (chaîne, offset du tronçon dans la chaîne, sens ±1) ;
    `longueur[c]`, `classe[c]` ; `situer(c, S)` rend (tronçon, abscisse locale).
    """
    # Qui aboutit où. Les coordonnées de `rues.json` sont écrites au décimètre :
    # la clef est donc exacte, comme dans `journee.js`.
    clef = lambda x, y: (round(x * 10), round(y * 10))
    bouts = {}
    for e, (x1, y1, x2, y2, cap, g, lg) in enumerate(segs):
        bouts.setdefault(clef(x1, y1), []).append((e, 0))
        bouts.setdefault(clef(x2, y2), []).append((e, 1))

    def suivant(e, bout):
        """Le tronçon qui prolonge `e` par ce bout-là, ou None."""
        x1, y1, x2, y2, cap, g, lg = segs[e]
        n = clef(x2, y2) if bout == 1 else clef(x1, y1)
        ici = bouts.get(n, ())
        if len(ici) != 2:            # un carrefour, un cul-de-sac : la rue s'arrête
            return None
        f, bf = ici[0] if ici[0][0] != e else ici[1]
        if f == e or segs[f][5] != g:
            return None
        # L'angle se mesure dans le SENS DE PARCOURS : le tronçon suivant est
        # pris à l'endroit s'il nous présente son début, à l'envers sinon.
        cf = segs[f][4] + (180. if bf == 1 else 0.)
        ce = cap + (180. if bout == 0 else 0.)
        if abs((cf - ce + 180.) % 360. - 180.) > ANGLE_CHAINE:
            return None
        return f, bf

    par_seg, longueur, classe, ordre = {}, {}, {}, {}
    cid = 0
    for e0 in range(len(segs)):
        if e0 in par_seg:
            continue
        # Remonter jusqu'au début de la rue, puis la parcourir d'un bout à
        # l'autre. On garde une garde de boucle : une rue en anneau (ça existe,
        # une place ronde) se refermerait sinon sur elle-même sans fin.
        debut, sens, vus = e0, 1, {e0}
        while True:
            pr = suivant(debut, 0 if sens > 0 else 1)
            if pr is None:
                break
            f, bf = pr
            if f in vus:
                break
            vus.add(f)
            # On arrive par le bout `bf` de `f` : il se parcourt donc vers
            # l'autre bout, c'est-à-dire à l'endroit si l'on est entré par sa
            # fin, à l'envers si l'on est entré par son début.
            debut, sens = f, (1 if bf == 1 else -1)
        suite, off = [], 0.
        e, s = debut, sens
        vus = set()
        while e is not None and e not in vus:
            vus.add(e)
            par_seg[e] = (cid, off, s)
            suite.append((off, e))
            off += segs[e][6]
            nx = suivant(e, 1 if s > 0 else 0)
            if nx is None:
                break
            f, bf = nx
            e, s = f, (1 if bf == 0 else -1)
        longueur[cid] = off
        classe[cid] = segs[debut][5]
        ordre[cid] = suite
        cid += 1

    def situer(c, S):
        suite = ordre[c]
        S = min(max(S, 0.), longueur[c])
        lo, hi = 0, len(suite) - 1
        while lo < hi:                       # le dernier tronçon dont l'offset ≤ S
            mi = (lo + hi + 1) // 2
            if suite[mi][0] <= S:
                lo = mi
            else:
                hi = mi - 1
        off, e = suite[lo]
        lg = segs[e][6]
        d = min(max(S - off, 0.), lg)
        return e, (d if par_seg[e][2] > 0 else lg - d)

    return {"par_seg": par_seg, "longueur": longueur, "classe": classe,
            "ordre": ordre, "situer": situer, "n": cid}


def _ligne_de_front(ch, segs, cid, cote, bord):
    """La polyligne des FAÇADES : l'axe de la rue décalé de `bord`, d'un côté.

    POURQUOI ELLE EXISTE, ET C'EST TOUT LE SUJET. On rangeait les maisons bord à
    bord SUR L'AXE de la rue — des abscisses contiguës sur la ligne médiane —,
    puis on les dessinait cinq à quinze mètres plus loin, chacune décalée le
    long de la normale de SON tronçon. Or deux voisines de rang tombent souvent
    sur deux tronçons différents : mesuré, trois degrés et demi d'écart d'angle
    en médiane, et trois mètres vingt-neuf d'écart entre les deux. Des abscisses
    contiguës sur l'axe ne sont plus contiguës une fois décalées — elles ne le
    restent que sur une rue droite. D'où vingt et un pour cent de murs mitoyens
    là où l'on en déclarait cinquante-huit.

    On range donc sur la ligne où les maisons se touchent VRAIMENT : celle de
    leurs façades. Deux voisines y partagent un mur par construction, courbe
    comprise.

    L'ONGLET EST PLAFONNÉ. Dans un virage serré, la ligne décalée du côté
    intérieur se replie sur elle-même et le point d'onglet part à l'infini :
    on borne son allongement, quitte à mordre un peu dans le coin. Un carrefour
    n'est de toute façon pas un endroit où l'on bâtit au cordeau.
    """
    axe = []
    for _off, e in ch["ordre"][cid]:
        x1, y1, x2, y2, _cap, _g, _lg = segs[e]
        a, b = (((x1, y1), (x2, y2)) if ch["par_seg"][e][2] > 0
                else ((x2, y2), (x1, y1)))
        if not axe:
            axe.append(a)
        if abs(b[0] - axe[-1][0]) > 1e-9 or abs(b[1] - axe[-1][1]) > 1e-9:
            axe.append(b)
    if len(axe) < 2:
        return None

    dirs = []
    for i in range(len(axe) - 1):
        dx, dy = axe[i + 1][0] - axe[i][0], axe[i + 1][1] - axe[i][1]
        L = math.hypot(dx, dy)
        dirs.append((dx / L, dy / L) if L > 1e-9
                    else (dirs[-1] if dirs else (1., 0.)))

    def normale(u):
        return (-u[1] * cote, u[0] * cote)

    pts = []
    for i, p in enumerate(axe):
        if i == 0:
            n, k = normale(dirs[0]), 1.
        elif i == len(axe) - 1:
            n, k = normale(dirs[-1]), 1.
        else:
            a, b = normale(dirs[i - 1]), normale(dirs[i])
            mx, my = a[0] + b[0], a[1] + b[1]
            L = math.hypot(mx, my)
            if L < 1e-6:                       # demi-tour : pas d'onglet possible
                n, k = a, 1.
            else:
                n = (mx / L, my / L)
                k = 1. / max(n[0] * a[0] + n[1] * a[1], .35)
        pts.append((p[0] + n[0] * bord * k, p[1] + n[1] * bord * k))

    cum = [0.]
    for i in range(len(pts) - 1):
        cum.append(cum[-1] + math.hypot(pts[i + 1][0] - pts[i][0],
                                        pts[i + 1][1] - pts[i][1]))
    return pts, cum


def _sur_ligne(pts, cum, t):
    """Le point et la direction locale, à l'abscisse curviligne `t`."""
    t = min(max(t, 0.), cum[-1])
    lo, hi = 0, len(cum) - 2
    while lo < hi:
        mi = (lo + hi + 1) // 2
        if cum[mi] <= t:
            lo = mi
        else:
            hi = mi - 1
    L = cum[lo + 1] - cum[lo]
    dx = pts[lo + 1][0] - pts[lo][0]
    dy = pts[lo + 1][1] - pts[lo][1]
    if L < 1e-9:
        return pts[lo], (1., 0.)
    q = (t - cum[lo]) / L
    return (pts[lo][0] + dx * q, pts[lo][1] + dy * q), (dx / L, dy / L)


def _voie_de_la_porte(px, py, segs, grille):
    """Le tronçon de voie le plus proche du point : (rang, abscisse, côté).

    L'abscisse est en mètres depuis le premier bout du tronçon ; le côté vaut
    +1 ou −1 selon qu'on est à gauche ou à droite du sens de parcours. Ces
    trois chiffres suffisent à reposer la maison contre sa rue.
    """
    meilleur, trouve = RAYON_VOIE ** 2, None
    for i in range(int((px - RAYON_VOIE) // MAILLE), int((px + RAYON_VOIE) // MAILLE) + 1):
        for j in range(int((py - RAYON_VOIE) // MAILLE), int((py + RAYON_VOIE) // MAILLE) + 1):
            for k in grille.get((i, j), ()):
                x1, y1, x2, y2, c, g, lg = segs[k]
                dx, dy = x2 - x1, y2 - y1
                t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
                t = 0. if t < 0 else (1. if t > 1 else t)
                ex, ey = px - (x1 + t * dx), py - (y1 + t * dy)
                d = ex * ex + ey * ey
                if d < meilleur:
                    # Le côté se lit sur le produit en croix ; à cheval sur
                    # l'axe (d ≈ 0) on tranche à gauche, faute de mieux.
                    cote = 1. if (dx * ey - dy * ex) >= 0 else -1.
                    meilleur, trouve = d, (k, t * lg, cote)
    return trouve


def redresser(source, rues):
    """Repose chaque maison contre la voie devant sa porte. Rend (x, y, cap).

    QUATRE GESTES, ET LE SEMIS N'EN FAISAIT AUCUN. Le monde a été engendré par
    la circulation : les maisons sont le long des rues, mais posées de travers,
    à cheval sur la chaussée une fois sur cinq, et à des reculs qui vont de
    moins quatre à plus sept mètres. Un plan comme ça ne se lit pas — l'œil
    cherche la ligne des façades, et il n'y en a pas.

      1. LE DEVANT EST DU CÔTÉ DE LA PORTE. On oriente le cap modulo 360°, et
         non plus 180° : tant que tout était rectangulaire, se tromper de sens
         ne se voyait pas ; depuis que les silhouettes ont un devant et un
         derrière (voir `_pieces`), une maison sur deux ouvrait sa cour sur la
         rue et présentait son mur aveugle au jardin.
      2. ON SORT DE LA CHAUSSÉE. La façade se pose à `demi-largeur de la voie
         + trottoir`, largeur lue sur la classe. Passé RECUL_MAX, on ne pousse
         pas : la voie trouvée n'est pas la sienne.
      3. UNE SEULE LIGNE DE FRONT PAR TRONÇON. Toutes les maisons d'un même
         côté d'un même tronçon prennent le MÊME recul. C'est ce geste-là qui
         fait qu'un îlot se lit comme un îlot.
      4. ET, PASSÉ UNE DENSITÉ, LES MURS SE TOUCHENT. Voir `_mitoyenner`.

    ON NE TOUCHE PAS À `bati.json`. Les lieux du jeu sont attachés aux
    bâtiments PAR LEUR RANG (voir `scripts/affecter.py`) : rebâtir le semis
    casserait toutes les affectations. On rectifie ici, à la cuisson du plan,
    et le rang de chacun ne bouge pas d'une ligne.
    """
    col = source["_colonnes"]
    icap = col.index("cap")
    ix, iy = col.index("x"), col.index("y")
    ifa, ipr, icat = col.index("facade_m"), col.index("profondeur_m"), col.index("cat")
    poses = [[r[ix], r[iy], r[icap] or 0.] for r in source["bati"]]
    # On repart à vide : une seconde cuisson dans le même processus (les essais,
    # `--rectifier` comparé) hériterait sinon des mitoyennetés de la première.
    LARGEURS[0], COLLES[0] = {}, {}
    # PAS DE PORTE SUR RUE, PAS DE REDRESSEMENT. Tout ce qui suit part du côté
    # où la maison ouvre : sans cette colonne, on ne sait pas de quel côté est
    # son devant, et la « rectifier » reviendrait à la faire pivoter au hasard.
    # Un semis qui n'a pas de porte est un semis qui a été posé à la main
    # (Peyredragon, soixante-sept maisons) : il borde déjà sa rue, on le laisse
    # où il est. Le plan se cuit, simplement sans cette passe-là.
    if "porte_x" not in col or "porte_y" not in col:
        print("  bâti sans porte sur rue : le semis est posé tel quel, "
              "sans redressement")
        return poses
    ipx, ipy = col.index("porte_x"), col.index("porte_y")
    segs, grille = _index_voies(rues)
    ch = _chainer(segs)

    fronts = {}                       # (rue, côté) → les maisons qui y donnent
    orphelins = 0
    for k, r in enumerate(source["bati"]):
        px, py = r[ipx], r[ipy]
        if px is None or py is None:  # pas de porte : on se rabat sur le corps
            px, py = r[ix], r[iy]
        vu = _voie_de_la_porte(px, py, segs, grille)
        if vu is None:
            orphelins += 1
            continue
        e, s, cote = vu
        # DE QUEL CÔTÉ EST LA MAISON — pas de quel côté est la PORTE. La porte
        # est posée SUR l'axe de la chaussée (un centimètre de médiane, mesuré) :
        # le produit vectoriel qui décide du côté y vaut zéro, et son signe est
        # alors un tirage au sort — `_voie_de_la_porte` le dit elle-même, « on
        # tranche à gauche, faute de mieux ». Quatre maisons sur dix se
        # retrouvaient dos à la rue pour cette seule raison. Le corps, lui, est
        # franchement d'un côté : c'est lui qu'on interroge.
        ax, ay, bx, by, _cp, _cl, lg_ = segs[e]
        ex, ey = (bx - ax) / lg_, (by - ay) / lg_
        # `nx, ny = -uy*cote, ux*cote` est la normale QUI S'ÉLOIGNE de la rue :
        # le corps doit s'y projeter positivement, d'où ce signe-ci et pas
        # l'autre.
        cote = 1. if ((r[iy] - ay) * ex - (r[ix] - ax) * ey) >= 0 else -1.
        # ON GROUPE PAR RUE, PAS PAR TRONÇON. Le côté et l'abscisse passent dans
        # le repère de la CHAÎNE : un tronçon pris à l'envers a sa gauche du
        # côté droit de la rue, et l'oublier mêlerait les deux fronts.
        cid, off, sens = ch["par_seg"][e]
        S = off + (s if sens > 0 else lg_ - s)
        fronts.setdefault((cid, cote * sens), []).append((k, S))

    tournes = deplaces = mitoyens = 0
    somme = 0.
    for (cid, cote), gens in fronts.items():
        lg = ch["longueur"][cid]
        classe = ch["classe"][cid]
        bord = LARGEUR_VOIE.get(classe, 2.3) / 2. + TROTTOIR.get(classe, .5)

        # LA LIGNE OÙ ILS SE TOUCHENT. On range sur la façade, pas sur l'axe —
        # voir `_ligne_de_front`. Sa longueur n'est pas celle de l'axe (plus
        # longue à l'extérieur d'un virage, plus courte à l'intérieur), et c'est
        # elle qui décide combien de maisons tiennent dans le front.
        front = (_ligne_de_front(ch, segs, cid, cote, bord)
                 if RECTIFICATION == "plein" else None)
        if front is not None:
            fpts, fcum = front
            lgf = fcum[-1]
            # Les abscisses du semis sont comptées sur l'axe : on les reporte au
            # prorata sur la façade, sinon le rang partirait d'un bout.
            gensf = [(k, s * lgf / lg if lg > 1e-9 else s) for k, s in gens]
        else:
            fpts = fcum = None
            lgf, gensf = lg, gens

        abscisses = (_mitoyenner(source, gensf, lgf, ifa, icat)
                     if RECTIFICATION == "plein" else None)
        range_ = abscisses is not None
        if range_:
            mitoyens += len(gens)
            # « Gauche » et « droite » se lisent dans le repère de la maison, et
            # le cap vaut la direction du front FOIS LE CÔTÉ : d'un côté de la
            # rue, l'ordre des abscisses est celui du repère local ; de l'autre,
            # il est inversé. Sans ce retournement, on interdit le pan coupé du
            # mauvais bord et l'équerre s'adosse au vide.
            if cote < 0:
                for k in abscisses:
                    if k in COLLES[0]:
                        g, d = COLLES[0][k]
                        COLLES[0][k] = (d, g)
        else:
            abscisses = {k: s for k, s in gensf}

        for k, _ in gens:
            # --- la pose sur la ligne de façade -----------------------------
            if fpts is not None:
                r = source["bati"][k]
                (fx, fy), (wx, wy) = _sur_ligne(fpts, fcum, abscisses[k])
                nx, ny = -wy * cote, wx * cote     # la normale qui s'éloigne
                neuf = math.degrees(math.atan2(wy * cote, wx * cote))
                cx = fx + nx * (r[ipr] or 4) / 2.
                cy = fy + ny * (r[ipr] or 4) / 2.
                somme += abs((neuf - poses[k][2] + 90.) % 180. - 90.)
                tournes += 1
                # LE GARDE-FOU NE S'APPLIQUE PAS DANS UN RANG, et c'est la
                # dernière pièce du puzzle. `RECUL_MAX` existe pour ne pas
                # déraciner une maison vers une rue qui n'est pas la sienne — un
                # doute qui a un sens quand on la déplace seule. Dans un front
                # RANGÉ, le doute est levé : le test de densité a établi que ces
                # maisons-là forment un pâté, et l'ordre du rang est celui du
                # semis. Laisser sur place les trente pour cent que le plafond
                # refusait, c'était trouer chaque rangée — mesuré, quarante-cinq
                # pour cent des paires de voisines seulement avaient bougé
                # toutes les deux, et le mur mitoyen n'existait que pour
                # celles-là. Là où les deux bougent, l'écart médian est nul.
                if range_ or abs((poses[k][0] - fx) * nx +
                                 (poses[k][1] - fy) * ny
                                 - (r[ipr] or 4) / 2.) <= RECUL_MAX:
                    poses[k] = [cx, cy, neuf]
                    deplaces += 1
                else:
                    poses[k][2] = neuf
                continue
            # --- l'ancien chemin, pour `aucun` et `filet` -------------------
            r = source["bati"][k]
            # De l'abscisse de RUE au tronçon qui la porte : c'est là qu'une
            # maison serrée contre sa voisine peut glisser dans le tronçon d'à
            # côté — elle ne quitte pas sa rue pour autant.
            e, s = ch["situer"](cid, abscisses[k])
            x1, y1, x2, y2, cap, _cl, lg_e = segs[e]
            c = cote * ch["par_seg"][e][2]      # le côté vu du tronçon
            ux, uy = (x2 - x1) / lg_e, (y2 - y1) / lg_e
            nx, ny = -uy * c, ux * c            # la normale qui s'éloigne de la rue
            # 3. la ligne de front est celle des FAÇADES, pas celle des centres :
            # chacune recule de sa propre demi-profondeur derrière le même bord.
            # Un recul commun aux centres remettrait les grosses dans la rue, ou
            # creuserait un trou devant les petites.
            recul = bord + (r[ipr] or 4) / 2.
            cx = x1 + ux * s + nx * recul
            cy = y1 + uy * s + ny * recul
            # Le cap : la façade suit la rue, et la PROFONDEUR s'éloigne d'elle
            # — c'est-à-dire que l'axe local des y vaut la normale sortante.
            neuf = math.degrees(math.atan2(uy * c, ux * c))
            somme += abs((neuf - poses[k][2] + 90.) % 180. - 90.)
            tournes += 1
            # ON NE PLAFONNE QUE LE MOUVEMENT PERPENDICULAIRE. Le long de la
            # rue, une maison peut glisser tant qu'elle veut — c'est le rang
            # qui se serre, et il ne quitte pas la rue. En travers, passé
            # RECUL_MAX, la voie trouvée n'est pas la sienne : on la tourne
            # sans la déraciner.
            # Et l'on mesure le déplacement de la FAÇADE, pas celui du centre :
            # une halle de vingt-six mètres de fond dont la façade est déjà
            # bonne n'a rien à corriger, alors que son centre, lui, est loin.
            ecx, ecy = poses[k][0] - x1, poses[k][1] - y1
            if RECTIFICATION != "plein":
                poses[k][2] = neuf          # le sens, et rien de plus
            elif abs((ecx * nx + ecy * ny) - (r[ipr] or 4) / 2. - bord) <= RECUL_MAX:
                poses[k] = [cx, cy, neuf]
                deplaces += 1
            else:
                poses[k][2] = neuf

    # L'ORDRE COMPTE, ET IL EST CELUI-CI. On démêle d'abord — sinon `_degager`
    # sort du pavé des maisons encore encastrées les unes dans les autres, et il
    # les y remet en les poussant. On dégage ensuite, parce que la rue est plus
    # sacrée que l'écart entre deux murs : une maison dans la chaussée se voit,
    # dix centimètres de mur partagé non. Puis on redémêle une fois, pour
    # reprendre le peu que le dégagement a réenchevêtré.
    meles = 0
    if RECTIFICATION == "plein":
        _desenchevetrer(source, poses, ifa, ipr)
    degages = (_degager(source, poses, segs, grille, ifa, ipr)
               if RECTIFICATION in ("plein", "filet") else 0)
    if RECTIFICATION == "plein":
        # HUIT PASSES, ET LE CHIFFRE EST MESURÉ. La séparation converge
        # géométriquement — 15 900 paires après le dégagement, 13 900 à deux
        # passes, 11 000 à quatre, 7 900 à six —, et chaque passe coûte six
        # dixièmes de seconde sur quarante-cinq mille maisons. On s'arrête là où
        # la médiane passe sous le décimètre : en dessous, on déplace des
        # maisons pour un défaut qu'aucune échelle du plan ne rend.
        meles = _desenchevetrer(source, poses, ifa, ipr, passes=8)
    print("  voirie %d tronçons rechaînés en %d rues, %d fronts"
          % (len(segs), ch["n"], len(fronts)))
    print("  bati %d/%d façades alignées, %d reposées, %d mitoyennes, "
          "%d dégagées, %d sans voie, écart moyen %.1f°"
          % (tournes, len(poses), deplaces, mitoyens, degages, orphelins,
             somme / tournes if tournes else 0.))
    print("  chevauchements restants : %d paires" % meles)
    return poses


def _desenchevetrer(source, poses, ifa, ipr, passes=4):
    """Sépare les maisons qui se traversent — celles que la ROTATION a mêlées.

    LE RANG NE SUFFIT PAS, ET C'EST LA MESURE QUI LE DIT. Ranger les façades
    bord à bord (`_mitoyenner`) règle le front, et le front seulement : de
    vingt-trois mille paisqui se traversaient on tombe à vingt mille. Le reste
    ne vient pas du rang, il vient du geste d'avant — on TOURNE chaque maison
    pour la mettre face à sa rue, vingt-six degrés en moyenne, et une maison
    qu'on fait pivoter sur son centre entre dans ses voisines. Le semis, lui,
    était propre : vingt et un centimètres de pénétration maximale sur
    quarante-cinq mille maisons. Tout le mal est né du redressement.

    Deux maisons mêlées ne sont jamais sur le même front — celles-là se
    touchent exactement, et un contact n'est pas un chevauchement. Ce sont les
    maisons de COIN, et les maisons DOS À DOS de deux rues parallèles : chacune
    a été alignée sur sa rue à elle, sans que personne regarde l'autre.

    ON ÉCARTE, ON NE TOURNE PAS. Le cap vient d'être calculé et il est juste :
    la façade suit sa rue. On pousse donc chacune de la moitié de ce qui les
    sépare, le long de l'axe le plus court — celui qui coûte le moins de
    mouvement. Quelques passes suffisent : écarter deux maisons peut en toucher
    une troisième, mais l'enchevêtrement est peu profond et ça converge.

    Ce qui reste après ces passes est du chevauchement PROFOND — une halle et
    une masure qu'on ne peut pas séparer sans en jeter une hors de sa rue. On
    les laisse, on les compte, et on le dit.
    """
    R = source["bati"]
    n = len(poses)
    dem = [((R[k][ifa] or 4) / 2., (R[k][ipr] or 4) / 2.) for k in range(n)]
    for k in range(n):
        if k in LARGEURS[0]:
            dem[k] = (LARGEURS[0][k] / 2., dem[k][1])

    def quad(k):
        x, y, cap = poses[k]
        a = math.radians(cap)
        ca, sa = math.cos(a), math.sin(a)
        hf, hp = dem[k]
        return [(x + dx * ca - dy * sa, y + dx * sa + dy * ca)
                for dx, dy in ((-hf, -hp), (hf, -hp), (hf, hp), (-hf, hp))]

    def separer(A, B):
        """L'axe et la profondeur du chevauchement, ou None s'ils sont libres."""
        best, axe = 1e9, None
        for poly in (A, B):
            for i in range(4):
                x1, y1 = poly[i]
                x2, y2 = poly[(i + 1) % 4]
                nx, ny = -(y2 - y1), (x2 - x1)
                L = math.hypot(nx, ny)
                if L < 1e-9:
                    continue
                nx /= L
                ny /= L
                pa = [px * nx + py * ny for px, py in A]
                pb = [px * nx + py * ny for px, py in B]
                o = min(max(pa), max(pb)) - max(min(pa), min(pb))
                if o <= 0.:
                    return None
                if o < best:
                    best, axe = o, (nx, ny)
        return best, axe

    # UNE PASSE DE PLUS, QUI NE POUSSE PAS. Sans elle, on rend le compte tel
    # qu'il était AU DÉBUT de la dernière passe — c'est-à-dire avant la dernière
    # correction —, et le chiffre imprimé est faux d'un tiers. Le tour à vide
    # coûte trois dixièmes de seconde et dit la vérité.
    MAILLE_S = 24.
    reste = 0
    for tour in range(passes + 1):
        dernier = (tour == passes)
        qs = [quad(k) for k in range(n)]
        bb = [(min(p[0] for p in q), min(p[1] for p in q),
               max(p[0] for p in q), max(p[1] for p in q)) for q in qs]
        g = {}
        for k, (x0, y0, x1, y1) in enumerate(bb):
            for i in range(int(x0 // MAILLE_S), int(x1 // MAILLE_S) + 1):
                for j in range(int(y0 // MAILLE_S), int(y1 // MAILLE_S) + 1):
                    g.setdefault((i, j), []).append(k)
        pousse = [[0., 0.] for _ in range(n)]
        vus = set()
        reste = 0
        for ks in g.values():
            for u in range(len(ks)):
                for v in range(u + 1, len(ks)):
                    a, b = (ks[u], ks[v]) if ks[u] < ks[v] else (ks[v], ks[u])
                    if (a, b) in vus:
                        continue
                    vus.add((a, b))
                    A, B = bb[a], bb[b]
                    if A[2] < B[0] or B[2] < A[0] or A[3] < B[1] or B[3] < A[1]:
                        continue
                    s = separer(qs[a], qs[b])
                    if s is None:
                        continue
                    prof, (nx, ny) = s
                    reste += 1
                    # Le sens : de A vers B, lu sur les centres. Sans ce test on
                    # les pousse une fois sur deux l'une DANS l'autre.
                    dx = poses[b][0] - poses[a][0]
                    dy = poses[b][1] - poses[a][1]
                    if dx * nx + dy * ny < 0:
                        nx, ny = -nx, -ny
                    # UNE MAISON DE RANG NE BOUGE PAS, et c'est ce qui décide
                    # s'il y aura des murs. Deux fronts qui se font dos ont des
                    # maisons qui se traversent ; les écarter toutes deux, c'est
                    # tirer chacune hors de sa rangée, et la rangée était le
                    # seul endroit où un mur mitoyen existait. Mesuré : en
                    # poussant tout le monde, on retombait à vingt-sept pour
                    # cent de murs. Celle qui est dans un rang tient donc sa
                    # place, et c'est l'autre qui s'écarte — de tout l'écart.
                    ra, rb = a in COLLES[0], b in COLLES[0]
                    if ra and rb:
                        continue          # deux rangs : on n'y touche pas
                    h = prof + 0.02 if (ra or rb) else prof / 2. + 0.02
                    if not ra:
                        pousse[a][0] -= nx * h
                        pousse[a][1] -= ny * h
                    if not rb:
                        pousse[b][0] += nx * h
                        pousse[b][1] += ny * h
        if not reste or dernier:
            break
        # ON PLAFONNE LE PAS. Une maison prise entre trois voisines reçoit trois
        # poussées qui s'additionnent, et elle part à l'autre bout de l'îlot au
        # premier tour. Un mètre par passe, et la convergence fait le reste.
        for k in range(n):
            px, py = pousse[k]
            L = math.hypot(px, py)
            if L < 1e-9:
                continue
            if L > 1.:
                px, py = px / L, py / L
            poses[k][0] += px
            poses[k][1] += py
    return reste


def _degager(source, poses, segs, grille, ifa, ipr, passes=3):
    """Sort du pavé ce qui reste dedans, une fois les fronts alignés.

    ALIGNER SUR SA RUE MET DANS CELLE D'À CÔTÉ. Une maison de coin qu'on
    repousse pour dégager la rue des Sœurs vient se planter dans la ruelle qui
    la croise ; une maison qu'on serre contre ses voisines glisse dans le
    carrefour. Le front ne se calcule que par rapport à UN tronçon, et il n'y a
    pas moyen de traiter tous les tronçons à la fois sans écrire un solveur.

    On finit donc par une relaxation, qui est courte et qui suffit : on sonde
    le pourtour de chaque bâtiment, on mesure ce qui trempe dans une chaussée,
    et l'on pousse d'autant, perpendiculairement à la voie qui déborde. Trois
    passes, deux mètres au plus par passe — au-delà, on préfère une maison qui
    mord la ruelle à une maison qui a traversé son îlot.
    """
    n = 0
    for _ in range(passes):
        bouge = 0
        for k, (x, y, cap) in enumerate(poses):
            r = source["bati"][k]
            f, p = (r[ifa] or 4) / 2., (r[ipr] or 4) / 2.
            a = math.radians(cap)
            ca, sa = math.cos(a), math.sin(a)
            pire, vx, vy = 0., 0., 0.
            for dx, dy in ((-f, -p), (f, -p), (f, p), (-f, p), (0, -p), (0, p),
                           (-f, 0), (f, 0), (0, 0)):
                px = x + dx * ca - dy * sa
                py = y + dx * sa + dy * ca
                for i in range(int((px - 10) // MAILLE), int((px + 10) // MAILLE) + 1):
                    for j in range(int((py - 10) // MAILLE), int((py + 10) // MAILLE) + 1):
                        for e in grille.get((i, j), ()):
                            x1, y1, x2, y2, cp, cl, lg = segs[e]
                            ux, uy = (x2 - x1) / lg, (y2 - y1) / lg
                            t = (px - x1) * ux + (py - y1) * uy
                            t = 0. if t < 0 else (lg if t > lg else t)
                            ex, ey = px - (x1 + t * ux), py - (y1 + t * uy)
                            d = math.hypot(ex, ey)
                            creux = LARGEUR_VOIE.get(cl, 2.3) / 2. - d
                            if creux > pire:
                                if d < 1e-6:      # pile sur l'axe : on sort de côté
                                    ex, ey, d = -uy, ux, 1.
                                pire, vx, vy = creux, ex / d, ey / d
            if pire <= .05:
                continue
            pas = min(pire + .1, 2.)
            poses[k][0] = x + vx * pas
            poses[k][1] = y + vy * pas
            bouge += 1
        n = max(n, bouge)
        if not bouge:
            break
    return n


def _mitoyenner(source, gens, lg, ifa, icat):
    """Met en rang les façades d'un même front, si le front est assez plein.

    Rend les abscisses serrées, ou None quand le tronçon n'est pas assez dense
    pour qu'on ait le droit d'y coller les maisons.

    LA DENSITÉ TRANCHE, PAS LE GOÛT. Un front dont les façades occupent les
    deux tiers de la longueur est un pâté de maisons : dans une ville sans
    place, on bâtit contre le mur du voisin, et les trous d'un mètre et demi
    qu'a laissés le semis n'existent nulle part. En dessous du seuil, c'est un
    faubourg, et l'écart entre deux maisons est une vraie ruelle qu'on peut
    prendre — la serrer serait mentir sur ce qui se passe.

    On garde L'ORDRE du semis le long de la rue : personne ne double son
    voisin, et une maison affectée à un lieu du jeu reste chez elle.
    """
    if len(gens) < MITOYENS_MIN:
        return None
    largeurs = {k: (source["bati"][k][ifa] or 4) for k, _ in gens}
    if any(source["bati"][k][icat] in SANS_MITOYENNETE for k, _ in gens):
        return None
    total = sum(largeurs.values())
    if total / lg < DENSITE_MITOYENNE:
        return None
    ordre = sorted(gens, key=lambda ks: ks[1])
    out = {}

    # COMBIEN DE PLACE CHACUN A DROIT. Ça rentre, ou ça ne rentre pas — et dans
    # le second cas on COMPRIME au prorata au lieu de laisser les murs se
    # traverser. Une rue trop chargée fait des maisons étroites ; c'est ce que
    # fait une vraie ville sans place, et c'est la seule réponse qui laisse un
    # front continu SANS demander à la soudure de fondre deux propriétaires.
    serre = min(1., lg / total)
    prises = {k: largeurs[k] * serre for k, _ in ordre}

    depart = (0. if serre < 1. else
              min(max((sum(s for _, s in ordre) / len(ordre)) - total / 2., 0.),
                  lg - total))
    c = depart
    for k, _ in ordre:
        out[k] = c + prises[k] / 2.
        c += prises[k]

    # Ce que le dessin doit savoir et que le semis ne dit pas : la largeur
    # retenue, et de quel côté on touche. Le premier du rang n'a personne à sa
    # gauche, le dernier personne à sa droite — et « gauche » est ici le sens
    # des abscisses croissantes du front, qui est aussi celui du repère local
    # une fois la maison tournée face à sa rue.
    for i, (k, _) in enumerate(ordre):
        LARGEURS[0][k] = prises[k]
        COLLES[0][k] = (i > 0, i < len(ordre) - 1)
    return out


def _dedans(px, py, poly, marge=1e-6):
    """Le point est-il STRICTEMENT dans le convexe ?

    Le bâti n'est plus fait de rectangles seuls (voir `_pieces`) : on teste donc
    un convexe quelconque, par le signe des produits en croix. Le sens de
    parcours n'est pas garanti le même partout — on le lit sur le premier bord
    qui tranche plutôt que de le supposer.
    """
    n = len(poly)
    signe = 0
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        lg = math.hypot(dx, dy)
        if lg < 1e-12:
            continue
        d = (dx * (py - y1) - dy * (px - x1)) / lg
        if abs(d) <= marge:
            return False
        s = 1 if d > 0 else -1
        if signe == 0:
            signe = s
        elif s != signe:
            return False
    return signe != 0


# --- la forme d'une maison -------------------------------------------------
# Le bâti brut ne dit qu'un centre, un cap, une façade et une profondeur : un
# rectangle, et quarante-huit mille rectangles font un damier qu'on lit comme
# du papier peint. On en tire donc une SILHOUETTE, tirée au sort mais toujours
# la même pour un bâtiment donné (le tirage sort de son rang).
#
# DEUX RÈGLES QUI NE SE NÉGOCIENT PAS :
#   • tout tient DANS le rectangle d'origine — une aile qui déborde, c'est une
#     maison dans la rue, et le plan ment sur ce qu'on peut y passer ;
#   • chaque morceau reste CONVEXE, parce que la soudure des silhouettes
#     (`souder`) ne sait recouper que des convexes. Une équerre se fabrique en
#     posant deux morceaux qui se recouvrent : l'union s'en charge toute seule.

def _melange(k):
    """Un petit générateur déterministe : même rang, même maison, toujours."""
    z = (k * 2654435761 + 1013904223) & 0xFFFFFFFF

    def suivant(a=0., b=1.):
        nonlocal z
        z = (z * 1664525 + 1013904223) & 0xFFFFFFFF
        return a + (b - a) * (z / 4294967296.)
    return suivant


def _quad(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# CHAQUE MÉTIER A SA FORME, et c'est le vrai intérêt de la chose : un plan où
# tout se ressemble ne dit rien, un plan où les cours d'artisans se voient dit
# le quartier avant qu'on ait lu son nom. Les poids, par catégorie de bâti :
#
#   pleine   le rectangle nu
#   angle    un ou deux angles abattus
#   trapeze  façade plus étroite (ou plus large) que l'arrière
#   biais    le pignon de guingois, sur une parcelle en coin
#   equerre  corps sur rue + aile en retour — la maison de ville ordinaire
#   te       corps sur rue + appentis au fond
#   cour     deux ailes et un corps : l'union creuse un U
#   croix    nef et transept — les septuaires, et rien d'autre
FORMES = {
    "habitat":     {"pleine": 34, "angle":  7, "trapeze":  5, "biais":  7,
                    "equerre": 27, "te": 15, "cour":  5, "croix": 0},
    "commerce":    {"pleine": 42, "angle":  6, "trapeze": 13, "biais": 10,
                    "equerre": 20, "te":  9, "cour":  0, "croix": 0},
    "artisanat":   {"pleine": 24, "angle":  4, "trapeze":  4, "biais":  6,
                    "equerre": 26, "te": 20, "cour": 16, "croix": 0},
    "nuisance":    {"pleine": 40, "angle":  3, "trapeze":  6, "biais": 11,
                    "equerre": 18, "te": 18, "cour":  4, "croix": 0},
    "service":     {"pleine": 38, "angle":  5, "trapeze":  6, "biais":  8,
                    "equerre": 21, "te": 16, "cour":  6, "croix": 0},
    "plaisir":     {"pleine": 26, "angle": 12, "trapeze":  8, "biais": 16,
                    "equerre": 22, "te": 12, "cour":  4, "croix": 0},
    "civique":     {"pleine": 20, "angle": 18, "trapeze":  6, "biais":  2,
                    "equerre": 22, "te":  7, "cour": 25, "croix": 0},
    "institution": {"pleine": 12, "angle": 18, "trapeze":  4, "biais":  0,
                    "equerre": 20, "te":  6, "cour": 40, "croix": 0},
    "culte":       {"pleine":  8, "angle": 22, "trapeze":  8, "biais":  0,
                    "equerre":  8, "te":  9, "cour": 10, "croix": 35},
}


def _annexes(f, p, ann, mur=0.):
    """Ce que la maison a pris autour d'elle : remise au fond, appentis aux flancs.

    SEULS MORCEAUX AUTORISÉS À SORTIR DU RECTANGLE, et c'est assumé : la règle
    « tout tient dans le gabarit » existe parce qu'une aile qui déborde est une
    maison dans la rue. Ici, le débord a été MESURÉ contre le sol libre par
    `scripts/monde/annexes.py`, chaussée comprise, avec son jour de dégagement.
    Ce n'est donc plus une aile qui déborde, c'est un fond de parcelle qu'on
    occupe — et c'est ce qui manquait au tissu : un cœur d'îlot ne reste pas nu.

    Le devant (y = -p) n'est jamais touché : le front de rue garde sa ligne.
    """
    fo, g, d = ann
    # ELLES MORDENT SUR LE PARENT, ET C'EST NÉCESSAIRE. Posées bord à bord elles
    # le TOUCHENT sans le RECOUVRIR, et `_croisent` exige un recouvrement : la
    # soudure les laissait donc à part, cinquante-quatre mille silhouettes pour
    # quarante-six mille maisons. Quarante centimètres de chevauchement, et
    # l'annexe redevient ce qu'elle est — un morceau de la maison.
    M = 0.4
    out = []
    if fo > 0.:
        if fo <= 7.:
            # Petite remise adossée : on garde un passage de côté.
            out.append(_quad(-f*0.82, f*0.82, p - M*2.5, p + fo))
        else:
            # Une longue prise n'est pas un hangar plein. C'est une aile de
            # service qui longe une arrière-cour et rejoint un fond de cour :
            # on densifie l'îlot tout en gardant une cour commune lisible.
            aile = max(1.6, min(3.2, f*0.42))
            gauche = g <= d
            if gauche:
                out.append(_quad(-f*0.82, -f*0.82 + aile,
                                 p - M*2.5, p + fo))
            else:
                out.append(_quad(f*0.82 - aile, f*0.82,
                                 p - M*2.5, p + fo))
            fond = min(4.8, max(2.8, fo*0.28))
            out.append(_quad(-f*0.82, f*0.82,
                             p + fo - fond, p + fo))
    if g > 0.:
        out.append(_quad(-f - g, -f + M*2.5, -p*0.72, p))
    if d > 0.:
        out.append(_quad(f - M*2.5, f + d, -p*0.72, p))
    # LE MUR DE CLÔTURE, sur la ligne de façade et donc parallèle à la voirie :
    # il part du bord droit et va rejoindre la maison suivante. Fin et long,
    # c'est tout ce qu'il est — mais c'est lui qui referme la cour sur la rue,
    # et un front de rue continu est ce qui fait qu'on lit un couloir plutôt
    # qu'une file de maisons posées. Il ne se dessine qu'À DROITE : l'autre
    # moitié de l'intervalle appartient au voisin, qui a le sien.
    if mur > 0.:
        # IL PART DU MILIEU, PAS DU BORD. Mordre de quarante centimètres sur le
        # coin ne suffit pas : les silhouettes en `angle`, `trapeze` ou `biais`
        # ont justement ce coin COUPÉ, parfois de trois mètres — le mur les
        # touchait sans les recouvrir, donc la soudure le laissait à part et
        # l'on comptait quatre cent cinquante silhouettes de trop. Depuis l'axe
        # de la maison, on est toujours dans le plein du corps ; la portion qui
        # passe sous la maison ne se voit pas, l'union l'avale.
        out.append(_quad(0., f + mur, -p, -p + 0.6))
    return out


def _pieces(f, p, k, cat, ann=(0., 0., 0.), mur=0., colle=(False, False)):
    """Les morceaux convexes d'un bâtiment, en repère local (façade sur x).

    Rend une liste de polygones inscrits dans [-f, f] × [-p, p], plus les
    ANNEXES qui, elles, en sortent (voir `_annexes`). Un seul morceau pour les
    formes pleines, deux ou trois pour les équerres et les cours — l'union s'en
    charge, et elle recoud aussi les annexes puisqu'elles appartiennent au même
    bâtiment.

    LE MUR QU'ON PARTAGE RESTE DROIT. `colle` dit de quel côté il y a un voisin
    au contact. De ce côté-là, deux choses sont interdites : les formes qui
    rongent le flanc (pan coupé, trapèze, biais), parce qu'un mur mitoyen taillé
    en biseau ouvre un vide entre deux maisons qui sont censées se toucher ; et
    l'appentis de flanc, qui s'en irait dans la maison d'à côté. Ce n'est pas un
    raffinement de dessin : sans ça, ranger les façades bord à bord ne suffit
    pas — on aligne les centres et les murs continuent de se croiser.
    """
    cg, cd = colle
    # L'appentis de flanc ne sort que du côté libre. Le fond, lui, ne gêne
    # personne : il donne sur le cœur d'îlot.
    sup = _annexes(f, p, (ann[0], 0. if cg else ann[1], 0. if cd else ann[2]), mur)
    d = _melange(k)
    # Une cabane de quatre mètres n'a pas d'aile en retour : on ne découpe que
    # ce qui est assez grand pour que la découpe se voie.
    if f < 3. or p < 3.:
        return [_quad(-f, f, -p, p)] + sup
    poids = FORMES.get(cat) or FORMES["habitat"]
    if cg or cd:
        poids = {n: v for n, v in poids.items() if n not in RONGENT_LE_FLANC}
        if not poids:
            poids = {"pleine": 1.}
    # Une cour ou une croix demandent de la place : sur une petite parcelle on
    # les rend au rectangle plutôt que de fabriquer des slivers illisibles.
    petit = f < 7. or p < 7.
    t = d(0., float(sum(v for c, v in poids.items()
                        if not (petit and c in ("cour", "croix")))))
    forme = "pleine"
    for nom, v in poids.items():
        if petit and nom in ("cour", "croix"):
            continue
        t -= v
        if t < 0:
            forme = nom
            break

    if forme == "angle":                          # un ou deux angles abattus
        c = min(f, p) * d(.28, .55)
        if d() < .5:
            return [[(-f + c, -p), (f - c, -p), (f, -p + c), (f, p),
                     (-f, p), (-f, -p + c)]] + sup
        return [[(-f + c, -p), (f - c, -p), (f, -p + c), (f, p - c),
                 (f - c, p), (-f + c, p), (-f, p - c), (-f, -p + c)]] + sup
    if forme == "trapeze":                        # façade et arrière inégaux
        s = d(.62, .88)
        if d() < .35:
            return [[(-f, -p), (f, -p), (f * s, p), (-f * s, p)]] + sup
        return [[(-f * s, -p), (f * s, -p), (f, p), (-f, p)]] + sup
    if forme == "biais":                          # le pignon de guingois
        b = f * d(.12, .3)
        return [[(-f + b, -p), (f, -p), (f - b, p), (-f, p)]] + sup
    if forme == "equerre":                        # corps sur rue + aile en retour
        g = d(.42, .62)                           # profondeur du corps sur rue
        w = d(.34, .54)                           # largeur de l'aile
        corps = _quad(-f, f, -p, -p + 2 * p * g)
        # L'AILE VA CONTRE LE VOISIN, quand il n'y en a qu'un : c'est de ce
        # côté-là qu'un mur plein sur toute la profondeur a un sens, et c'est
        # ainsi qu'on bâtit — on s'adosse au mur qui est déjà debout. Adossée du
        # mauvais côté, l'équerre laisse un renfoncement sur le mur partagé et
        # un pignon nu sur la cour.
        gauche = cg if cg != cd else d() < .5
        if gauche:
            return [corps, _quad(-f, -f + 2 * f * w, -p, p)] + sup
        return [corps, _quad(f - 2 * f * w, f, -p, p)] + sup
    if forme == "te":                             # corps sur rue + appentis au fond
        g = d(.4, .58)
        w = d(.3, .5)
        m = d(-.25, .25) * f                      # l'appentis n'est pas centré
        return [_quad(-f, f, -p, -p + 2 * p * g),
                _quad(max(-f, m - f * w), min(f, m + f * w), -p, p)] + sup
    if forme == "cour":                           # deux ailes et un corps
        g = d(.34, .5)
        w = d(.26, .38)
        return [_quad(-f, f, -p, -p + 2 * p * g),
                _quad(-f, -f + 2 * f * w, -p, p),
                _quad(f - 2 * f * w, f, -p, p)] + sup
    if forme == "croix":                          # nef et transept : un septuaire
        n = d(.26, .4)                            # demi-largeur de la nef
        b = d(.2, .34)                            # demi-profondeur du transept
        c = min(d(.4, .8) * f * n, p * .5)        # l'abside, en biseau au fond
        m = d(-.15, .15) * p                      # le transept n'est pas au milieu
        nef = [(-f * n, -p), (f * n, -p), (f * n, p - c), (f * n - c, p),
               (-f * n + c, p), (-f * n, p - c)]
        return [nef, _quad(-f, f, m - p * b, m + p * b)] + sup
    return [_quad(-f, f, -p, p)] + sup            # pleine


def souder(coins, vois, ks):
    """Le contour extérieur d'un paquet de rectangles qui se recouvrent.

    POURQUOI PAS UNE UNION DE POLYGONES. `shapely` n'est pas là, et une union
    générale écrite à la main est longue et lente. Or le cas est plus simple
    que le cas général : on n'a que des rectangles, et un point du bord de la
    silhouette est exactement un point de bord d'un rectangle qui n'est dans
    aucun autre. On découpe donc chaque arête aux endroits où elle croise les
    voisines, on jette les morceaux qui tombent dedans, et l'on recoud le reste
    avec `coudre` — le même recousage que le trait de côte. Le tracé reste net,
    au trait, sans l'escalier qu'aurait donné une rasterisation.
    """
    gardes = []
    for k in ks:
        quad = coins[k]
        for e in range(len(quad)):
            x1, y1 = quad[e]
            x2, y2 = quad[(e + 1) % len(quad)]
            dx, dy = x2 - x1, y2 - y1
            coupes = [0., 1.]
            for v in vois[k]:                # les voisins qui la recouvrent
                autre = coins[v]
                for g in range(len(autre)):
                    x3, y3 = autre[g]
                    x4, y4 = autre[(g + 1) % len(autre)]
                    ex, ey = x4 - x3, y4 - y3
                    det = dx * ey - dy * ex
                    if abs(det) < 1e-12:
                        continue
                    t = ((x3 - x1) * ey - (y3 - y1) * ex) / det
                    u = ((x3 - x1) * dy - (y3 - y1) * dx) / det
                    if 0. < t < 1. and 0. <= u <= 1.:
                        coupes.append(t)
            coupes.sort()
            for a, b in zip(coupes, coupes[1:]):
                if b - a < 1e-9:
                    continue
                m = (a + b) / 2.
                mx, my = x1 + m * dx, y1 + m * dy
                if any(_dedans(mx, my, coins[v]) for v in vois[k]):
                    continue
                pa = (round((x1 + a * dx) / COLLE) * COLLE, round((y1 + a * dy) / COLLE) * COLLE)
                pb = (round((x1 + b * dx) / COLLE) * COLLE, round((y1 + b * dy) / COLLE) * COLLE)
                if pa != pb:
                    gardes.append((pa, pb))
    # Un « anneau » de deux points est un éclat de bord long de rien, coincé
    # entre deux découpes : invisible au dessin, et un Z de plus dans le fichier.
    return [l for l in coudre(gardes, tol=COLLE) if len(l) > 2]


# --- les monuments ---------------------------------------------------------
# UN MONUMENT N'EST PAS UNE MAISON PLUS GRANDE. Le semis leur a donné les cotes
# du tout-venant — la Fosse aux Dragons faisait 6,9 m sur 11, le Donjon Rouge
# neuf cabanes de onze mètres —, et une silhouette tirée au sort par-dessus ne
# répare rien : à cette échelle, la Fosse était un grain de ville comme les
# quarante-huit mille autres. Leur emprise s'écrit donc À LA MAIN, dans
# `monde/<x>.monuments.json`, en mètres et en repère local.
#
# ON NE TOUCHE PAS À `bati.json`, pour la même raison que `redresser` n'y
# touche pas : les lieux du jeu sont attachés aux RANGS de ce fichier, et le
# monde en volume le lit tel quel. La correction se fait ici, au four, et elle
# ne concerne que le plan 2D.
#
# ET LE MONUMENT MANGE SON SOL. Le semis a bâti jusque sur la crête de Rhaenys ;
# laisser deux cents taudis dessinés à l'intérieur de la coupole serait un plan
# qui ment sur ce qu'on peut y passer. Tout bâtiment dont le centre tombe dans
# l'emprise (ou à `degage_m` d'elle) est donc RETIRÉ DU PLAN — et les rangs de
# son propre usage avec, puisque l'emprise les remplace.

def _sens(poly):
    """+1 si le contour tourne dans le sens trigonométrique, -1 sinon."""
    a = 0.
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        a += x1 * y2 - x2 * y1
    return 1 if a >= 0 else -1


def _dedans_large(px, py, poly, marge):
    """Dans le convexe, ou à moins de `marge` de son bord."""
    s = _sens(poly)
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        dx, dy = x2 - x1, y2 - y1
        lg = math.hypot(dx, dy)
        if lg < 1e-12:
            continue
        if s * (dx * (py - y1) - dy * (px - x1)) / lg < -marge:
            return False
    return True


# --- l'enceinte et ses sept portes ------------------------------------------
# ON NE LA REDESSINE PAS : elle est tracée depuis toujours dans la carte
# d'origine, `etat/villes/port-real.json`, et c'est déjà d'elle que `batir.py`
# tire la courtine en volume. La reprendre ici est la seule façon d'avoir LE
# MÊME MUR en plan et en relief — un rempart dessiné deux fois est un rempart
# qui finit par passer à deux endroits.
#
# LA COURTINE NE S'INTERROMPT PAS AUX PORTES. La carte laisse un vide de deux
# cents mètres à chaque porte — c'est un schéma, et le schéma marque l'entrée en
# écartant le trait. Sur un plan métré ce vide serait un mensonge : on passerait
# la muraille de Port-Réal sur deux cents mètres de front, ce qui n'est ni un
# rempart ni un jeu. Le trait court donc en circuit fermé, et la porte se dit
# par ce qui la dit vraiment : DEUX TOURS qui flanquent un passage de huit
# mètres, au milieu du tronçon.
MUR_E = 6.0        # l'épaisseur de la courtine, en mètres — la même que batir.py
PORTE_L = 8.0      # la largeur du passage charretier
PORTE_R = 9.0      # le rayon des tours qui le flanquent
CARTE_MU = 12.0    # mètres par unité de la carte d'origine (graph.echelle)


def _du_plan(p):
    """Un point de la carte d'origine, en mètres. Même transformation que
    `batir.py` : l'axe y de la carte descend, celui du monde monte."""
    return (p[0] * CARTE_MU, (300 - p[1]) * CARTE_MU)


def region_port_real(lieu):
    """La couronne régionale qui relie le plan urbain au royaume.

    Elle ne régénère ni le bâti ni ses adresses : elle apporte seulement les
    invariants qui manquaient au recul — côte continue, routes d'approche,
    campagnes, bourgs et ouvrages portuaires. La même source est consommable
    par la carte du royaume ; le plan 2D n'en cuit ici que la projection SVG.
    """
    if lieu != "port-real":
        return None
    chem = os.path.join(RACINE, "scripts", "ville", "port-real-region.json")
    if not os.path.exists(chem):
        return None
    with open(chem, encoding="utf-8") as f:
        src = json.load(f)

    # La première esquisse portait douze ovales écrits à la main. Dès que le
    # champ physique régional existe, ses isolignes les remplacent : une
    # courbe doit désormais sortir d'une altitude mesurable, jamais suggérer
    # vaguement une bosse que le moteur ne connaîtrait pas.
    relief_cuit = None
    terrain_meta = None
    chem_relief = os.path.join(RACINE, "monde", "portreal.region-terrain.json")
    if os.path.exists(chem_relief):
        with open(chem_relief, encoding="utf-8") as f:
            tr = json.load(f)
        niveaux_region = (src.get("topographie") or {}).get("niveaux_m") or NIVEAUX
        tx0, ty0 = float(tr.get("x0_m", 0)), float(tr.get("y0_m", 0))
        tres = float(tr["res_m"])
        coeur = [0., 0., 440. * CARTE_MU, 300. * CARTE_MU]
        relief_cuit = []
        for z in niveaux_region:
            segs = segments(tr["z"], tr["nx"], tr["ny"], z, tres)
            # Le cœur possède ses propres isolignes à 10 m. On coupe la couche
            # régionale une maille avant lui pour qu'aucun double trait ne
            # fabrique une fausse terrasse contre la muraille.
            traduits = []
            for a, b in segs:
                a = (a[0] + tx0, a[1] + ty0)
                b = (b[0] + tx0, b[1] + ty0)
                mx, my = (a[0] + b[0]) / 2., (a[1] + b[1]) / 2.
                if coeur[0] - tres <= mx <= coeur[2] + tres and \
                        coeur[1] - tres <= my <= coeur[3] + tres:
                    continue
                traduits.append((a, b))
            lignes = [alleger(l, 18.) for l in coudre(traduits)
                      if len(l) > 3]
            if lignes:
                relief_cuit.append({"z": z, "d": chemin(lignes, dec=1)})
        terrain_meta = {k: tr.get(k) for k in
                        ("x0_m", "y0_m", "res_m", "nx", "ny", "bornes_m",
                         "statistiques")}
        terrain_meta["source"] = "/monde/terrain-region"

    # L'occupation rurale est une sortie dérivée distincte : le relief peut
    # ainsi être corrigé sans mêler à son autorité les parcelles, les fermes
    # et les chemins que cette correction rend possibles ou impossibles.
    occupation = None
    chem_occupation = os.path.join(
        RACINE, "monde", "portreal.region-occupation.json")
    if os.path.exists(chem_occupation):
        with open(chem_occupation, encoding="utf-8") as f:
            occupation = json.load(f)

    def ligne(points, ferme=False):
        return chemin([[_du_plan(p) for p in points]], dec=1, ferme=ferme)

    def courbe(points, ferme=False):
        """Catmull-Rom converti en Bézier : les chemins suivent le terrain.

        Les routes régionales n'ont aucune raison d'être des cordes tendues
        entre deux portes. Les quais restent rectilignes, mais les chemins et
        les limites de culture passent par une interpolation douce et stable.
        """
        pts = [_du_plan(p) for p in points]
        if len(pts) < 3:
            return ligne(points, ferme)
        n = len(pts)
        if ferme:
            depart, tours = pts[0], n
        else:
            depart, tours = pts[0], n - 1
        d = "M%.1f %.1f" % depart
        for i in range(tours):
            i1 = i % n
            i2 = (i + 1) % n
            p0 = pts[(i - 1) % n] if ferme or i > 0 else pts[i1]
            p1, p2 = pts[i1], pts[i2]
            p3 = pts[(i + 2) % n] if ferme or i + 2 < n else p2
            c1 = (p1[0] + (p2[0] - p0[0]) / 6.,
                  p1[1] + (p2[1] - p0[1]) / 6.)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6.,
                  p2[1] - (p3[1] - p1[1]) / 6.)
            d += ("C%.1f %.1f %.1f %.1f %.1f %.1f" %
                  (c1[0], c1[1], c2[0], c2[1], p2[0], p2[1]))
        return d + ("Z" if ferme else "")

    def semis_regional(lieux, routes):
        """De vrais petits bourgs, pas seulement quatre étiquettes."""
        toits, arbres = [], []
        for l in lieux:
            if l.get("genre") == "gue":
                continue
            graine = sum(ord(c) for c in l["id"]) + 129
            alea = random.Random(graine)
            nombre = {"bourg": 34, "hameau": 13, "relais": 8}.get(l.get("genre"), 8)
            cx, cy = l["point"]
            for i in range(nombre):
                a = alea.random() * math.tau
                rayon = (alea.random() ** .62) * (15 if l.get("genre") == "bourg" else 8)
                x, y = cx + math.cos(a) * rayon, cy + math.sin(a) * rayon * .55
                cap = a * .22 + alea.uniform(-.35, .35)
                lo, la = alea.uniform(1.2, 2.7), alea.uniform(.7, 1.35)
                ux, uy = math.cos(cap), math.sin(cap)
                vx, vy = -uy, ux
                poly = [[x + ux * lo * s + vx * la * t,
                         y + uy * lo * s + vy * la * t]
                        for s, t in ((-1,-1),(1,-1),(1,1),(-1,1))]
                toits.append([_du_plan(p) for p in poly])
        # Fermes-rues et relais secondaires : un chemin n'est crédible que
        # s'il dessert quelque chose. On en pose peu, en retrait, jamais comme
        # un ruban urbain continu autour de la capitale.
        alea = random.Random(129131)
        for route in routes:
            points = route.get("points", [])
            for i in range(2, len(points) - 1, 3):
                x, y = points[i]
                ax, ay = points[i - 1]
                bx, by = points[i + 1]
                dx, dy = bx - ax, by - ay
                norme = math.hypot(dx, dy) or 1.
                nx, ny = -dy / norme, dx / norme
                cote = -1 if (i + len(route.get("id", ""))) % 2 else 1
                for j in range(1 + (i % 2)):
                    recul = cote * alea.uniform(2.1, 4.4)
                    avance = alea.uniform(-2.2, 2.2) + j * 2.4
                    cx = x + nx * recul + dx / norme * avance
                    cy = y + ny * recul + dy / norme * avance
                    cap = math.atan2(dy, dx) + alea.uniform(-.14, .14)
                    lo, la = alea.uniform(.9, 1.8), alea.uniform(.55, 1.05)
                    ux, uy = math.cos(cap), math.sin(cap)
                    vx, vy = -uy, ux
                    poly = [[cx + ux * lo * s + vx * la * t,
                             cy + uy * lo * s + vy * la * t]
                            for s, t in ((-1,-1),(1,-1),(1,1),(-1,1))]
                    toits.append([_du_plan(p) for p in poly])
        # Un semis de houppiers rend le bois lisible sans le transformer en
        # masse grise. Ils sont volontairement schématiques à cette échelle.
        alea = random.Random(129130)
        for _ in range(95):
            x, y = alea.uniform(315, 485), alea.uniform(-60, -2)
            r = alea.uniform(.8, 1.8)
            arbres.append([_du_plan([x + math.cos(k * math.tau / 6) * r,
                                     y + math.sin(k * math.tau / 6) * r])
                            for k in range(6)])
        return chemin(toits, dec=1, ferme=True), chemin(arbres, dec=1, ferme=True)

    rep = src["repere"]
    coins = [_du_plan([rep[0], rep[1]]), _du_plan([rep[2], rep[3]])]
    bornes = [min(p[0] for p in coins), min(p[1] for p in coins),
              max(p[0] for p in coins), max(p[1] for p in coins)]
    port = src.get("port") or {}
    if occupation:
        bourgs = chemin(occupation.get("batiments", []), dec=1, ferme=True)
        arbres = chemin(occupation.get("arbres", []), dec=1, ferme=True)
        cultures = [
            {"genre": genre,
             "d": chemin(polys, dec=1, ferme=True)}
            for genre, polys in occupation.get("parcelles", {}).items()
            if polys
        ]
        bois_exploites = chemin(occupation.get("bois", []), dec=1, ferme=True)
        chemins_secondaires = [
            {"id": c["id"], "route": c.get("route"),
             "d": chemin([c["points"]], dec=1)}
            for c in occupation.get("chemins", []) if len(c.get("points", [])) > 1
        ]
        occupation_meta = occupation.get("statistiques")
    else:
        # Repli compatible avec les plans cuits avant la génération rurale.
        semis = src.get("semis_legacy") or src
        bourgs, arbres = semis_regional(semis.get("lieux", []),
                                         semis.get("routes", []))
        cultures, bois_exploites, chemins_secondaires = [], "", []
        occupation_meta = None
    eau_polygones = [[_du_plan(p) for p in e["points"]]
                     for e in src.get("eau", [])]
    cadrage = src.get("cadrage_initial") or src["repere"]
    cadrage_coins = [_du_plan([cadrage[0], cadrage[1]]),
                     _du_plan([cadrage[2], cadrage[3]])]
    return {
        "version": src.get("version", 1),
        "orientation": src.get("orientation"),
        "bornes": bornes,
        "cadrage_initial": [min(p[0] for p in cadrage_coins),
                             min(p[1] for p in cadrage_coins),
                             max(p[0] for p in cadrage_coins),
                             max(p[1] for p in cadrage_coins)],
        # Ces sommets crus sont la même autorité que le chemin SVG ci-dessous.
        # Le banc de bataille les interroge hors du raster urbain : la côte
        # visible et la côte infranchissable ne peuvent plus diverger.
        "eau_polygones": eau_polygones,
        "eau": chemin(eau_polygones, dec=1, ferme=True),
        "terrains": [{"genre": t["genre"], "nom": t.get("nom"),
                       "d": courbe(t["points"], True)}
                      for t in src.get("terrains", [])],
        "cultures": cultures,
        "bois_exploites": bois_exploites,
        "relief": relief_cuit if relief_cuit is not None else [
            {"nom": n.get("nom"), "z": n.get("z"),
             "d": courbe(n["points"], True)} for n in src.get("relief", [])],
        "terrain": terrain_meta,
        "routes": [{"id": r["id"], "nom": r["nom"],
                    "destination": r.get("destination"),
                    "d": courbe(r["points"])} for r in src.get("routes", [])],
        "chemins": chemins_secondaires,
        "bourgs": bourgs,
        "arbres": arbres,
        "occupation": occupation_meta,
        "lieux": [dict(l, x=_du_plan(l["point"])[0],
                       y=_du_plan(l["point"])[1]) for l in src.get("lieux", [])],
        "port": {
            "quais": [dict(q, d=ligne(q["points"]))
                       for q in port.get("quais", [])],
            "appontements": [dict(q, d=ligne(q["points"]))
                              for q in port.get("appontements", [])],
            "bassins": [dict(q, d=ligne(q["points"], True))
                        for q in port.get("bassins", [])],
        },
    }


def remparts(lieu):
    """La courtine en polyligne, les portes en tours. Carte absente : rien.

    LA CARTE EST CELLE DU LIEU, et il a fallu qu'on voie un trou dans le mur
    pour s'en apercevoir : le chemin était écrit en dur sur « port-real », de
    sorte que le plan de Peyredragon portait la muraille de Port-Réal — neuf
    kilomètres et demi de courtine et sept portes nommées sur une île qui n'en
    a aucune. Un lieu sans carte de ville n'a pas de rempart dessiné, et c'est
    la bonne réponse : le château de Peyredragon est servi en maillage.
    """
    chem = os.path.join(RACINE, "etat", "villes", lieu + ".json")
    if not os.path.exists(chem):
        print("  rempart  pas de carte de ville pour « %s » : aucune courtine"
              % lieu)
        return {}
    with open(chem, encoding="utf-8") as f:
        murs = [s for s in (json.load(f).get("sol") or [])
                if s.get("genre") == "mur"]
    trace, tours, noms = [], [], []
    for s in murs:
        large = s.get("largeur")
        if large is not None and large != 6:
            continue                      # les grands édifices, pas le mur
        pts = [_du_plan(p) for p in s["points"]]
        trace.append(pts)                 # porte comprise : le circuit se ferme
        if large != 6:
            continue
        # Le châtelet, au milieu du tronçon que la carte a écarté.
        (ax, ay), (bx, by) = pts[0], pts[-1]
        cx, cy = (ax + bx) / 2., (ay + by) / 2.
        lg = math.hypot(bx - ax, by - ay) or 1.
        ux, uy = (bx - ax) / lg, (by - ay) / lg          # le long du mur
        for sens in (-1, 1):
            tx = cx + ux * (PORTE_L / 2. + PORTE_R) * sens
            ty = cy + uy * (PORTE_L / 2. + PORTE_R) * sens
            tours.append([(tx + PORTE_R * math.cos(math.pi * (2 * i + 1) / 8),
                           ty + PORTE_R * math.sin(math.pi * (2 * i + 1) / 8))
                          for i in range(8)])
        noms.append({"nom": s.get("nom") or "Une porte",
                     "x": round(cx, 1), "y": round(cy, 1)})
    if not trace:
        return {}
    print("  rempart  %d tronçons, %.0f m de courtine, %d portes"
          % (len(trace), sum(math.dist(a, b) for l in trace
                             for a, b in zip(l, l[1:])), len(noms)))
    return {"courtine": chemin(trace, dec=1), "epaisseur_m": MUR_E,
            "tours": chemin(tours, dec=1, ferme=True), "portes": noms,
            # Consommé puis retiré par `cuire` : la même boucle est la limite
            # du bâti urbain, pas seulement un trait décoratif.
            "_limite": [p for ligne in trace for p in ligne]}


def _enveloppe(pts):
    """L'enveloppe convexe d'un nuage — la marche de Andrew, sens trigo."""
    p = sorted(set(pts))
    if len(p) < 3:
        return list(p)

    def demi(suite):
        out = []
        for q in suite:
            while len(out) > 1:
                (ax, ay), (bx, by) = out[-2], out[-1]
                if (bx - ax) * (q[1] - ay) - (by - ay) * (q[0] - ax) > 0:
                    break
                out.pop()
            out.append(q)
        return out[:-1]
    return demi(p) + demi(p[::-1])


def monuments(source, poses):
    """Les emprises écrites à la main, posées dans le plan.

    Rend `({usage: [polygones en mètres]}, {rangs avalés})`. Fichier absent ou
    illisible : on ne fait rien et le plan se cuit comme avant.
    """
    chem = os.path.join(RACINE, "monde", PREFIXE[0] + ".monuments.json")
    if not os.path.exists(chem):
        return {}, set()
    with open(chem, encoding="utf-8") as f:
        table = (json.load(f) or {}).get("monuments") or {}
    col = source["_colonnes"]
    iusg = col.index("usage")

    formes, avale = {}, set()
    for usage, m in table.items():
        ax, ay = m["ancre"]
        a = math.radians(m.get("cap") or 0.)
        ca, sa = math.cos(a), math.sin(a)
        pieces = [[(ax + dx * ca - dy * sa, ay + dx * sa + dy * ca)
                   for dx, dy in piece] for piece in m["pieces"]]
        formes[usage] = pieces
        marge = float(m.get("degage_m") or 0.)
        mange = 0
        # UN CHÂTEAU AVALE SA COUR, PAS SEULEMENT SES MURS. Une enceinte est un
        # anneau de morceaux : le vide du milieu n'est couvert par aucun d'eux,
        # et le semis y laisse ses cabanes — quinze taudis dessinés dans la cour
        # du Donjon Rouge, ce qui est pire que pas de château du tout. Avec
        # `avale_enclos`, le test de dégagement se fait sur l'ENVELOPPE de
        # l'emprise ; le dessin, lui, ne change pas et garde sa cour vide.
        garde = ([_enveloppe([q for p in pieces for q in p])]
                 if m.get("avale_enclos") else pieces)
        # La boîte englobante d'abord — quarante-huit mille points contre neuf
        # convexes, autant ne payer le test exact que pour le voisinage.
        xs = [q[0] for p in pieces for q in p]
        ys = [q[1] for p in pieces for q in p]
        bx0, bx1 = min(xs) - marge, max(xs) + marge
        by0, by1 = min(ys) - marge, max(ys) + marge
        for k, r in enumerate(source["bati"]):
            if r[iusg] == usage:
                avale.add(k)                       # l'emprise le remplace
                continue
            x, y = poses[k][0], poses[k][1]
            if x < bx0 or x > bx1 or y < by0 or y > by1:
                continue
            if any(_dedans_large(x, y, p, marge) for p in garde):
                avale.add(k)
                mange += 1
        print("  monument %-20s %2d morceaux, %d bâtiments avalés"
              % (usage, len(pieces), mange))
    return formes, avale


def bati(source, rues, limite=None):
    col = source["_colonnes"]
    ix, iy = col.index("x"), col.index("y")
    ifa, ipr = col.index("facade_m"), col.index("profondeur_m")
    icat, iusg = col.index("cat"), col.index("usage")
    # les annexes sont facultatives : le plan se cuit même sans `annexes.py`
    iaf = col.index("ann_f") if "ann_f" in col else None
    iag = col.index("ann_g") if "ann_g" in col else None
    iad = col.index("ann_d") if "ann_d" in col else None
    imu = col.index("mur_d") if "mur_d" in col else None
    poses = redresser(source, rues)
    COMPTE[0] = len(poses)
    # Le semis historique contient encore des cabanes, entrepôts et tavernes
    # posés comme des excroissances derrière les portes et sur la grève. Tant
    # que les vrais faubourgs ne sont pas construits comme une zone autonome,
    # ces formes ne sont ni une campagne ni la ville : on les retranche de la
    # projection urbaine. La pose rectifiée est l'autorité, car c'est elle qui
    # produit réellement le toit et, plus bas, son obstacle de collision.
    hors = {k for k, p in enumerate(poses)
            if limite and not _dedans(p[0], p[1], limite)}
    mons, avale = monuments(source, poses)
    if limite:
        for usage, pieces in list(mons.items()):
            mons[usage] = [piece for piece in pieces if _dedans(
                sum(x for x, _ in piece) / len(piece),
                sum(y for _, y in piece) / len(piece), limite)]
    POSES[0], POSES[1] = poses, frozenset(avale | hors)
    if hors:
        print("  bati  %d bâtiments extramuros écartés de la ville" % len(hors))

    # Une maison rend un ou plusieurs morceaux convexes (`_pieces`), posés dans
    # le plan par son centre et son cap. Les morceaux d'une même maison se
    # recouvrent : la soudure les rendra comme une seule silhouette.
    # CHAQUE MORCEAU PORTE LE NOM DE SA MAISON. Sans ça, la soudure ne sait pas
    # distinguer les deux morceaux d'une équerre — qu'il FAUT recoudre — des
    # deux maisons mitoyennes d'une même rue, qu'il ne faut surtout pas fondre.
    # Elle fondait les deux, et huit taudis contigus de six mètres sortaient en
    # une dalle de cinquante : la rue cessait de se lire comme une rangée de
    # maisons. Un monument entier compte pour un seul propriétaire, ses
    # morceaux étant un anneau qui doit rester d'une pièce.
    par_cat, par_prop = {}, {}
    # LE MASQUE PART DE CE MÊME DESSIN. Garder une seconde recette ici
    # (les rectangles bruts de `bati.json`) fabriquait deux villes : le plan
    # montrait les maisons redressées, découpées, agrandies de leurs annexes et
    # remplacées par les monuments, tandis que les jambes heurtaient encore le
    # semis d'origine. On garde ci-dessous les CONTOURS FINAUX, après soudure et
    # au décimètre effectivement écrit dans le SVG : dessin et collision
    # reçoivent donc exactement les mêmes sommets.
    emprises = []

    def au_decimetre(piece):
        return [(float("%.1f" % x), float("%.1f" % y)) for x, y in piece]

    for u, pieces in mons.items():
        pieces = [au_decimetre(piece) for piece in pieces]
        par_cat.setdefault(u, []).extend(pieces)
        par_prop.setdefault(u, []).extend([("m", u)] * len(pieces))
    for k, r in enumerate(source["bati"]):
        if k in avale or k in hors:
            continue
        x, y, cap = poses[k]
        a = math.radians(cap)
        ca, sa = math.cos(a), math.sin(a)
        # LA FAÇADE RETENUE EST CELLE DU RANG, pas celle du semis : sur un front
        # plus chargé que long, `_mitoyenner` a comprimé tout le monde au
        # prorata pour que les murs se touchent au lieu de se traverser.
        f = (LARGEURS[0].get(k) or r[ifa] or 4) / 2.
        p = (r[ipr] or 4) / 2.
        colle = COLLES[0].get(k) or (False, False)
        nom = r[icat] or "habitat"
        # La FORME suit la catégorie (une institution a des cours, une cabane
        # non), mais le GROUPE suit le type : c'est lui qui portera la couleur,
        # et la couleur ne peut pas traverser une silhouette soudée.
        u = r[iusg] or nom
        cat = par_cat.setdefault(u, [])
        prop = par_prop.setdefault(u, [])
        ann = ((r[iaf] or 0.), (r[iag] or 0.), (r[iad] or 0.)) if iaf is not None             else (0., 0., 0.)
        mur = (r[imu] or 0.) if imu is not None else 0.
        for piece in _pieces(f, p, k, nom, ann, mur, colle):
            piece = au_decimetre(
                [(x + dx * ca - dy * sa, y + dx * sa + dy * ca)
                 for dx, dy in piece])
            cat.append(piece)
            prop.append(k)

    # On soude PAR TYPE, jamais entre types : deux couches n'ont pas la même
    # teinte, et une silhouette commune devrait choisir laquelle porter. Un
    # taudis mitoyen d'une échoppe garde donc son trait — et c'est juste : ce
    # sont deux maisons, pas un pâté. Et, depuis `par_prop`, un taudis mitoyen
    # d'un TAUDIS garde le sien aussi, ce qui l'est tout autant.
    out = {}
    for cat, coins in par_cat.items():
        prop = par_prop[cat]
        vois = [[] for _ in coins]
        bb = []
        grille = {}
        for k, quad in enumerate(coins):
            xs = [q[0] for q in quad]
            ys = [q[1] for q in quad]
            bb.append((min(xs), min(ys), max(xs), max(ys)))
            for i in range(int(bb[k][0] // MAILLE), int(bb[k][2] // MAILLE) + 1):
                for j in range(int(bb[k][1] // MAILLE), int(bb[k][3] // MAILLE) + 1):
                    grille.setdefault((i, j), []).append(k)
        # Qui recouvre qui : boîtes d'abord (gratuit), puis l'axe séparateur.
        vus = set()
        pere = list(range(len(coins)))

        def racine(z):
            while pere[z] != z:
                pere[z] = pere[pere[z]]
                z = pere[z]
            return z

        for ks in grille.values():
            for u in range(len(ks)):
                for v in range(u + 1, len(ks)):
                    a, b = (ks[u], ks[v]) if ks[u] < ks[v] else (ks[v], ks[u])
                    if (a, b) in vus:
                        continue
                    vus.add((a, b))
                    # deux maisons voisines se touchent : c'est la mitoyenneté,
                    # pas une raison de n'en faire qu'une.
                    if prop[a] != prop[b]:
                        continue
                    A, B = bb[a], bb[b]
                    if A[2] < B[0] or B[2] < A[0] or A[3] < B[1] or B[3] < A[1]:
                        continue
                    if not _croisent(coins[a], coins[b]):
                        continue
                    vois[a].append(b)
                    vois[b].append(a)
                    ra, rb = racine(a), racine(b)
                    if ra != rb:
                        pere[ra] = rb
        paquets = {}
        for k in range(len(coins)):
            paquets.setdefault(racine(k), []).append(k)
        lignes = []
        for ks in paquets.values():
            if len(ks) == 1:                 # seul dans son coin : rien à souder
                lignes.append(coins[ks[0]])
                continue
            lignes.extend(souder(coins, vois, ks))
        # LE DÉCIMÈTRE, ET PAS LE MÈTRE. Le bâti s'écrivait arrondi à l'unité —
        # ce qui était sans conséquence tant que les maisons flottaient, et
        # ruineux depuis qu'on les range bord à bord : un mur mitoyen calé au
        # centimètre voit chacun de ses sommets sauter d'un demi-mètre à
        # l'écriture, et la rue qu'on venait de rendre continue se rouvre en
        # trous d'un mètre. On a mesuré la façade au centimètre pour la perdre
        # à l'impression. Le décimètre coûte quelques centaines de kilo-octets
        # et vaut un demi-pixel à l'échelle la plus serrée du client.
        lignes = [au_decimetre(ligne) for ligne in lignes]
        out[cat] = chemin(lignes, dec=1, ferme=True)
        emprises.extend(lignes)
    return out, emprises


def types(source):
    """Quel type appartient à quelle famille, et combien pèse-t-il.

    Le plan porte trente-sept couches de bâti — une par type — et la carte a
    besoin de savoir laquelle est un artisanat et laquelle un habitat : la
    FAMILLE donne la teinte, le TYPE la clarté. Sans cette table, le dessin
    devrait connaître par cœur ce que le monde a semé, et une taverne de plus
    dans `usages.py` serait une couche muette de plus sur la carte.
    """
    col = source["_colonnes"]
    icat, iusg = col.index("cat"), col.index("usage")
    # Le nom en clair est déjà dans la source (`_types`, écrit par usages.py) :
    # on le recopie plutôt que de le réinventer côté carte. Sans lui, le survol
    # d'une maison rendrait « septuaire-quartier » au lieu de « Septuaire de
    # quartier », et un identifiant n'a rien à faire sous les yeux du joueur.
    noms = source.get("_types") or {}
    n = {}
    for r in source["bati"]:
        u = r[iusg] or r[icat] or "habitat"
        e = n.setdefault(u, {"cat": r[icat] or "habitat", "n": 0,
                             "nom": (noms.get(u) or {}).get("nom") or u})
        # L'enseigne se range AVEC le type, pas dans une table à part : la carte
        # a déjà celle-ci sous la main pour la teinte et le nom au survol, et
        # deux tables qui se répondent finissent toujours par diverger.
        if u in MARQUES:
            e["signe"] = MARQUES[u]
        e["n"] += 1
    # Du plus commun au plus rare : c'est l'ordre du DESSIN, et ce qui est
    # écrit en premier passe dessous. Les trente et un mille maisons font le
    # fond ; les vingt bâtiments d'institution se posent dessus, jamais
    # l'inverse — sinon le seul bureau du maître de port disparaît sous la
    # ville entière.
    return {u: n[u] for u in sorted(n, key=lambda u: -n[u]["n"])}


# --- les enseignes ----------------------------------------------------------
# UNE VILLE OÙ TOUT SE RESSEMBLE NE SE LIT PAS DE PRÈS. Le bâti se colore par
# type, ce qui suffit à voir qu'un pâté n'est pas de l'habitat — mais pas à
# savoir si c'est la forge ou la tannerie, et c'est justement la question qu'on
# se pose quand on approche à trente mètres. On pose donc une marque sur la
# PORTE de chaque bâtiment qui n'est pas un logis.
#
# Sur la porte, et pas au milieu du toit : une enseigne pend sur la rue, du
# côté par où l'on entre. C'est aussi ce qui la rend utile — elle dit d'un coup
# d'œil par quelle venelle on aborde la maison.
#
# ON NE MARQUE PAS LES LOGIS. Trente mille maisons, six mille taudis : les
# marquer, c'est du confetti, et ça noierait les six cent soixante autres qui
# sont tout l'intérêt de la couche. Un logis se lit à sa teinte, comme avant.
LOGIS = {"maison", "taudis", "cabane", "manse", "maison-officier"}

# Ce que porte chaque type. Un type absent de cette table n'a pas d'enseigne —
# c'est le repli, et il est silencieux : une ville qui sème un usage neuf ne
# casse rien, elle n'a simplement pas de marque tant qu'on ne lui en donne pas.
MARQUES = {
    "echoppe": "🪧", "taverne": "🍺", "boulangerie": "🍞", "forge": "🔨",
    "puits": "🪣", "entrepot": "📦", "brasserie": "🛢", "bordel": "🌹",
    "ecurie": "🐎", "auberge": "🛏", "tannerie": "🐄", "chantier-bois": "🪵",
    "septuaire-quartier": "⭐", "teinturerie": "🎨", "etuve": "♨",
    "poterie": "🏺", "abattoir": "🔪", "moulin": "⚙", "fosse-vidange": "🕳",
    "corps-de-garde": "🛡", "marche-quartier": "🧺", "donjon-rouge": "🏰",
    "corderie": "🪢", "change": "🪙", "voilerie": "⛵", "grenier": "🌾",
    "caserne": "⚔", "geole": "⛓", "guilde-alchimistes": "⚗",
    "fosse-dragons": "🐉", "vieux-septuaire": "⭐", "bureau-port": "⚓",
}


def enseignes(source):
    """Où est la porte de chaque bâtiment marquable, par type.

    Rend `{<type>: "x,y x,y …"}` au décimètre — une chaîne plutôt qu'un tableau
    de couples, parce que six mille six cents points en JSON structuré pèsent
    trois fois le même semis écrit en clair, et que le navigateur découpe une
    chaîne aussi vite qu'il lit un tableau.

    LA PORTE SUIT SA MAISON. `redresser` a reposé toute la ville contre ses
    rues : la porte du semis n'est plus devant la façade dessinée. On ramène
    donc la porte dans le repère de sa maison d'origine (son décalage au centre,
    tourné du cap d'origine), puis on la repose avec la pose redressée. Sans ce
    tour, une enseigne sur deux tomberait dans la rue d'à côté.
    """
    col = source["_colonnes"]
    ix, iy, icap = col.index("x"), col.index("y"), col.index("cap")
    ifa, ipr = col.index("facade_m"), col.index("profondeur_m")
    iusg, icat = col.index("usage"), col.index("cat")
    if "porte_x" not in col or "porte_y" not in col:
        return {}
    ipx, ipy = col.index("porte_x"), col.index("porte_y")
    poses, avale = POSES[0], POSES[1]
    out = {}
    for k, r in enumerate(source["bati"]):
        u = r[iusg] or r[icat] or "habitat"
        if u in LOGIS or u not in MARQUES or k in avale:
            continue
        px, py = r[ipx], r[ipy]
        if px is None or py is None:
            continue
        x0, y0, c0 = r[ix], r[iy], math.radians(r[icap] or 0.)
        dx, dy = px - x0, py - y0
        # dans le repère de la maison…
        lx = dx * math.cos(c0) + dy * math.sin(c0)
        ly = -dx * math.sin(c0) + dy * math.cos(c0)
        # LA PORTE DU SEMIS N'EST PAS SUR LE MUR : c'est le point de la RUE où
        # elle débouche, ce que `portes.py` doit faire — une porte donne sur la
        # voie devant elle, et c'est par là qu'on chiffre un itinéraire.
        # Mesuré sur les 6 660 bâtiments marquables : la médiane tombe à 5,7 m
        # au-delà du rectangle, et le neuvième décile à 17 m. Une enseigne
        # posée là flotte au milieu de la chaussée, et dans une venelle elle
        # pend devant la maison d'en face — elle dirait le contraire du vrai.
        #
        # On la ramène donc CONTRE SON MUR : la porte garde son abscisse le
        # long de la façade (c'est bien là qu'on entre), et sa profondeur est
        # ramenée juste en deçà du mur de devant. L'enseigne tombe alors dans
        # la silhouette dessinée, du côté par où l'on aborde la maison.
        f = (r[ifa] or 4) / 2.
        p = (r[ipr] or 4) / 2.
        lx = max(-.7 * f, min(.7 * f, lx))
        ly = (.6 * p) if ly >= 0 else (-.6 * p)
        # …puis dans le repère de la maison redressée.
        x1, y1, c1 = poses[k] if poses else (x0, y0, r[icap] or 0.)
        a = math.radians(c1)
        out.setdefault(u, []).append("%.1f,%.1f" % (
            x1 + lx * math.cos(a) - ly * math.sin(a),
            y1 + lx * math.sin(a) + ly * math.cos(a)))
    return {u: " ".join(v) for u, v in out.items()}


def _croisent(A, B):
    """Deux convexes se recouvrent-ils ? Axe séparateur, sur les quatre normales."""
    for poly in (A, B):
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            ax, ay = y1 - y2, x2 - x1
            a1 = min(ax * q[0] + ay * q[1] for q in A)
            a2 = max(ax * q[0] + ay * q[1] for q in A)
            b1 = min(ax * q[0] + ay * q[1] for q in B)
            b2 = max(ax * q[0] + ay * q[1] for q in B)
            if a2 <= b1 or b2 <= a1:
                return False
    return True


def quartiers(source):
    """Le nom d'un quartier se pose au milieu de ses maisons, pas à son bord."""
    col = source["_colonnes"]
    ix, iy, iq = col.index("x"), col.index("y"), col.index("quartier")
    som = {}
    for r in source["bati"]:
        q = r[iq]
        if not q:
            continue
        s = som.setdefault(q, [0., 0., 0])
        s[0] += r[ix]
        s[1] += r[iy]
        s[2] += 1
    return [{"nom": q, "x": round(s[0] / s[2], 1), "y": round(s[1] / s[2], 1),
             "n": s[2]} for q, s in sorted(som.items(), key=lambda kv: -kv[1][2])]


def reperes(rues):
    out = []
    for nom, cle in rues.get("reperes", {}).items():
        p = rues["noeuds"].get(cle)
        if not p:
            continue
        if cle.split(":")[0].startswith("regard"):
            continue
        out.append({"nom": nom, "x": round(p[0], 1), "y": round(p[1], 1),
                    "genre": cle.split(":")[0]})
    return out


# ---------------------------------------------------------------------------
# LE MASQUE DU BÂTI — pour que personne ne marche jamais dans un mur
# ---------------------------------------------------------------------------
# La foule du plan (`ecrans/modules/foule2d.js`) pose des gens en mètres, et
# rien ne lui dit ce qui est bâti : les attroupements débordaient sur les toits
# et les piétons coupaient à travers les maisons. Aucune règle géométrique ne
# couvre tous les cas — les emprises se chevauchent, une arête de voirie
# traverse une cour, une porte est sur la façade et non devant. Le seul moyen
# d'être CERTAIN est un filet : on cuit une fois l'empreinte au sol de la ville
# et l'on repousse ce qui tombe dessus.
#
# UN BIT PAR MÈTRE CARRÉ. À cette résolution une ruelle de deux mètres reste
# franchissable et une maison ne se dissout pas. Port-Réal fait 5 280 × 3 600
# mètres, soit 19 millions de cases — 19 Mo en octets, 2,4 Mo en bits. C'est
# moins que le plan lui-même, et ça se lit d'un décalage et d'un ET.
#
# On rasterise les MORCEAUX qui ont effectivement produit les silhouettes du
# plan. Ils portent déjà la pose rectifiée, la largeur comprimée des rangs, les
# découpes, les annexes et les monuments qui ont avalé le semis sous eux. Lire à
# nouveau les rectangles de `bati.json` n'est pas une approximation : c'est
# revenir à la ville d'avant la cuisson, donc faire dire deux choses différentes
# au dessin et aux jambes.
MASQUE_PAS = 1.0                 # mètres par case

def masque(emprises, larg_m, haut_m):
    """Rasterise les contours SVG dessinés, au centre des cases."""
    nx = int(larg_m / MASQUE_PAS)
    ny = int(haut_m / MASQUE_PAS)
    bits = bytearray((nx * ny + 7) // 8)
    pose = 0
    for poly in emprises:
        if len(poly) < 3:
            continue
        ys = [p[1] for p in poly]
        # Une case appartient au bâti si son CENTRE tombe dans le polygone.
        j0 = max(0, int(math.ceil(min(ys) / MASQUE_PAS - .5)))
        j1 = min(ny - 1, int(math.floor(max(ys) / MASQUE_PAS - .5)))
        for j in range(j0, j1 + 1):
            cy = (j + .5) * MASQUE_PAS
            coupes = []
            for n, (x1, y1) in enumerate(poly):
                x2, y2 = poly[(n + 1) % len(poly)]
                # Règle demi-ouverte : un sommet rencontré par la ligne ne doit
                # compter qu'une fois.
                if (y1 <= cy < y2) or (y2 <= cy < y1):
                    coupes.append(x1 + (cy - y1) * (x2 - x1) / (y2 - y1))
            if len(coupes) < 2:
                continue
            # Un contour final peut être concave (équerre, cour). Les coupes se
            # prennent donc deux par deux selon la règle paire/impaire du SVG,
            # et non du bord gauche au bord droit comme pour un convexe.
            coupes.sort()
            for gauche, droite in zip(coupes[0::2], coupes[1::2]):
                i0 = max(0, int(math.ceil(gauche / MASQUE_PAS - .5)))
                i1 = min(nx - 1, int(math.floor(droite / MASQUE_PAS - .5)))
                for i in range(i0, i1 + 1):
                    k = j * nx + i
                    if not (bits[k >> 3] >> (k & 7)) & 1:
                        bits[k >> 3] |= 1 << (k & 7)
                        pose += 1
    return bits, nx, ny, pose


def graver_courtine(bits, nx, ny, lieu):
    """Les murs dans le masque — TOUS les murs, et les portes seules percées.

    POURQUOI ÇA MANQUAIT, ET CE QUE ÇA COÛTAIT. Le masque ne gravait que
    `bati`. La courtine était DESSINÉE (on la voit sur le plan) mais elle
    n'était inscrite nulle part : ni la foule ni la bataille ne savaient qu'elle
    est solide. Les hommes la traversaient — pas par un défaut de trajectoire,
    mais parce que pour eux elle n'existait pas.

    PUIS ELLE A ÉTÉ GRAVÉE À MOITIÉ, ET C'EST PIRE, parce qu'un mur à trous ne
    proteste pas. Le filtre était `largeur is None` : il ne gardait que les sept
    tronçons de courtine nue et jetait tout le reste. Mesuré sur le masque cuit
    le 14 août, mur par mur, à un demi-mètre :

        les 7 tronçons de courtine        12 100 m      0 % de trou
        les 7 tronçons dits « portes »     1 450 m     93 % de trou
        les 9 enceintes intérieures        5 250 m     56 % de trou
        ----------------------------------------------------------
                                          18 815 m     36 % de trou

    Les deux dernières lignes sont deux fautes différentes.

    LES « PORTES » NE SONT PAS DES PORTES : ce sont des TRONÇONS DE MUR de deux
    cents mètres qui en contiennent une. On les sautait en entier — sept brèches
    de deux cents mètres dans une muraille qu'on croyait fermée. Et le plan les
    dessine, lui : `remparts()` les met dans la courtine et pose le châtelet au
    milieu. Ce qui était dessiné et ce qui était gravé n'étaient donc pas la
    même ville. On grave le tronçon et l'on perce le passage charretier à
    l'endroit exact où `remparts()` plante ses deux tours — même point, même
    largeur, un seul calcul recopié.

    ⚠ LES NEUF AUTRES FORMES NE SONT PAS DES MURS, ET ON A ESSAYÉ. Le Donjon
    Rouge, la Fosse aux Dragons, la tour de la Main, le vieux septuaire, la
    Guilde des Alchimistes, les casernes du Guet portent `genre: "mur"` avec une
    `largeur` (2,5 à 4) : ce sont les CONTOURS des grands lieux sur la carte de
    ville, pas des enceintes. Gravés une fois, ils ont rendu ce qu'on voyait à
    l'œil sur le masque — de grands rectangles posés au travers du tissu urbain.

    Ce qui le prouve, et c'est une mesure et non un avis : à l'intérieur de ces
    formes la voirie court à 260-345 m par hectare quand la ville entière est à
    129, et le bâti y couvre 38 % — la densité ordinaire. On n'enferme pas
    vingt-cinq ruelles dans la cour d'un donjon. Le Donjon Rouge « enceint »
    trente et un hectares traversés par quarante-sept rues.

    Le critère est donc celui que `remparts()` écrivait déjà quatre cents lignes
    plus haut — « les grands édifices, pas le mur » —, et on le lui reprend mot
    pour mot : `largeur in (None, 6)`. Ce qui est gravé est exactement ce qui est
    dessiné en courtine, ni plus ni moins. Le jour où le Donjon Rouge aura une
    vraie enceinte, elle s'écrira comme telle et non comme un contour de lieu.

    ON NE ROUVRE JAMAIS UNE CASE QU'ON N'A PAS POSÉE SOI-MÊME. Percer efface des
    cases ; si une maison est adossée à la porte, elle serait effacée avec. On
    retient donc ce que la courtine a posé, et le perçage ne mord que là-dessus.
    """
    chem = os.path.join(RACINE, "etat", "villes", lieu + ".json")
    if not os.path.exists(chem):
        return 0
    with open(chem, encoding="utf-8") as f:
        murs = [s for s in (json.load(f).get("sol") or [])
                if s.get("genre") == "mur"
                and s.get("largeur") in (None, 6)]
    if not murs:
        return 0

    def cases(cx, cy, ux, uy, demi_long, demi_large):
        """Les cases d'une boîte : `demi_long` le long de (ux,uy), `demi_large`
        en travers. Sert à graver un tronçon comme à percer une porte."""
        rayon = math.hypot(demi_long, demi_large)
        i0 = max(0, int((cx - rayon) / MASQUE_PAS))
        i1 = min(nx - 1, int((cx + rayon) / MASQUE_PAS) + 1)
        j0 = max(0, int((cy - rayon) / MASQUE_PAS))
        j1 = min(ny - 1, int((cy + rayon) / MASQUE_PAS) + 1)
        for j in range(j0, j1 + 1):
            dy = (j + .5) * MASQUE_PAS - cy
            for i in range(i0, i1 + 1):
                dx = (i + .5) * MASQUE_PAS - cx
                if abs(dx * ux + dy * uy) > demi_long:
                    continue
                if abs(-dx * uy + dy * ux) > demi_large:
                    continue
                yield j * nx + i

    mien = set()          # les cases posées par la courtine, et elles seules
    portes = []           # où percer, une fois tout gravé
    pose = 0
    for s in murs:
        e = float(s.get("largeur") or MUR_E)
        demi = e / 2.
        pts = [_du_plan(p) for p in s["points"]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            lx, ly = bx - ax, by - ay
            lg = math.hypot(lx, ly)
            if lg < 1e-6:
                continue
            ux, uy = lx / lg, ly / lg
            # LE MILIEU DU SEGMENT ET NON SON DÉPART, et la demi-longueur avec :
            # une boîte centrée se ferme sur ses deux bouts. Bornée à `[0, lg]`
            # depuis un bout, elle laissait une encoche à chaque sommet de la
            # polyligne — un mur en pointillé aux angles.
            #
            # On allonge d'une demi-épaisseur de chaque côté : c'est le joint.
            # Deux segments qui font un coude ne se recouvrent pas sinon, et un
            # angle de courtine est justement l'endroit où l'on passe.
            for k in cases((ax + bx) / 2., (ay + by) / 2., ux, uy,
                           lg / 2. + demi, demi):
                # `mien` NE PREND QUE CE QU'ON VIENT DE POSER, et c'est ce qui
                # protège les maisons : une case déjà noire l'était pour une
                # autre raison — un bâtiment adossé au mur —, et le perçage
                # n'aura pas le droit d'y toucher.
                if not (bits[k >> 3] >> (k & 7)) & 1:
                    pose += 1
                    mien.add(k)
                bits[k >> 3] |= 1 << (k & 7)

        if float(s.get("largeur") or 0.) == 6.:
            # Le passage charretier, au milieu du tronçon — LE MÊME POINT que
            # celui où `remparts()` plante les deux tours du châtelet. Si l'un
            # des deux calculs bouge un jour, l'autre doit bouger avec.
            (ax, ay), (bx, by) = pts[0], pts[-1]
            lg = math.hypot(bx - ax, by - ay) or 1.
            portes.append(((ax + bx) / 2., (ay + by) / 2.,
                           (bx - ax) / lg, (by - ay) / lg,
                           e, s.get("nom") or "une porte"))

    perce = 0
    for (cx, cy, ux, uy, e, nom) in portes:
        for k in cases(cx, cy, ux, uy, PORTE_L / 2., e / 2. + 1.):
            if k in mien and (bits[k >> 3] >> (k & 7)) & 1:
                bits[k >> 3] &= ~(1 << (k & 7))
                perce += 1
    if portes:
        print("  masque      %d passages percés (%d m², %.0f m de large)"
              % (len(portes), perce, PORTE_L))
    return pose - perce


def ecrire_masque(emprises, prefixe, larg, haut, lieu=None):
    bits, nx, ny, pose = masque(emprises, larg, haut)
    mur = graver_courtine(bits, nx, ny, lieu) if lieu else 0
    if mur:
        print("  masque      + %d m² de courtine (les portes restent ouvertes)"
              % mur)
    chem = os.path.join(RACINE, "monde", prefixe + ".masque.bin")
    with open(chem, "wb") as f:
        f.write(bits)
    print("  masque      %d x %d cases, %.1f Mo, %d m² bâtis"
          % (nx, ny, len(bits) / 1048576., pose))
    return {"nx": nx, "ny": ny, "pas": MASQUE_PAS,
            "fichier": prefixe + ".masque.bin"}


# ---------------------------------------------------------------------------
# LE BÂTI N'A PAS TOUJOURS LES MÊMES COLONNES, et c'est légitime
# ---------------------------------------------------------------------------
# Port-Réal est semé par `densifier.py` puis complété par `usages.py`, qui lui
# donne `cat`, `toit` et la porte sur rue. Peyredragon est bâti par
# `peyredragon.py` — soixante-sept maisons d'un bourg sous les murs, pas
# quarante-cinq mille — et n'a jamais eu besoin de ces colonnes-là.
#
# On les COMPLÈTE ici plutôt que de les exiger. Deux raisons : réécrire
# `bati.json` déplacerait des rangs, et le rang est l'adresse par laquelle le
# jeu tient ses lieux (`scripts/affecter.py`) ; et un plan de château n'a pas à
# attendre qu'on lui invente un cadastre pour se laisser dessiner.
#
# `porte_x`/`porte_y` restent absentes quand elles le sont, et `redresser` s'en
# accommode : aligner soixante-sept maisons sur une rue qu'elles bordent déjà
# ne rendrait rien de plus qu'un déplacement qu'on n'a pas demandé.
FAMILLES = {
    "maison": "habitat", "taudis": "habitat", "cabane": "habitat",
    "manse": "habitat", "maison-officier": "habitat",
}


def completer_bati(source):
    col = source["_colonnes"]
    if "cat" in col:
        return
    iusg = col.index("usage") if "usage" in col else None
    # La table des familles de `usages.py` fait foi quand elle est là ; la
    # petite table ci-dessus ne sert qu'aux usages qu'elle ne connaît pas.
    familles = dict(FAMILLES)
    for u, t in (source.get("_types") or {}).items():
        if isinstance(t, dict) and t.get("cat"):
            familles[u] = t["cat"]
    col.append("cat")
    for r in source["bati"]:
        u = r[iusg] if iusg is not None else None
        r.append(familles.get(u, "habitat"))
    print("  bâti sans « cat » : colonne dérivée de l'usage pour %d bâtiments"
          % len(source["bati"]))


def cuire(lieu):
    prefixe = PREFIXES.get(lieu)
    if not prefixe:
        raise SystemExit("lieu inconnu : " + lieu)
    PREFIXE[0] = prefixe
    if lieu == "port-real":
        # Bon marché si rien n'a changé, déterministe sinon. Le plan ne peut
        # ainsi jamais cuire des courbes plus vieilles que leur source.
        from relief_region import assurer as assurer_relief_region
        assurer_relief_region()
        from occupation_region import assurer as assurer_occupation_region
        assurer_occupation_region()
    t = lire(os.path.join("monde", prefixe + ".terrain.json"))
    r = lire(os.path.join("monde", prefixe + ".rues.json"))
    b = lire(os.path.join("monde", prefixe + ".bati.json"))
    completer_bati(b)
    nx, ny, pas = t["nx"], t["ny"], t["res_m"]

    eau = coudre(segments(t["eau"], nx, ny, .5, pas))
    eau = [alleger(l, 4.) for l in eau if len(l) > 4]

    niveaux = []
    for z in NIVEAUX:
        lignes = [alleger(l, 6.) for l in coudre(segments(t["z"], nx, ny, z, pas))
                  if len(l) > 6]
        if lignes:
            niveaux.append({"z": z, "d": chemin(lignes)})

    mur = remparts(lieu)
    limite = mur.pop("_limite", None)
    bati_plan, emprises = bati(b, r, limite)
    region = region_port_real(lieu)
    bornes_coeur = [0, 0, round((nx - 1) * pas), round((ny - 1) * pas)]
    plan = {
        "_lisez_moi": "Plan 2D cuit par scripts/monde/plan_ville.py — ne pas "
                      "modifier à la main : la source est monde/" + prefixe + ".*",
        "lieu": lieu,
        "bornes": region["bornes"] if region else bornes_coeur,
        "bornes_coeur": bornes_coeur,
        "region": region,
        "cote": chemin(eau),
        "niveaux": niveaux,
        "voies": voies(r),
        "rempart": mur,
        # `bati` a déjà redressé la ville. Son dessin et son masque reçoivent les
        # mêmes `emprises`; `enseignes` lit aussi cette pose (voir POSES).
        "bati": bati_plan,
        "types": types(b),
        "enseignes": enseignes(b),
        "masque": ecrire_masque(emprises, prefixe, round((nx - 1) * pas),
                                 round((ny - 1) * pas), lieu),
        "reperes": reperes(r),
        "quartiers": quartiers(b),
    }
    # Une toponymie cuite reste une information du monde : le navigateur la
    # montre, mais les messagers et les ordres pourront interroger la même.
    from toponymie import enrichir_plan
    return enrichir_plan(plan, r, prefixe)


def main():
    ap = argparse.ArgumentParser(description="Cuire le plan 2D d'une ville")
    ap.add_argument("--lieu", default="port-real")
    ap.add_argument("--sortie", default=None)
    ap.add_argument("--rectifier", choices=("plein", "filet", "aucun"),
                    default=RECTIFICATION,
                    help="jusqu'où repositionner le bâti (voir RECTIFICATION)")
    a = ap.parse_args()
    globals()["RECTIFICATION"] = a.rectifier
    d = cuire(a.lieu)
    sortie = a.sortie or os.path.join("monde", PREFIXES[a.lieu] + ".plan2d.json")
    chem = os.path.join(RACINE, sortie)
    with open(chem, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    o = os.path.getsize(chem)
    print("%s — %.1f Mo" % (sortie, o / 1048576.))
    print("  cote        %6d signes" % len(d["cote"]))
    for n in d["niveaux"]:
        print("  niveau %3d m %6d signes" % (n["z"], len(n["d"])))
    for g in COUCHES_VOIES:
        if g in d["voies"]:
            print("  voie %-9s %6d signes" % (g, len(d["voies"][g])))
    silhouettes = 0
    for u, t in d["types"].items():
        if u in d["bati"]:
            n = d["bati"][u].count("M")
            silhouettes += n
            print("  bati %-20s %-12s %7d signes, %5d silhouettes"
                  % (u, t["cat"], len(d["bati"][u]), n))
    print("  %d silhouettes pour %d bâtiments semés" % (silhouettes, COMPTE[0]))
    ens = sum(s.count(",") for s in d["enseignes"].values())
    print("  %d enseignes sur %d types marqués (%d types sans marque)"
          % (ens, len(d["enseignes"]),
             sum(1 for u in d["types"] if u not in d["enseignes"])))
    print("  %d reperes, %d quartiers" % (len(d["reperes"]), len(d["quartiers"])))


if __name__ == "__main__":
    sys.exit(main())
