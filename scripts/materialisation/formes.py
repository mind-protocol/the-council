# -*- coding: utf-8 -*-
"""Les primitives : tout ce qu'on bâtit se ramène à des triangles.

Repère du monde, en MÈTRES : +x au levant, +y au nord, +z vers le ciel.
Une forme rend toujours (triangles, matieres) — triangles (N,3,3) float32,
matieres (N,) de chaînes qui disent de quoi c'est fait.
"""
import math
import numpy as np


def _t(liste, matiere):
    if not liste:
        return np.zeros((0, 3, 3), np.float32), np.zeros((0,), object)
    a = np.asarray(liste, np.float32)
    return a, np.array([matiere] * len(a), object)


def joindre(*morceaux):
    """Recolle des (triangles, matieres) en un seul corps."""
    tri = [m[0] for m in morceaux if len(m[0])]
    mat = [m[1] for m in morceaux if len(m[0])]
    if not tri:
        return np.zeros((0, 3, 3), np.float32), np.zeros((0,), object)
    return np.concatenate(tri), np.concatenate(mat)


def quad(a, b, c, d):
    """Un quadrilatère en deux triangles, dans l'ordre donné."""
    return [[a, b, c], [a, c, d]]


# ---------------------------------------------------------------------------
# les volumes
# ---------------------------------------------------------------------------
def prisme(contour, z0, z1, matiere, dessus=True, dessous=False):
    """Un polygone extrudé : un mur, une plateforme, une assise."""
    n = len(contour)
    tris = []
    for i in range(n):
        (x0, y0), (x1, y1) = contour[i], contour[(i + 1) % n]
        tris += quad([x0, y0, z0], [x1, y1, z0], [x1, y1, z1], [x0, y0, z1])
    if dessus:
        tris += eventail(contour, z1)
    if dessous:
        tris += [list(reversed(t)) for t in eventail(contour, z0)]
    return _t(tris, matiere)


def eventail(contour, z):
    """Un polygone convexe (ou peu concave) rempli en éventail."""
    return [[[contour[0][0], contour[0][1], z],
             [contour[i][0], contour[i][1], z],
             [contour[i + 1][0], contour[i + 1][1], z]]
            for i in range(1, len(contour) - 1)]


def bande(axe, largeur, z0, z1, matiere, fermer=False):
    """Une courtine : une polyligne épaissie, puis extrudée.

    Le mur suit l'axe ; `largeur` est son épaisseur. On renvoie le prisme et le
    contour extérieur, dont on se sert pour poser les tours aux angles.
    """
    pts = list(axe) + ([axe[0]] if fermer else [])
    gauche, droite = [], []
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n, dx / n
        gauche.append((p[0] + nx * largeur / 2, p[1] + ny * largeur / 2))
        droite.append((p[0] - nx * largeur / 2, p[1] - ny * largeur / 2))
    contour = gauche + list(reversed(droite))
    tris = []
    m = len(gauche)
    for i in range(m - 1):
        g0, g1 = gauche[i], gauche[i + 1]
        d0, d1 = droite[i], droite[i + 1]
        tris += quad([g0[0], g0[1], z0], [g1[0], g1[1], z0],
                     [g1[0], g1[1], z1], [g0[0], g0[1], z1])
        tris += quad([d1[0], d1[1], z0], [d0[0], d0[1], z0],
                     [d0[0], d0[1], z1], [d1[0], d1[1], z1])
        tris += quad([g0[0], g0[1], z1], [g1[0], g1[1], z1],
                     [d1[0], d1[1], z1], [d0[0], d0[1], z1])
    return _t(tris, matiere), contour


def creneaux(axe, largeur, z, hauteur, matiere, pas=2.6, plein=1.5, fermer=False):
    """Le hourd : des merlons posés le long des deux arêtes d'une courtine."""
    pts = list(axe) + ([axe[0]] if fermer else [])
    tris = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        lg = math.hypot(b[0] - a[0], b[1] - a[1])
        if lg < 1e-6:
            continue
        ux, uy = (b[0] - a[0]) / lg, (b[1] - a[1]) / lg
        nx, ny = -uy, ux
        n = max(1, int(lg / pas))
        for k in range(n):
            s = (k + 0.5) * lg / n
            cx, cy = a[0] + ux * s, a[1] + uy * s
            for cote in (1, -1):
                ex = cx + nx * (largeur / 2 - 0.55) * cote
                ey = cy + ny * (largeur / 2 - 0.55) * cote
                d, e = plein / 2, 0.55
                coin = [(ex + ux * d + nx * e, ey + uy * d + ny * e),
                        (ex + ux * d - nx * e, ey + uy * d - ny * e),
                        (ex - ux * d - nx * e, ey - uy * d - ny * e),
                        (ex - ux * d + nx * e, ey - uy * d + ny * e)]
                tris.append(prisme(coin, z, z + hauteur, matiere)[0])
    if not tris:
        return _t([], matiere)
    a = np.concatenate(tris)
    return a, np.array([matiere] * len(a), object)


