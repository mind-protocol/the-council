# -*- coding: utf-8 -*-
# GEOGRAPHIE_TRACES — masques, cadrage, contours, simplification, routes.
# Matiere de scripts/carte_geo.py (lot 2), deplacee telle quelle ;
# geographie_sortie.py consomme ces traces, geographie.py porte le main.
import math
import os
import re

from monde.geographie import FONDS, PAS, REGIONS

# ------------------------------------------------------- masques & cadrage

MER, EAU_DOUCE, TERRE_NUE = 0, 1, 2      # ids reserves de la grille


def construire_grille(mod, np, couleurs, prov_empire, eau, interieures):
    """provinces.png sous-echantillonne -> grille d'ids de region.

    ids : 0 = mer, 1 = lacs et rivieres, 2 = terre hors region,
    3+i = REGIONS[i], puis les fonds (au_dela, essos).
    """
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(os.path.join(mod, "map_data", "provinces.png")).convert("RGB")
    arr = np.asarray(im, dtype=np.uint8)[::PAS, ::PAS]
    packe = ((arr[:, :, 0].astype(np.uint32) << 16)
             | (arr[:, :, 1].astype(np.uint32) << 8)
             | arr[:, :, 2].astype(np.uint32))
    del arr

    cles = [c for c, _, _ in REGIONS]
    base = TERRE_NUE + 1
    idx = {c: base + i for i, c in enumerate(cles)}
    noms_fonds = []
    for nom in FONDS.values():
        if nom not in noms_fonds:
            noms_fonds.append(nom)
    for empire, nom in FONDS.items():
        idx[empire] = base + len(cles) + noms_fonds.index(nom)

    # couleur packee -> id de region
    packe_id = {}
    for pid, coul in couleurs.items():
        if pid in interieures:
            packe_id[coul] = EAU_DOUCE
        elif pid in eau:
            packe_id[coul] = MER
        else:
            empire = prov_empire.get(pid)
            packe_id[coul] = idx.get(empire, TERRE_NUE)

    # Table de correspondance directe sur les 2^24 couleurs possibles : 16 Mo
    # fixes, contre un np.unique qui aurait produit un tableau d'indices de
    # 8 octets par pixel — 450 Mo a pleine resolution, pour le meme resultat.
    lut = np.zeros(1 << 24, dtype=np.uint8)
    for coul, ident in packe_id.items():
        lut[coul] = ident
    grille = lut[packe]
    del lut
    return grille, packe, idx, cles + noms_fonds


def cadrer(np, grille, ids_westeros, marge=0.012):
    """Boite englobante des regions de Westeros, avec une marge relative."""
    masque = np.isin(grille, list(ids_westeros))
    lig = np.where(masque.any(axis=1))[0]
    col = np.where(masque.any(axis=0))[0]
    h, l = grille.shape
    y0, y1 = int(lig[0]), int(lig[-1]) + 1
    x0, x1 = int(col[0]), int(col[-1]) + 1
    m = round(marge * max(x1 - x0, y1 - y0))
    return (max(0, x0 - m), min(l, x1 + m), max(0, y0 - m), min(h, y1 + m))


# ------------------------------------------------------- contours & tracés

