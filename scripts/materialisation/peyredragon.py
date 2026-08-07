# -*- coding: utf-8 -*-
"""Peyredragon, en mètres et à l'échelle 1:1.

Le sol n'est pas dessiné : il est CALCULÉ. Une fonction d'altitude donne
l'île entière — le cône du Dragonmont, sa caldeira, ses coulées, la frange de
falaises et l'unique grève. Le château et le bourg se posent dessus, et rien
n'est placé à la main qui puisse se déduire du relief.

Repère : mètres, origine au milieu de l'île, +x au levant, +y au nord, z = 0
au niveau de la mer.
"""
import math
import numpy as np

import formes as F

# ---------------------------------------------------------------------------
# les repères du monde — tout le reste en découle
# ---------------------------------------------------------------------------
ILE = (-400.0, 100.0)          # le milieu de l'île
RAYON = 2350.0                 # sa demi-largeur moyenne
SOMMET = (-1400.0, 500.0)      # le Dragonmont
CIME = 760.0
PIED = 2150.0
RADE = math.radians(-14.0)     # l'angle où la côte se couche : la grève et la rade
ANCRE = (ILE[0] + math.cos(RADE) * 1500, ILE[1] + math.sin(RADE) * 1500)


# ---------------------------------------------------------------------------
# le bruit — ce qui empêche une montagne d'être un cône
# ---------------------------------------------------------------------------
def _hache(i, j, graine):
    n = (i * np.int64(374761393) + j * np.int64(668265263) + np.int64(graine * 2654435761)) & np.int64(0x7FFFFFFF)
    n = (n ^ (n >> np.int64(13))) * np.int64(1274126177) & np.int64(0x7FFFFFFF)
    return ((n ^ (n >> np.int64(16))) & np.int64(0xFFFFFF)).astype(np.float32) / float(0xFFFFFF)


def _bruit(X, Y, taille, graine):
    fx, fy = X / taille, Y / taille
    i, j = np.floor(fx).astype(np.int64), np.floor(fy).astype(np.int64)
    tx, ty = fx - i, fy - j
    tx = tx * tx * (3 - 2 * tx)
    ty = ty * ty * (3 - 2 * ty)
    a = _hache(i, j, graine) * (1 - tx) + _hache(i + 1, j, graine) * tx
    b = _hache(i, j + 1, graine) * (1 - tx) + _hache(i + 1, j + 1, graine) * tx
    return a * (1 - ty) + b * ty


def _fbm(X, Y, taille, graine, octaves=4):
    # chaque octave tourne d'un angle irrationnel : sans ça, le réseau du bruit
    # s'aligne sur les axes et le terrain se met à onduler en velours côtelé.
    s, amp, t = 0.0, 1.0, taille
    ca, sa = 0.8, 0.6
    for k in range(octaves):
        s = s + _bruit(X, Y, t, graine + k * 17) * amp
        X, Y = X * ca - Y * sa, X * sa + Y * ca
        amp *= 0.5
        t *= 0.5
    return s / 1.875 - 0.5