def tour(cx, cy, z0, z1, rayon, matiere, cotes=14, fruit=0.86, couronne=None):
    """Une tour ronde, un peu fruitée : plus large au pied qu'au sommet."""
    def cercle(r, z):
        return [[cx + math.cos(2 * math.pi * i / cotes) * r,
                 cy + math.sin(2 * math.pi * i / cotes) * r, z] for i in range(cotes)]
    bas, haut = cercle(rayon, z0), cercle(rayon * fruit, z1)
    tris = []
    for i in range(cotes):
        j = (i + 1) % cotes
        tris += quad(bas[i], bas[j], haut[j], haut[i])
    tris += [[haut[0], haut[i], haut[i + 1]] for i in range(1, cotes - 1)]
    corps = _t(tris, matiere)
    if couronne is None:
        return corps
    # le chemin de ronde du sommet, en dents
    dents = []
    r = rayon * fruit
    for i in range(cotes):
        if i % 2:
            continue
        a0 = 2 * math.pi * i / cotes
        a1 = 2 * math.pi * (i + 1) / cotes
        c = [(cx + math.cos(a) * r, cy + math.sin(a) * r) for a in (a0, a1)]
        c += [(cx + math.cos(a) * (r - 1.1), cy + math.sin(a) * (r - 1.1)) for a in (a1, a0)]
        dents.append(prisme(c, z1, z1 + couronne, matiere)[0])
    if dents:
        d = np.concatenate(dents)
        return joindre(corps, (d, np.array([matiere] * len(d), object)))
    return corps


def fleche(cx, cy, z0, hauteur, rayon, matiere, cotes=10):
    """Une flèche, un toit conique : ce qui coiffe une tour."""
    tris = []
    for i in range(cotes):
        a0 = 2 * math.pi * i / cotes
        a1 = 2 * math.pi * (i + 1) / cotes
        tris.append([[cx + math.cos(a0) * rayon, cy + math.sin(a0) * rayon, z0],
                     [cx + math.cos(a1) * rayon, cy + math.sin(a1) * rayon, z0],
                     [cx, cy, z0 + hauteur]])
    return _t(tris, matiere)


def maison(cx, cy, z, larg, long_, haut, angle, mur, toit, pente=0.62):
    """Un feu du bourg : quatre murs et deux pans de toit, faîtage au vent."""
    ca, sa = math.cos(angle), math.sin(angle)
    def p(u, v, w):
        return [cx + u * ca - v * sa, cy + u * sa + v * ca, z + w]
    a, b = long_ / 2, larg / 2
    murs = []
    coins = [p(-a, -b, 0), p(a, -b, 0), p(a, b, 0), p(-a, b, 0)]
    hauts = [p(-a, -b, haut), p(a, -b, haut), p(a, b, haut), p(-a, b, haut)]
    for i in range(4):
        j = (i + 1) % 4
        murs += quad(coins[i], coins[j], hauts[j], hauts[i])
    hf = haut + larg * pente / 2
    f0, f1 = p(-a, 0, hf), p(a, 0, hf)
    toits = quad(hauts[0], hauts[1], f1, f0) + quad(hauts[2], hauts[3], f0, f1)
    pignons = [[hauts[1], hauts[2], f1], [hauts[3], hauts[0], f0]]
    return joindre(_t(murs, mur), _t(toits + pignons, toit))


