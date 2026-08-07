# -*- coding: utf-8 -*-
"""Les lieux du château — bâtis d'après `ecrans/modules/plans.js`, pas réinventés.

Le plan du jeu est la liste qui fait foi : c'est lui qui dit quelles salles
existent, où elles sont les unes par rapport aux autres, et à quel étage. On le
LIT, on cale son tracé sur l'enceinte du modèle 3D par une similitude ajustée
sur les dix pans de la muraille, et on donne à chaque salle un volume.

Conséquence voulue : le plan qu'on montre au joueur et le modèle qu'on rend en
images ne peuvent plus se contredire. Ajouter une salle dans `plans.js` la fait
apparaître ici sans qu'on y touche.
"""
import math
import os
import re

import numpy as np

import formes as F
import peyredragon as P

PLANS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "ecrans", "modules", "plans.js")

# Ce que le modèle 3D bâtit déjà par ailleurs : on ne le refait pas ici.
DEJA = {"cour", "tambour-de-pierre", "tour-dragon-mer", "guivre-des-vents",
        "porte-de-mer", "quai", "bourg", "greve", "grand-escalier",
        "chemin-ronde"}

# Le plan est une carte mentale, pas un relevé : il met le quai à cent pas du
# mur alors qu'il est à cinq cents mètres et cent vingt mètres plus bas. Pour
# ceux-là, la position du plan ne vaut rien — on prend celle du modèle.
SCHEMATIQUE = {"quai", "bourg", "greve", "grand-escalier", "chemin-ronde"}

# Ce qui n'est pas un bâtiment : une aire de sol, qu'on rend à plat.
AIRES = {"jardin-aegon", "lices", "fosses"}

# ---------------------------------------------------------------------------
# LES MESURES — en mètres, déclarées, jamais tirées du dessin
#
# Le plan est une carte mentale : il grossit ce qui compte. Métrisé tel quel
# (0,70 m par unité, facteur calé sur l'enceinte), il donnait une grande salle
# de 87 × 32 m — plus grande que Westminster Hall — et une chambre de la Table
# Peinte de 42 × 42 m. Le projet connaît déjà ce travers : `echelle.js` porte
# une table qui ramène le Donjon Rouge de 720 m à 330 m.
#
# Donc : le plan donne la POSITION et l'étage, cette table donne les MESURES.
# (longueur × largeur × hauteur sous faîtage, en mètres). Une salle absente
# d'ici prend le défaut au bas de la table — et c'est un signe qu'elle reste
# à mesurer, pas un droit à sortir du dessin.
# ---------------------------------------------------------------------------
TAILLE = {
    # les grands volumes de la cour
    "grande-salle":    (44.0, 15.0, 16.0),   # l'estrade, deux rangs de tables
    "septuaire":       (26.0, 14.0, 15.0),
    "communs":         (32.0, 10.0, 9.5),
    "cuisines":        (17.0, 11.0, 9.0),
    "chambres-hotes":  (19.0,  9.0, 12.0),
    "salle-levant":    (13.0,  9.5, 10.0),
    "antichambre":     (11.0,  7.0, 8.5),
    "officine":        ( 8.0,  6.0, 7.5),
    "forge":           ( 9.0,  7.0, 6.5),
    "roukerie":        ( 9.0,  9.0, 19.0),   # ronde : la tour aux corbeaux
    "porte-dragon":    (13.0, 10.0, 15.0),
    "baraques":        ( 6.5,  4.5, 4.0),
    # les aires : du sol, pas du bâti
    "jardin-aegon":    (24.0, 17.0, 0.6),
    "lices":           (42.0, 24.0, 0.6),
    "fosses":          (58.0, 28.0, 0.6),
    # les étages — mesurés pour les repères et la coupe, pas posés au sol
    "table-peinte":    (13.0, 12.0, 7.5),    # la table fait 4 m de long
    "appartements-reine": (15.0, 9.0, 8.0),
    "chambre-enfants": ( 9.0,  7.5, 6.0),
    # ce qui est taillé sous l'assise
    "cachots":         (11.0,  8.0, 4.5),
    "archives":        ( 9.5,  7.0, 5.0),
    "cellier":         (15.0,  9.0, 6.0),
    "salle-froide":    ( 7.5,  6.0, 4.0),
    "etuves":          ( 8.5,  7.0, 4.5),
    "galeries":        (58.0,  5.0, 6.5),    # quatre-vingts pas sous la mer
}
DEFAUT = (10.0, 8.0, 8.0)


def mesures(cle):
    """Longueur, largeur et hauteur d'un lieu, en mètres."""
    return TAILLE.get(cle, DEFAUT)


