# -*- coding: utf-8 -*-
"""Le programme du château — architecturé, pas dessiné.

    python scripts/materialisation/programme.py

Ce module remplace la lecture du plan du jeu. Le plan était une carte mentale :
des salles qui flottent au milieu d'une cour, à distance les unes des autres.
Aucun château n'a jamais été bâti comme ça.

LA RÈGLE QUI CHANGE TOUT : **on n'habite pas le milieu d'une cour, on habite
CONTRE LE MUR.** Les corps de logis forment un anneau plaqué à l'intérieur de la
courtine, le dos à la muraille, la façade sur la cour. C'est vrai de Carcassonne
à Harlech, et c'est ce qui fait qu'un plan de château se reconnaît au premier
coup d'œil. Trois conséquences tombent gratuitement :

  · les corps voisins PARTAGENT leur mur de refend — plus de boîtes séparées ;
  · la courtine sert de mur arrière — on ne la double pas ;
  · la cour est ce qui RESTE, elle n'est pas dessinée.

Le second principe est la SÉQUENCE. Une grande salle médiévale n'est pas une
pièce isolée : c'est une chaîne obligée — le retrait du seigneur à l'estrade,
puis la salle, puis le passage des écrans, puis l'office et la bouteillerie,
puis les cuisines. On ne place donc pas des pièces, on déroule un ordre autour
de l'anneau depuis la porte, et l'adjacence est acquise par construction.
"""
import math
import sys

import numpy as np

import formes as F
import peyredragon as P

# ---------------------------------------------------------------------------
# LES NIVEAUX — altitudes partagées, 5,4 m de plancher à plancher
# ---------------------------------------------------------------------------
SOUS_PLAFOND = 5.4
PROFONDEUR_AILE = 11.0          # la profondeur d'un corps de logis, en mètres
REFEND = 0.8                    # le mur entre deux corps voisins
MUR_ARRIERE = 0.0               # néant : la courtine EST le mur du fond
DEBORD = 0.55                   # ce dont le toit dépasse le nu de la façade
PENTE = 0.30                    # de montée par mètre de profondeur


def niv(n):
    return P.ASSISE + n * SOUS_PLAFOND


# ---------------------------------------------------------------------------
# LE PROGRAMME — l'ordre autour de l'anneau, depuis la porte
#
# Ce n'est pas une liste de pièces : c'est un PARCOURS. On entre par la porte,
# et l'on croise dans l'ordre ce qu'un château met dans cet ordre-là — le
# service près de l'entrée (on ne fait pas traverser la cour à un cheval), le
# noble au fond (le plus loin de ce qui entre), et la chaîne de la grande salle
# d'un seul tenant. Changer cet ordre change l'architecture, et c'est le seul
# endroit où on la décide.
# ---------------------------------------------------------------------------
#   id, nom, façade en mètres, étages, ce que c'est
DROITE = [                      # en tournant vers la droite depuis la porte
    ("ecuries",     "Les écuries",           34.0, 2, "service"),
    ("forge",       "La forge",              11.0, 1, "service"),
    ("selleries",   "Les selleries",         12.0, 1, "service"),
    ("greniers",    "Les greniers",          26.0, 2, "service"),
    ("cuisines",    "Les cuisines",          19.0, 2, "office"),
    ("office",      "L'office et la bouteillerie", 13.0, 2, "office"),
    ("ecrans",      "Le passage des écrans", 5.0, 1, "passage"),
    ("grande-salle", "La grande salle",      44.0, 3, "noble"),
    ("retrait",     "Le retrait du seigneur", 13.0, 3, "noble"),
    ("chambre-haute", "La chambre haute",    16.0, 3, "noble"),
    ("galerie",     "La galerie",            20.0, 1, "noble"),
    ("chambre-enfants", "La chambre des enfants", 14.0, 2, "noble"),
    ("garde-robe",  "La garde-robe",         10.0, 2, "noble"),
]
GAUCHE = [                      # et vers la gauche, l'autre aile
    ("corps-de-garde", "Le corps de garde",  20.0, 2, "service"),
    ("garnison",    "Le logis de la garnison", 30.0, 3, "service"),
    ("armurerie",   "L'armurerie",           14.0, 2, "service"),
    ("hotes",       "Le logis des hôtes",    22.0, 3, "noble"),
    ("septuaire",   "Le septuaire",          24.0, 3, "culte"),
    ("roukerie",    "La roukerie",           10.0, 3, "office"),
    ("archives",    "L'archive",             12.0, 1, "office"),
    ("boulangerie", "La boulangerie",        15.0, 1, "office"),
    ("brasserie",   "La brasserie",          17.0, 1, "office"),
    ("buanderie",   "La buanderie",          12.0, 1, "service"),
    ("charretterie", "La charretterie",      22.0, 1, "service"),
    ("infirmerie",  "L'infirmerie",          16.0, 1, "office"),
]
LIBRES = [                      # ce qui se tient dans la cour, et pourquoi
    ("puits", "Le puits", 2.6, "Une cour sans puits est une cour qu'on rend"),
]
CAVES = [                       # sous la grande salle : le cellier voûté
    ("cellier",     "Le cellier",            "grande-salle"),
    ("salle-froide", "La salle froide",      "office"),
    ("cachots",     "Les cachots",           "corps-de-garde"),
]