def _adoucir(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------------------
# L'ALTITUDE — la seule vérité du lieu
# ---------------------------------------------------------------------------
def relief(X, Y):
    """L'île telle qu'elle est venue : sans rien de ce que les hommes y ont fait."""
    X = np.asarray(X, np.float32)
    Y = np.asarray(Y, np.float32)

    # --- la forme de l'île : un rayon qui varie avec l'angle ---------------
    dx, dy = X - ILE[0], Y - ILE[1]
    d = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    R = RAYON * (1 + 0.14 * np.sin(3 * th + 0.7) + 0.09 * np.sin(5 * th - 1.9)
                 + 0.05 * np.sin(8 * th + 2.4)) + _fbm(X, Y, 900, 5) * 210
    u = d / R

    # le plateau, puis la frange : falaise partout, sauf du côté de la rade
    plateau = 150.0 * (1 - 0.58 * u ** 2)
    ecart = np.abs(np.arctan2(np.sin(th - RADE), np.cos(th - RADE)))
    douceur = 1 - _adoucir(0.30, 0.95, ecart)          # 1 sur la grève, 0 ailleurs

    s_fal = _adoucir(0.972, 1.0, u)
    z_fal = plateau * (1 - s_fal) + (-30.0) * s_fal
    s_dou = _adoucir(0.90, 1.03, u)
    z_dou = plateau * (1 - s_dou) + (-6.0) * s_dou
    z = z_fal * (1 - douceur) + z_dou * douceur
    z = z - 420.0 * np.clip(u - 1.02, 0, 4) ** 1.2      # le fond, au large

    # --- le Dragonmont ----------------------------------------------------
    # Le cône donne la masse ; ce qui fait une montagne, ce sont les CRÊTES.
    # On déforme d'abord le plan (le ravin ne descend jamais droit), puis on
    # prend un bruit crêté — 1 − |bruit| — qui creuse des vallées à fond aigu
    # au lieu des plis réguliers d'une sinusoïde d'angle.
    mx, my = X - SOMMET[0], Y - SOMMET[1]
    dm = np.hypot(mx, my)
    tm = np.arctan2(my, mx)
    gx = X + _fbm(X, Y, 780, 71) * 220
    gy = Y + _fbm(X, Y, 780, 73) * 220
    flanc = np.clip(1 - dm / PIED, 0, 1)
    cone = CIME * flanc ** 1.75

    crete = 1 - np.abs(_fbm(gx, gy, 620, 61) * 2.0)        # 0 au fond du ravin
    crete = crete ** 1.4
    cone = cone * (0.74 + 0.26 * crete)
    # le grain propre à la montagne : d'autant plus marqué qu'on monte
    cone = cone + (_fbm(gx, gy, 240, 11) * 34 + _fbm(gx, gy, 88, 13) * 12) * flanc ** 0.6

    creux = 130.0 * np.clip(1 - (dm / 190.0) ** 2, 0, 1)   # la caldeira, ouverte au levant
    creux = creux * (1 - _adoucir(0.0, 1.4, np.abs(np.arctan2(np.sin(tm), np.cos(tm)))))
    z = z + np.maximum(cone - creux, 0)

    # --- le grain de la roche : l'île n'est lisse nulle part ---------------
    terre = _adoucir(-10.0, 30.0, z)
    ondes = 1 - np.abs(_fbm(gx, gy, 460, 41) * 2.0)
    z = z + (ondes * 30 + _fbm(gx, gy, 150, 47) * 15
             + _fbm(X, Y, 52, 53) * 5.0) * terre

    # --- l'éperon : la crête qui porte le château jusqu'à la montagne -------
    ax, ay = SOMMET
    bx, by = ANCRE
    vx, vy = bx - ax, by - ay
    q = vx * vx + vy * vy
    t = np.clip(((X - ax) * vx + (Y - ay) * vy) / q, 0, 1)
    dsg = np.hypot(X - (ax + vx * t), Y - (ay + vy * t))
    z = z + 120.0 * np.exp(-(dsg / 300.0) ** 2) * (0.35 + 0.65 * t)

    return z


# ---------------------------------------------------------------------------
# LE SITE — où l'on bâtit ne se décide pas : ça se lit sur le relief
# ---------------------------------------------------------------------------
def _rive(angle, r0=1200.0, r1=3400.0, pas=4.0):
    """Le trait de côte le long d'un rayon : le dernier mètre au-dessus de l'eau."""
    r = np.arange(r0, r1, pas, dtype=np.float32)
    x = ILE[0] + np.cos(angle) * r
    y = ILE[1] + np.sin(angle) * r
    z = relief(x, y)
    sec = np.where(z > 0.0)[0]
    return float(r[sec[-1]]) if len(sec) else r1


_RIVE = _rive(RADE)
_D = (math.cos(RADE), math.sin(RADE))
CHATEAU = (ILE[0] + _D[0] * (_RIVE - 470), ILE[1] + _D[1] * (_RIVE - 470))
QUAI = (ILE[0] + _D[0] * (_RIVE + 4), ILE[1] + _D[1] * (_RIVE + 4))
# l'assise : on n'a pas remblayé une colline, on a arasé le sommet de l'éperon
ASSISE = float(round(relief(np.float32([CHATEAU[0]]), np.float32([CHATEAU[1]]))[0] / 2) * 2)


def altitude(X, Y):
    """Le relief, plus ce que la pioche en a fait : l'assise du château."""
    z = relief(X, Y)
    r = np.hypot(np.asarray(X, np.float32) - CHATEAU[0],
                 np.asarray(Y, np.float32) - CHATEAU[1])
    k = _adoucir(250.0, 160.0, r)
    return z * (1 - k) + ASSISE * k


def _sol(x, y):
    return float(altitude(np.array([x], np.float32), np.array([y], np.float32))[0])


def matiere_du_sol(centres, normales):
    """De quoi le sol est fait : la pente et l'altitude tranchent, pas le goût."""
    z = centres[:, 2]
    pente = 1 - np.clip(normales[:, 2], 0, 1)
    # un seuil net dessine une frontière au cordeau, qui se voit à mille pas.
    # On le fait trembler d'un bruit : la roche perce l'herbe par plaques.
    j = _fbm(centres[:, 0], centres[:, 1], 130, 91)
    zz = z + j * 90
    pp = pente + j * 0.14
    m = np.full(len(z), "herbe", object)
    m[zz > 70] = "lande"
    m[zz > 260] = "coulee"
    m[zz > 470] = "cendre"
    m[pp > 0.30] = "roche"
    m[(pp > 0.46) & (zz > 40)] = "basalte"
    m[(z < 7) & (pente < 0.26)] = "greve"
    m[z < -1.0] = "haut-fond"
    return m


# ---------------------------------------------------------------------------
# LE CHÂTEAU — la pierre valyrienne, posée sur son assise
# ---------------------------------------------------------------------------
ENCEINTE = [(-115, -62), (-55, -90), (35, -94), (100, -64), (120, -6),
            (102, 56), (36, 86), (-46, 84), (-100, 52), (-122, -6)]
TOURS = [   # (x, y, rayon, sommet au-dessus de l'assise, flèche)
    # Une enceinte n'aligne pas huit tours identiques. Il y a une MAÎTRESSE
    # TOUR — celle qui voit la rade et qu'on nomme —, deux fortes aux angles
    # exposés, et des tourelles de flanquement qui ne font que battre le pied
    # du mur. C'est cette inégalité qui donne une silhouette au lieu d'une
    # couronne de dents.
    (120, -6, 15.0, 46, 18),     # la tour du Dragon de Mer : la maîtresse
    (-122, -6, 11.0, 30, 12),    # la Guivre des Vents, face au couchant
    (35, -94, 9.0, 22, 9),       # la tour du Nord
    (36, 86, 9.0, 20, 9),        # la tour du Midi
    (-55, -90, 6.5, 13, 0),      # flanquement
    (-100, 52, 6.5, 12, 0),
    (-115, -62, 6.0, 11, 0),
    (102, 56, 7.5, 17, 7),
]
PORTE = (112, 28)               # la porte de mer, d'où descend la montée


_CA, _SA = math.cos(RADE), math.sin(RADE)


def _monde(p):
    """Du repère de l'enceinte au monde : la porte regarde la rade."""
    return (CHATEAU[0] + p[0] * _CA - p[1] * _SA,
            CHATEAU[1] + p[0] * _SA + p[1] * _CA)


def _pan_de_la_porte():
    """Sur quel pan de l'enceinte tombe la porte, et à quelle position dessus."""
    px, py = _monde(PORTE)
    pts = [_monde(q) for q in ENCEINTE]
    mieux = (1e9, 0, 0.5)
    for i, (a, b) in enumerate(zip(pts, pts[1:] + pts[:1])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        q = dx * dx + dy * dy
        t = 0 if q == 0 else max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / q))
        d = math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)
        if d < mieux[0]:
            mieux = (d, i, t)
    return mieux[1], mieux[2]