def rampe(axe, largeur, sol, matiere, garde=None):
    """Une montée taillée : une bande dont chaque point porte son altitude.

    `axe` est une liste de (x, y, z) ; `sol` donne l'altitude du terrain, pour
    que la rampe repose sur la roche au lieu de flotter au-dessus.
    """
    tris = []
    bords = ([], [])
    for i, (x, y, z) in enumerate(axe):
        a = axe[max(0, i - 1)]
        b = axe[min(len(axe) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n, dx / n
        g = (x + nx * largeur / 2, y + ny * largeur / 2, z)
        d = (x - nx * largeur / 2, y - ny * largeur / 2, z)
        bords[0].append(g)
        bords[1].append(d)
    for i in range(len(axe) - 1):
        g0, g1 = bords[0][i], bords[0][i + 1]
        d0, d1 = bords[1][i], bords[1][i + 1]
        tris += quad(list(g0), list(g1), list(d1), list(d0))
        for (p0, p1) in ((g0, g1), (d1, d0)):
            s0 = min(sol(p0[0], p0[1]), p0[2]) - 1.5
            s1 = min(sol(p1[0], p1[1]), p1[2]) - 1.5
            tris += quad([p0[0], p0[1], p0[2]], [p1[0], p1[1], p1[2]],
                         [p1[0], p1[1], s1], [p0[0], p0[1], s0])
    corps = _t(tris, matiere)
    if not garde:
        return corps
    murets = []
    for cote in (0, 1):
        for i in range(len(axe) - 1):
            p0, p1 = bords[cote][i], bords[cote][i + 1]
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            n = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / n * 0.5, dx / n * 0.5
            c = [(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny),
                 (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)]
            z = min(p0[2], p1[2])
            murets.append(prisme(c, z, max(p0[2], p1[2]) + garde, matiere)[0])
    m = np.concatenate(murets)
    return joindre(corps, (m, np.array([matiere] * len(m), object)))


def grille(x0, y0, x1, y1, n, hauteur, matiere_de):
    """Le terrain : une nappe échantillonnée sur une fonction d'altitude.

    `hauteur` prend deux tableaux (X, Y) et rend Z ; `matiere_de` prend le
    centre et la normale d'une facette et dit de quoi le sol est fait là.
    """
    xs = np.linspace(x0, x1, n + 1, dtype=np.float32)
    ys = np.linspace(y0, y1, n + 1, dtype=np.float32)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    Z = hauteur(X, Y).astype(np.float32)
    S = np.stack([X, Y, Z], -1)
    a, b = S[:-1, :-1], S[1:, :-1]
    c, d = S[1:, 1:], S[:-1, 1:]
    t1 = np.stack([a, b, c], -2).reshape(-1, 3, 3)
    t2 = np.stack([a, c, d], -2).reshape(-1, 3, 3)
    tris = np.concatenate([t1, t2]).astype(np.float32)
    centres = tris.mean(1)
    normales = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    normales /= (np.linalg.norm(normales, axis=1, keepdims=True) + 1e-9)
    return tris, matiere_de(centres, normales)


# ---------------------------------------------------------------------------
# LES PAROIS — de l'épaisseur, et des trous dedans
#
# Tout ce qui précède fabrique du PLEIN : un prisme est une peau extérieure,
# une tour est un cylindre massif. C'est assez pour une silhouette, pas pour un
# bâtiment — on ne peut ni entrer dans une salle, ni franchir une porte, et une
# enceinte fermée sur tout son tour est un château où l'on n'entre pas.
#
# Une seule primitive règle les trois : une paroi a une ÉPAISSEUR (donc deux
# faces et un dessus) et porte des BAIES (donc des trous). Percer la courtine,
# creuser une salle et ouvrir une fenêtre deviennent le même geste.
#
# Pas de soustraction booléenne : autour d'une baie on émet quatre panneaux —
# à gauche, à droite, l'allège dessous, le linteau dessus. C'est exact, c'est
# étanche, et ça reste du triangle plat comme tout le reste.
# ---------------------------------------------------------------------------
def _panneau(a, b, ep, z0, z1, matiere):
    """Un morceau de mur droit, plein, d'épaisseur `ep` autour de son axe."""
    if z1 - z0 < 1e-6:
        return _t([], matiere)
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    if n < 1e-6:
        return _t([], matiere)
    nx, ny = -dy / n * ep / 2, dx / n * ep / 2
    return prisme([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny),
                   (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)],
                  z0, z1, matiere)


def paroi(axe, epaisseur, z0, z1, matiere, baies=(), fermer=False):
    """Un mur suivi le long d'`axe`, épais, et percé.

    `baies` : des dicts {segment, t, larg, appui, linteau}. `segment` est l'index
    du pan, `t` la position sur ce pan (0 à 1), `appui` et `linteau` sont des
    altitudes absolues — une porte a un appui au niveau du sol, une fenêtre plus
    haut. Une baie plus large que son pan est ramenée à ce que le pan permet.
    """
    pts = list(axe) + ([axe[0]] if fermer else [])
    par_segment = {}
    for b in baies:
        par_segment.setdefault(int(b.get("segment", 0)), []).append(b)

    corps = []
    for i in range(len(pts) - 1):
        a, c = pts[i], pts[i + 1]
        lg = math.hypot(c[0] - a[0], c[1] - a[1])
        if lg < 1e-6:
            continue
        ux, uy = (c[0] - a[0]) / lg, (c[1] - a[1]) / lg
        def au(s):
            s = max(0.0, min(lg, s))
            return (a[0] + ux * s, a[1] + uy * s)

        ouv = []
        for b in sorted(par_segment.get(i, []), key=lambda q: q.get("t", 0.5)):
            larg = min(b.get("larg", 2.0), lg - 0.6)
            if larg <= 0.2:
                continue
            milieu = b.get("t", 0.5) * lg
            g = max(0.3, milieu - larg / 2)
            d = min(lg - 0.3, milieu + larg / 2)
            if d - g < 0.2:
                continue
            ouv.append((g, d, max(z0, b.get("appui", z0)),
                        min(z1, b.get("linteau", z1))))

        bord = 0.0
        for (g, d, appui, linteau) in ouv:
            corps.append(_panneau(au(bord), au(g), epaisseur, z0, z1, matiere))
            if appui > z0:                       # l'allège, sous la baie
                corps.append(_panneau(au(g), au(d), epaisseur, z0, appui, matiere))
            if linteau < z1:                     # le linteau, au-dessus
                corps.append(_panneau(au(g), au(d), epaisseur, linteau, z1, matiere))
            bord = d
        corps.append(_panneau(au(bord), au(lg), epaisseur, z0, z1, matiere))
    return joindre(*corps)


# --- LES TRÉMIES ------------------------------------------------------------
#
# Un escalier qui traverse un plancher plein n'est pas un escalier : c'est une
# vis prise dans la dalle. Percer la dalle demande le même geste que percer un
# mur — et la même méthode, puisqu'on n'a toujours pas de booléen : on découpe
# le plancher en bandes qui contournent le trou, et l'on ferme le contre-cœur.
#
# La trémie est RECTANGULAIRE, quelle que soit la forme donnée : on prend la
# boîte de l'emprise. Ce n'est pas une approximation par paresse — une dalle ne
# se troue pas en rond, on la perce entre deux poutres, et le trou est carré.
def _boite(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _couper(poly, a, b, c):
    """Ce qui reste du polygone du côté a*x + b*y <= c (Sutherland–Hodgman)."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        dp = a * p[0] + b * p[1] - c
        dq = a * q[0] + b * q[1] - c
        if dp <= 0:
            out.append(p)
        if (dp < 0) != (dq < 0):
            t = dp / (dp - dq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def _contourner(contour, boites):
    """Le contour rendu en morceaux qui laissent chaque boîte vide."""
    morceaux = [list(contour)]
    for b in boites:
        x0, y0 = b[0]
        x1, y1 = b[2]
        suite = []
        for m in morceaux:
            xs = [p[0] for p in m]
            ys = [p[1] for p in m]
            if max(xs) <= x0 or min(xs) >= x1 or max(ys) <= y0 or min(ys) >= y1:
                suite.append(m)                    # la boîte ne le touche pas
                continue
            # de part et d'autre de la boîte, puis devant et derrière elle
            for (a, bb, c) in ((1.0, 0.0, x0), (-1.0, 0.0, -x1)):
                q = _couper(m, a, bb, c)
                if len(q) >= 3:
                    suite.append(q)
            milieu = _couper(_couper(m, 1.0, 0.0, x1), -1.0, 0.0, -x0)
            if len(milieu) >= 3:
                for (a, bb, c) in ((0.0, 1.0, y0), (0.0, -1.0, -y1)):
                    q = _couper(milieu, a, bb, c)
                    if len(q) >= 3:
                        suite.append(q)
        morceaux = suite
    return morceaux


def dalle(contour, z0, z1, matiere, tremies=()):
    """Un plancher épais, percé de ses trémies."""
    if not tremies:
        return prisme(contour, z0, z1, matiere)
    boites = [_boite(t) for t in tremies]
    tris = []
    for m in _contourner(contour, boites):
        tris += eventail(m, z1)
        tris += [list(reversed(t)) for t in eventail(m, z0)]
    for c in [list(contour)] + boites:
        n = len(c)
        for i in range(n):
            (x0, y0), (x1, y1) = c[i], c[(i + 1) % n]
            tris += quad([x0, y0, z0], [x1, y1, z0], [x1, y1, z1], [x0, y0, z1])
    return _t(tris, matiere)


def salle(contour, z_sol, hauteur, epaisseur, mur, sol=None, plafond=None,
          baies=(), tremies_sol=(), tremies_plafond=()):
    """Une pièce : des parois épaisses, un plancher, un plafond, des baies.

    Le plancher est posé un peu sous le sol de la pièce et le plafond un peu
    au-dessus de sa hauteur : c'est ce qui fait qu'on ne voit pas le jour entre
    le mur et le sol quand on entre par la porte.

    Les trémies se donnent séparément pour le sol et pour le plafond : une vis
    perce le plafond de l'étage qu'elle quitte et le sol de celui qu'elle
    gagne, mais on ne troue pas le rez sous lequel il n'y a rien.
    """
    corps = [paroi(contour, epaisseur, z_sol, z_sol + hauteur, mur,
                   baies=baies, fermer=True)]
    if sol:
        corps.append(dalle(contour, z_sol - 0.4, z_sol + 0.05, sol, tremies_sol))
    if plafond:
        corps.append(dalle(contour, z_sol + hauteur - 0.05,
                           z_sol + hauteur + 0.4, plafond, tremies_plafond))
    return joindre(*corps)


def tour_creuse(cx, cy, z0, z1, rayon, epaisseur, matiere, cotes=14,
                couronne=None, baies=()):
    """Une tour dont on peut voir l'intérieur par ses baies.

    Le fût est une paroi épaisse refermée sur elle-même ; `baies` prend les
    mêmes dicts que `paroi`, avec `segment` compté sur les côtés du polygone.
    """
    c = [(cx + math.cos(2 * math.pi * i / cotes) * rayon,
          cy + math.sin(2 * math.pi * i / cotes) * rayon) for i in range(cotes)]
    corps = [paroi(c, epaisseur, z0, z1, matiere, baies=baies, fermer=True)]
    if couronne:
        corps.append(_t(eventail([(cx + (p[0] - cx) * 0.97, cy + (p[1] - cy) * 0.97)
                                  for p in c], z1), matiere))
        for i in range(0, cotes, 2):
            a, b = c[i], c[(i + 1) % cotes]
            corps.append(_panneau(a, b, epaisseur * 0.8, z1, z1 + couronne, matiere))
    return joindre(*corps)


# ---------------------------------------------------------------------------
# LES MOULURES — ce qui sépare la pierre taillée du carton
#
# Un mur nu se lit comme un panneau ; le même mur avec une plinthe au pied, un
# cordon à l'étage et une corniche en tête se lit comme de la maçonnerie. C'est
# le rapport qualité/prix le plus élevé de tout le générateur : un profil de
# quatre points balayé le long d'un tracé, et la lumière fait le reste — parce
# qu'une moulure crée des ARÊTES, donc des ombres, donc de l'échelle.
#
# Un profil se donne dans le plan perpendiculaire au tracé : une liste de
# (déport, hauteur) en mètres, déport positif vers l'extérieur du mur.
# ---------------------------------------------------------------------------
PLINTHE = [(0.0, 0.0), (0.18, 0.0), (0.18, 0.46), (0.06, 0.62), (0.0, 0.62)]
CORDON = [(0.0, 0.0), (0.14, 0.06), (0.14, 0.22), (0.0, 0.30)]
CORNICHE = [(0.0, 0.0), (0.10, 0.10), (0.34, 0.34), (0.34, 0.50),
            (0.10, 0.50), (0.0, 0.62)]
LARMIER = [(0.0, 0.0), (0.26, 0.12), (0.26, 0.20), (0.20, 0.20),
           (0.20, 0.30), (0.0, 0.36)]


def moulure(axe, profil, z, matiere, fermer=False, dehors=True):
    """Un profil balayé le long d'un tracé, à l'altitude `z`.

    `dehors` dit de quel côté du tracé le profil saille. Les extrémités sont
    laissées ouvertes : une moulure se retourne sur elle-même ou meurt dans un
    angle, elle n'a pas de bouchon.
    """
    pts = list(axe) + ([axe[0]] if fermer else [])
    if len(pts) < 2:
        return _t([], matiere)
    sens = 1.0 if dehors else -1.0

    sections = []
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n * sens, dx / n * sens
        sections.append([[p[0] + nx * d, p[1] + ny * d, z + h] for (d, h) in profil])

    tris = []
    for s0, s1 in zip(sections, sections[1:]):
        for k in range(len(profil) - 1):
            tris += quad(s0[k], s1[k], s1[k + 1], s0[k + 1])
    return _t(tris, matiere)


def mouler_un_corps(facade, z_pied, z_tete, etages, hauteur_etage, matiere):
    """L'habillage complet d'une façade : plinthe, cordons d'étage, corniche."""
    corps = [moulure(facade, PLINTHE, z_pied, matiere)]
    for e in range(1, etages):
        corps.append(moulure(facade, CORDON, z_pied + e * hauteur_etage, matiere))
    corps.append(moulure(facade, CORNICHE, z_tete - 0.62, matiere))
    return joindre(*corps)


# ---------------------------------------------------------------------------
# LES ESCALIERS — ce qui rend un étage réel
#
# Tant qu'un étage se gagne par un trait dans un graphe, il est théorique. Une
# marche a 17 cm de haut et 29 de giron : c'est cette mesure-là qui décide de
# l'emprise d'une vis et de la longueur d'une volée, et donc du plan.
# ---------------------------------------------------------------------------
HAUTEUR_MARCHE = 0.17
GIRON = 0.29
MARCHES_PAR_TOUR = 13          # une vis médiévale tourne en douze ou treize


def vis(cx, cy, z0, z1, rayon, matiere, noyau=0.22, sens=1):
    """Un escalier à vis : un noyau, et des marches qui tournent autour.

    Le noyau porte les marches et fait la rampe — c'est pour ça qu'une vis tient
    dans si peu de place, et pourquoi on en met une dans chaque tour.
    """
    n = max(2, int(round((z1 - z0) / HAUTEUR_MARCHE)))
    da = sens * 2 * math.pi / MARCHES_PAR_TOUR
    tris = []
    for k in range(n):
        z = z0 + k * (z1 - z0) / n
        h = z0 + (k + 1) * (z1 - z0) / n
        a0, a1 = k * da, (k + 1.06) * da
        p = []
        for (a, r) in ((a0, noyau), (a1, noyau), (a1, rayon), (a0, rayon)):
            p.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        tris += quad([p[0][0], p[0][1], h], [p[1][0], p[1][1], h],
                     [p[2][0], p[2][1], h], [p[3][0], p[3][1], h])
        # la contremarche, sinon on voit sous l'escalier
        tris += quad([p[3][0], p[3][1], h], [p[2][0], p[2][1], h],
                     [p[2][0], p[2][1], z], [p[3][0], p[3][1], z])
    noy = prisme([(cx + math.cos(2 * math.pi * i / 8) * noyau,
                   cy + math.sin(2 * math.pi * i / 8) * noyau) for i in range(8)],
                 z0 - 0.4, z1, matiere)
    return joindre(_t(tris, matiere), noy)


def volee(depart, arrivee, largeur, matiere, garde=None):
    """Une volée droite : des marches, et un limon plein sur les côtés.

    `depart` et `arrivee` sont des (x, y, z). La course nécessaire se déduit de
    la montée — 29 cm de giron pour 17 de hauteur — et si la distance donnée ne
    suffit pas, c'est que le plan ne loge pas cet escalier : on le dit.
    """
    dx, dy = arrivee[0] - depart[0], arrivee[1] - depart[1]
    course = math.hypot(dx, dy)
    montee = arrivee[2] - depart[2]
    n = max(2, int(round(abs(montee) / HAUTEUR_MARCHE)))
    if course < n * GIRON * 0.75:
        n = max(2, int(course / GIRON))
    ux, uy = (dx / course, dy / course) if course else (1.0, 0.0)
    nx, ny = -uy * largeur / 2, ux * largeur / 2
    tris = []
    for k in range(n):
        s0, s1 = course * k / n, course * (k + 1) / n
        z0 = depart[2] + montee * k / n
        z1 = depart[2] + montee * (k + 1) / n
        a = (depart[0] + ux * s0, depart[1] + uy * s0)
        b = (depart[0] + ux * s1, depart[1] + uy * s1)
        c = [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny),
             (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]
        tris.append(prisme(c, min(z0, z1) - 0.9, z1, matiere)[0])
    a = np.concatenate(tris)
    corps = (a, np.array([matiere] * len(a), object))
    if not garde:
        return corps
    murets = []
    for cote in (1, -1):
        axe = [(depart[0] + nx * cote, depart[1] + ny * cote),
               (arrivee[0] + nx * cote, arrivee[1] + ny * cote)]
        murets.append(_panneau(axe[0], axe[1], 0.4,
                               min(depart[2], arrivee[2]) - 0.9,
                               max(depart[2], arrivee[2]) + garde, matiere)[0])
    m = np.concatenate(murets)
    return joindre(corps, (m, np.array([matiere] * len(m), object)))


# ---------------------------------------------------------------------------
# LES MÂCHICOULIS — le hourd de pierre, et ce qui le porte
#
# Un parapet posé au nu du mur donne une silhouette plate. Le mâchicoulis, lui,
# fait SAILLIR le chemin de ronde sur des corbeaux, avec le vide entre eux par
# où l'on jette : la couronne du château se détache du fût, et l'ombre portée
# des corbeaux compte les travées. C'est le détail qui dit « défendu » de loin.
# ---------------------------------------------------------------------------
def machicoulis(axe, largeur, z, matiere, pas=2.4, saillie=0.55,
                corbeau=0.9, fermer=False):
    """Des corbeaux, puis la dalle qu'ils portent — le vide reste entre eux."""
    pts = list(axe) + ([axe[0]] if fermer else [])
    tris = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        lg = math.hypot(b[0] - a[0], b[1] - a[1])
        if lg < 1e-6:
            continue
        ux, uy = (b[0] - a[0]) / lg, (b[1] - a[1]) / lg
        nx, ny = -uy, ux
        n = max(1, int(lg / pas))
        for k in range(n):
            s = (k + 0.5) * lg / n
            cx, cy = a[0] + ux * s, a[1] + uy * s
            for cote in (1, -1):
                # le corbeau : deux ressauts, comme on les taillait
                for (r, h0, h1) in ((saillie * 0.5, 0.0, corbeau * 0.45),
                                    (saillie, corbeau * 0.45, corbeau)):
                    d = largeur / 2 + r
                    c = [(cx + ux * 0.28 + nx * d * cote, cy + uy * 0.28 + ny * d * cote),
                         (cx - ux * 0.28 + nx * d * cote, cy - uy * 0.28 + ny * d * cote),
                         (cx - ux * 0.28 + nx * (largeur / 2) * cote,
                          cy - uy * 0.28 + ny * (largeur / 2) * cote),
                         (cx + ux * 0.28 + nx * (largeur / 2) * cote,
                          cy + uy * 0.28 + ny * (largeur / 2) * cote)]
                    tris.append(prisme(c, z + h0, z + h1, matiere)[0])
    dalle = _panneau_large(pts, largeur + saillie * 2, z + corbeau,
                           z + corbeau + 0.45, matiere)
    if not tris:
        return dalle
    a = np.concatenate(tris)
    return joindre((a, np.array([matiere] * len(a), object)), dalle)


def _panneau_large(pts, largeur, z0, z1, matiere):
    """Une bande épaisse le long d'une polyligne — la dalle de couronnement."""
    tris = []
    for a, b in zip(pts, pts[1:]):
        tris.append(_panneau(a, b, largeur, z0, z1, matiere)[0])
    if not tris:
        return _t([], matiere)
    a = np.concatenate(tris)
    return a, np.array([matiere] * len(a), object)


def parapet(axe, deport, z, hauteur, epaisseur, matiere, fermer=False,
            dedans=True):
    """Le garde-corps d'un chemin de ronde, du côté où l'on ne se défend pas.

    Les créneaux regardent le dehors. Côté cour il n'y a personne à repousser,
    mais il y a douze mètres de vide, et une courtine dont l'arête intérieure
    est nue n'est pas un chemin de ronde : c'est une corniche. Le parapet est
    donc PLEIN et bas — il comble aussi les vides que les merlons intérieurs
    laissent entre eux, ce qui est très exactement ce qu'on maçonnait.

    `deport` est la distance depuis l'axe de la courtine ; `dedans` dit de quel
    côté, tranché par le barycentre du tracé — un mur d'enceinte est un anneau,
    son dedans ne se devine pas autrement.
    """
    pts = list(axe)
    n = len(pts)
    if n < 2:
        return _t([], matiere)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    sens = 1.0 if dedans else -1.0
    ligne = []
    for i, p in enumerate(pts):
        if fermer:
            a, b = pts[(i - 1) % n], pts[(i + 1) % n]
        else:
            a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / d, dx / d
        if ((cx - p[0]) * nx + (cy - p[1]) * ny) * sens < 0:
            nx, ny = -nx, -ny
        ligne.append((p[0] + nx * deport, p[1] + ny * deport))
    return paroi(ligne, epaisseur, z, z + hauteur, matiere, fermer=fermer)


def chambranle(a, b, ep, appui, linteau, matiere, saillie=0.13, joue=0.22):
    """L'encadrement d'une baie : deux jambages, un linteau, un appui saillant.

    Une baie sans encadrement est un trou. Les jambages et le linteau donnent
    l'épaisseur du mur au regard, et l'appui saillant jette l'eau — c'est à ça
    qu'on voit qu'une fenêtre a été taillée et non découpée.
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    lg = math.hypot(dx, dy)
    if lg < 1e-6:
        return _t([], matiere)
    ux, uy = dx / lg, dy / lg
    e = ep / 2 + saillie
    corps = []
    for (s0, s1, z0, z1) in ((-joue, 0.0, appui, linteau),          # jambage
                             (lg, lg + joue, appui, linteau),
                             (-joue, lg + joue, linteau, linteau + 0.24),  # linteau
                             (-joue - 0.08, lg + joue + 0.08,
                              appui - 0.18, appui)):                # appui
        p0 = (a[0] + ux * s0, a[1] + uy * s0)
        p1 = (a[0] + ux * s1, a[1] + uy * s1)
        corps.append(_panneau(p0, p1, e * 2, z0, z1, matiere))
    return joindre(*corps)


# ---------------------------------------------------------------------------
# LE MEUBLE — ce qui donne sa taille à une pièce vide
#
# Une salle creuse de quarante mètres n'a pas d'échelle : les murs sont trop
# loin les uns des autres pour qu'on se mesure à eux. Deux objets suffisent à
# la rendre habitable, et ce sont les deux qu'on trouve dans tous les inven-
# taires — un foyer contre le mur du fond, et le meuble où l'on pose l'argent.
# On ne meuble pas tout le château : on donne l'étalon, et l'œil fait le reste.
#
# Les deux se posent de la même façon : un point du mur, et le vecteur qui va
# vers l'intérieur de la pièce. Rien à faire tourner à la main.
# ---------------------------------------------------------------------------
def _repere(ou, vers):
    """Le repère d'un meuble adossé : le long du mur, et vers la pièce."""
    n = math.hypot(vers[0], vers[1]) or 1.0
    nx, ny = vers[0] / n, vers[1] / n
    return (-ny, nx), (nx, ny)


def _pave(ou, u, v, demi, prof, decal, z0, z1, matiere):
    """Un bloc droit posé dans le repère d'un meuble."""
    c = []
    for (s, d) in ((demi, decal), (demi, decal + prof),
                   (-demi, decal + prof), (-demi, decal)):
        c.append((ou[0] + u[0] * s + v[0] * d, ou[1] + u[1] * s + v[1] * d))
    return prisme(c, z0, z1, matiere, dessous=True)


def cheminee(ou, vers, z, matiere, largeur=2.6, hauteur=2.3, saillie=1.2,
             souche=0.0):
    """Une cheminée adossée : les jambages, le manteau, la hotte, la souche.

    Le foyer fait deux mètres et demi et l'on s'y tient debout : c'est la mesure
    qui manque le plus à une grande salle. La hotte se rétrécit en montant —
    sans ce fruit, la cheminée n'est qu'un placard, et c'est le fruit qu'on
    reconnaît de l'autre bout de la pièce.
    """
    u, v = _repere(ou, vers)
    demi = largeur / 2
    corps = [_pave(ou, u, v, demi + 0.24, 0.16, 0.0, z, z + 0.16, matiere)]  # l'âtre
    for cote in (1, -1):                                  # les deux jambages
        corps.append(_pave((ou[0] + u[0] * demi * cote, ou[1] + u[1] * demi * cote),
                           u, v, 0.26, saillie, 0.0, z, z + hauteur, matiere))
    corps.append(_pave(ou, u, v, demi + 0.26, saillie + 0.16, -0.08,
                       z + hauteur, z + hauteur + 0.34, matiere))   # le manteau

    # la hotte : un tronc de pyramide entre le manteau et le conduit
    z0, z1 = z + hauteur + 0.34, z + hauteur + 2.0
    def rect(d, p, zz):
        return [[ou[0] + u[0] * s + v[0] * q, ou[1] + u[1] * s + v[1] * q, zz]
                for (s, q) in ((d, 0.0), (d, p), (-d, p), (-d, 0.0))]
    bas, haut = rect(demi + 0.26, saillie + 0.16, z0), rect(demi * 0.5, saillie * 0.45, z1)
    tris = []
    for i in range(4):
        j = (i + 1) % 4
        tris += quad(bas[i], bas[j], haut[j], haut[i])
    corps.append(_t(tris, matiere))
    if souche > z1:                                       # le conduit, s'il monte
        corps.append(_pave(ou, u, v, demi * 0.5, saillie * 0.45, 0.0, z1, souche,
                           matiere))
    return joindre(*corps)


def dressoir(ou, vers, z, matiere, long_=2.4, prof=0.62, haut=1.05, etages=2):
    """Le dressoir : le meuble où l'on montre l'argenterie, adossé au mur.

    Un bahut, ses pieds, sa tablette, et les degrés au-dessus — c'est le nombre
    de degrés qui disait le rang de la maison, et c'est pour ça qu'on le voit
    dans toutes les grandes salles.
    """
    u, v = _repere(ou, vers)
    demi = long_ / 2
    corps = []
    for cote in (1, -1):                                  # les pieds
        corps.append(_pave((ou[0] + u[0] * (demi - 0.12) * cote,
                            ou[1] + u[1] * (demi - 0.12) * cote),
                           u, v, 0.12, prof, 0.04, z, z + 0.22, matiere))
    corps.append(_pave(ou, u, v, demi, prof, 0.0, z + 0.22, z + haut, matiere))
    corps.append(_pave(ou, u, v, demi + 0.07, prof + 0.07, -0.04,
                       z + haut, z + haut + 0.07, matiere))   # la tablette
    for k in range(etages):                               # les degrés
        d = demi - 0.16 * (k + 1)
        p = prof - 0.12 * (k + 1)
        if d <= 0.2 or p <= 0.12:
            break
        z0 = z + haut + 0.07 + k * 0.46
        corps.append(_pave(ou, u, v, d, p, 0.02, z0, z0 + 0.40, matiere))
        corps.append(_pave(ou, u, v, d + 0.06, p + 0.06, -0.01, z0 + 0.40,
                           z0 + 0.46, matiere))
    return joindre(*corps)