# ---------------------------------------------------------------------------
# L'ANNEAU — la bande habitable, plaquée contre la courtine
# ---------------------------------------------------------------------------
def _decaler(poly, d):
    """Le polygone rentré de `d` : on décale chaque côté, puis on recoupe."""
    n = len(poly)
    cotes = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        lg = math.hypot(dx, dy) or 1.0
        # la normale vers l'intérieur : le polygone est parcouru dans un sens
        # connu, on prend celle qui rapproche du centre
        nx, ny = -dy / lg, dx / lg
        cx = sum(p[0] for p in poly) / n
        cy = sum(p[1] for p in poly) / n
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if (cx - mx) * nx + (cy - my) * ny < 0:
            nx, ny = -nx, -ny
        cotes.append(((a[0] + nx * d, a[1] + ny * d), (b[0] + nx * d, b[1] + ny * d)))
    out = []
    for i in range(n):
        (p1, p2), (q1, q2) = cotes[i - 1], cotes[i]
        d1 = (p2[0] - p1[0], p2[1] - p1[1])
        d2 = (q2[0] - q1[0], q2[1] - q1[1])
        det = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(det) < 1e-9:
            out.append(q1)
            continue
        t = ((q1[0] - p1[0]) * d2[1] - (q1[1] - p1[1]) * d2[0]) / det
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out


def _longueurs(poly):
    L = [math.hypot(b[0] - a[0], b[1] - a[1])
         for a, b in zip(poly, poly[1:] + poly[:1])]
    return L, sum(L)


def _cote_et_part(poly, s):
    """L'abscisse `s` dite autrement : sur quel côté elle tombe, et où dessus."""
    L, tot = _longueurs(poly)
    s = s % tot
    for i, lg in enumerate(L):
        if s <= lg:
            return i, (s / lg if lg else 0.0)
        s -= lg
    return len(L) - 1, 1.0


def _sur(poly, i, t):
    a, b = poly[i], poly[(i + 1) % len(poly)]
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _tranche(dedans, facade, s0, s1, pas=3.0):
    """Le dos et la façade d'un corps, pris AU MÊME endroit de l'anneau.

    Les deux lignes n'ont pas le même périmètre : la façade est rentrée de onze
    mètres de plus que le dos, ce qui la raccourcit de soixante-douze. Prendre
    la même abscisse curviligne sur l'une et sur l'autre fait donc glisser la
    façade d'un corps le long du mur, de plus en plus loin de son dos à mesure
    qu'on tourne — jusqu'à quatre-vingts mètres de profondeur d'aile au bout de
    l'anneau, et le corps traverse la cour au lieu de la border.

    La correspondance juste est celle des SOMMETS : `_decaler` conserve l'ordre
    et le nombre des côtés, donc le côté i de l'une répond au côté i de l'autre,
    et l'on interpole à l'identique à l'intérieur du côté. Les deux bords
    sortent d'ici appairés point à point, ce dont la toiture a besoin.
    """
    n = max(2, int(abs(s1 - s0) / pas))
    arriere, avant = [], []
    for k in range(n + 1):
        i, t = _cote_et_part(dedans, s0 + (s1 - s0) * k / n)
        arriere.append(_sur(dedans, i, t))
        avant.append(_sur(facade, i, t))
    return arriere, avant