def contours(np, masque):
    """Suivi de contour sur les aretes entre pixels (crack following).

    Renvoie la liste des boucles fermees, en coordonnees de coins de pixels
    (entiers). Deux masques voisins produisent exactement la meme arete sur
    leur frontiere commune : les regions s'emboitent sans jour.
    """
    h, l = masque.shape
    p = np.zeros((h + 2, l + 2), dtype=bool)
    p[1:-1, 1:-1] = masque
    m = p[1:-1, 1:-1]
    haut = m & ~p[0:-2, 1:-1]
    bas = m & ~p[2:, 1:-1]
    gauche = m & ~p[1:-1, 0:-2]
    droite = m & ~p[1:-1, 2:]

    pas_l = l + 1                       # largeur de la grille de coins
    aretes = {}                         # coin de depart -> [(arrivee, sens)]

    def ajouter(rs, cs, dr0, dc0, dr1, dc1, sens):
        for r, c in zip(rs.tolist(), cs.tolist()):
            a = (r + dr0) * pas_l + (c + dc0)
            b = (r + dr1) * pas_l + (c + dc1)
            aretes.setdefault(a, []).append((b, sens))

    ajouter(*np.nonzero(haut), 0, 0, 0, 1, 0)      # ->  vers +x
    ajouter(*np.nonzero(droite), 0, 1, 1, 1, 1)    # v   vers +y
    ajouter(*np.nonzero(bas), 1, 1, 1, 0, 2)       # <-  vers -x
    ajouter(*np.nonzero(gauche), 1, 0, 0, 0, 3)    # ^   vers -y

    boucles = []
    for depart in list(aretes):
        while aretes.get(depart):
            coin, sens = depart, None
            boucle = []
            while True:
                sortantes = aretes.get(coin)
                if not sortantes:
                    break
                if len(sortantes) == 1 or sens is None:
                    suivant, s = sortantes.pop(0)
                else:
                    # carrefour en diagonale : on tourne a droite d'abord,
                    # ce qui garde les isthmes diagonaux connectes
                    ordre = [(sens + 1) % 4, sens, (sens + 3) % 4,
                             (sens + 2) % 4]
                    i = min(range(len(sortantes)),
                            key=lambda k: ordre.index(sortantes[k][1]))
                    suivant, s = sortantes.pop(i)
                if not sortantes:
                    aretes.pop(coin, None)
                boucle.append(divmod(coin, pas_l))     # (ligne, colonne)
                coin, sens = suivant, s
                if coin == depart:
                    break
            if len(boucle) >= 4:
                boucles.append(boucle)
    return boucles


def aire(pts):
    """Aire signee (lacet de Gauss)."""
    s = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def simplifier(pts, eps):
    """Douglas-Peucker iteratif sur une polyligne ouverte."""
    n = len(pts)
    if n < 3:
        return list(pts)
    garder = [False] * n
    garder[0] = garder[n - 1] = True
    pile = [(0, n - 1)]
    while pile:
        i, j = pile.pop()
        if j <= i + 1:
            continue
        x1, y1 = pts[i]
        x2, y2 = pts[j]
        dx, dy = x2 - x1, y2 - y1
        norme = math.hypot(dx, dy)
        best, bi = -1.0, -1
        for k in range(i + 1, j):
            x, y = pts[k]
            if norme == 0.0:
                d = math.hypot(x - x1, y - y1)
            else:
                d = abs(dy * (x - x1) - dx * (y - y1)) / norme
            if d > best:
                best, bi = d, k
        if best > eps:
            garder[bi] = True
            pile.append((i, bi))
            pile.append((bi, j))
    return [pts[k] for k in range(n) if garder[k]]


def simplifier_boucle(pts, eps):
    """Douglas-Peucker sur une boucle fermee (coupee en deux au point le
    plus eloigne du depart, pour ne pas biaiser la simplification)."""
    n = len(pts)
    if n < 4:
        return pts
    x0, y0 = pts[0]
    loin = max(range(n), key=lambda k: (pts[k][0] - x0) ** 2 + (pts[k][1] - y0) ** 2)
    a = simplifier(pts[:loin + 1], eps)
    b = simplifier(pts[loin:] + [pts[0]], eps)
    return a[:-1] + b[:-1]


def chemin(boucles, transformer, eps, aire_min):
    """Boucles de pixels -> chaine `d` SVG (sous-chemins fermes)."""
    morceaux = []
    for boucle in boucles:
        if abs(aire(boucle)) < aire_min:
            continue
        pts = [transformer(c, r) for r, c in boucle]
        pts = simplifier_boucle(pts, eps)
        if len(pts) < 3:
            continue
        d = "M" + f"{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for x, y in pts[1:]:
            d += f"L{x:.1f},{y:.1f}"
        morceaux.append(d + "Z")
    return "".join(morceaux)


def point_interieur(np, masque, transformer):
    """Un point bien au centre du masque, pour poser une etiquette.

    Centroide, ramene au pixel du masque le plus proche s'il tombe dehors
    (regions concaves comme le Bief ou le Nord).
    """
    lig, col = np.nonzero(masque)
    if not len(lig):
        return None
    cy, cx = float(lig.mean()), float(col.mean())
    if masque[int(round(cy)), int(round(cx))]:
        return transformer(cx, cy)
    d2 = (lig - cy) ** 2 + (col - cx) ** 2
    k = int(np.argmin(d2))
    return transformer(float(col[k]), float(lig[k]))