HAUTEUR = {k: v[2] for k, v in TAILLE.items()}   # ce que les appelants attendent
# À quelle profondeur sous l'assise chaque salle taillée a son plafond, en
# mètres. La hauteur, elle, est dans TAILLE comme pour tout le reste.
PROFONDEUR = {"cachots": 9.0, "archives": 7.0, "cellier": 6.0,
              "salle-froide": 11.0, "etuves": 8.0, "galeries": 58.0}
CREUX = {k: (v, TAILLE[k][2]) for k, v in PROFONDEUR.items()}


# ---------------------------------------------------------------------------
# lire le plan
# ---------------------------------------------------------------------------
def _nombres(t):
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", t)]


def _forme(t):
    """Le centre et les demi-dimensions d'une forme de plan, y déjà retourné."""
    m = re.search(r"forme:\s*\{\s*c:\s*\[([^\]]+)\]", t)
    if m:
        cx, cy, r = _nombres(m.group(1))[:3]
        return (cx, -cy), (r, r), "rond"
    m = re.search(r"forme:\s*\{\s*r:\s*\[([^\]]+)\]", t)
    if m:
        n = _nombres(m.group(1))
        x, y, l, h = n[0], n[1], n[2], n[3]
        return (x + l / 2, -(y + h / 2)), (l / 2, h / 2), "carre"
    m = re.search(r'forme:\s*\{\s*d:\s*"([^"]+)"', t)
    if m:
        n = _nombres(m.group(1))
        xs, ys = n[0::2], n[1::2]
        k = min(len(xs), len(ys))
        xs, ys = xs[:k], ys[:k]
        return ((min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2), \
               ((max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2), "carre"
    return None


def lire_plan():
    src = open(PLANS, encoding="utf-8").read()
    i = src.index("peyredragon:")
    bloc = src[i:src.index("\n  },\n", i)]
    mur = _nombres(re.search(r'mur:\s*"([^"]+)"', bloc).group(1))
    mur = [(mur[k], -mur[k + 1]) for k in range(0, len(mur) - 1, 2)]

    salles = []
    # Les entrées ne se terminent pas toutes de la même façon ; on découpe donc
    # sur le début de chacune plutôt que de deviner sa fin.
    debuts = [m.start() for m in re.finditer(r'\{ id: "', bloc)]
    for k, d in enumerate(debuts):
        corps = bloc[d:debuts[k + 1] if k + 1 < len(debuts) else len(bloc)]
        t = re.match(r'\{ id: "([^"]+)", nom: "([^"]+)"', corps)
        if not t:
            continue
        cle, nom = t.group(1), t.group(2)
        f = _forme(corps)
        if not f:
            continue
        centre, demi, genre = f
        etage = re.search(r'etage:\s*"([^"]+)"', corps)
        quoi = re.search(r'quoi:\s*"([^"]*)"', corps)
        salles.append({
            "id": cle, "nom": nom, "centre": centre, "demi": demi, "genre": genre,
            "etage": etage.group(1) if etage else None,
            "dehors": "dehors: true" in corps,
            "quoi": quoi.group(1) if quoi else "",
            # Le texte brut de l'entrée, gardé tel quel : `_forme` n'en rend que
            # la boîte, et bâtir un INTÉRIEUR demande le tracé lui-même (voir
            # scripts/monde/peyredragon_interieurs.py). Rien d'autre ne le lit.
            "corps": corps,
        })
    return mur, salles


# ---------------------------------------------------------------------------
# caler le plan sur l'enceinte
# ---------------------------------------------------------------------------
def _similitude(a, b):
    """Échelle, rotation et translation qui posent au mieux `a` sur `b`."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ca, cb = a.mean(0), b.mean(0)
    A, B = a - ca, b - cb
    U, S, Vt = np.linalg.svd(A.T @ B)
    R = (U @ Vt).T
    if np.linalg.det(R) < 0:                     # jamais de miroir
        Vt[-1] *= -1
        R = (U @ Vt).T
    s = S.sum() / (A ** 2).sum()
    return s, R, ca, cb


def _caler(mur, enceinte):
    """On ignore par quel coin le plan commence : on essaie les dix départs."""
    mieux = None
    if len(mur) != len(enceinte):
        raise ValueError("le plan et l'enceinte n'ont pas le même nombre de pans")
    # retourner y a inversé le sens de parcours : on essaie les deux, et les dix
    # départs de chacun — le plan ne commence pas forcément par le même coin.
    for sens in (mur, list(reversed(mur))):
        for k in range(len(sens)):
            tourne = sens[k:] + sens[:k]
            s, R, ca, cb = _similitude(tourne, enceinte)
            proj = (np.asarray(tourne) - ca) @ R.T * s + cb
            ecart = np.linalg.norm(proj - np.asarray(enceinte), axis=1).mean()
            if mieux is None or ecart < mieux[0]:
                mieux = (ecart, s, R, ca, cb)
    return mieux


_MUR, _SALLES = lire_plan()
_ECART, _S, _R, _CA, _CB = _caler(_MUR, P.ENCEINTE)


def _vers_local(p):
    q = (np.asarray(p, float) - _CA) @ _R.T * _S + _CB
    return (float(q[0]), float(q[1]))


# Il n'y a plus de conversion de longueur : le facteur du plan ne sert QU'aux
# positions. Toute dimension du modèle est en mètres, déclarée dans TAILLE.


# ---------------------------------------------------------------------------
# donner un volume à chaque salle
# ---------------------------------------------------------------------------
def lieux():
    """Chaque salle du plan, posée dans le monde : (id, nom, point, niveau)."""
    out = []
    for s in _SALLES:
        loc = _vers_local(s["centre"])
        x, y = P._monde(loc)
        # La POSITION vient du plan ; les MESURES viennent de la table. Métriser
        # les formes du dessin donnait un facteur deux sur toutes les salles.
        lg, la, _h = mesures(s["id"])
        dx, dy = lg / 2, la / 2
        haut = P.ASSISE
        if s["etage"] == "sommet":
            haut = P.ASSISE + 34
        elif s["etage"] == "dessous":
            haut = P.ASSISE - CREUX.get(s["id"], (8.0, 4.0))[0]
        elif s["dehors"]:
            haut = P._sol(x, y)
        out.append({"id": s["id"], "nom": s["nom"], "quoi": s["quoi"],
                    "ou": (x, y, haut), "demi": (dx, dy), "genre": s["genre"],
                    "etage": s["etage"], "dehors": s["dehors"]})
    return out


def dedans_poly(poly, x, y):
    """Le rayon lancé — le même test que partout ailleurs dans le projet."""
    d = False
    j = len(poly) - 1
    for i in range(len(poly)):
        if (poly[i][1] > y) != (poly[j][1] > y) and            x < (poly[j][0] - poly[i][0]) * (y - poly[i][1]) /                (poly[j][1] - poly[i][1]) + poly[i][0]:
            d = not d
        j = i
    return d


def _rect(x, y, dx, dy):
    """Le contour d'une salle, tourné comme l'enceinte."""
    c = [(x - dx, y - dy), (x + dx, y - dy), (x + dx, y + dy), (x - dx, y + dy)]
    return [(x + (u - x) * P._CA - (v - y) * P._SA,
             y + (u - x) * P._SA + (v - y) * P._CA) for (u, v) in c]


def _toit(contour, x, y, z, pente=0.8):
    """Quatre pans qui se rejoignent en pointe, posés sur les murs."""
    s = z + min(math.hypot(contour[0][0] - x, contour[0][1] - y),
                math.hypot(contour[1][0] - x, contour[1][1] - y)) * pente
    tris = [[[a[0], a[1], z], [b[0], b[1], z], [x, y, s]]
            for a, b in zip(contour, contour[1:] + contour[:1])]
    return np.asarray(tris, np.float32), np.array(["toit"] * len(tris), object)


def _ouvertures(contour, x, y, z_sol, haut, vers, porte=1.5):
    """Une porte du côté d'où l'on vient, des fenêtres sur les autres pans.

    `vers` est le point vers lequel la salle s'ouvre — la cour, en général : on
    perce sa porte sur le pan qui le regarde, et pas sur celui du fond.
    """
    baies, mieux, i_porte = [], -1e9, 0
    for i, (a, b) in enumerate(zip(contour, contour[1:] + contour[:1])):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        d = ((mx - x) * (vers[0] - x) + (my - y) * (vers[1] - y))
        if d > mieux:
            mieux, i_porte = d, i
    baies.append({"segment": i_porte, "t": 0.5, "larg": porte,
                  "appui": z_sol, "linteau": z_sol + min(2.4, haut - 0.6)})
    for i in range(len(contour)):
        if i == i_porte:
            continue
        for t in (0.32, 0.68):
            baies.append({"segment": i, "t": t, "larg": 0.9,
                          "appui": z_sol + 1.3,
                          "linteau": z_sol + min(3.1, haut - 0.5)})
    return baies


def _bloc(x, y, z, dx, dy, h, matiere, toit=None, vers=None, creuse=True,
          sol=None, plafond=None):
    """Un lieu bâti. CREUX par défaut : des murs épais, un plancher, des baies.

    Un volume plein suffit à une silhouette, jamais à un bâtiment : on ne peut
    ni y entrer ni voir qu'il est habité. L'épaisseur des murs est celle qu'on
    bâtissait — 0,9 m pour un logis de cour, ce qui laisse un embrasement
    visible à chaque baie.
    """
    c = _rect(x, y, dx, dy)
    if not creuse:
        corps = [F.prisme(c, z, z + h, matiere)]
        if toit:
            corps.append(_toit(c, x, y, z + h))
        return F.joindre(*corps)

    baies = _ouvertures(c, x, y, z, h, vers or (P.CHATEAU[0], P.CHATEAU[1]))
    corps = [F.salle(c, z, h, 0.9, matiere, sol=sol or "taille",
                     plafond=plafond, baies=baies)]
    if toit:
        corps.append(_toit(c, x, y, z + h))
    return F.joindre(*corps)


def bati():
    """Tout ce que le plan nomme et que le modèle n'avait pas encore bâti."""
    corps = []
    for L in lieux():
        cle = L["id"]
        if cle in DEJA:
            continue
        x, y, z = L["ou"]
        dx, dy = L["demi"]
        r = max(4.0, (dx + dy) / 2)

        if cle in CREUX:                       # les salles taillées sous l'assise
            prof, h = CREUX[cle]
            # taillées dans le roc : pas de toit, mais un plafond — sinon on
            # regarde le ciel depuis un cachot qui est censé être sous la cour
            corps.append(_bloc(x, y, P.ASSISE - prof, dx, dy, h, "taille",
                               plafond="basalte", sol="basalte"))
            continue

        if cle in AIRES:                       # une aire de sol, pas un bâtiment
            sol = P._sol(x, y) if L["dehors"] else P.ASSISE
            mat = "cendre" if cle == "fosses" else "greve"
            corps.append(_bloc(x, y, sol - 0.4, dx, dy, 0.6, mat, creuse=False))
            if cle == "fosses":                # les gueules de caverne
                for k in (-1, 0, 1):
                    corps.append(F.tour(x + k * dx * 0.55, y - dy * 0.3,
                                        sol - 2, sol + 9 + abs(k) * -2, 7.0,
                                        "basalte", cotes=10))
            continue

        if L["etage"] == "sommet":             # un étage : un corps posé plus haut
            corps.append(_bloc(x, y, P.ASSISE + 26, dx * 0.8, dy * 0.8,
                               mesures(cle)[2], "pierre", toit="toit"))
            continue

        if L["genre"] == "rond":
            h = mesures(cle)[2]
            sol = P._sol(x, y) if L["dehors"] else P.ASSISE
            corps.append(F.tour_creuse(
                x, y, sol - 6, sol + h, r, 0.9, "pierre", cotes=14, couronne=2.2,
                baies=[{"segment": 0, "t": 0.5, "larg": 1.4,
                        "appui": sol, "linteau": sol + 2.4}] +
                      [{"segment": k, "t": 0.5, "larg": 0.8,
                        "appui": sol + 3 + j * 4.5, "linteau": sol + 5.4 + j * 4.5}
                       for j in range(max(1, int((h - 4) // 4.5)))
                       for k in (3, 7, 11)]))
            corps.append(F.fleche(x, y, sol + h + 2.4, r * 0.9, r * 0.84, "toit"))
            continue

        sol = P._sol(x, y) if L["dehors"] else P.ASSISE
        mat = "mur-bourg" if cle == "baraques" else "pierre"
        toit = "chaume" if cle == "baraques" else "toit"
        corps.append(_bloc(x, y, sol - 3, dx, dy, mesures(cle)[2], mat, toit))

    # le puits de la cour, que le plan porte en ornement
    px, py = P._monde(_vers_local((185, -92)))
    corps.append(F.tour(px, py, P.ASSISE, P.ASSISE + 1.4, 2.6, "taille", cotes=10))
    return F.joindre(*corps)


def boites():
    """Les volumes taillés sous l'assise, pour percer la face de coupe.

    Une section qui passe au travers d'une salle doit l'OUVRIR : sans ces
    trous, la paroi de roche recouvre le cellier qu'on voulait montrer.
    """
    b = []
    for L in lieux():
        if L["id"] not in CREUX:
            continue
        prof, h = CREUX[L["id"]]
        x, y, _ = L["ou"]
        dx, dy = L["demi"]
        b.append((x, y, P.ASSISE - prof, P.ASSISE - prof + h, dx, dy))
    return b


def dans_une_salle(pts):
    """Vrai pour les points qui tombent dans une salle taillée."""
    dedans = np.zeros(len(pts), bool)
    for (x, y, z0, z1, dx, dy) in boites():
        u = (pts[:, 0] - x) * P._CA + (pts[:, 1] - y) * P._SA
        v = -(pts[:, 0] - x) * P._SA + (pts[:, 1] - y) * P._CA
        dedans |= ((np.abs(u) < dx) & (np.abs(v) < dy)
                   & (pts[:, 2] > z0) & (pts[:, 2] < z1))
    return dedans


def taille_sous_roche():
    """Les seules salles creusées, en volumes nus : de quoi les peindre par-dessus."""
    corps = []
    for L in lieux():
        if L["id"] not in CREUX:
            continue
        prof, h = CREUX[L["id"]]
        x, y, _ = L["ou"]
        corps.append(_bloc(x, y, P.ASSISE - prof, L["demi"][0], L["demi"][1],
                           h, "taille"))
    return F.joindre(*corps)


def place_libre():
    """Le point de la cour le plus éloigné de tout ce qui est bâti.

    On ne devine pas où poser une caméra à hauteur d'homme : le plan remplit la
    cour de logis, et un point choisi à vue finit dans un mur. On cherche donc
    le plus grand vide, et il se déplace tout seul si le plan change.
    """
    ronds = [(-8.0, -4.0, 33.0)]                          # le Tambour de Pierre
    ronds += [(float(x), float(y), r + 2.0) for (x, y, r, h, fl) in P.TOURS]
    rects = []
    for L in lieux():
        if L["id"] in DEJA or L["dehors"] or L["etage"] == "dessous":
            continue
        u = (L["ou"][0] - P.CHATEAU[0]) * P._CA + (L["ou"][1] - P.CHATEAU[1]) * P._SA
        v = -(L["ou"][0] - P.CHATEAU[0]) * P._SA + (L["ou"][1] - P.CHATEAU[1]) * P._CA
        # un rectangle, pas un disque de son grand côté : prendre le rayon
        # circonscrit d'une grande salle de 86 m barrerait toute la cour.
        rects.append((u, v, L["demi"][0] + 2.5, L["demi"][1] + 2.5))

    mur = np.asarray(P.ENCEINTE, float)
    mieux, ou = -1e9, (0.0, 0.0)
    for u in np.arange(-108, 114, 1.5):
        for v in np.arange(-86, 82, 1.5):
            d = min([math.hypot(u - a, v - b) - r for (a, b, r) in ronds] +
                    [math.hypot(max(0.0, abs(u - a) - dx), max(0.0, abs(v - b) - dy))
                     if (abs(u - a) > dx or abs(v - b) > dy) else
                     -min(dx - abs(u - a), dy - abs(v - b))
                     for (a, b, dx, dy) in rects])
            bord = min(math.hypot(u - m[0], v - m[1]) for m in mur)
            d = min(d, bord - 6.0)
            if d > mieux:
                mieux, ou = d, (u, v)
    x, y = P._monde(ou)
    return (x, y, P.ASSISE), mieux


def reperes_reels():
    """Les lieux dont le plan ment sur la place : on les ancre sur le modèle."""
    r = []
    for L in lieux():
        if L["id"] not in SCHEMATIQUE:
            continue
        if L["id"] == "quai":
            p = (P.QUAI[0], P.QUAI[1], 6.0)
        elif L["id"] in ("bourg", "greve"):
            u = -170 if L["id"] == "bourg" else 150
            p = (P.QUAI[0] - P._SA * u - P._D[0] * 70,
                 P.QUAI[1] + P._CA * u - P._D[1] * 70, 12.0)
        elif L["id"] == "grand-escalier":
            m = P._lacets()
            p = m[len(m) // 2]
        else:                                   # le chemin de ronde : sur le mur
            p = P._monde(P.ENCEINTE[2]) + (P.ASSISE + 30,)
        r.append((p, L["nom"]))
    return r


if __name__ == "__main__":
    print("plan calé sur l'enceinte à %.1f m d'écart moyen, échelle %.2f m/unité"
          % (_ECART * _S, _S))
    for L in lieux():
        print("  %-18s %-32s %6.0f %6.0f %6.0f  %s"
              % (L["id"], L["nom"][:32], L["ou"][0], L["ou"][1], L["ou"][2],
                 L["etage"] or ("dehors" if L["dehors"] else "cour")))