def _quartier(s, tot):
    """Un nom de lieu pour un appentis : a quel quart du tour il se trouve."""
    q = (s / tot) % 1.0
    return ("levant" if q < 0.25 else "midi" if q < 0.5
            else "couchant" if q < 0.75 else "nord")


def _abscisse_de_la_porte(dedans):
    """Où la porte tombe sur l'anneau : c'est de là que le programme se déroule."""
    px, py = P._monde(P.PORTE)
    L, tot = _longueurs(dedans)
    mieux, s = (1e9, 0.0), 0.0
    for i, lg in enumerate(L):
        a, b = dedans[i], dedans[(i + 1) % len(dedans)]
        for k in range(int(lg) + 1):
            t = k / max(1, lg)
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            d = math.hypot(px - x, py - y)
            if d < mieux[0]:
                mieux = (d, s + k)
        s += lg
    return mieux[1], tot


# ---------------------------------------------------------------------------
# LE PLAN — dérouler le programme autour de l'anneau
# ---------------------------------------------------------------------------
def plan():
    """Chaque corps, découpé dans la bande : un trapèze qui suit la courtine.

    Un corps n'est PAS une boîte posée : c'est une tranche de l'anneau, entre la
    face intérieure du mur et la ligne de façade. Il épouse donc les angles de
    l'enceinte, et son mur de refend est celui de son voisin.
    """
    mur = [P._monde(p) for p in P.ENCEINTE]
    dedans = _decaler(mur, 3.5)                     # la face intérieure du mur
    facade = _decaler(mur, 3.5 + PROFONDEUR_AILE)   # la ligne de façade
    s_porte, tot = _abscisse_de_la_porte(dedans)

    corps, s = [], s_porte
    for sens, liste in ((1, DROITE), (-1, GAUCHE)):
        s = s_porte + sens * 2.0
        for (cle, nom, facade_m, etages, genre) in liste:
            s0, s1 = (s, s + facade_m) if sens > 0 else (s - facade_m, s)
            if abs(s1 - s_porte) > tot * 0.52 and abs(s0 - s_porte) > tot * 0.52:
                break                               # les deux ailes se rejoignent
            arriere, avant = _tranche(dedans, facade, s0, s1)
            corps.append({
                "id": cle, "nom": nom, "genre": genre, "etages": etages,
                "contour": arriere + list(reversed(avant)),
                "facade": avant, "arriere": arriere,
                "s": (min(s0, s1), max(s0, s1)),
                "aire": facade_m * PROFONDEUR_AILE,
                "milieu": _sur(facade, *_cote_et_part(dedans, (s0 + s1) / 2)),
            })
            s += sens * (facade_m + REFEND)

    # CE QUI RESTE DE MUR NU SE COMBLE. Un programme ne tombe jamais juste sur
    # un perimetre : plutot que d'inventer quinze noms de pieces pour boucher,
    # on remplit les vides avec ce qu'un chateau y met vraiment — des appentis
    # adosses, bas et sans etage — et l'on garde les petits vides comme
    # passages vers le chemin de ronde. Le generateur dit ce qu'il a comble.
    corps.sort(key=lambda c: c["s"][0])
    combles = []
    bornes = [(c["s"][0], c["s"][1]) for c in corps]
    vides = []
    for (a0, a1), (b0, b1) in zip(bornes, bornes[1:]):
        if b0 - a1 > 1.0:
            vides.append((a1 + REFEND, b0 - REFEND))
    if bornes:
        vides.append((bornes[-1][1] + REFEND, bornes[0][0] + tot - REFEND))
    # Un vide de deux cents metres ne se comble pas d'un seul batiment : on le
    # decoupe en travees de vingt-six metres au plus. C'est ce qu'on voit le
    # long d'une courtine — une suite d'appentis adosses, chacun sa porte et son
    # toit, pas une halle interminable.
    TRAVEE = 26.0
    decoupes = []
    for (v0, v1) in vides:
        lg = v1 - v0
        if lg < 9.0:
            continue                       # un passage, pas un batiment
        n = max(1, int(round(lg / TRAVEE)))
        pas = lg / n
        for j in range(n):
            decoupes.append((v0 + j * pas + (REFEND if j else 0), v0 + (j + 1) * pas))
    for k, (v0, v1) in enumerate(decoupes):
        lg = v1 - v0
        arriere, avant = _tranche(dedans, facade, v0, v1)
        c = {"id": "appentis-%d" % k, "nom": "L'appentis du %s" % _quartier(v0, tot),
             "genre": "appentis", "etages": 1,
             "contour": arriere + list(reversed(avant)),
             "facade": avant, "arriere": arriere, "s": (v0, v1),
             "aire": lg * PROFONDEUR_AILE,
             "milieu": _sur(facade, *_cote_et_part(dedans, (v0 + v1) / 2)),
             "comble": True}
        corps.append(c)
        combles.append(c)
    corps.sort(key=lambda c: c["s"][0])

    # ce qui se tient dans la cour
    libres = []
    tx, ty = P._monde((-8, -4))
    libres.append({"id": "tambour-de-pierre", "nom": "Le Tambour de Pierre",
                   "genre": "donjon", "etages": 8, "ou": (tx, ty), "rayon": 31.0,
                   "raison": "Le donjon tient le milieu : il voit par-dessus tout"})
    # le puits, au barycentre de la cour libre
    cx = sum(p[0] for p in facade) / len(facade)
    cy = sum(p[1] for p in facade) / len(facade)
    for (cle, nom, r, raison) in LIBRES:
        libres.append({"id": cle, "nom": nom, "genre": "cour", "etages": 0,
                       "ou": (cx + 26.0, cy - 18.0), "rayon": r, "raison": raison})

    # les caves, sous les corps qui les portent
    caves = []
    par_id = {c["id"]: c for c in corps}
    for (cle, nom, sous) in CAVES:
        h = par_id.get(sous)
        if not h:
            continue
        caves.append({"id": cle, "nom": nom, "genre": "cave", "etages": 1,
                      "contour": h["contour"], "sous": sous,
                      "milieu": h["milieu"],
                      "raison": "Voûtée sous %s — on n'en creuse pas ailleurs"
                                % h["nom"].lower()})
    return {"mur": mur, "dedans": dedans, "facade": facade, "combles": combles,
            "corps": corps, "libres": libres, "caves": caves,
            "porte": s_porte, "perimetre": tot}


