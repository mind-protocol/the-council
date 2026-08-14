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
# deux tiers, on est dans un pâté de maisons : les murs se touchent, et c'est
# ainsi que se bâtit une ville qui n'a plus de place. En dessous, on est dans
# un faubourg : les maisons gardent leur écart, et les serrer serait un
# mensonge sur ce qu'on peut passer entre elles.
DENSITE_MITOYENNE = 0.62
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
    ipx, ipy = col.index("porte_x"), col.index("porte_y")
    ix, iy = col.index("x"), col.index("y")
    ifa, ipr, icat = col.index("facade_m"), col.index("profondeur_m"), col.index("cat")
    segs, grille = _index_voies(rues)

    poses = [[r[ix], r[iy], r[icap] or 0.] for r in source["bati"]]
    fronts = {}                       # (tronçon, côté) → les maisons qui y donnent
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
        fronts.setdefault((e, cote), []).append((k, s))

    tournes = deplaces = mitoyens = 0
    somme = 0.
    for (e, cote), gens in fronts.items():
        x1, y1, x2, y2, cap, classe, lg = segs[e]
        ux, uy = (x2 - x1) / lg, (y2 - y1) / lg
        nx, ny = -uy * cote, ux * cote          # la normale qui s'éloigne de la rue
        bord = LARGEUR_VOIE.get(classe, 2.3) / 2. + TROTTOIR.get(classe, .5)

        abscisses = (_mitoyenner(source, gens, lg, ifa, icat)
                     if RECTIFICATION == "plein" else None)
        if abscisses is not None:
            mitoyens += len(gens)
        else:
            abscisses = {k: s for k, s in gens}

        for k, _ in gens:
            r = source["bati"][k]
            s = abscisses[k]
            # 3. la ligne de front est celle des FAÇADES, pas celle des centres :
            # chacune recule de sa propre demi-profondeur derrière le même bord.
            # Un recul commun aux centres remettrait les grosses dans la rue, ou
            # creuserait un trou devant les petites.
            recul = bord + (r[ipr] or 4) / 2.
            cx = x1 + ux * s + nx * recul
            cy = y1 + uy * s + ny * recul
            # Le cap : la façade suit la rue, et la PROFONDEUR s'éloigne d'elle
            # — c'est-à-dire que l'axe local des y vaut la normale sortante.
            neuf = math.degrees(math.atan2(uy * cote, ux * cote))
            somme += abs((neuf - poses[k][2] + 90.) % 180. - 90.)
            tournes += 1
            # ON NE PLAFONNE QUE LE MOUVEMENT PERPENDICULAIRE. Le long de la
            # rue, une maison peut glisser tant qu'elle veut — c'est le rang
            # qui se serre, et il ne quitte pas le tronçon. En travers, passé
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

    degages = (_degager(source, poses, segs, grille, ifa, ipr)
               if RECTIFICATION in ("plein", "filet") else 0)
    print("  bati %d/%d façades alignées, %d reposées, %d mitoyennes, "
          "%d dégagées, %d sans voie, écart moyen %.1f°"
          % (tournes, len(poses), deplaces, mitoyens, degages, orphelins,
             somme / tournes if tournes else 0.))
    return poses


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
    if total <= lg:
        # Ça rentre : on colle le rang et on le centre sur ce qu'il occupait,
        # pour que les maisons ne migrent pas vers un bout du tronçon.
        depart = min(max((sum(s for _, s in ordre) / len(ordre)) - total / 2., 0.),
                     lg - total)
        c = depart
        for k, _ in ordre:
            out[k] = c + largeurs[k] / 2.
            c += largeurs[k]
        return out
    # Ça déborde : on répartit à égalité sur toute la longueur. Les murs se
    # recouvrent un peu, la soudure en fera un front continu — ce qui est
    # exactement ce qu'on voulait montrer.
    for i, (k, _) in enumerate(ordre):
        out[k] = lg * (i + .5) / len(ordre)
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
        # la remise est plus étroite que la maison : on garde un passage de côté
        out.append(_quad(-f*0.82, f*0.82, p - M*2.5, p + fo))
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


def _pieces(f, p, k, cat, ann=(0., 0., 0.), mur=0.):
    """Les morceaux convexes d'un bâtiment, en repère local (façade sur x).

    Rend une liste de polygones inscrits dans [-f, f] × [-p, p], plus les
    ANNEXES qui, elles, en sortent (voir `_annexes`). Un seul morceau pour les
    formes pleines, deux ou trois pour les équerres et les cours — l'union s'en
    charge, et elle recoud aussi les annexes puisqu'elles appartiennent au même
    bâtiment.
    """
    sup = _annexes(f, p, ann, mur)
    d = _melange(k)
    # Une cabane de quatre mètres n'a pas d'aile en retour : on ne découpe que
    # ce qui est assez grand pour que la découpe se voie.
    if f < 3. or p < 3.:
        return [_quad(-f, f, -p, p)] + sup
    poids = FORMES.get(cat) or FORMES["habitat"]
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
        if d() < .5:
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


def remparts():
    """La courtine en polyligne, les portes en tours. Carte absente : rien."""
    chem = os.path.join(RACINE, "etat", "villes", "port-real.json")
    if not os.path.exists(chem):
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
            "tours": chemin(tours, dec=1, ferme=True), "portes": noms}


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


