# -*- coding: utf-8 -*-
"""Les INTÉRIEURS de Peyredragon — des pièces creuses, avec leurs portes percées.

    python scripts/monde/peyredragon_interieurs.py             ce qu'il ferait
    python scripts/monde/peyredragon_interieurs.py --vraiment  et il l'écrit
    python scripts/monde/peyredragon_interieurs.py --verifier  et il se mesure

`monde/peyredragon.maillage.json` est le château vu du DEHORS : sept matières de
volumes pleins. Poser une caméra dedans met le joueur dans de la roche. Ce
script bâtit l'autre moitié : pour chaque salle du plan, une dalle, une ceinture
de murs épais (face intérieure ET face extérieure), un plafond, et une ouverture
percée vers chacune de ses voisines.

TROIS PARTIS PRIS, et ils décident tout le fichier.

1. LE PLAN DONNE LA FORME, LA TABLE DONNE LA TAILLE. C'est déjà la règle de
   `materialisation/lieux.py` : le plan est une carte mentale, il grossit ce qui
   compte, et métrisé tel quel il rend une grande salle de 87 m. On lit donc le
   TRACÉ de `plans.js` (le cercle devient un polygone, le chemin SVG se lit tel
   quel), puis on le REDIMENSIONNE pour que sa boîte fasse exactement les mètres
   déclarés dans `lieux.TAILLE`. La silhouette est celle du dessin, les mesures
   sont celles de la table.

2. SAUF DEHORS. Les salles `dehors` et celles que le modèle 3D bâtit déjà
   (`lieux.DEJA`) n'ont pas de mesure déclarée — et pour cause : la cour, c'est
   l'enceinte, et l'enceinte est justement ce sur quoi le plan a été calé. Pour
   celles-là on métrise le tracé au facteur du calage (`lieux._S`), sans
   correction, et on ne les couvre pas : on y voit le ciel, avec un parapet.

3. UNE PORTE EST UN TROU, PAS UNE PORTE. Chaque arête de `etat/chemins.json`
   perce 1,1 m sur 2,1 m dans le mur de CHAQUE salle, au point de son emprise le
   plus proche du centre de sa voisine. On ne modélise ni battant, ni marche, ni
   escalier : deux salles d'étages différents ont chacune leur trou, à leur
   propre hauteur, et ce qui les relie reste dans la tête du joueur.

Sortie : `monde/peyredragon.interieurs.json`, au format de `peyredragon.maillage.json`
(`sommets`, `index`, `groupes`), plus une clef `salles` qui donne à chaque pièce
sa tranche d'index — c'est elle qui permet au viewer de n'afficher qu'une pièce
et ses voisines.
"""
import json
import math
import os
import re
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
MONDE = os.path.join(RACINE, "monde")
sys.path.insert(0, os.path.join(RACINE, "scripts", "materialisation"))

import lieux as Li            # noqa: E402
import peyredragon as P       # noqa: E402

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from etat.expose import tables  # LA PORTE de etat/

# Le repère : la matérialisation compte depuis le milieu de l'île, le monde 3D
# depuis le coin sud-ouest. Même décalage que `peyredragon_chateau.py`.
DECALAGE = (3000.0, 2500.0)

SORTIE = os.path.join(MONDE, "peyredragon.interieurs.json")
CHEMINS = os.path.join(RACINE, "etat", "chemins.json")

EPAISSEUR = 0.6      # l'épaisseur des murs, en mètres
PORTE_L = 1.1        # la largeur d'une ouverture
PORTE_H = 2.1        # sa hauteur sous linteau
JAMBAGE = 0.25       # ce qu'on laisse de mur entre une porte et le coin
PARAPET = 2.4        # la hauteur du muret des aires découvertes
PALIER_M = 3.0       # au-delà, une porte est un escalier et non une ouverture
COTES = 20           # de combien de pans on fait un cercle

# Ce qui n'a pas de plafond : on y voit le ciel.
OUVERT = set(Li.AIRES) | {"cour", "quai", "bourg", "greve", "grand-escalier",
                          "chemin-ronde", "porte-de-mer", "baraques", "lices"}
# Ce qui n'a pas de mesure déclarée dans `lieux.TAILLE` : on métrise son tracé.
SANS_MESURE = set(Li.DEJA) - set(Li.TAILLE)


# ---------------------------------------------------------------------------
# lire le TRACÉ du plan — ce que `lieux._forme` jette
# ---------------------------------------------------------------------------
def contour_plan(corps, diametre_m=None):
    """Le tracé d'une salle en unités de plan, y déjà retourné, sens quelconque.

    `diametre_m` : la taille que la salle FERA une fois remise à sa mesure. Elle
    ne sert qu'aux cercles, et elle n'est pas cosmétique — une porte se perce
    DANS un pan, et vingt pans sur une roukerie de neuf mètres donnent des pans
    de 1,4 m où rien ne passe.
    """
    m = re.search(r"forme:\s*\{\s*c:\s*\[([^\]]+)\]", corps)
    if m:
        cx, cy, r = Li._nombres(m.group(1))[:3]
        peri = math.pi * (diametre_m if diametre_m else 2 * r * Li._S)
        # des pans d'environ 2,6 m : jamais moins de six, jamais plus de vingt
        cotes = max(6, min(COTES, int(round(peri / 2.6))))
        return [(cx + r * math.cos(2 * math.pi * k / cotes),
                 -(cy + r * math.sin(2 * math.pi * k / cotes)))
                for k in range(cotes)]
    m = re.search(r"forme:\s*\{\s*r:\s*\[([^\]]+)\]", corps)
    if m:
        x, y, l, h = Li._nombres(m.group(1))[:4]
        return [(x, -y), (x + l, -y), (x + l, -(y + h)), (x, -(y + h))]
    m = re.search(r'forme:\s*\{\s*d:\s*"([^"]+)"', corps)
    if m:
        n = Li._nombres(m.group(1))
        pts = [(n[i], -n[i + 1]) for i in range(0, len(n) - 1, 2)]
        # un chemin fermé répète parfois son premier point
        if len(pts) > 2 and math.dist(pts[0], pts[-1]) < 1e-6:
            pts = pts[:-1]
        return pts
    return None


# ---------------------------------------------------------------------------
# géométrie plane
# ---------------------------------------------------------------------------
def aire(poly):
    s = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return s / 2


def anti_horaire(poly):
    return poly if aire(poly) > 0 else poly[::-1]


def nettoyer(poly, mini=0.35):
    """Ôte les points confondus : un pan de 2 cm ne porte pas de porte."""
    out = []
    for p in poly:
        if not out or math.dist(p, out[-1]) > mini:
            out.append(p)
    while len(out) > 3 and math.dist(out[0], out[-1]) < mini:
        out.pop()
    return out


def dedans(poly, x, y):
    """Le rayon lancé — le même test que partout ailleurs dans le projet."""
    d = False
    j = len(poly) - 1
    for i in range(len(poly)):
        if (poly[i][1] > y) != (poly[j][1] > y) and \
           x < (poly[j][0] - poly[i][0]) * (y - poly[i][1]) / \
               (poly[j][1] - poly[i][1]) + poly[i][0]:
            d = not d
        j = i
    return d