if __name__ == "__main__":
    p = plan()
    print("L'ANNEAU  %d m de périmètre intérieur, %.0f m de profondeur d'aile"
          % (p["perimetre"], PROFONDEUR_AILE))
    occupe = sum(c["s"][1] - c["s"][0] for c in p["corps"])
    print("          %d corps, %.0f m de façade bâtie (%.0f %% du tour)"
          % (len(p["corps"]), occupe, occupe / p["perimetre"] * 100))
    print("\nLES CORPS, dans l'ordre depuis la porte")
    for c in sorted(p["corps"], key=lambda c: c["s"][0]):
        print("  %-16s %-30s %5.0f m2  %d etage%s  %s"
              % (c["id"], c["nom"][:30], c["aire"], c["etages"],
                 "s" if c["etages"] > 1 else " ", c["genre"]))
    print("\nDANS LA COUR")
    for l in p["libres"]:
        print("  %-16s %-30s  %s" % (l["id"], l["nom"][:30], l["raison"]))
    print("\nLES CAVES")
    for c in p["caves"]:
        print("  %-16s %-30s  %s" % (c["id"], c["nom"][:30], c["raison"]))


# ---------------------------------------------------------------------------
# LA GÉOMÉTRIE — les corps sont des TRANCHES, pas des boîtes
# ---------------------------------------------------------------------------
MATIERE = {"service": "pierre", "office": "pierre", "noble": "pierre",
           "culte": "pierre", "passage": "pierre", "cave": "taille",
           "donjon": "pierre", "cour": "taille",
           # un appentis de comblement est de moindre appareil : moellon et
           # bois, pas de la pierre de taille — et ça se voit, ce qui est juste
           "appentis": "mur-bourg"}