def chateau():
    ext = [_monde(p) for p in ENCEINTE]
    pan, t_porte = _pan_de_la_porte()

    # LA COURTINE EST PERCÉE. Une enceinte fermée sur tout son tour est un
    # château où l'on n'entre pas : la montée arrivait devant un mur plein.
    # La porte de mer est une baie de 6 m sous un linteau à 9 m, et les
    # archères ponctuent les pans — un mur aveugle n'a jamais été bâti.
    baies = [{"segment": pan, "t": t_porte, "larg": 6.0,
              "appui": ASSISE - 1.0, "linteau": ASSISE + 9.0}]
    for i in range(len(ENCEINTE)):
        if i == pan:
            continue
        for t in (0.3, 0.7):
            baies.append({"segment": i, "t": t, "larg": 0.5,
                          "appui": ASSISE + 6.0, "linteau": ASSISE + 9.5})

    corps = [
        F.paroi(ext, 7.0, ASSISE - 14, ASSISE + 12, "pierre",
                baies=baies, fermer=True),
        # le hourd de pierre : des corbeaux, la dalle qu'ils portent, et les
        # créneaux dessus — le chemin de ronde saille au lieu d'être au nu
        F.machicoulis(ext, 7.0, ASSISE + 12, "pierre", pas=2.6, saillie=0.6,
                      fermer=True),
        F.creneaux(ext, 8.2, ASSISE + 13.5, 2.6, "pierre", pas=3.0, plein=1.7,
                   fermer=True),
    ]

    # LES TOURS SONT CREUSES : un fût de 1,4 m de paroi, des archères aux
    # étages, et une baie plus large au chemin de ronde.
    for (x, y, r, h, fl) in TOURS:
        cx, cy = _monde((x, y))
        fen = []
        for etage, z in enumerate(np.arange(ASSISE + 6, ASSISE + h - 3, 7.5)):
            for k in (1, 5, 9, 13):
                fen.append({"segment": (k + etage * 2) % 16, "t": 0.5,
                            "larg": 0.6, "appui": float(z),
                            "linteau": float(z) + 2.2})
        corps.append(F.tour_creuse(cx, cy, ASSISE - 16, ASSISE + h, r, 1.4,
                                   "pierre", cotes=16, couronne=3.0, baies=fen))
        if fl:
            corps.append(F.fleche(cx, cy, ASSISE + h + 3.0, fl, r * 0.9, "toit"))

    # le Tambour de Pierre : le donjon, creux lui aussi — c'est là que sont la
    # grande salle en bas et la chambre de la Table Peinte au sommet
    tx, ty = _monde((-8, -4))
    fen = []
    for etage, z in enumerate(np.arange(ASSISE + 5, ASSISE + 50, 9.0)):
        for k in range(0, 22, 3):
            fen.append({"segment": (k + etage) % 22, "t": 0.5,
                        "larg": 1.1 if etage else 2.4, "appui": float(z),
                        "linteau": float(z) + (3.0 if etage else 4.5)})
    corps.append(F.tour_creuse(tx, ty, ASSISE - 4, ASSISE + 52, 31.0, 2.6,
                               "pierre", cotes=22, couronne=4.0, baies=fen))
    corps.append(F.tour_creuse(tx - 6, ty + 4, ASSISE + 52, ASSISE + 74, 13.0,
                               1.6, "pierre", cotes=14, couronne=2.4,
                               baies=[{"segment": k, "t": 0.5, "larg": 1.6,
                                       "appui": ASSISE + 58, "linteau": ASSISE + 64}
                                      for k in range(0, 14, 2)]))
    corps.append(F.fleche(tx - 6, ty + 4, ASSISE + 76.4, 17, 11.0, "toit"))

    # UN DONJON N'EST PAS UN TUYAU. Cinquante-deux mètres de fût lisse, c'est la
    # pièce la plus visible et la moins travaillée. Trois choses le corrigent, et
    # ce sont celles qu'on taillait : des contreforts qui montent du talus, un
    # cordon qui marque le retrait à mi-hauteur, et des échauguettes en encorbel-
    # lement au couronnement.
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        for (r0, r1, z0, z1, larg) in ((31.0, 33.4, ASSISE - 4, ASSISE + 26, 4.2),
                                       (31.0, 32.6, ASSISE + 26, ASSISE + 48, 3.4)):
            cx0, cy0 = tx + math.cos(a) * r0, ty + math.sin(a) * r0
            cx1, cy1 = tx + math.cos(a) * r1, ty + math.sin(a) * r1
            corps.append(F._panneau((cx0, cy0), (cx1, cy1), larg, z0, z1, "pierre"))
    cercle = [(tx + math.cos(2 * math.pi * i / 22) * 31.6,
               ty + math.sin(2 * math.pi * i / 22) * 31.6) for i in range(22)]
    corps.append(F.moulure(cercle, F.CORDON, ASSISE + 25.4, "taille", fermer=True))
    corps.append(F.moulure(cercle, F.LARMIER, ASSISE + 46.6, "taille", fermer=True))
    # les échauguettes : de petites tourelles portées par des corbeaux, à la
    # rencontre du fût et du couronnement. C'est ce qui casse la rondeur.
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.7
        ex, ey = tx + math.cos(a) * 30.0, ty + math.sin(a) * 30.0
        corps.append(F.machicoulis([(ex - 0.4, ey), (ex + 0.4, ey)], 5.0,
                                   ASSISE + 44.0, "pierre", pas=1.6, saillie=0.5))
        corps.append(F.tour_creuse(ex, ey, ASSISE + 45.4, ASSISE + 56.0, 3.1, 0.7,
                                   "pierre", cotes=8, couronne=1.4,
                                   baies=[{"segment": 1, "t": 0.5, "larg": 0.5,
                                           "appui": ASSISE + 48,
                                           "linteau": ASSISE + 51}]))
        corps.append(F.fleche(ex, ey, ASSISE + 57.6, 5.5, 3.0, "toit"))

    # Les bâtiments de cour ne s'inventent plus ici : ils viennent du plan du
    # jeu, par `lieux.py`. Ce module ne fait que la coquille — mur, tours, donjon.

    # LA PORTERIE. Une porte n'est pas un trou dans un mur : c'est un ouvrage
    # qui SORT, pour qu'on soit battu de trois côtés avant d'y arriver, et
    # qu'on passe sous les mâchicoulis avant de passer sous la herse.
    pan, t_p = _pan_de_la_porte()
    pts = [_monde(q) for q in ENCEINTE]
    a0, b0 = pts[pan], pts[(pan + 1) % len(pts)]
    seuil = (a0[0] + (b0[0] - a0[0]) * t_p, a0[1] + (b0[1] - a0[1]) * t_p)
    vx, vy = seuil[0] - CHATEAU[0], seuil[1] - CHATEAU[1]
    nrm = math.hypot(vx, vy) or 1.0
    vx, vy = vx / nrm, vy / nrm
    lx, ly = -vy, vx
    AV, DEMI = 15.0, 8.5
    avant = [(seuil[0] + lx * DEMI, seuil[1] + ly * DEMI),
             (seuil[0] + vx * AV + lx * DEMI, seuil[1] + vy * AV + ly * DEMI),
             (seuil[0] + vx * AV - lx * DEMI, seuil[1] + vy * AV - ly * DEMI),
             (seuil[0] - lx * DEMI, seuil[1] - ly * DEMI)]
    corps.append(F.paroi(avant, 3.0, ASSISE - 12, ASSISE + 16, "pierre", fermer=True,
                         baies=[{"segment": 1, "t": 0.5, "larg": 5.0,
                                 "appui": ASSISE - 1.0, "linteau": ASSISE + 8.0},
                                {"segment": 0, "t": 0.5, "larg": 0.5,
                                 "appui": ASSISE + 10, "linteau": ASSISE + 13},
                                {"segment": 2, "t": 0.5, "larg": 0.5,
                                 "appui": ASSISE + 10, "linteau": ASSISE + 13}]))
    corps.append(F.machicoulis(avant, 3.0, ASSISE + 16, "pierre", pas=2.2,
                               saillie=0.7, fermer=True))
    corps.append(F.creneaux(avant, 4.4, ASSISE + 17.6, 2.4, "pierre", pas=2.6,
                            plein=1.5, fermer=True))
    # la rainure de herse, juste derrière l'entrée
    for cote in (1, -1):
        corps.append(F._panneau(
            (seuil[0] + vx * (AV - 1.6) + lx * 2.6 * cote,
             seuil[1] + vy * (AV - 1.6) + ly * 2.6 * cote),
            (seuil[0] + vx * (AV - 1.0) + lx * 2.6 * cote,
             seuil[1] + vy * (AV - 1.0) + ly * 2.6 * cote),
            1.0, ASSISE, ASSISE + 8.0, "taille"))

    # la porte : deux tourelles qui l'encadrent, creuses comme les autres
    for d in (-9, 9):
        cx, cy = _monde((PORTE[0] - 2, PORTE[1] + d))
        corps.append(F.tour_creuse(cx, cy, ASSISE - 14, ASSISE + 34, 6.0, 1.2,
                                   "pierre", cotes=12, couronne=2.2,
                                   baies=[{"segment": 3, "t": 0.5, "larg": 0.6,
                                           "appui": ASSISE + 20,
                                           "linteau": ASSISE + 23}]))
    return F.joindre(*corps)