def _tri_aire(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def trianguler(poly):
    """L'oreille coupée : un polygone simple anti-horaire en triangles.

    Une éventail depuis le centre suffit aux convexes et ment sur les autres —
    le tracé de la cour et celui du grand escalier ne sont pas convexes.
    """
    n = len(poly)
    if n < 3:
        return []
    reste = list(range(n))
    tris, garde = [], 0
    while len(reste) > 3 and garde < 4 * n:
        garde += 1
        coupe = False
        for k in range(len(reste)):
            i0 = reste[k - 1]
            i1 = reste[k]
            i2 = reste[(k + 1) % len(reste)]
            a, b, c = poly[i0], poly[i1], poly[i2]
            if _tri_aire(a, b, c) <= 1e-9:
                continue
            libre = True
            for j in reste:
                if j in (i0, i1, i2):
                    continue
                p = poly[j]
                if (_tri_aire(a, b, p) >= 0 and _tri_aire(b, c, p) >= 0
                        and _tri_aire(c, a, p) >= 0):
                    libre = False
                    break
            if not libre:
                continue
            tris.append((i0, i1, i2))
            reste.pop(k)
            coupe = True
            garde = 0
            break
        if not coupe:                       # tracé retors : on ferme en éventail
            break
    if len(reste) >= 3:
        for k in range(1, len(reste) - 1):
            tris.append((reste[0], reste[k], reste[k + 1]))
    return tris


def normale(a, b):
    """La normale SORTANTE du pan a→b d'un polygone anti-horaire."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1.0
    return (dy / n, -dx / n)


def decaler(poly, e):
    """Le contour extérieur : chaque coin poussé sur sa bissectrice.

    Un décalage pan par pan laisserait un coin ouvert à chaque angle saillant.
    """
    n = len(poly)
    out = []
    for i in range(n):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        n1, n2 = normale(a, b), normale(b, c)
        bx, by = n1[0] + n2[0], n1[1] + n2[1]
        m = math.hypot(bx, by)
        if m < 1e-6:                        # demi-tour : on pousse tout droit
            bx, by, k = n1[0], n1[1], 1.0
        else:
            bx, by = bx / m, by / m
            cos = bx * n2[0] + by * n2[1]
            k = 1.0 / max(0.34, cos)        # angle très aigu : on écrête
        out.append((b[0] + bx * e * k, b[1] + by * e * k))
    return out


def _sur_pan(poly, i, cible):
    """Le point du pan `i` le plus proche d'une cible : (t, distance, longueur)."""
    a, b = poly[i], poly[(i + 1) % len(poly)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    ll = dx * dx + dy * dy
    t = 0.5 if ll < 1e-9 else max(0.0, min(1.0, ((cible[0] - a[0]) * dx +
                                                 (cible[1] - a[1]) * dy) / ll))
    return t, math.dist((a[0] + dx * t, a[1] + dy * t), cible), math.sqrt(ll)


def placer_porte(poly, cible, pris):
    """Où percer vers `cible` : (pan, t0, t1), ou (None, pourquoi).

    On vise le point de l'emprise le plus proche du centre de la voisine. Si la
    place y est déjà prise par une autre porte, on GLISSE le long du même pan
    avant de changer de pan : deux salles voisines qui tirent au même endroit
    doivent avoir deux portes, pas une seule et un trou dans la topologie.
    """
    pans = sorted(range(len(poly)),
                  key=lambda i: _sur_pan(poly, i, cible)[1])
    court = 0
    for i in pans:
        t, _d, L = _sur_pan(poly, i, cible)
        if L < PORTE_L + 2 * JAMBAGE:
            court += 1
            continue
        demi = (PORTE_L / 2) / L
        marge = (PORTE_L / 2 + JAMBAGE) / L
        pas = (PORTE_L + JAMBAGE) / L
        t = max(marge, min(1 - marge, t))
        for k in range(0, int(1 / pas) + 2):
            for u in ((t,) if k == 0 else (t - k * pas, t + k * pas)):
                if u < marge or u > 1 - marge:
                    continue
                t0, t1 = u - demi, u + demi
                if all(t1 <= v0 - JAMBAGE / L or t0 >= v1 + JAMBAGE / L
                       for (v0, v1) in pris.get(i, [])):
                    return i, t0, t1
    if court == len(poly):
        return None, "tous les pans font moins de %.1f m" % (PORTE_L + 2 * JAMBAGE)
    return None, "aucune place libre sur le contour"


# ---------------------------------------------------------------------------
# le sac à triangles
# ---------------------------------------------------------------------------
class Sac:
    """Des triangles avec leur matière, dédoublonnés à la sortie."""

    def __init__(self):
        self.tris = []          # (p0, p1, p2, matiere, part)
        # « la coque » = les murs, la dalle, le plafond ; « le dedans » = les
        # vantaux et le mobilier. La distinction n'est pas cosmétique : c'est la
        # coque, et elle seule, qui doit être creuse — on ne peut pas le mesurer
        # au rayon lancé si une table traîne dans le compte.
        self.part = "coque"

    def tri(self, a, b, c, mat):
        self.tris.append((a, b, c, mat, self.part))

    def quad(self, a, b, c, d, mat):
        self.tri(a, b, c, mat)
        self.tri(a, c, d, mat)


def _p(q, z):
    return (q[0], q[1], z)


def pan(sac, a, b, A, B, z0, z1, mat):
    """Les deux FACES d'un morceau de mur — jamais ses tranches.

    La ceinture de murs est un anneau continu : ses tranches n'existent qu'aux
    embrasures. Émettre une boîte fermée par pan poserait deux quads confondus
    à chaque coin et à chaque jambage — le compte des faces devient impair et
    l'on ne peut plus mesurer que la pièce est creuse.
    """
    sac.quad(_p(a, z0), _p(b, z0), _p(b, z1), _p(a, z1), mat)      # dedans
    sac.quad(_p(B, z0), _p(A, z0), _p(A, z1), _p(B, z1), mat)      # dehors


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ---------------------------------------------------------------------------
# LE MOBILIER — quelques volumes, et l'on sait où l'on est
#
# Ce n'est pas de la décoration : une pièce nue ne se reconnaît pas. Quatre
# tables en long et une estrade DISENT la grande salle ; six paillasses disent
# les communs. On en met peu, et on ne cherche pas la scène de théâtre.
#
# Deux sources, dans cet ordre :
#  1. `plans.js` fait foi. Il porte déjà un vocabulaire d'`orne` par salle
#     (`orne: ["puits", 185, 92, 8]`) — un nom et un POINT, dans les unités du
#     plan. Le puits de la cour est là où le plan le met, comme la forme des
#     salles vient du plan et pas d'ailleurs.
#  2. Là où le plan ne dit rien, l'USAGE : des appartements ont un lit, une
#     galerie de taille a son établi. Table courte, et signalée comme telle.
#
# Les pièces sont écrites en MÈTRES, dans le repère de la salle : `du` le long
# de son grand axe, `dv` en travers, `dz` depuis le plancher. Ce qui suit se lit
# donc comme un plan de mobilier, pas comme de la géométrie.
#   ("b", du, dv, dz, demi_u, demi_v, hauteur, matière)   une boîte
#   ("c", du, dv, dz, rayon, hauteur, matière)            un cylindre
# ---------------------------------------------------------------------------
BOIS, PIERRE, TAILLE, FER, CHAUME, FEU = ("bois", "pierre", "taille",
                                          "basalte", "chaume", "toit")
DEGAGEMENT = 1.1     # ce qu'on laisse libre devant une porte, en mètres
NOMBRIL = 1.0        # …et autour du point où le joueur est posé


def _rond(n, r, faire):
    """n pièces en cercle de rayon r — tabourets, autels, tonneaux."""
    return [p for k in range(n)
            for p in faire(r * math.cos(2 * math.pi * k / n),
                           r * math.sin(2 * math.pi * k / n))]


def _colimacon(h):
    """Un noyau et ses marches : ce qui monte à l'étage, et qu'on voit monter."""
    p = [("c", 0, 0, 0, 0.35, max(2.5, h - 0.2), TAILLE)]
    n = max(8, int(h / 0.22))
    for k in range(n):
        a = k * 0.52
        p.append(("b", math.cos(a) * 0.95, math.sin(a) * 0.95, k * 0.21,
                  0.75, 0.28, 0.2, TAILLE))
    return p


MEUBLES = {
    # --- ce que le plan nomme ------------------------------------------------
    "puits": [("c", 0, 0, 0, 1.35, 0.85, TAILLE),
              ("b", -1.35, 0, 0.85, 0.09, 0.09, 2.1, BOIS),
              ("b", 1.35, 0, 0.85, 0.09, 0.09, 2.1, BOIS),
              ("b", 0, 0, 2.95, 1.5, 0.1, 0.14, BOIS)],
    "colimacon": None,                    # bâti à la hauteur de la pièce
    "ronde": [("c", 0, 0, 0, 2.0, 0.78, BOIS)] +
             _rond(8, 2.7, lambda x, y: [("c", x, y, 0, 0.22, 0.46, BOIS)]),
    "tables": [("b", 0, -3.1, 0, 7.5, 0.45, 0.78, BOIS),
               ("b", 0, 3.1, 0, 7.5, 0.45, 0.78, BOIS),
               ("b", 0, -4.0, 0, 7.5, 0.2, 0.45, BOIS),
               ("b", 0, 4.0, 0, 7.5, 0.2, 0.45, BOIS),
               ("b", -13.0, 0, 0, 2.4, 3.4, 0.35, BOIS),
               ("b", -14.6, 0, 0.35, 0.6, 0.9, 1.25, BOIS)],
    "table6": [("b", 0, 0, 0, 1.7, 0.5, 0.75, BOIS)] +
              [("c", u, v, 0, 0.2, 0.45, BOIS)
               for u in (-1.1, 0, 1.1) for v in (-1.0, 1.0)],
    "lances": [("b", 0, 0, 0, 1.4, 0.25, 0.25, BOIS),
               ("b", 0, 0, 1.7, 1.4, 0.1, 0.1, BOIS)] +
              [("c", u, 0, 0.25, 0.05, 2.0, BOIS) for u in (-1.1, -0.5, 0.2, 0.9)],
    "corbeau": [("b", 0, 0, 1.6 + k * 0.62, 1.3, 0.05, 0.06, BOIS)
                for k in range(3)] +
               [("b", -1.3, 0, 1.5, 0.06, 0.06, 2.1, BOIS),
                ("b", 1.3, 0, 1.5, 0.06, 0.06, 2.1, BOIS)],
    "etoile": _rond(7, 2.5, lambda x, y: [("c", x, y, 0, 0.36, 0.95, TAILLE)]),
    "arbres": [p for k in (-1, 0, 1)
               for p in (("c", k * 2.6, 0, 0, 0.26, 2.4, BOIS),
                         ("c", k * 2.6, 0, 2.4, 1.4, 1.9, CHAUME))],
    "paillasses": [("b", (k % 3 - 1) * 2.4, (k // 3) * 2.0 - 1.0, 0,
                    0.95, 0.32, 0.24, CHAUME) for k in range(6)],
    "lit": [("b", 0, 0, 0, 1.05, 0.85, 0.5, BOIS),
            ("b", -1.05, 0, 0.5, 0.08, 0.85, 1.1, BOIS),
            ("b", 1.5, -0.6, 0, 0.5, 0.3, 0.45, BOIS)],
    "toiles": [("b", k * 1.7, 0, 0, 1.1, 0.85, 1.15, CHAUME) for k in (-1, 1)],
    "barreaux": [("b", u, 0, 0, 0.05, 0.05, 2.2, FER)
                 for u in (-1.2, -0.72, -0.24, 0.24, 0.72, 1.2)] +
                [("b", 0, 0, 2.2, 1.3, 0.06, 0.08, FER),
                 ("b", 0, 1.6, 0, 0.9, 0.5, 0.16, CHAUME)],
    "rouleau": [("b", 0, v, z, 1.6, 0.28, 0.06, BOIS)
                for v in (-0.9, 0.9) for z in (0.55, 1.15, 1.75)] +
               [("b", u, v, 0, 0.06, 0.28, 2.0, BOIS)
                for u in (-1.6, 1.6) for v in (-0.9, 0.9)],
    "nef": [("b", 0, 0, 0, 3.2, 0.85, 1.1, BOIS),
            ("b", 0, 0, 1.1, 0.1, 0.1, 3.4, BOIS)],
    "chaudron": [("b", 0, -1.0, 0, 1.5, 0.7, 1.0, PIERRE),
                 ("c", 0, -1.0, 1.0, 0.55, 0.65, FER),
                 ("b", 0, 1.3, 0, 1.2, 0.5, 0.85, BOIS)],
    "tonneaux": _rond(5, 1.6, lambda x, y: [("c", x, y, 0, 0.44, 1.0, BOIS)]),
    "cierge": [("b", 0, 0, 0, 1.15, 0.45, 0.62, PIERRE),
               ("c", -1.4, 0, 0, 0.09, 0.95, BOIS),
               ("c", 1.4, 0, 0, 0.09, 0.95, BOIS)],
    "cuve": [("c", -1.2, 0, 0, 0.9, 0.82, BOIS),
             ("c", 1.2, 0, 0, 0.9, 0.82, BOIS)],
    "berceau": [("b", 0, 0, 0.22, 0.52, 0.34, 0.42, BOIS),
                ("b", 0, 0, 0, 0.52, 0.08, 0.22, BOIS),
                ("b", 1.4, 0, 0, 0.5, 0.32, 0.45, BOIS)],
    "banc": [("b", 0, 0, 0, 2.2, 0.22, 0.46, BOIS),
             ("b", 0, 0.25, 0.46, 2.2, 0.06, 0.5, BOIS)],
    "fiole": [("b", 0, 0, 0, 1.4, 0.4, 0.85, BOIS),
              ("b", 0, 0.3, 1.5, 1.4, 0.2, 0.06, BOIS)] +
             [("c", u, 0, 0.85, 0.07, 0.22, BOIS) for u in (-0.6, -0.2, 0.3)],
    "enclume": [("c", 0, 0, 0, 0.38, 0.5, BOIS),
                ("b", 0, 0, 0.5, 0.42, 0.16, 0.26, FER),
                ("b", 0, 1.9, 0, 1.1, 0.7, 1.0, PIERRE)],
    "herse": [("b", u, 0, 0, 0.06, 0.12, 2.3, FER)
              for u in (-1.2, -0.6, 0, 0.6, 1.2)] +
             [("b", 0, 0, z, 1.3, 0.14, 0.1, FER) for z in (0.8, 2.3)],
    "quintaine": [("c", 0, 0, 0, 0.18, 2.3, BOIS),
                  ("b", 0, 0, 2.1, 1.3, 0.09, 0.1, BOIS),
                  ("b", 1.2, 0, 1.6, 0.16, 0.16, 0.5, BOIS)],
    "coques": [("b", k * 3.2, 0, 0, 2.4, 0.75, 0.9, BOIS) for k in (-1, 1)],
    "flamme": [("c", 0, 0, 0, 1.3, 0.5, FER), ("c", 0, 0, 0.5, 0.95, 0.9, FEU)],
    # le chemin de ronde a déjà son parapet : ses créneaux SONT le mur
    "creneaux": [],
    # --- ce que l'usage demande, là où le plan ne dit rien -------------------
    "coffre": [("b", 0, 0, 0, 0.65, 0.35, 0.5, BOIS),
               ("b", 1.6, 0, 0, 0.5, 0.32, 0.42, BOIS)],
    "etabli": [("b", 0, 0, 0, 1.5, 0.45, 0.82, BOIS),
               ("b", 0, 0, 0.82, 0.5, 0.3, 0.12, FER),
               ("c", 2.0, 0, 0, 0.3, 0.55, TAILLE)],
}

# Ce que l'usage réclame là où `plans.js` ne pose aucun ornement. Court exprès :
# meubler ce que le plan ne nomme pas, c'est inventer, et l'on n'invente qu'au
# strict nécessaire — une chambre sans lit ne se reconnaît pas, une tour de guet
# sans rien se reconnaît très bien.
USAGE = {
    "appartements-reine": ["lit", "coffre"],
    "tour-dragon-mer": ["coffre"],
    "galeries": ["etabli"],
}


def _axe(poly):
    """Le grand axe d'une pièce, en vecteur unitaire — les tables suivent la salle."""
    long_pan, ux, uy = 0.0, 1.0, 0.0
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        d = math.dist(a, b)
        if d > long_pan:
            long_pan, ux, uy = d, (b[0] - a[0]) / d, (b[1] - a[1]) / d
    return ux, uy


def _bord(poly, x, y):
    """La distance d'un point au mur le plus proche — négative s'il est dehors."""
    d = min(_sur_pan(poly, i, (x, y))[1] for i in range(len(poly)))
    return d if dedans(poly, x, y) else -d


def _rentrer(poly, p, centre, marge=0.7):
    """Ramener une ancre à l'intérieur de la pièce, sans plus.

    Le plan pose ses ornements pour l'œil du dessus ; il lui arrive de les
    mettre sur le trait du mur. On ne cherche pas à le corriger — seulement à
    ce que le meuble soit DANS la pièce.
    """
    x, y = p
    for _tour in range(24):
        if _bord(poly, x, y) > marge:
            return (x, y)
        # On rentre PERPENDICULAIREMENT au mur le plus proche, pas vers le
        # centre : un banc est contre son mur, et le tirer au milieu de la pièce
        # le met sous les pieds du joueur — qui est justement au milieu.
        i = min(range(len(poly)), key=lambda k: _sur_pan(poly, k, (x, y))[1])
        nx, ny = normale(poly[i], poly[(i + 1) % len(poly)])
        x, y = x - nx * 0.4, y - ny * 0.4
    return centre


def _poser_pieces(sac, pieces, x, y, z, ux, uy, k, genants):
    """Les volumes d'un meuble, orientés comme la pièce — et TRIÉS.

    On écarte à la PIÈCE et non au meuble entier : déplacer les deux tables de
    la grande salle parce que l'estrade tombe devant une porte, c'est déménager
    la salle pour une planche. Une planche qui gêne se retire, les autres
    restent où le plan les a mises. Rend (posées, retirées).
    """
    vx, vy = -uy, ux
    pose, hors = 0, 0
    for pc in pieces:
        du, dv = pc[1], pc[2]
        cx = x + ux * du * k + vx * dv * k
        cy = y + uy * du * k + vy * dv * k
        rayon = (math.hypot(pc[4], pc[5]) if pc[0] == "b" else pc[4]) * k
        if any(math.hypot(cx - gx, cy - gy) < r + rayon for (gx, gy, r) in genants):
            hors += 1
            continue
        if pc[0] == "b":
            _boite(sac, cx, cy, z + pc[3] * k, pc[4] * k, pc[5] * k, pc[6] * k,
                   pc[7], ux, uy)
        else:
            _cylindre(sac, cx, cy, z + pc[3] * k, pc[4] * k, pc[5] * k, pc[6])
        pose += 1
    return pose, hors


def _boite(sac, cx, cy, z, dx, dy, h, mat, ux=1.0, uy=0.0):
    vx, vy = -uy, ux
    c = [(cx - ux * dx - vx * dy, cy - uy * dx - vy * dy),
         (cx + ux * dx - vx * dy, cy + uy * dx - vy * dy),
         (cx + ux * dx + vx * dy, cy + uy * dx + vy * dy),
         (cx - ux * dx + vx * dy, cy - uy * dx + vy * dy)]
    for i in range(4):
        a, b = c[i], c[(i + 1) % 4]
        sac.quad(_p(a, z), _p(b, z), _p(b, z + h), _p(a, z + h), mat)
    sac.quad(_p(c[0], z + h), _p(c[1], z + h), _p(c[2], z + h), _p(c[3], z + h), mat)
    sac.quad(_p(c[3], z), _p(c[2], z), _p(c[1], z), _p(c[0], z), mat)


def _cylindre(sac, cx, cy, z, r, h, mat, cotes=8):
    c = [(cx + r * math.cos(2 * math.pi * k / cotes),
          cy + r * math.sin(2 * math.pi * k / cotes)) for k in range(cotes)]
    for i in range(cotes):
        a, b = c[i], c[(i + 1) % cotes]
        sac.quad(_p(a, z), _p(b, z), _p(b, z + h), _p(a, z + h), mat)
    for i in range(1, cotes - 1):
        sac.tri(_p(c[0], z + h), _p(c[i], z + h), _p(c[i + 1], z + h), mat)
        sac.tri(_p(c[i + 1], z), _p(c[i], z), _p(c[0], z), mat)


def meubler(sac, s, poly, z0, h, portes, centre, vers, rapport):
    """Ce qu'il y a DANS la pièce. Rend le nombre de meubles posés."""
    ux, uy = _axe(poly)
    lg, la = _oriente(poly)
    poses, sautes = 0, []

    # 1. ce que le plan nomme, à la place que le plan lui donne
    voulus = []
    for m in re.finditer(r'orne:\s*\[\s*"([^"]+)"\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)',
                         s["corps"]):
        voulus.append((m.group(1), vers(float(m.group(2)), -float(m.group(3)))))
    # 2. et ce que l'usage réclame là où il n'a rien nommé
    if not voulus:
        for nom in USAGE.get(s["id"], []):
            voulus.append((nom, None))

    for i, (nom, ou) in enumerate(voulus):
        pieces = _colimacon(h) if nom == "colimacon" else MEUBLES.get(nom)
        if pieces is None:
            sautes.append((nom, "pas de volume écrit pour cet ornement"))
            continue
        if not pieces:
            continue
        # l'encombrement du meuble, pour le rentrer dans une petite pièce
        etendue = max(max(abs(p[1]) + (p[4] if p[0] == "b" else p[4]),
                          abs(p[2]) + (p[5] if p[0] == "b" else p[4]))
                      for p in pieces)
        haut = max((p[3] + p[6]) if p[0] == "b" else (p[3] + p[5]) for p in pieces)
        k = min(1.0, (min(lg, la) - 1.6) / (2 * etendue) if etendue > 0 else 1.0,
                (h - 0.4) / haut if haut > 0 else 1.0)
        if k < 0.28:
            sautes.append((nom, "la pièce est trop petite (%.0f %%)" % (k * 100)))
            continue
        if ou is None:                      # sans point du plan : le long du mur
            ou = (centre[0] + ux * (lg * 0.26) - uy * (la * 0.24) * (1 if i % 2 else -1),
                  centre[1] + uy * (lg * 0.26) + ux * (la * 0.24) * (1 if i % 2 else -1))
        cale = _rentrer(poly, ou, centre, 0.6 + etendue * k * 0.25)
        genants = [(d["x"], d["y"], DEGAGEMENT) for d in portes]
        genants.append((centre[0], centre[1], NOMBRIL))
        n_pose, n_hors = _poser_pieces(sac, pieces, cale[0], cale[1], z0,
                                       ux, uy, k, genants)
        if not n_pose:
            sautes.append((nom, "tout tombait devant une porte ou sous vos pieds"))
            continue
        if n_hors:
            sautes.append((nom, "%d volume(s) sur %d retiré(s) : porte ou passage"
                           % (n_hors, n_pose + n_hors)))
        poses += 1
    rapport["meubles"] += [(s["id"], n, q) for (n, q) in sautes]
    return poses


# ---------------------------------------------------------------------------
# bâtir une salle
# ---------------------------------------------------------------------------
def projeter(s):
    """De l'unité de plan au mètre du monde, POUR CETTE SALLE.

    Ce n'est pas une transformation globale : chaque salle est remise à sa
    propre mesure autour de son propre centre. Un ornement du plan (un puits,
    une enclume) doit passer par la MÊME, sans quoi il tombe hors de sa pièce.
    """
    cle = s["id"]
    vise = None if cle in SANS_MESURE else sum(Li.mesures(cle)[:2]) / 2
    pts = contour_plan(s["corps"], vise)
    if not pts or len(pts) < 3:
        return None, None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    if cle in SANS_MESURE:
        kx = ky = 1.0
    else:
        lg, la, _h = Li.mesures(cle)
        w = max(1e-6, max(xs) - min(xs))
        hh = max(1e-6, max(ys) - min(ys))
        # `_S` est le facteur du calage : diviser par lui rend des unités de
        # plan, que `_vers_local` remultipliera. On ne le court-circuite pas.
        kx = (lg / Li._S) / w
        ky = (la / Li._S) / hh

    # LE PLAN MENT SUR LA PLACE DE CINQ SALLES, et il le dit lui-même : le quai,
    # la grève, le bourg, le grand escalier et le chemin de ronde y sont posés
    # près du mur pour tenir dans la page, alors qu'ils sont à cinq cents mètres
    # et cent vingt mètres plus bas. `lieux.SCHEMATIQUE` les nomme et
    # `lieux.reperes_reels()` donne leur vraie place — c'est ce dont se servent
    # déjà `blender_batir.py` et `vues.py`. Ne pas le faire ici mettait le quai
    # sur le plateau du château : une salle « le quai » à cent vingt mètres
    # au-dessus de la mer, et des barques posées sur la falaise.
    dx = dy = 0.0
    if cle in Li.SCHEMATIQUE:
        vrai = _ancrages().get(cle)
        if vrai:
            loc0 = Li._vers_local((cx, cy))
            w0 = P._monde(loc0)
            dx = vrai[0] - (w0[0] + DECALAGE[0])
            dy = vrai[1] - (w0[1] + DECALAGE[1])

    def vers(x, y):
        loc = Li._vers_local((cx + (x - cx) * kx, cy + (y - cy) * ky))
        wx, wy = P._monde(loc)
        return (wx + DECALAGE[0] + dx, wy + DECALAGE[1] + dy)

    return pts, vers


_ANCRAGES = None


def _ancrages():
    """Les cinq salles que le plan déplace, ancrées sur le modèle.

    `Li.reperes_reels()` rend des couples (point, nom) — on les recroise avec
    les noms de `Li.lieux()` pour retrouver l'id. Le point est dans le repère de
    la matérialisation ; il passe par le même décalage que le reste.
    """
    global _ANCRAGES
    if _ANCRAGES is not None:
        return _ANCRAGES
    par_nom = {L["nom"]: L["id"] for L in Li.lieux() if L["id"] in Li.SCHEMATIQUE}
    _ANCRAGES = {}
    for p, nom in Li.reperes_reels():
        cle = par_nom.get(nom)
        if cle:
            _ANCRAGES[cle] = (p[0] + DECALAGE[0], p[1] + DECALAGE[1], p[2])
    return _ANCRAGES


def emprise(s):
    """Le contour intérieur d'une salle, en mètres dans le repère du monde."""
    pts, vers = projeter(s)
    if not pts:
        return None
    return nettoyer(anti_horaire([vers(x, y) for (x, y) in pts]))


def _oriente(poly):
    """Longueur et largeur d'une emprise DANS SON PROPRE SENS, en mètres.

    La boîte alignée sur les axes du monde ne mesure rien : le château est de
    biais, et une grande salle de 44 × 15 y rend 46 × 28. On projette donc le
    contour sur l'axe qui porte son plus long pan.
    """
    long_pan, ux, uy = 0.0, 1.0, 0.0
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        d = math.dist(a, b)
        if d > long_pan:
            long_pan, ux, uy = d, (b[0] - a[0]) / d, (b[1] - a[1]) / d
    u = [p[0] * ux + p[1] * uy for p in poly]
    v = [-p[0] * uy + p[1] * ux for p in poly]
    a, b = max(u) - min(u), max(v) - min(v)
    return (max(a, b), min(a, b))


def hauteur(cle):
    """La hauteur sous plafond, en mètres."""
    if cle in OUVERT:
        return PARAPET
    return max(2.8, Li.mesures(cle)[2])


# ---------------------------------------------------------------------------
# LES ALTITUDES — une salle se pose sur ce qui la porte
#
# `lieux()` monte TOUT étage « sommet » à l'assise + 34 m, quelle que soit la
# hauteur de la tour qui le porte : la Table Peinte se retrouvait à 158 m au-
# dessus d'un Tambour dont le plafond est à 132. Vingt-six mètres de vide, et
# la pièce flotte dès qu'on la voit depuis sa voisine.
#
# On ne corrige PAS `lieux()` : `peyredragon_chateau.py` s'en sert pour poser
# ses volumes dans le bâti, et lui déplacer ses planchers déplacerait 795 corps
# sans qu'on l'ait demandé. La correction vit ici, et ici seulement.
#
# La règle : l'altitude se dérive de la salle qui CONTIENT celle-ci — un étage
# se pose sur le plafond de sa tour, une salle taillée se creuse sous le
# plancher de ce qu'elle porte. La containment se lit dans le tracé du plan,
# qui est la source pour tout le reste (`Li._SALLES` ne contient QUE le bloc
# `peyredragon:` — le Donjon Rouge est lu par ailleurs et n'entre jamais ici).
# ---------------------------------------------------------------------------
PLANCHER = 0.5          # l'épaisseur d'un plancher entre deux étages, en mètres
PROF_DEFAUT = 6.0       # à défaut de tout, on creuse de six mètres
ETAGE_NU = 4.5          # …et à défaut d'hôte, on monte d'un étage ordinaire


def _hotes():
    """Pour chaque salle d'étage, la salle de plain-pied qui la contient."""
    tracks = {}
    for s in Li._SALLES:
        pts = contour_plan(s["corps"])
        if pts and len(pts) >= 3:
            tracks[s["id"]] = (pts, abs(aire(pts)))
    out = {}
    for s in Li._SALLES:
        if not s["etage"] or s["id"] not in tracks:
            continue
        pts, _a = tracks[s["id"]]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        mieux = None
        for t in Li._SALLES:
            # Un hôte est de plain-pied, COUVERT, et plus grand que ce qu'il
            # porte. La condition « couvert » n'est pas cosmétique : le tracé
            # de la cour est l'enceinte entière, elle contient donc toutes les
            # salles du plan — et l'on ne bâtit pas un étage sur un pavé.
            if t["etage"] or t["dehors"] or t["id"] == s["id"] or t["id"] in OUVERT:
                continue
            if t["id"] not in tracks:
                continue
            tp, ta = tracks[t["id"]]
            if ta <= tracks[s["id"]][1]:
                continue
            if not dedans(tp, cx, cy):
                continue
            if mieux is None or ta < mieux[1]:
                mieux = (t["id"], ta)
        if mieux:
            out[s["id"]] = mieux[0]
    return out


_ALT = None
_ALT_NOTES = None


def altitudes():
    """Le z du plancher de chaque salle, et comment on l'a obtenu."""
    global _ALT, _ALT_NOTES
    if _ALT is not None:
        return _ALT, _ALT_NOTES
    hotes = _hotes()
    par_id = {s["id"]: s for s in Li.lieux()}
    z, note = {}, {}
    # 1. le plain-pied et le dehors : ce que `lieux()` en dit déjà, et il a raison
    anc = _ancrages()
    for cle, s in par_id.items():
        if s["etage"]:
            continue
        # Les cinq salles déplacées prennent AUSSI leur altitude du modèle : le
        # relief sous le point du plan est celui du plateau, et lire `ou[2]` y
        # donnait 124 m pour un quai qui est à 3,4 m.
        if cle in anc:
            z[cle] = anc[cle][2]
            note[cle] = "ancrée sur le modèle (lieux.reperes_reels)"
            continue
        z[cle] = s["ou"][2]
        note[cle] = "dehors, sur le relief" if s["dehors"] else "de plain-pied, sur l'assise"
    # 2. les étages, dérivés de leur hôte
    for cle, s in par_id.items():
        if s["etage"] != "sommet":
            continue
        h = hotes.get(cle)
        if h and h in z:
            z[cle] = z[h] + hauteur(h) + PLANCHER
            note[cle] = "sur le plafond de %s" % h
        else:
            # Un logis isolé dont le rez n'est pas dessiné : son étage se pose
            # une hauteur d'homme et demie au-dessus de l'assise, pas à
            # vingt-six mètres dans le ciel. C'est arbitraire, et signalé.
            z[cle] = P.ASSISE + ETAGE_NU
            note[cle] = "SANS HÔTE — un étage nu au-dessus de l'assise"
    # 3. ce qui est taillé sous l'assise
    for cle, s in par_id.items():
        if s["etage"] != "dessous":
            continue
        h = hauteur(cle)
        if cle in Li.PROFONDEUR:
            z[cle] = P.ASSISE - Li.PROFONDEUR[cle] - h
            note[cle] = "plafond à %.0f m sous l'assise (lieux.PROFONDEUR)" % Li.PROFONDEUR[cle]
        elif hotes.get(cle) in z:
            hote = hotes[cle]
            z[cle] = z[hote] - PLANCHER - h
            note[cle] = "sous le plancher de %s" % hote
        else:
            z[cle] = P.ASSISE - PROF_DEFAUT - h
            note[cle] = "SANS HÔTE NI PROFONDEUR — creusée d'autorité de %.0f m" % PROF_DEFAUT
    _ALT, _ALT_NOTES = z, note
    return _ALT, _ALT_NOTES


def sol_et_haut(s):
    """Le z du plancher et la hauteur sous plafond, en mètres."""
    z, _n = altitudes()
    cle = s["id"]
    return z.get(cle, s["ou"][2]), hauteur(cle)


def matieres(s):
    """De quoi sont faits le sol, les murs et le plafond."""
    if s["etage"] == "dessous":
        return "basalte", "taille", "basalte"
    if s["id"] in OUVERT:
        return "quai", "mur-bourg", None
    return "taille", "pierre", "bois"


# ---------------------------------------------------------------------------
# LES PORTES — un trou, un encadrement, et un vantail quand il y a lieu
#
# Il n'existe AUCUN état de porte dans `etat/`, et ce script n'en crée pas :
# ouvrir ou barrer une porte est une décision de jeu, pas de géométrie. L'état
# posé ici est donc DÉRIVÉ de ce que sont les deux pièces, en trois valeurs, et
# il est écrit dans le JSON pour qu'une scène puisse un jour le contredire.
# ---------------------------------------------------------------------------
# Ce qu'on ferme à clef ou qu'on tient pour soi : la porte y est close.
PRIVE = {"appartements-reine", "chambre-enfants", "table-peinte", "cachots",
         "archives", "cellier", "salle-froide", "officine", "etuves"}
# Ce qui travaille : la porte y est poussée, jamais tout à fait fermée.
SERVICE = {"cuisines", "communs", "roukerie", "forge", "chambres-hotes",
           "antichambre", "baraques", "galeries", "porte-dragon", "porte-de-mer"}
# Ce qu'on barre pour de bon.
BARREES = {"cachots"}


def huisserie(ici, la_bas):
    """(genre, état, barrée) d'un passage entre deux salles.

    Un passage n'est pas toujours une porte : entre deux endroits à ciel ouvert
    — la cour et le jardin, le quai et la grève —, c'est une arche ou rien du
    tout, et l'on n'y pend pas de battant.
    """
    if ici in OUVERT and la_bas in OUVERT:
        return "baie", "ouverte", False
    barree = ici in BARREES or la_bas in BARREES
    if barree or ici in PRIVE or la_bas in PRIVE:
        return "porte", "close", barree
    if ici in SERVICE or la_bas in SERVICE:
        return "porte", "poussee", False
    return "porte", "ouverte", False


ANGLE = {"close": 0.0, "poussee": 55.0, "ouverte": 88.0}
VANTAIL_EP = 0.07


def poser_vantail(sac, a, b, A, B, t0, t1, z0, etat):
    """Le battant, pendu au jambage de gauche, et ses deux pentures.

    Il pivote autour du gond : à 0° il ferme le trou, à 88° il est rangé contre
    son mur et le passage est libre. Ce n'est pas un réglage d'apparence — un
    battant laissé en travers de son embrasure, on ne peut plus passer.
    """
    gond = lerp(a, b, t0)
    loin = lerp(a, b, t1)
    L = math.dist(gond, loin)
    if L < 0.4:
        return None
    ux, uy = (loin[0] - gond[0]) / L, (loin[1] - gond[1]) / L
    # la normale RENTRANTE : le vantail bat vers l'intérieur de la pièce
    nx, ny = normale(a, b)
    nx, ny = -nx, -ny
    th = math.radians(ANGLE[etat])
    dx, dy = ux * math.cos(th) + nx * math.sin(th), uy * math.cos(th) + ny * math.sin(th)
    # l'épaisseur, prise en travers du battant
    ex, ey = -dy, dx
    # posé dans l'épaisseur du mur quand il ferme, contre sa face quand il ouvre
    recul = (EPAISSEUR / 2 - VANTAIL_EP / 2) * math.cos(th)
    ox, oy = gond[0] + nx * -recul, gond[1] + ny * -recul
    cx, cy = ox + dx * L / 2, oy + dy * L / 2
    haut = PORTE_H - 0.05
    _boite(sac, cx, cy, z0 + 0.02, L / 2, VANTAIL_EP / 2, haut, BOIS, dx, dy)
    for zz in (0.35, haut - 0.4):               # les pentures
        _boite(sac, ox + dx * L * 0.42, oy + dy * L * 0.42, z0 + zz,
               L * 0.42, VANTAIL_EP / 2 + 0.015, 0.07, FER, dx, dy)
    _cylindre(sac, ox + dx * (L - 0.16) - ex * 0.06,
              oy + dy * (L - 0.16) - ey * 0.06, z0 + 1.05, 0.05, 0.1, FER, 6)
    # ce qu'il faut pour vérifier qu'il ne bouche rien : son rectangle au sol
    return {"gond": [round(gond[0], 2), round(gond[1], 2)],
            "axe": [round(dx, 3), round(dy, 3)], "long": round(L, 2),
            "angle": ANGLE[etat]}


def passage_libre(ai, bi, ao, bo, battant, marge=0.02):
    """Vrai si le battant ne couvre aucun point du passage."""
    gx, gy = battant["gond"]
    dx, dy = battant["axe"]
    L, ep = battant["long"], VANTAIL_EP / 2 + marge
    for u in range(1, 6):                       # d'un jambage à l'autre
        p0 = lerp(ai, bi, u / 6.0)
        p1 = lerp(ao, bo, u / 6.0)
        for v in range(0, 4):                   # d'une face du mur à l'autre
            x, y = lerp(p0, p1, v / 3.0)
            s = (x - gx) * dx + (y - gy) * dy
            t = -(x - gx) * dy + (y - gy) * dx
            if -0.02 <= s <= L + 0.02 and abs(t) <= ep:
                return False
    return True


def encadrement(sac, a, b, A, B, t0, t1, z0, mat=TAILLE):
    """Deux piédroits et un linteau de pierre de taille, sur la face intérieure.

    L'embrasure nue se lit comme un trou dans un mur ; l'encadrement se lit
    comme une porte, et c'est tout ce qu'on lui demande.
    """
    zp = z0 + PORTE_H
    ux, uy = normale(a, b)
    dl = 0.11                                    # la saillie dans la pièce
    for u in (t0, t1):
        p = lerp(a, b, u)
        _boite(sac, p[0] - ux * dl / 2, p[1] - uy * dl / 2, z0,
               0.09, dl / 2, PORTE_H + 0.13, mat, *_dir(a, b))
    m = lerp(a, b, (t0 + t1) / 2)
    L = math.dist(lerp(a, b, t0), lerp(a, b, t1))
    _boite(sac, m[0] - ux * dl / 2, m[1] - uy * dl / 2, zp,
           L / 2 + 0.09, dl / 2, 0.13, mat, *_dir(a, b))


def _dir(a, b):
    d = math.dist(a, b) or 1.0
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def batir_salle(s, portes_voulues, rapport):
    """Une pièce creuse et ses ouvertures. Rend (sac, fiche) ou (None, None)."""
    inner = emprise(s)
    if not inner or len(inner) < 3:
        rapport["sans_forme"].append(s["id"])
        return None, None
    outer = decaler(inner, EPAISSEUR)
    z0, h = sol_et_haut(s)
    z1 = z0 + h
    m_sol, m_mur, m_plafond = matieres(s)
    sac = Sac()

    # ---- les ouvertures, rangées par pan --------------------------------
    par_pan, pris = {}, {}
    posees, ratees, vantaux = [], [], []
    for (vers, cible) in portes_voulues:
        if h < PORTE_H + 0.2:
            ratees.append((vers, "mur de %.1f m, plus bas que la porte" % h))
            continue
        i, t0, t1 = placer_porte(inner, cible, pris)
        if i is None:
            ratees.append((vers, t0))
            continue
        par_pan.setdefault(i, []).append((t0, t1, vers))
        pris.setdefault(i, []).append((t0, t1))
        a, b = inner[i], inner[(i + 1) % len(inner)]
        p = lerp(a, b, (t0 + t1) / 2)
        nx, ny = normale(a, b)                    # la normale SORTANTE du pan
        g, e, barree = huisserie(s["id"], vers)
        # Le vantail est bâti UNE FOIS pour les deux pièces : la plus petite par
        # l'id le porte. Sans cette règle, le même passage aurait deux battants
        # — et comme chaque salle a son propre mur, on en verrait deux.
        porte_le = (g == "porte" and s["id"] == min(s["id"], vers))
        d = {"vers": vers, "x": round(p[0], 2), "y": round(p[1], 2),
             "z": round(z0, 2),
             # Le cap de la normale sortante, en degrés depuis le levant : c'est
             # à lui qu'on accroche un vantail, et sans lui une porte ouverte
             # s'ouvre au hasard.
             "cap": round(math.degrees(math.atan2(ny, nx)) % 360, 1),
             "normale": [round(nx, 3), round(ny, 3)],
             "demi_l": round(PORTE_L / 2, 2), "haut": PORTE_H,
             "genre": g, "etat": e, "barree": barree,
             "gond": "gauche", "bat": "dedans", "vantail": porte_le}
        posees.append(d)
        if porte_le:
            vantaux.append((i, t0, t1, d))

    # ---- les murs --------------------------------------------------------
    n = len(inner)
    zp = z0 + PORTE_H
    for i in range(n):
        a, b = inner[i], inner[(i + 1) % n]
        A, B = outer[i], outer[(i + 1) % n]
        # l'arase et l'assise : l'anneau se ferme en haut et en bas, sur toute
        # sa longueur — le bas passe SOUS les embrasures et leur fait le seuil.
        sac.quad(_p(a, z1), _p(b, z1), _p(B, z1), _p(A, z1), m_mur)
        sac.quad(_p(A, z0), _p(B, z0), _p(b, z0), _p(a, z0), m_sol)
        trous = sorted(par_pan.get(i, []))
        if not trous:
            pan(sac, a, b, A, B, z0, z1, m_mur)
            continue
        bornes = [0.0]
        for (t0, t1, _v) in trous:
            bornes += [t0, t1]
        bornes.append(1.0)
        for k in range(0, len(bornes) - 1, 2):    # les pleins, de fond en comble
            u0, u1 = bornes[k], bornes[k + 1]
            if u1 - u0 < 1e-4:
                continue
            pan(sac, lerp(a, b, u0), lerp(a, b, u1),
                lerp(A, B, u0), lerp(A, B, u1), z0, z1, m_mur)
        for (t0, t1, _v) in trous:
            # le linteau au-dessus du trou, puis l'embrasure : deux jambages et
            # le dessous du linteau. Le seuil, c'est l'assise, déjà posée.
            pan(sac, lerp(a, b, t0), lerp(a, b, t1),
                lerp(A, B, t0), lerp(A, B, t1), zp, z1, m_mur)
            # L'embrasure est en pierre de TAILLE, pas dans la matière du mur :
            # une porte se voit d'abord à ce que son encadrement est appareillé.
            for (u, sens) in ((t0, 1), (t1, -1)):
                ai, ao = lerp(a, b, u), lerp(A, B, u)
                q = [_p(ai, z0), _p(ao, z0), _p(ao, zp), _p(ai, zp)]
                if sens > 0:
                    sac.quad(q[0], q[1], q[2], q[3], TAILLE)
                else:
                    sac.quad(q[3], q[2], q[1], q[0], TAILLE)
            sac.quad(_p(lerp(a, b, t0), zp), _p(lerp(a, b, t1), zp),
                     _p(lerp(A, B, t1), zp), _p(lerp(A, B, t0), zp), TAILLE)
            encadrement(sac, a, b, A, B, t0, t1, z0)

    # ---- la dalle et le plafond ------------------------------------------
    for (i0, i1, i2) in trianguler(inner):
        a, b, c = inner[i0], inner[i1], inner[i2]
        sac.tri((a[0], a[1], z0), (b[0], b[1], z0), (c[0], c[1], z0), m_sol)
        if m_plafond:
            sac.tri((c[0], c[1], z1), (b[0], b[1], z1), (a[0], a[1], z1), m_plafond)

    # ---- ce qui n'est pas la coque : les vantaux, puis le mobilier ---------
    sac.part = "dedans"
    for (i, t0, t1, d) in vantaux:
        a, b = inner[i], inner[(i + 1) % n]
        A, B = outer[i], outer[(i + 1) % n]
        pose = poser_vantail(sac, a, b, A, B, t0, t1, z0, d["etat"])
        if pose is None:
            d["vantail"] = False
            rapport["ratees"].append((s["id"], d["vers"], "vantail trop étroit"))
        else:
            d["battant"] = pose
            # Peut-on encore passer ? On sème le rectangle du passage — d'un
            # jambage à l'autre, de la face intérieure à l'extérieure — et l'on
            # regarde si le battant en couvre un point. Un vantail OUVERT qui
            # reste en travers de son embrasure est un mur, pas une porte.
            d["libre"] = passage_libre(
                lerp(a, b, t0), lerp(a, b, t1), lerp(A, B, t0), lerp(A, B, t1),
                pose)
            if d["etat"] == "ouverte" and not d["libre"]:
                rapport["ratees"].append(
                    (s["id"], d["vers"], "vantail ouvert en travers du passage"))

    xs = [p[0] for p in inner]
    ys = [p[1] for p in inner]
    # Le centre est celui de la plus grande oreille, pas la moyenne des coins :
    # le chemin de ronde et la cour ne sont pas convexes, et leur moyenne tombe
    # hors de la pièce — c'est là qu'on plante la caméra, ça ne peut pas mentir.
    tris = trianguler(inner)
    gros = max(tris, key=lambda t: abs(_tri_aire(inner[t[0]], inner[t[1]],
                                                 inner[t[2]]))) if tris else None
    if gros:
        cx = sum(inner[k][0] for k in gros) / 3
        cy = sum(inner[k][1] for k in gros) / 3
    else:
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    lg, la = _oriente(inner)
    # ---- le mobilier, en dernier : il doit éviter les portes et les pieds --
    _pts, vers_monde = projeter(s)
    tri_avant = len(sac.tris)
    n_meubles = meubler(sac, s, inner, z0, h, posees, (cx, cy), vers_monde,
                        rapport) if vers_monde else 0
    fiche = {
        "id": s["id"], "nom": s["nom"], "etage": s["etage"],
        "centre": [round(cx, 2), round(cy, 2), round(z0, 2)],
        "sol_z": round(z0, 2), "hauteur": round(h, 2),
        "couvert": m_plafond is not None,
        "long_m": round(lg, 1), "larg_m": round(la, 1),
        "boite": [round(min(xs), 2), round(min(ys), 2),
                  round(max(xs), 2), round(max(ys), 2)],
        "contour": [[round(x, 2), round(y, 2)] for (x, y) in inner],
        "portes": posees,
        "meubles": n_meubles,
    }
    rapport["ratees"] += [(s["id"], v, q) for (v, q) in ratees]
    rapport["tris_meubles"] = rapport.get("tris_meubles", 0) + len(sac.tris) - tri_avant
    return sac, fiche


# ---------------------------------------------------------------------------
# assembler
# ---------------------------------------------------------------------------
def voisins():
    """Qui touche qui, d'après etat/chemins.json."""
    d = tables.lire(CHEMINS)
    alias = d.get("alias", {})
    v, aretes = {}, []
    for a in d["aretes"]:
        x, y = alias.get(a[0], a[0]), alias.get(a[1], a[1])
        if x == y:
            continue
        aretes.append((x, y))
        v.setdefault(x, set()).add(y)
        v.setdefault(y, set()).add(x)
    return v, aretes


def engendrer():
    salles = {s["id"]: s for s in Li.lieux()}
    # `lieux()` ne garde pas le tracé : on le reprend de la lecture du plan.
    for s in Li._SALLES:
        if s["id"] in salles:
            salles[s["id"]]["corps"] = s["corps"]

    vois, aretes = voisins()
    centres = {}
    for cle, s in salles.items():
        e = emprise(s)
        if e:
            centres[cle] = (sum(p[0] for p in e) / len(e),
                            sum(p[1] for p in e) / len(e))

    rapport = {"sans_forme": [], "ratees": [], "inconnues": set(),
               "meubles": [], "tris_meubles": 0}
    for (x, y) in aretes:
        for c in (x, y):
            if c not in salles:
                rapport["inconnues"].add(c)

    sommets, index, groupes, fiches = [], [], [], []
    cache = {}

    def pousser(p):
        cle = (round(p[0], 3), round(p[1], 3), round(p[2], 3))
        i = cache.get(cle)
        if i is None:
            i = len(sommets) // 3
            cache[cle] = i
            sommets.extend(cle)
        return i

    for cle in sorted(salles):
        s = salles[cle]
        veut = [(v, centres[v]) for v in sorted(vois.get(cle, ()))
                if v in centres and v != cle]
        sac, fiche = batir_salle(s, veut, rapport)
        if sac is None:
            continue
        debut = len(index)
        # les triangles d'une salle sont contigus, et rangés par matière DEDANS :
        # c'est ce qui permet à la fois un groupe par matière et une tranche par
        # pièce.
        par_mat = {}
        for (a, b, c, m, part) in sac.tris:
            par_mat.setdefault((part, m), []).append((a, b, c))
        # la coque D'ABORD, d'un seul tenant : sa tranche est ce qu'on vérifie
        for cle_g in sorted(par_mat, key=lambda k: (k[0] != "coque", k[1])):
            part, m = cle_g
            g0 = len(index)
            for (a, b, c) in par_mat[cle_g]:
                index.extend((pousser(a), pousser(b), pousser(c)))
            groupes.append({"matiere": m, "part": part, "debut": g0,
                            "compte": len(index) - g0, "salle": cle})
        fiche["debut"] = debut
        fiche["compte"] = len(index) - debut
        fiche["coque"] = sum(g["compte"] for g in groupes
                             if g["salle"] == cle and g["part"] == "coque")
        fiches.append(fiche)

    return {
        "_lisez_moi": "Les intérieurs de Peyredragon : une pièce creuse par "
                      "salle du plan, murs épais et portes percées d'après "
                      "etat/chemins.json. En mètres, dans le repère du monde. "
                      "Engendré par scripts/monde/peyredragon_interieurs.py.",
        "sommets": [round(float(v), 2) for v in sommets],
        "index": index,
        "groupes": groupes,
        "salles": fiches,
    }, rapport


# ---------------------------------------------------------------------------
# se mesurer
# ---------------------------------------------------------------------------
def _croisements(paquet, fiche, o, d):
    """Combien de faces de la pièce un rayon traverse — Möller-Trumbore."""
    S, I = paquet["sommets"], paquet["index"]
    n = 0
    for k in range(fiche["debut"], fiche["debut"] + fiche.get("coque", fiche["compte"]), 3):
        p = [S[I[k + j] * 3:I[k + j] * 3 + 3] for j in range(3)]
        e1 = [p[1][i] - p[0][i] for i in range(3)]
        e2 = [p[2][i] - p[0][i] for i in range(3)]
        h = (d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2],
             d[0] * e2[1] - d[1] * e2[0])
        a = sum(e1[i] * h[i] for i in range(3))
        if abs(a) < 1e-9:
            continue
        f = 1.0 / a
        s = [o[i] - p[0][i] for i in range(3)]
        u = f * sum(s[i] * h[i] for i in range(3))
        if u < 0 or u > 1:
            continue
        q = (s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2],
             s[0] * e1[1] - s[1] * e1[0])
        v = f * sum(d[i] * q[i] for i in range(3))
        if v < 0 or u + v > 1:
            continue
        if f * sum(e2[i] * q[i] for i in range(3)) > 1e-6:
            n += 1
    return n


def verifier_portes(paquet):
    """Un vantail par passage, jamais deux, et rien en travers de l'embrasure."""
    par = {f["id"]: f for f in paquet["salles"]}
    _v, aretes = voisins()
    print("VÉRIFICATION — les portes")
    compte, doubles, bouches, sans = {}, [], [], []
    etats = {}
    for (a, b) in aretes:
        cle = tuple(sorted((a, b)))
        n = 0
        genre, etat = None, None
        for (x, y) in ((a, b), (b, a)):
            f = par.get(x)
            if not f:
                continue
            for d in f["portes"]:
                if d["vers"] != y:
                    continue
                genre, etat = d["genre"], d["etat"]
                if d.get("vantail"):
                    n += 1
                    if not d.get("libre") and d["etat"] == "ouverte":
                        bouches.append("%s → %s" % (x, y))
        compte[cle] = n
        etats[cle] = (genre, etat)
        if genre == "porte" and n == 0:
            sans.append("%s ↔ %s" % cle)
        if n > 1:
            doubles.append("%s ↔ %s (%d)" % (cle[0], cle[1], n))

    vantaux = sum(1 for c in compte.values() if c == 1)
    baies = sum(1 for k, (g, _e) in etats.items() if g == "baie")
    par_etat = {}
    for (g, e) in etats.values():
        par_etat["%s/%s" % (g, e)] = par_etat.get("%s/%s" % (g, e), 0) + 1
    print("  %d passages : %d vantaux bâtis, %d baies sans battant"
          % (len(aretes), vantaux, baies))
    print("  par nature : %s"
          % ", ".join("%s %d" % (k, v) for k, v in sorted(par_etat.items())))
    print("  vantaux bâtis deux fois : %s" % (", ".join(doubles) or "aucun"))
    print("  vantaux ouverts en travers du passage : %s"
          % (", ".join(bouches) or "aucun"))
    if sans:
        print("  ! portes sans vantail : %s" % ", ".join(sans))


def verifier_altitudes(paquet):
    """Personne ne flotte : chaque étage repose sur ce qui le porte."""
    z, note = altitudes()
    hotes = _hotes()
    par = {f["id"]: f for f in paquet["salles"]}
    print("VÉRIFICATION — les altitudes")
    print("  %-22s %8s %8s  %s" % ("salle", "sol", "plafond", "d'où elle tient"))
    for cle in sorted(z):
        f = par.get(cle)
        if not f:
            continue
        print("  %-22s %8.1f %8.1f  %s"
              % (cle, f["sol_z"], f["sol_z"] + f["hauteur"], note[cle]))

    fautes = []
    for cle, h in hotes.items():
        if cle not in par or h not in par:
            continue
        s, e = par[cle], par[h]
        if s["etage"] == "sommet" and s["sol_z"] < e["sol_z"] + e["hauteur"] - 0.01:
            fautes.append("%s (%.1f) sous le plafond de %s (%.1f)"
                          % (cle, s["sol_z"], h, e["sol_z"] + e["hauteur"]))
        if s["etage"] == "sommet" and s["sol_z"] > e["sol_z"] + e["hauteur"] + PLANCHER + 0.01:
            fautes.append("%s flotte à %.1f m au-dessus de %s"
                          % (cle, s["sol_z"] - e["sol_z"] - e["hauteur"], h))
        if s["etage"] == "dessous" and s["sol_z"] + s["hauteur"] > e["sol_z"] - 0.01:
            fautes.append("%s (plafond %.1f) déborde dans %s (plancher %.1f)"
                          % (cle, s["sol_z"] + s["hauteur"], h, e["sol_z"]))
    print()
    print("  %d salle(s) qui flotte(nt) ou se chevauchent : %s"
          % (len(fautes), ", ".join(fautes) if fautes else "aucune"))

    # Les portes : de plain-pied ou escalier, mais rien entre les deux.
    _v, aretes = voisins()
    plat, marches, absentes = [], [], []
    for (a, b) in aretes:
        if a not in par or b not in par:
            absentes.append("%s↔%s" % (a, b))
            continue
        d = abs(par[a]["sol_z"] - par[b]["sol_z"])
        (plat if d <= PALIER_M else marches).append((d, a, b))
    print()
    print("  %d portes de plain-pied (écart ≤ %.0f m), écart max %.2f m"
          % (len(plat), PALIER_M, max([d for d, _a, _b in plat] or [0])))
    print("  %d escaliers assumés (la vue ne montre pas la voisine) :" % len(marches))
    for (d, a, b) in sorted(marches, reverse=True):
        print("      %6.1f m  %-22s ↔ %s" % (d, a, b))
    if absentes:
        print("  ! arêtes vers une salle sans volume : %s" % ", ".join(absentes))


def verifier(paquet):
    print("VÉRIFICATION — le creux, mesuré au rayon lancé")
    print("  Un point au centre de la pièce, à 1,65 m du sol. On lance douze")
    print("  rayons obliques (jamais sur un axe : une direction alignée passe")
    print("  par les arêtes et les compte deux fois) et l'on compte les faces")
    print("  de SA pièce qu'ils traversent. Nombre PAIR = le point est dans le")
    print("  vide ; impair = il est dans la matière. Un rayon qui sort par une")
    print("  porte n'en traverse aucune, et c'est juste.")
    print()
    print("  %-22s %8s %7s %7s  %-8s %s"
          % ("salle", "rayons", "haut", "bas", "verdict", "mesuré / déclaré"))
    bons, faux = 0, []
    for f in paquet["salles"]:
        z = f["sol_z"] + (1.65 if f["hauteur"] >= 1.8 else f["hauteur"] / 2)
        o = (f["centre"][0], f["centre"][1], z)
        pairs, mure = 0, 0
        for k in range(12):
            a = (k + 0.37) * math.pi / 6
            n = _croisements(paquet, f, o, (math.cos(a), math.sin(a), 0.0))
            if n % 2 == 0:
                pairs += 1
            if n >= 2:
                mure += 1
        haut = _croisements(paquet, f, o, (0.03, 0.02, 1.0))
        bas = _croisements(paquet, f, o, (0.03, 0.02, -1.0))
        # couvert : un plafond au-dessus et une dalle en dessous ; découvert :
        # le ciel au-dessus, la dalle quand même.
        ok = (pairs == 12 and mure >= 8 and bas == 1
              and haut == (1 if f["couvert"] else 0))
        if ok:
            bons += 1
        else:
            faux.append(f["id"])
        t = Li.TAILLE.get(f["id"])
        dit = ("%.0f×%.0f" % (t[0], t[1])) if t else "—"
        print("  %-22s %5d/12 %7d %7d  %-8s %.0f×%.0f / %s"
              % (f["id"], pairs, haut, bas, "creux" if ok else "FAUX",
                 f["long_m"], f["larg_m"], dit))
    print()
    print("  %d pièces creuses sur %d" % (bons, len(paquet["salles"])))
    if faux:
        print("  ! à revoir : %s" % ", ".join(faux))


# ---------------------------------------------------------------------------
def main():
    paquet, rapport = engendrer()
    vois, aretes = voisins()
    perces = sum(len(f["portes"]) for f in paquet["salles"])
    attendues = sum(2 for (x, y) in aretes)

    print("Les intérieurs de Peyredragon")
    print("  %d salles au plan, %d bâties" % (len(Li._SALLES), len(paquet["salles"])))
    coque = sum(f.get("coque", 0) for f in paquet["salles"]) // 3
    total = len(paquet["index"]) // 3
    mob = rapport["tris_meubles"]
    print("  %d sommets, %d triangles, %d groupes" %
          (len(paquet["sommets"]) // 3, total, len(paquet["groupes"])))
    print("     dont coque (murs, embrasures, encadrements, dalle, plafond) : %d"
          % coque)
    print("          — encadrements de pierre de taille : %d (3 volumes × %d baies)"
          % (perces * 36, perces))
    print("     dont vantaux : %d" % (total - coque - mob))
    print("     dont mobilier : %d" % mob)
    print("  %d arêtes dans etat/chemins.json → %d ouvertures attendues, %d percées"
          % (len(aretes), attendues, perces))
    if rapport["sans_forme"]:
        print("  ! sans tracé exploitable : %s" % ", ".join(rapport["sans_forme"]))
    if rapport["inconnues"]:
        print("  ! salles nommées par chemins.json et absentes du plan : %s"
              % ", ".join(sorted(rapport["inconnues"])))
    meubles = sum(f.get("meubles", 0) for f in paquet["salles"])
    print("  %d meubles posés dans %d salles, %d triangles de mobilier"
          % (meubles, sum(1 for f in paquet["salles"] if f.get("meubles")),
             rapport["tris_meubles"]))
    if rapport["meubles"]:
        print("  ! meubles non posés :")
        for (cle, nom, pourquoi) in rapport["meubles"]:
            print("      %-22s %-14s %s" % (cle, nom, pourquoi))
    if rapport["ratees"]:
        print("  ! ouvertures non percées :")
        for (cle, vers, pourquoi) in rapport["ratees"]:
            print("      %-22s → %-22s %s" % (cle, vers, pourquoi))

    if "--verifier" in sys.argv:
        print()
        verifier_altitudes(paquet)
        print()
        verifier_portes(paquet)
        print()
        verifier(paquet)

    if "--vraiment" in sys.argv:
        with open(SORTIE, "w", encoding="utf-8") as f:
            json.dump(paquet, f, ensure_ascii=False, separators=(",", ":"))
        print()
        print("  écrit : %s (%.1f Mo)"
              % (os.path.relpath(SORTIE, RACINE), os.path.getsize(SORTIE) / 1e6))
    else:
        print()
        print("  — essai à blanc. Relance avec --vraiment pour écrire dans")
        print("    monde/peyredragon.interieurs.json")


if __name__ == "__main__":
    main()