def _baies(contour, n_facade, z0, haut, porte=True, graine=0):
    """Portes et fenêtres : sur la FAÇADE, jamais sur le dos.

    Un corps de logis a la courtine dans le dos — on n'y perce pas, ou l'on
    ouvre le château sur le dehors. Toute la lumière vient de la cour, et c'est
    ce qui donne à ces plans leur caractère : dedans clair, dehors aveugle.

    Les travées sont INÉGALES. Une file de baies identiques au même entraxe est
    le dernier réflexe de dessinateur qui trahit un bâtiment engendré : on ne
    perçait pas au compas, on perçait où la pièce en avait besoin, et une baie
    sur cinq est aveugle parce qu'un mur de refend passe derrière.
    """
    b, n = [], len(contour)
    R = np.random.RandomState(1300 + graine)
    debut = n - n_facade
    for i in range(debut, n - 1):
        t = (i - debut) / max(1, n_facade - 2)
        if porte and abs(t - 0.42) < 0.08:
            b.append({"segment": i, "t": 0.5, "larg": 2.4,
                      "appui": z0, "linteau": z0 + min(3.2, haut - 0.4)})
            continue
        if R.random() < 0.18:
            continue                    # aveugle : un refend passe derrière
        larg = 1.0 + R.random() * 0.7
        appui = z0 + 1.0 + R.random() * 0.5
        b.append({"segment": i, "t": 0.35 + R.random() * 0.3, "larg": larg,
                  "appui": appui,
                  "linteau": min(appui + 1.6 + R.random() * 0.8, z0 + haut - 0.5)})
    return b


EPAISSEUR_TOIT = 0.22           # la couverture et son voligeage, vus de dessous


def _toiture(c, haut):
    """Le toit d'un corps : un pan qui verse dans la cour, ET QUI DÉBORDE.

    Un pan qui meurt au nu de la façade n'est pas une toiture, c'est un plan
    posé sur une boîte — et c'est ce qui reste quand on ne fait que la pente.
    Ce qu'on voit d'un vrai toit, c'est l'ÉGOUT : le débord qui jette l'ombre
    en travers de la façade et signale que le mur s'arrête là.

    Quatre choses, donc, et aucune n'est décorative :
      · le débord de 55 cm, qui porte cette ombre ;
      · son dessous fermé — sans quoi on voit le jour entre le toit et le mur,
        et le bâtiment redevient une coquille ;
      · le larmier sous l'égout, qui jette l'eau au lieu de la laisser courir
        sur la pierre — la moulure qui sépare la maçonnerie du carton ;
      · les deux pignons de bout, qui ferment la travée. Sans eux les toits
        voisins fondent en UNE SEULE pente qui fait le tour du château, et l'on
        cesse de compter les corps.
    """
    ar, av = c["arriere"], c["facade"]
    n = min(len(ar), len(av))
    if n < 2:
        return []

    # le plan du toit passe par le nu de la façade à l'altitude `haut` et monte
    # vers la courtine : la profondeur de chaque tranche décide de son faîtage
    egout, faite = [], []
    for k in range(n):
        a, b = ar[k], av[k]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1.0
        egout.append((b[0] + dx / d * DEBORD, b[1] + dy / d * DEBORD))
        faite.append(haut + d * PENTE)
    z_eg = haut - DEBORD * PENTE
    ep = EPAISSEUR_TOIT

    tris = []
    for k in range(n - 1):
        a0, a1, e0, e1 = ar[k], ar[k + 1], egout[k], egout[k + 1]
        f0, f1 = faite[k], faite[k + 1]
        # le pan, puis le dessous — la couverture a une épaisseur, sinon le
        # débord est une feuille de papier vue par la tranche
        tris += F.quad([a0[0], a0[1], f0], [a1[0], a1[1], f1],
                       [e1[0], e1[1], z_eg], [e0[0], e0[1], z_eg])
        tris += F.quad([a0[0], a0[1], f0 - ep], [e0[0], e0[1], z_eg - ep],
                       [e1[0], e1[1], z_eg - ep], [a1[0], a1[1], f1 - ep])
        # la planche d'égout, de chant : c'est elle qui prend la lumière
        tris += F.quad([e0[0], e0[1], z_eg - ep], [e1[0], e1[1], z_eg - ep],
                       [e1[0], e1[1], z_eg], [e0[0], e0[1], z_eg])

    # les pignons : un rampant maçonné qui monte au-dessus du pan, aux deux
    # bouts du corps — le refend qui perce le toit et sépare les travées
    SAILLIE_PIGNON = 0.40
    for (k, sens) in ((0, -1), (n - 1, 1)):
        a, e = ar[k], egout[k]
        dx, dy = e[0] - a[0], e[1] - a[1]
        d = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / d * REFEND * sens, dx / d * REFEND * sens
        # le rampant, vu comme une bande : deux points en plan (dos, égout),
        # chacun avec l'altitude du dessous du pan et celle du dessus du pignon
        bas = (faite[k] - ep, z_eg - ep)
        sur = (faite[k] + SAILLIE_PIGNON, z_eg + SAILLIE_PIGNON)
        A, B = [a, e], [(a[0] + nx, a[1] + ny), (e[0] + nx, e[1] + ny)]
        for cote in (A, B):                        # les deux joues
            tris += F.quad([cote[0][0], cote[0][1], bas[0]],
                           [cote[1][0], cote[1][1], bas[1]],
                           [cote[1][0], cote[1][1], sur[1]],
                           [cote[0][0], cote[0][1], sur[0]])
        tris += F.quad([A[0][0], A[0][1], sur[0]], [B[0][0], B[0][1], sur[0]],
                       [B[1][0], B[1][1], sur[1]], [A[1][0], A[1][1], sur[1]])
        tris += F.quad([A[1][0], A[1][1], bas[1]], [B[1][0], B[1][1], bas[1]],
                       [B[1][0], B[1][1], sur[1]], [A[1][0], A[1][1], sur[1]])

    return [(np.asarray(tris, np.float32),
             np.array(["toit"] * len(tris), object)),
            # Le larmier court sous l'égout, au nu de la façade — mais SOUS la
            # corniche, que `mouler_un_corps` a déjà posée dans les 62 derniers
            # centimètres et qui saille davantage. Collé dessous, il disparaît
            # dedans : on le descend de sa propre hauteur pour que les deux
            # moulures se lisent comme un entablement au lieu d'une seule.
            F.moulure(av, F.LARMIER, haut - 1.04, "taille")]