def bati(source, rues):
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
    mons, avale = monuments(source, poses)

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
    for u, pieces in mons.items():
        par_cat.setdefault(u, []).extend(pieces)
        par_prop.setdefault(u, []).extend([("m", u)] * len(pieces))
    for k, r in enumerate(source["bati"]):
        if k in avale:
            continue
        x, y, cap = poses[k]
        a = math.radians(cap)
        ca, sa = math.cos(a), math.sin(a)
        f, p = (r[ifa] or 4) / 2., (r[ipr] or 4) / 2.
        nom = r[icat] or "habitat"
        # La FORME suit la catégorie (une institution a des cours, une cabane
        # non), mais le GROUPE suit le type : c'est lui qui portera la couleur,
        # et la couleur ne peut pas traverser une silhouette soudée.
        u = r[iusg] or nom
        cat = par_cat.setdefault(u, [])
        prop = par_prop.setdefault(u, [])
        ann = ((r[iaf] or 0.), (r[iag] or 0.), (r[iad] or 0.)) if iaf is not None             else (0., 0., 0.)
        mur = (r[imu] or 0.) if imu is not None else 0.
        for piece in _pieces(f, p, k, nom, ann, mur):
            cat.append([(x + dx * ca - dy * sa, y + dx * sa + dy * ca)
                        for dx, dy in piece])
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
        out[cat] = chemin(lignes, dec=0, ferme=True)
    return out


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
        e["n"] += 1
    # Du plus commun au plus rare : c'est l'ordre du DESSIN, et ce qui est
    # écrit en premier passe dessous. Les trente et un mille maisons font le
    # fond ; les vingt bâtiments d'institution se posent dessus, jamais
    # l'inverse — sinon le seul bureau du maître de port disparaît sous la
    # ville entière.
    return {u: n[u] for u in sorted(n, key=lambda u: -n[u]["n"])}


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
# On rasterise les RECTANGLES ORIENTÉS de `bati.json` et non les silhouettes
# soudées : c'est la même empreinte au sol, ça évite d'analyser trente mille
# chemins SVG, et deux produits scalaires suffisent à savoir si une case est
# dans un rectangle tourné.
MASQUE_PAS = 1.0                 # mètres par case

def masque(source, larg_m, haut_m):
    col = source["_colonnes"]
    ix, iy = col.index("x"), col.index("y")
    ifa, ipr = col.index("facade_m"), col.index("profondeur_m")
    icap = col.index("cap")
    nx = int(larg_m / MASQUE_PAS)
    ny = int(haut_m / MASQUE_PAS)
    bits = bytearray((nx * ny + 7) // 8)
    pose = 0
    for r in source["bati"]:
        a = math.radians(r[icap] or 0.)
        ca, sa = math.cos(a), math.sin(a)
        f = (r[ifa] or 4.) / 2.
        p = (r[ipr] or 4.) / 2.
        x, y = r[ix], r[iy]
        # La boîte englobante du rectangle tourné : on ne teste que dedans.
        demi = math.hypot(f, p)
        i0 = max(0, int((x - demi) / MASQUE_PAS))
        i1 = min(nx - 1, int((x + demi) / MASQUE_PAS) + 1)
        j0 = max(0, int((y - demi) / MASQUE_PAS))
        j1 = min(ny - 1, int((y + demi) / MASQUE_PAS) + 1)
        for j in range(j0, j1 + 1):
            dy = (j + .5) * MASQUE_PAS - y
            for i in range(i0, i1 + 1):
                dx = (i + .5) * MASQUE_PAS - x
                # dans le repère du bâtiment : façade sur x, profondeur sur y
                u = dx * ca + dy * sa
                v = -dx * sa + dy * ca
                if -f <= u <= f and -p <= v <= p:
                    k = j * nx + i
                    bits[k >> 3] |= 1 << (k & 7)
                    pose += 1
    return bits, nx, ny, pose


def ecrire_masque(b, prefixe, larg, haut):
    bits, nx, ny, pose = masque(b, larg, haut)
    chem = os.path.join(RACINE, "monde", prefixe + ".masque.bin")
    with open(chem, "wb") as f:
        f.write(bits)
    print("  masque      %d x %d cases, %.1f Mo, %d m² bâtis"
          % (nx, ny, len(bits) / 1048576., pose))
    return {"nx": nx, "ny": ny, "pas": MASQUE_PAS,
            "fichier": prefixe + ".masque.bin"}


def cuire(lieu):
    prefixe = PREFIXES.get(lieu)
    if not prefixe:
        raise SystemExit("lieu inconnu : " + lieu)
    PREFIXE[0] = prefixe
    t = lire(os.path.join("monde", prefixe + ".terrain.json"))
    r = lire(os.path.join("monde", prefixe + ".rues.json"))
    b = lire(os.path.join("monde", prefixe + ".bati.json"))
    nx, ny, pas = t["nx"], t["ny"], t["res_m"]

    eau = coudre(segments(t["eau"], nx, ny, .5, pas))
    eau = [alleger(l, 4.) for l in eau if len(l) > 4]

    niveaux = []
    for z in NIVEAUX:
        lignes = [alleger(l, 6.) for l in coudre(segments(t["z"], nx, ny, z, pas))
                  if len(l) > 6]
        if lignes:
            niveaux.append({"z": z, "d": chemin(lignes)})

    return {
        "_lisez_moi": "Plan 2D cuit par scripts/monde/plan_ville.py — ne pas "
                      "modifier à la main : la source est monde/" + prefixe + ".*",
        "lieu": lieu,
        "bornes": [0, 0, round((nx - 1) * pas), round((ny - 1) * pas)],
        "cote": chemin(eau),
        "niveaux": niveaux,
        "voies": voies(r),
        "rempart": remparts(),
        "bati": bati(b, r),
        "types": types(b),
        "masque": ecrire_masque(b, prefixe, round((nx - 1) * pas),
                                round((ny - 1) * pas)),
        "reperes": reperes(r),
        "quartiers": quartiers(b),
    }


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
    print("  %d reperes, %d quartiers" % (len(d["reperes"]), len(d["quartiers"])))


if __name__ == "__main__":
    sys.exit(main())