# ------------------------------------- les masques fins : rivieres, routes,
#                                       relief. Chacun a son grain propre.

def reduire(np, a, f, moyenne=False):
    """Reduction par blocs f x f. Max par defaut — un trait d'un pixel de
    large survit —, moyenne pour le relief, qui se veut lisse."""
    if f <= 1:
        return a
    h, l = a.shape
    h2, l2 = h // f, l // f
    bloc = a[:h2 * f, :l2 * f].reshape(h2, f, l2, f)
    return bloc.mean(axis=(1, 3)) if moyenne else bloc.max(axis=(1, 3))


def lire_masque(mod, nom, np, boite, f, canal=None, seuil=None, indices=None):
    """Un masque du mod, cadre sur Westeros puis reduit par blocs.

    `canal` : indice de bande (le canal alpha des routes) ; `indices` : les
    valeurs de palette a garder (les nuances de bleu des rivieres).
    """
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    chemin_png = os.path.join(mod, "map_data", nom)
    if not os.path.isfile(chemin_png):
        return None
    x0, x1, y0, y1 = boite
    im = Image.open(chemin_png)
    arr = np.asarray(im)
    arr = arr[y0:y1, x0:x1] if arr.ndim == 2 else arr[y0:y1, x0:x1, canal or 0]
    if indices is not None:
        masque = np.isin(arr, list(indices))
    else:
        masque = arr > (seuil if seuil is not None else 0)
    del arr
    return reduire(np, masque, f)


def dilater(np, masque, n):
    """Epaissit un masque de n pixels — de quoi refermer les coupures du
    reseau (un gue, un pont que le masque du mod ne peint pas)."""
    m = masque
    for _ in range(n):
        d = m.copy()
        d[1:, :] |= m[:-1, :]
        d[:-1, :] |= m[1:, :]
        d[:, 1:] |= m[:, :-1]
        d[:, :-1] |= m[:, 1:]
        m = d
    return m


def tracer_route(np, reseau, etapes):
    """Suit le reseau de routes d'une etape a la suivante.

    `etapes` : des points (colonne, ligne) dans le repere du masque. On se
    raccroche au pixel de route le plus proche de chaque etape, puis on
    cherche le plus court chemin de l'un a l'autre par un parcours en
    largeur. Renvoie la polyligne complete, ou None si le reseau ne relie
    pas deux etapes (le masque du mod a des trous : mieux vaut ne rien
    tracer qu'inventer une route qui n'existe pas).
    """
    from collections import deque
    h, l = reseau.shape
    lig, col = np.nonzero(reseau)
    if not len(lig):
        return None
    idx = lig.astype(np.int64) * l + col.astype(np.int64)

    def accrocher(p):
        d2 = (col - p[0]) ** 2 + (lig - p[1]) ** 2
        k = int(np.argmin(d2))
        return int(lig[k]) * l + int(col[k])

    voisins = (-l - 1, -l, -l + 1, -1, 1, l - 1, l, l + 1)
    dedans = np.zeros(h * l, dtype=bool)
    dedans[idx] = True

    trace = []
    for a, b in zip(etapes, etapes[1:]):
        depart, arrivee = accrocher(a), accrocher(b)
        parent = {depart: -1}
        file = deque([depart])
        while file:
            n = file.popleft()
            if n == arrivee:
                break
            x = n % l
            for dv in voisins:
                v = n + dv
                # on refuse de sauter d'un bord a l'autre de la grille
                if v < 0 or v >= h * l or abs((v % l) - x) > 1:
                    continue
                if dedans[v] and v not in parent:
                    parent[v] = n
                    file.append(v)
        if arrivee not in parent:
            return None
        bout, n = [], arrivee
        while n != -1:
            bout.append((n % l, n // l))
            n = parent[n]
        bout.reverse()
        trace += bout if not trace else bout[1:]
    return trace