def _fins_de_corps(c):
    """Les deux pans de bout d'un corps — ses refends avec ses voisins.

    Le contour est monté arrière (de s0 vers s1) puis façade retournée : le pan
    du bout s1 est le dernier de l'arrière, et celui du bout s0 est le pan qui
    referme le contour.
    """
    return {"s1": len(c["arriere"]) - 1, "s0": len(c["contour"]) - 1}


def batir(perces=None):
    """Le château entier : anneau, caves, escaliers.

    `perces` est l'ensemble des couples de corps dont le refend est ouvert — il
    vient de `circulation.py`. Sans lui, on ne perce rien : une porte qui ne
    mène à rien n'a aucune raison d'exister, et c'est le graphe qui sait.
    """
    p = plan()
    perces = perces or set()
    ordre = sorted(p["corps"], key=lambda c: c["s"][0])
    voisin = {}
    for a, b in zip(ordre, ordre[1:] + ordre[:1]):
        voisin.setdefault(a["id"], {})["s1"] = b["id"]
        voisin.setdefault(b["id"], {})["s0"] = a["id"]

    # LES ESCALIERS D'ABORD, parce que les planchers doivent les laisser passer.
    # Une vis qui monte à travers une dalle pleine est l'endroit le plus visible
    # où l'intérieur cesse d'être crédible : on demande donc leurs emprises à la
    # circulation avant de trianguler quoi que ce soit, et l'on perce.
    import circulation as Circ
    g = Circ.engendrer_sur(p)
    tremies_de, sous_le_rez, tremies_cave = {}, {}, {}
    for e in g["escaliers"]:
        x, y = e["ou"]
        if e["genre"] == "vis":
            r = e["rayon"] + 0.45
            emprise = [(x - r, y - r), (x + r, y - r), (x + r, y + r), (x - r, y + r)]
            # La circulation loge la vis AU BOUT du corps, contre le refend —
            # elle est donc à cheval sur deux corps, et son emprise mord sur les
            # planchers du voisin. Percer le seul corps nommé laisserait une
            # demi-dalle en travers de la cage : on perce qui elle touche.
            for c in p["corps"]:
                if _mord(c["contour"], emprise):
                    tremies_de.setdefault(c["id"], []).append(emprise)
        else:
            dx = math.cos(P.RADE) * e["course"]
            dy = math.sin(P.RADE) * e["course"]
            emprise = [(x - 1.4, y - 1.4), (x + dx + 1.4, y - 1.4),
                       (x + dx + 1.4, y + dy + 1.4), (x - 1.4, y + dy + 1.4)]
            tremies_cave.setdefault(e["corps"], []).append(emprise)
            # la descente traverse aussi le rez du corps qui porte la cave
            hote = next((v["sous"] for v in p["caves"] if v["id"] == e["corps"]), None)
            if hote:
                sous_le_rez.setdefault(hote, []).append(emprise)

    corps = []
    for c in p["corps"]:
        n_fac = len(c["facade"])
        bouts = _fins_de_corps(c)
        refends = []
        for cote, seg in bouts.items():
            autre = voisin.get(c["id"], {}).get(cote)
            if autre and tuple(sorted((c["id"], autre))) in perces:
                refends.append({"segment": seg, "t": 0.42, "larg": 1.5,
                                "appui": niv(0), "linteau": niv(0) + 2.3})
        vis = tremies_de.get(c["id"], [])
        for etage in range(c["etages"]):
            z = niv(etage)
            corps.append(F.salle(
                c["contour"], z, SOUS_PLAFOND - 0.4, REFEND,
                MATIERE[c["genre"]], sol="taille",
                plafond="taille" if etage < c["etages"] - 1 else None,
                baies=_baies(c["contour"], n_fac, z, SOUS_PLAFOND - 0.4,
                             porte=(etage == 0),
                             graine=hash(c["id"]) % 997 + etage * 7)
                      + (refends if etage == 0 else []),
                # au rez, la vis ne perce rien sous elle : on ne troue pas le
                # sol de la cour. Ce qui l'y perce, c'est la descente de cave.
                tremies_sol=(sous_le_rez.get(c["id"], []) if etage == 0 else vis),
                tremies_plafond=vis))
        # l'habillage : plinthe au pied, cordon a chaque etage, corniche en tete.
        # C'est ce qui fait qu'une facade cesse d'etre un panneau.
        corps.append(F.mouler_un_corps(
            c["facade"], niv(0), niv(c["etages"]), c["etages"], SOUS_PLAFOND,
            "taille"))

        # le toit : un pan unique qui verse dans la cour, comme un appentis
        # adossé — c'est ce que fait un corps plaqué contre une courtine
        corps += _toiture(c, niv(c["etages"]))

    for c in p["caves"]:
        corps.append(F.salle(c["contour"], niv(-1), SOUS_PLAFOND - 0.9, REFEND,
                             "taille", sol="basalte", plafond="basalte",
                             baies=[{"segment": 0, "t": 0.5, "larg": 2.0,
                                     "appui": niv(-1),
                                     "linteau": niv(-1) + 2.6}],
                             tremies_plafond=tremies_cave.get(c["id"], [])))

    for e in g["escaliers"]:
        if e["genre"] == "vis":
            x, y = e["ou"]
            haut = niv(e["au"] + 1) - 0.4
            corps.append(F.vis(x, y, niv(0), haut, e["rayon"] + 0.35, "taille"))
            # la tourelle qui l'enveloppe : c'est elle qu'on voit saillir sur la
            # façade d'un corps, et c'est la signature d'un escalier dedans
            corps.append(F.tour_creuse(
                x, y, niv(0) - 1.0, haut + 1.6, e["rayon"] + 0.95, 0.6, "pierre",
                cotes=10, couronne=1.2,
                baies=[{"segment": k, "t": 0.5, "larg": 0.5,
                        "appui": niv(0) + 1.4 + j * 2.2,
                        "linteau": niv(0) + 3.0 + j * 2.2}
                       for j in range(max(1, int((haut - niv(0)) // 2.6)))
                       for k in (2, 7)]))
        else:
            x, y = e["ou"]
            corps.append(F.volee((x, y, niv(-1)),
                                 (x + math.cos(P.RADE) * e["course"],
                                  y + math.sin(P.RADE) * e["course"], niv(0)),
                                 2.2, "taille", garde=0.9))

    # le pavage de la cour, sa bordure au pied des façades, et le perron
    corps.append(F.prisme(p["facade"], niv(0) - 0.5, niv(0) + 0.02, "taille"))
    # une bordure saillante au pied des corps : le dallage ne bute plus dans le
    # mur, il s'arrête sur un rang de pierre dure — et c'est là que l'eau court
    corps.append(F.moulure(p["facade"] + p["facade"][:1], F.CORDON,
                           niv(0) - 0.04, "taille", dehors=False))
    tx, ty = P._monde((-8, -4))
    for k in range(4):
        corps.append(F.prisme(
            [(tx + 31 + 1.2 * k + dx, ty + dy) for (dx, dy) in
             ((0, -3.2), (1.3, -3.2), (1.3, 3.2), (0, 3.2))],
            niv(0), niv(0) + 0.17 * (4 - k), "taille"))

    for l in p["libres"]:
        if l["genre"] == "donjon":
            continue                      # le Tambour est bâti par peyredragon.py
        corps.append(F.tour(l["ou"][0], l["ou"][1], P.ASSISE - 1.0,
                            P.ASSISE + 1.2, l["rayon"], "taille", cotes=10))

    corps.append(_garde_corps_du_chemin_de_ronde())
    corps += _mobilier(p)
    return F.joindre(*corps)


# ---------------------------------------------------------------------------
# CE QU'IL Y A DEDANS, ET CE QUI EMPÊCHE D'EN TOMBER
# ---------------------------------------------------------------------------
def _garde_corps_du_chemin_de_ronde():
    """Le parapet plein de l'arête intérieure de la courtine.

    La courtine se bâtit dans `peyredragon.chateau()`, mais elle ne connaît que
    sa défense : mâchicoulis et créneaux, qui regardent le dehors. Côté cour, il
    n'y a rien, et douze mètres de vide sous les pieds. On le pose ici parce que
    c'est ici qu'on a déjà `P.ENCEINTE` et `P.ASSISE` sous la main, et que ce
    module bâtit tout ce qui vit à l'INTÉRIEUR des murs.

    Les cotes viennent de la courtine et doivent la suivre : la dalle du hourd
    est posée à ASSISE + 12 sur 1,35 m de corbeaux et de dalle, les merlons
    partent de ASSISE + 13,5 à 3,55 m de l'axe. Le parapet se cale là — il
    comble les vides entre les merlons intérieurs au lieu de doubler un mur.
    """
    return F.parapet([P._monde(q) for q in P.ENCEINTE], 3.55,
                     P.ASSISE + 13.5, 1.1, 1.1, "pierre",
                     fermer=True, dedans=True)


#   le corps, ce qu'on y met, et contre quel bout de son mur du fond
MEUBLES = [
    ("grande-salle", "cheminee", 0.42),
    ("grande-salle", "dressoir", 0.66),
    ("cuisines",     "cheminee", 0.30),
    ("cuisines",     "cheminee", 0.70),   # une cuisine de château a deux feux
    ("retrait",      "cheminee", 0.50),
]


def _mobilier(p):
    """Une cheminée au mur du fond, un dressoir : l'échelle, pas l'inventaire.

    On ne meuble pas trente-deux corps. Le but n'est pas de garnir le château,
    c'est de donner à l'œil un objet dont il connaît la taille — un foyer où
    l'on se tient debout, un bahut à hauteur de hanche. Trois pièces suffisent :
    au-delà, on ne gagne plus d'échelle, on gagne du triangle.
    """
    par_id = {c["id"]: c for c in p["corps"]}
    out = []
    for (cle, quoi, t) in MEUBLES:
        c = par_id.get(cle)
        if not c:
            continue
        ar, av = c["arriere"], c["facade"]
        k = max(0, min(len(ar) - 1, int(t * (len(ar) - 1))))
        # adossé au mur du fond, tourné vers la cour : le vecteur qui va du dos
        # à la façade dit à la fois où le meuble se pose et comment il regarde
        dos, face = ar[k], av[k]
        vers = (face[0] - dos[0], face[1] - dos[1])
        n = math.hypot(*vers) or 1.0
        ou = (dos[0] + vers[0] / n * REFEND, dos[1] + vers[1] / n * REFEND)
        if quoi == "cheminee":
            # la souche traverse le toit : c'est elle qu'on voit de la cour, et
            # c'est ce qui dit qu'un corps est habité et non remisé
            out.append(F.cheminee(ou, vers, niv(0), "taille",
                                  souche=niv(c["etages"]) + PROFONDEUR_AILE * PENTE + 2.6))
        else:
            out.append(F.dressoir(ou, vers, niv(0), "bois"))
    return out