# ---------------------------------------------------------------------------
# LA MONTÉE — du quai à la porte, en lacets, parce que c'est 78 mètres
# ---------------------------------------------------------------------------
LARGE_MONTEE = 7.0        # de quoi qu'un chariot passe, et qu'un homme se range
DEMI_ENTAILLE = 9.5       # jusqu'où la pioche a mordu, de part et d'autre de l'axe

_AXES = {}


def _lacets(lacets=3, large=105.0, pas=14.0):
    """La montée : on ne descend pas 80 mètres tout droit, on zigzague.

    Le tracé se pose SUR la roche — son altitude est celle du sol, lissée :
    une route taillée dans la pente, pas une passerelle.

    Gardé en mémoire : cinq modules le redemandent à chaque image, et le terrain
    l'interroge une fois par facette.
    """
    cle = (lacets, large, pas)
    if cle in _AXES:
        return _AXES[cle]
    # La montée part DE LA PORTE, pas d'un point voisin : elle arrivait jusqu'ici
    # à trente-quatre mètres du mur, et personne ne pouvait entrer.
    pan, t = _pan_de_la_porte()
    pts = [_monde(q) for q in ENCEINTE]
    a0, b0 = pts[pan], pts[(pan + 1) % len(pts)]
    seuil = (a0[0] + (b0[0] - a0[0]) * t, a0[1] + (b0[1] - a0[1]) * t)
    # cinq mètres au-dehors, le temps de franchir l'épaisseur du mur
    vers = (seuil[0] - CHATEAU[0], seuil[1] - CHATEAU[1])
    n = math.hypot(*vers) or 1.0
    depart = (seuil[0] + vers[0] / n * 6.0, seuil[1] + vers[1] / n * 6.0)
    arrivee = (QUAI[0] - _D[0] * 26, QUAI[1] - _D[1] * 26)
    lg = math.hypot(arrivee[0] - depart[0], arrivee[1] - depart[1])
    ux, uy = (arrivee[0] - depart[0]) / lg, (arrivee[1] - depart[1]) / lg
    nx, ny = -uy, ux
    jalons = []
    n = lacets * 2 + 1
    for i in range(n + 1):
        t = i / n
        cote = 0.0 if i in (0, n) else (1 if (i % 2) else -1) * large * math.sin(math.pi * t)
        jalons.append((depart[0] + ux * lg * t + nx * cote,
                       depart[1] + uy * lg * t + ny * cote))
    # on densifie, puis on prend l'altitude du sol et on la lisse
    dense = []
    for a, b in zip(jalons, jalons[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        for k in range(max(1, int(d / pas))):
            s = k / max(1, int(d / pas))
            dense.append((a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s))
    dense.append(jalons[-1])
    # AU NIVEAU DU SOL, à l'épaisseur du pavage près. Le tracé était perché à
    # 1,40 m au-dessus de la roche pour que la nappe du terrain ne le traverse
    # pas ; c'est le terrain qui cède la place maintenant (voir `_terrain_perce`),
    # et la chaussée retombe où elle doit être. Le lissage qui suit est ce qui
    # fait la pente régulière : là où il passe sous le sol, c'est une entaille,
    # là où il passe dessus, un remblai.
    z = [_sol(x, y) + 0.25 for x, y in dense]
    for _ in range(6):
        z = [z[0]] + [(z[i - 1] + 2 * z[i] + z[i + 1]) / 4 for i in range(1, len(z) - 1)] + [z[-1]]
    z[0] = ASSISE
    z[-1] = 3.4
    trace = [(p[0], p[1], zz) for p, zz in zip(dense, z)]
    _AXES[cle] = trace
    return trace


def _le_long_de_la_montee(pts):
    """Pour chaque point : sa distance à l'axe, et l'altitude de la chaussée en face.

    Segment par segment plutôt qu'en un seul tableau : le terrain compte trois
    cent mille facettes et l'axe soixante-dix segments — le produit des deux ne
    tient pas en mémoire, la boucle si.
    """
    axe = _lacets()
    x, y = pts[:, 0], pts[:, 1]
    plus_pres = np.full(len(pts), 1e18, np.float32)
    z_route = np.zeros(len(pts), np.float32)
    for (ax, ay, az), (bx, by, bz) in zip(axe, axe[1:]):
        dx, dy = bx - ax, by - ay
        q = dx * dx + dy * dy or 1e-9
        t = np.clip(((x - ax) * dx + (y - ay) * dy) / q, 0, 1)
        ex, ey = x - ax - t * dx, y - ay - t * dy
        d = ex * ex + ey * ey
        ou = d < plus_pres
        plus_pres = np.where(ou, d, plus_pres)
        z_route = np.where(ou, az + (bz - az) * t, z_route)
    return np.sqrt(plus_pres), z_route


def montee():
    """La montée taillée : entaille du côté qui monte, soutènement du côté du vide.

    Une route de versant ne se POSE pas sur la pente : on mord la roche à l'amont
    et l'on rejette la terre à l'aval, où un mur la retient. Il n'y a donc pas
    deux ouvrages symétriques mais deux ouvrages différents, et le parapet ne se
    justifie que là où il y a quelque chose à tomber. Bordée des deux côtés sur
    neuf cents mètres, comme elle l'était, la chaussée disparaissait entre ses
    propres murets et l'on ne voyait plus de la rade qu'une file de pierres
    plantées dans l'herbe.

    Quel bord domine le vide n'est pas décidé ici : on interroge le sol de part
    et d'autre, et c'est le gradient du terrain qui tranche, lacet par lacet.
    """
    axe = _lacets()
    demi = LARGE_MONTEE / 2
    normales, bords = [], ([], [])
    for i, (x, y, z) in enumerate(axe):
        a = axe[max(0, i - 1)]
        b = axe[min(len(axe) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n, dx / n
        normales.append((nx, ny))
        bords[0].append((x + nx * demi, y + ny * demi, z))
        bords[1].append((x - nx * demi, y - ny * demi, z))

    # Le sol au nu du bord et au bout de l'entaille, des deux côtés, une fois
    # pour toutes : `_sol` coûte un appel numpy et on le rappellerait six fois.
    dehors = ([], [])
    for i, ((x, y, z), (nx, ny)) in enumerate(zip(axe, normales)):
        for c, s in ((0, 1.0), (1, -1.0)):
            bx, by = bords[c][i][0], bords[c][i][1]
            ox = x + s * nx * DEMI_ENTAILLE
            oy = y + s * ny * DEMI_ENTAILLE
            dehors[c].append((_sol(bx, by), ox, oy, _sol(ox, oy)))

    chaussee, maconnerie, taillee, parapets = [], [], [], []
    for i in range(len(axe) - 1):
        g0, g1 = bords[0][i], bords[0][i + 1]
        d0, d1 = bords[1][i], bords[1][i + 1]
        chaussee += F.quad(list(g0), list(g1), list(d1), list(d0))

        for c in (0, 1):
            p0, p1 = bords[c][i], bords[c][i + 1]
            (s0, ox0, oy0, l0) = dehors[c][i]
            (s1, ox1, oy1, l1) = dehors[c][i + 1]
            if (l0 - p0[2]) + (l1 - p1[2]) > 0.8:
                # L'AMONT : la roche a été coupée. La joue descend un mètre et
                # demi sous la chaussée pour passer derrière elle — le terrain
                # est ôté à la maille, et une arête franche laisserait un jour.
                taillee += F.quad([p0[0], p0[1], p0[2] - 1.5],
                                  [p1[0], p1[1], p1[2] - 1.5],
                                  [ox1, oy1, l1], [ox0, oy0, l0])
                continue
            # L'AVAL : le mur de soutènement, du nu de la chaussée jusqu'au sol,
            # avec un pied enterré pour la même raison.
            pied0 = min(s0, p0[2]) - 1.5
            pied1 = min(s1, p1[2]) - 1.5
            maconnerie += F.quad([p0[0], p0[1], p0[2]], [p1[0], p1[1], p1[2]],
                                 [p1[0], p1[1], pied1], [p0[0], p0[1], pied0])
            if (p0[2] - l0) + (p1[2] - l1) < 3.0:
                continue                      # pas de vide : pas de parapet
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            n = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / n * 0.28, dx / n * 0.28
            parapets.append(F.prisme(
                [(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny),
                 (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)],
                min(p0[2], p1[2]), max(p0[2], p1[2]) + 0.95, "taille")[0])

    corps = [F._t(chaussee, "taille"), F._t(maconnerie, "taille"),
             F._t(taillee, "roche")]
    if parapets:
        m = np.concatenate(parapets)
        corps.append((m, np.array(["taille"] * len(m), object)))
    return F.joindre(*corps)


def _terrain_perce(x0, y0, x1, y1, maille):
    """Le terrain, moins la roche que la montée a emportée.

    Sans ce trou, la nappe du sol traverse la chaussée : c'est ce qui obligeait
    à percher la route en l'air. Le terrain lui cède la place, et les joues de
    l'entaille — que `montee()` dessine — referment la coupure.
    """
    tris, mat = F.grille(x0, y0, x1, y1, maille, altitude, matiere_du_sol)
    c = tris.mean(1)
    d, z_route = _le_long_de_la_montee(c)
    otee = (d < DEMI_ENTAILLE) & (c[:, 2] > z_route - 1.4)
    return tris[~otee], mat[~otee]


def quai():
    ca, sa = -_SA, _CA                       # le quai est en travers de la rade
    c = [(QUAI[0] + u * ca - v * sa, QUAI[1] + u * sa + v * ca)
         for (u, v) in [(-78, -13), (78, -13), (78, 13), (-78, 13)]]
    corps = [F.prisme(c, -4.0, 3.4, "quai")]
    for k in range(6):                      # les ducs-d'Albe, sur l'eau
        u = -60 + k * 24
        x, y = QUAI[0] + u * ca + 18 * _D[0], QUAI[1] + u * sa + 18 * _D[1]
        corps.append(F.prisme([(x - 1, y - 1), (x + 1, y - 1), (x + 1, y + 1), (x - 1, y + 1)],
                              -3.0, 2.6, "bois"))
    return F.joindre(*corps)


# ---------------------------------------------------------------------------
# LE BOURG — trois cent quarante âmes, donc quatre-vingts feux
# ---------------------------------------------------------------------------
def feux(graine=1293):
    """Les paramètres de chaque feu du bourg — pas encore de la géométrie.

    Séparé de `bourg()` exprès : le monde 3D du jeu veut ces bâtiments sous
    forme de LIGNES (x, y, cap, façade, profondeur, hauteur), pas de triangles.
    Deux consommateurs, une seule source — sinon le bourg du jeu et celui des
    images finissent par ne plus être le même village.
    """
    R = np.random.RandomState(graine)
    ux, uy = -_SA, _CA                         # le long de la rive
    def p(u, v):
        return (QUAI[0] + ux * u - _D[0] * v, QUAI[1] + uy * u - _D[1] * v)
    chemins = [
        ([p(-40, 30), p(-150, 46), p(-260, 78), p(-350, 128)], 26),
        ([p(40, 30), p(150, 44), p(250, 74), p(330, 120)], 24),
        ([p(-70, 55), p(0, 62), p(80, 58)], 16),
        ([p(-190, 96), p(-120, 128), p(-40, 150)], 12),
    ]
    dehors = []
    for pts, n in chemins:
        seg = [(math.hypot(b[0] - a[0], b[1] - a[1]), a, b) for a, b in zip(pts, pts[1:])]
        total = sum(s[0] for s in seg)
        for i in range(n):
            cible = total * (i + 0.5) / n
            acc = 0.0
            for lg, a, b in seg:
                if acc + lg >= cible:
                    t = (cible - acc) / lg
                    x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                    ang = math.atan2(b[1] - a[1], b[0] - a[0])
                    break
                acc += lg
            for cote in (1, -1):
                if R.random() > 0.74:
                    continue
                e = 9.0 + R.random() * 5.0
                px = x - math.sin(ang) * e * cote + (R.random() - 0.5) * 5
                py = y + math.cos(ang) * e * cote + (R.random() - 0.5) * 5
                z = _sol(px, py)
                if z < 2.0 or z > 62.0:
                    continue
                dehors.append({
                    "x": px, "y": py, "z": z, "cap": ang + (R.random() - 0.5) * 0.5,
                    "long": 7.5 + R.random() * 4.5, "larg": 5.0 + R.random() * 2.0,
                    "haut": 4.2 + R.random() * 1.4, "usage": "maison",
                    "quartier": "Le bourg sous les murs", "pente": 0.72,
                    "mur": "mur-bourg", "toit": "chaume"})
    # les séchoirs : longs, étroits, tous en travers du vent de mer
    for k in range(10):
        px, py = p(-300 + (k % 5) * 26, 26 + (k // 5) * 26)
        px += R.random() * 6
        py += R.random() * 6
        z = _sol(px, py)
        if z < 1.0 or z > 40.0:
            continue
        dehors.append({"x": px, "y": py, "z": z, "cap": RADE, "long": 22.0,
                       "larg": 3.4, "haut": 2.8, "usage": "sechoir",
                       "quartier": "Les séchoirs", "pente": 0.35,
                       "mur": "bois", "toit": "bois"})
    return dehors


def bourg(graine=1293):
    corps = [F.maison(f["x"], f["y"], f["z"] - (0.6 if f["usage"] == "maison" else 0.0),
                      f["larg"], f["long"], f["haut"], f["cap"],
                      f["mur"], f["toit"], f["pente"])
             for f in feux(graine)]
    return F.joindre(*corps)


def mer(etendue=260000.0):
    c = [(-etendue, -etendue), (etendue, -etendue), (etendue, etendue), (-etendue, etendue)]
    return F.prisme(c, -0.2, 0.0, "mer", dessus=True, dessous=False)


# ---------------------------------------------------------------------------
# l'assemblage — le terrain se ré-échantillonne pour chaque vue
# ---------------------------------------------------------------------------
def paroi(p0, direction, longueur, z_bas, pas=3.0):
    """La face d'une coupe : la roche vue en tranche, du fond jusqu'au sol.

    On la découpe en petites cases pour pouvoir en retirer celles qui tombent
    dans une salle — c'est ce qui ouvre le cellier au lieu de le murer.
    """
    import lieux

    ux, uy = direction
    n = max(2, int(longueur / pas))
    xs = np.array([p0[0] + ux * (k * longueur / n) for k in range(n + 1)], np.float32)
    ys = np.array([p0[1] + uy * (k * longueur / n) for k in range(n + 1)], np.float32)
    haut = altitude(xs, ys)
    tris = []
    for k in range(n):
        z1 = min(haut[k], haut[k + 1])
        m = max(2, int((z1 - z_bas) / pas))
        for j in range(m):
            a = z_bas + (z1 - z_bas) * j / m
            b = z_bas + (z1 - z_bas) * (j + 1) / m
            tris.append([[xs[k], ys[k], a], [xs[k + 1], ys[k + 1], a],
                         [xs[k + 1], ys[k + 1], b]])
            tris.append([[xs[k], ys[k], a], [xs[k + 1], ys[k + 1], b],
                         [xs[k], ys[k], b]])
        # le pan de sol qui reste entre la coupe et la crête voisine
        tris.append([[xs[k], ys[k], z1], [xs[k + 1], ys[k + 1], z1],
                     [xs[k + 1], ys[k + 1], haut[k + 1]]])
        tris.append([[xs[k], ys[k], z1], [xs[k + 1], ys[k + 1], haut[k + 1]],
                     [xs[k], ys[k], haut[k]]])
    a = np.asarray(tris, np.float32)
    garder = ~lieux.dans_une_salle(a.mean(1))
    a = a[garder]
    return a, np.array(["coupe"] * len(a), object)


def batir(cadre, maille, avec_mer=True, avec_bourg=True, coupe=None,
          avec_sol=True):
    """`cadre` = (x0, y0, x1, y1) en mètres, `maille` = nombre de cases par côté.

    `coupe` = (point, normale) : on retire tout ce qui est du côté de la
    normale. C'est ainsi qu'on ouvre la roche pour montrer ce qu'il y a dessous
    — les cachots, le cellier, les galeries — sans les modéliser deux fois.
    """
    # Le château n'est plus meublé d'après le plan du jeu (une carte mentale où
    # les salles flottent au milieu de la cour) mais d'après un PROGRAMME
    # architectural : un anneau de corps plaqués contre la courtine.
    import programme as Prog           # tardif : il a besoin de ce module

    x0, y0, x1, y1 = cadre
    # les refends que le graphe de circulation désigne : c'est lui qui sait
    # quelles portes ont une raison d'être, la pierre ne fait que les percer
    import circulation as Circ
    morceaux = [chateau(), Prog.batir(Circ.refends_perces(Circ.engendrer()))]
    if avec_sol:
        # sans le sol, on voit ce que la roche cache : les salles taillées
        # dessous, à leur vraie place et à leur vraie profondeur.
        morceaux.insert(0, _terrain_perce(x0, y0, x1, y1, maille))
        morceaux += [montee(), quai()]
    if avec_bourg:
        morceaux.append(bourg())
    if avec_mer:
        morceaux.append(mer())
    tris, mat = F.joindre(*morceaux)

    if coupe:
        # la paroi d'abord : elle doit être coupée comme le reste
        p0v = coupe[0]
        nv = np.asarray(coupe[1], np.float32)[:2]
        nv = nv / (np.linalg.norm(nv) + 1e-9)
        # la paroi se pose un demi-mètre EN ARRIÈRE du plan : posée dessus, la
        # moitié de ses facettes tomberait du mauvais côté de la coupe et le
        # rendu se hacherait en lanières.
        recul = 0.6
        tris, mat = F.joindre((tris, mat),
                              paroi((p0v[0] - nv[1] * 260 - nv[0] * recul,
                                     p0v[1] + nv[0] * 260 - nv[1] * recul),
                                    (nv[1], -nv[0]), 520, ASSISE - 92))
        p0 = np.asarray(coupe[0], np.float32)
        n = np.asarray(coupe[1], np.float32)
        n = n / (np.linalg.norm(n) + 1e-9)
        garder = ((tris.mean(1) - p0) @ n) <= 0
        tris, mat = tris[garder], mat[garder]
    return tris, mat
