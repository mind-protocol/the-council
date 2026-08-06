"""Genere la geometrie de la carte de Westeros a partir du mod AGOT.

Usage :
    python scripts/carte_geo.py                 -> ecrans/modules/geo.js
    python scripts/carte_geo.py --hauteur 620   (hauteur du viewBox)
    python scripts/carte_geo.py --tolerance 0.5 (simplification, unites SVG)

Outil de BUILD, lance a la main : il lit les donnees du mod AGOT installe
(Steam workshop 2962333032) et fige le resultat dans un fichier JS. Le jeu
ne depend jamais du mod ni de CK3 a l'execution — seulement de geo.js.

Chaine :
1. common/landed_titles : pile de blocs -> province -> (empire, royaume, comte)
2. map_data/definition.csv : province -> couleur RGB dans provinces.png
3. map_data/default.map : zones maritimes, lacs, rivieres navigables
4. map_data/provinces.png (9216x6144) : sous-echantillonne, chaque pixel
   devient l'id de sa region, puis cadre sur Westeros
5. suivi de contour (crack following) sur chaque masque -> polygones exacts,
   frontieres communes rigoureusement identiques entre regions voisines
6. simplification Douglas-Peucker -> chemins SVG

Le repere de sortie : viewBox cale sur Westeros, hauteur donnee par
--hauteur, largeur deduite du ratio reel du continent.

Doc : docs/carte.md
"""
import argparse
import json
import math
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJET = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(PROJET, "ecrans", "modules", "geo.js")

CANDIDATS_MOD = [
    r"C:\Program Files (x86)\Steam\steamapps\workshop\content\1158310\2962333032",
    r"C:\Program Files (x86)\Steam\steamapps\workshop\content\1158310",
]

# Sous-echantillonnage de provinces.png (9216x6144). 2 => 4608x3072, soit
# ~4 px par unite SVG une fois cadre sur Westeros : largement assez fin.
PAS = 2

# Les grandes regions, telles que le mod les nomme (rang empire), avec leur
# nom francais, un nom court pour les etiquettes de la carte, et l'ordre
# d'affichage.
REGIONS = [
    ("e_the_north",        "Le Nord",                  "Le Nord"),
    ("e_the_wall",         "Le Mur",                   "Le Mur"),
    ("e_the_vale",         "Le Val d'Arryn",           "Le Val"),
    ("e_the_riverlands",   "Le Conflans",              "Le Conflans"),
    ("e_the_iron_islands", "Les Îles de Fer",          "Îles de Fer"),
    ("e_the_westerlands",  "Les Terres de l'Ouest",    "L'Ouest"),
    ("e_the_crownlands",   "Les Terres de la Couronne", "La Couronne"),
    ("e_the_reach",        "Le Bief",                  "Le Bief"),
    ("e_the_stormlands",   "Les Terres de l'Orage",    "L'Orage"),
    ("e_dorne",            "Dorne",                    "Dorne"),
]
# Terres hors Westeros gardees en fond discret (decoupees au cadre).
FONDS = {"e_beyond_the_wall": "au_dela", "e_narrow_sea": "essos",
         "e_daoryrdembos": "essos"}

# Les lieux de etat/lieux.json -> comte du mod qui porte leur chateau.
LIEUX = {
    "port-real": "c_kings_landing",
    "peyredragon": "c_dragonstone",
    "lamarck": "c_high_tide",
    "rosby": "c_rosby",
    "stokeworth": "c_stokeworth",
    "sombreval": "c_duskendale",
    "repaire-aux-corneilles": "c_rooks_rest",
    "griffes": "c_claw_isle",
    "pointe-massey": "c_stonedance",
    "sharp-point": "c_sharp_point",
    "sweetport-sound": "c_sweetport_sound",
    "cracfosse": "c_dyre_den",
    "accalmie": "c_storms_end",
    "harrenhal": "c_harrenhal",
    "villevieille": "c_oldtown",
    "vivesaigues": "c_riverrun",
    "les-eyrie": "c_the_eyrie",
    "castral-roc": "c_casterly_rock",
    "winterfell": "c_winterfell",
}

# La vignette du plateau est cadree sur la baie de la Nera — la ou se joue
# la Danse. La grande table, elle, montre tout Westeros.
LIEUX_BAIE = ["port-real", "peyredragon", "lamarck", "rosby", "stokeworth",
              "sombreval", "repaire-aux-corneilles", "griffes",
              "pointe-massey", "sharp-point", "sweetport-sound",
              "cracfosse"]


# ------------------------------------------------------------------ le mod

def trouver_mod():
    """Dossier du mod AGOT : premier candidat qui porte une carte de Westeros."""
    candidats = []
    for c in CANDIDATS_MOD:
        if os.path.isdir(c) and os.path.isfile(
                os.path.join(c, "map_data", "definition.csv")):
            candidats.append(c)
        elif os.path.isdir(c):
            candidats += [os.path.join(c, d) for d in os.listdir(c)]
    for c in candidats:
        defcsv = os.path.join(c, "map_data", "definition.csv")
        if not os.path.isfile(defcsv):
            continue
        with open(defcsv, encoding="utf-8", errors="replace") as fh:
            tete = fh.read(20000)
        if "winterfell" in tete.lower():
            return c
    sys.exit("mod AGOT introuvable — verifier CANDIDATS_MOD")


def lire_definition(mod):
    """definition.csv -> {province_id: couleur RGB packee}."""
    couleurs = {}
    with open(os.path.join(mod, "map_data", "definition.csv"),
              encoding="utf-8", errors="replace") as fh:
        for ligne in fh:
            parts = ligne.split(";")
            if len(parts) < 4 or not parts[0].strip().isdigit():
                continue
            try:
                pid, r, g, b = (int(parts[0]), int(parts[1]),
                                int(parts[2]), int(parts[3]))
            except ValueError:
                continue
            couleurs[pid] = (r << 16) | (g << 8) | b
    return couleurs


def lire_default_map(mod):
    """default.map -> (toutes les provinces d'eau, les eaux interieures).

    Les eaux interieures (lacs et rivieres navigables) sont creusees dans la
    terre comme les mers, mais recoivent leur propre trace pour pouvoir etre
    peintes autrement que l'ocean.
    """
    eau, interieures = set(), set()
    with open(os.path.join(mod, "map_data", "default.map"),
              encoding="utf-8", errors="replace") as fh:
        for ligne in fh:
            m = re.match(r"\s*(\w+)\s*=\s*(RANGE|LIST)\s*\{([^}]*)\}", ligne)
            if not m:
                continue
            cle, mode, vals = m.group(1), m.group(2), m.group(3).split()
            if cle not in ("sea_zones", "lakes", "river_provinces"):
                continue
            if mode == "RANGE" and len(vals) == 2:
                ids = set(range(int(vals[0]), int(vals[1]) + 1))
            else:
                ids = {int(v) for v in vals}
            eau |= ids
            if cle in ("lakes", "river_provinces"):
                interieures |= ids
    return eau, interieures


def lire_titres(mod):
    """landed_titles -> {province: (empire, comte)} et {comte: [provinces]}.

    Parcours a pile : on empile le nom de chaque bloc ouvert, et tout
    `province = N` rencontre est attribue aux ancetres e_ et c_ courants.
    """
    prov_empire, prov_comte, comte_provinces = {}, {}, {}
    dossier = os.path.join(mod, "common", "landed_titles")
    re_bloc = re.compile(r"^\s*([a-zA-Z0-9_\-]+)\s*=\s*\{")
    re_prov = re.compile(r"^\s*province\s*=\s*(\d+)")
    for fichier in sorted(os.listdir(dossier)):
        if not fichier.endswith(".txt"):
            continue
        pile = []
        with open(os.path.join(dossier, fichier), encoding="utf-8-sig",
                  errors="replace") as fh:
            for ligne in fh:
                ligne = ligne.split("#", 1)[0]
                if not ligne.strip():
                    continue
                m = re_bloc.match(ligne)
                if m:
                    pile.append(m.group(1))
                    pile.extend([""] * (ligne.count("{") - 1))
                else:
                    mp = re_prov.match(ligne)
                    if mp:
                        pid = int(mp.group(1))
                        emp = next((n for n in pile if n.startswith("e_")), None)
                        cte = next((n for n in reversed(pile)
                                    if n.startswith("c_")), None)
                        if emp:
                            prov_empire[pid] = emp
                        if cte:
                            prov_comte[pid] = cte
                            comte_provinces.setdefault(cte, []).append(pid)
                    pile.extend([""] * ligne.count("{"))
                for _ in range(ligne.count("}")):
                    if pile:
                        pile.pop()
    return prov_empire, prov_comte, comte_provinces


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

    uniques, inverse = np.unique(packe, return_inverse=True)
    table = np.array([packe_id.get(int(u), 0) for u in uniques], dtype=np.uint8)
    grille = table[inverse].reshape(packe.shape)
    del inverse
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


# ------------------------------------------------------------------ sortie

def generer(hauteur, tolerance):
    try:
        import numpy as np
    except ImportError:
        sys.exit("numpy manquant : pip install numpy")
    try:
        import PIL  # noqa: F401
    except ImportError:
        sys.exit("Pillow manquant : pip install Pillow")

    t0 = time.time()
    mod = trouver_mod()
    print(f"mod AGOT : {mod}")

    couleurs = lire_definition(mod)
    eau, interieures = lire_default_map(mod)
    prov_empire, prov_comte, comte_provinces = lire_titres(mod)
    print(f"{len(couleurs)} provinces, {len(eau)} d'eau dont "
          f"{len(interieures)} interieures, {len(prov_empire)} rattachees "
          f"a un empire ({time.time()-t0:.1f}s)")

    grille, packe, idx, noms_ids = construire_grille(
        mod, np, couleurs, prov_empire, eau, interieures)
    print(f"grille {grille.shape[1]}x{grille.shape[0]} ({time.time()-t0:.1f}s)")

    ids_westeros = {idx[c] for c, _, _ in REGIONS}
    x0, x1, y0, y1 = cadrer(np, grille, ids_westeros)
    grille = grille[y0:y1, x0:x1]
    packe = packe[y0:y1, x0:x1]
    hg, lg = grille.shape
    print(f"cadre Westeros : {lg}x{hg} px de grille")

    # repere SVG : hauteur imposee, largeur deduite du ratio reel
    echelle = hauteur / hg
    largeur = round(lg * echelle, 1)

    def transformer(x, y):
        return (round(x * echelle, 1), round(y * echelle, 1))

    # une unite SVG = 1/echelle pixels de grille
    eps = tolerance
    aire_min = (1.2 / echelle) ** 2      # on jette les ilots < ~1.2 unite²

    geo = {
        "viewBox": f"0 0 {largeur} {hauteur}",
        "largeur": largeur,
        "hauteur": hauteur,
        "regions": [],
        "fonds": {},
        "lieux": {},
    }

    # --- terre : toutes les regions de Westeros d'un seul tenant
    terre = np.isin(grille, list(ids_westeros))
    geo["terre"] = chemin(contours(np, terre), transformer, eps, aire_min)
    print(f"terre : {len(geo['terre'])//1024} Ko ({time.time()-t0:.1f}s)")

    # --- une region par empire
    for cle, nom, court in REGIONS:
        masque = grille == idx[cle]
        if not masque.any():
            print(f"  (region vide : {cle})")
            continue
        d = chemin(contours(np, masque), transformer, eps, aire_min)
        p = point_interieur(np, masque, transformer)
        geo["regions"].append({"id": cle[2:], "nom": nom, "court": court,
                               "d": d, "etiquette": p})
        print(f"  {nom:28s} {len(d)//1024:3d} Ko")

    # --- lacs et rivieres navigables : deja creuses dans la terre, on leur
    # donne leur propre trace pour les peindre autrement que l'ocean
    douce = grille == EAU_DOUCE
    geo["eaux"] = chemin(contours(np, douce), transformer, eps * 0.7,
                         aire_min * 0.35) if douce.any() else ""
    print(f"  {'lacs et rivieres':28s} {len(geo['eaux'])//1024:3d} Ko")

    # --- fonds hors Westeros (au-dela du Mur, cote d'Essos)
    for nom in sorted(set(FONDS.values())):
        ids = [idx[e] for e, n in FONDS.items() if n == nom and e in idx]
        masque = np.isin(grille, ids)
        if masque.any():
            geo["fonds"][nom] = chemin(contours(np, masque), transformer,
                                       eps * 1.6, aire_min * 4)

    # --- lieux : centre de la province qui porte le chateau (chef-lieu du
    # comte, soit sa premiere baronnie)
    manquants = []
    for lieu_id, comte in sorted(LIEUX.items()):
        provs = comte_provinces.get(comte)
        if not provs:
            manquants.append(f"{lieu_id} ({comte})")
            continue
        coul = couleurs.get(provs[0])
        lig, col = np.nonzero(packe == coul)
        if not len(lig):
            manquants.append(f"{lieu_id} (hors cadre)")
            continue
        geo["lieux"][lieu_id] = transformer(float(col.mean()), float(lig.mean()))
    print(f"{len(geo['lieux'])}/{len(LIEUX)} lieux places "
          f"({time.time()-t0:.1f}s)")
    if manquants:
        print("  non places :", ", ".join(manquants))

    # --- les deux cadres : tout Westeros, et la baie de la Nera.
    # Le cadre du continent deborde a l'est : les places de la cote (Peyredragon,
    # l'Ile aux Griffes, Pointe-Massey) portent leur nom vers le large, et il
    # leur faut de la mer pour l'ecrire.
    geo["cadres"] = {
        "westeros": f"-8 0 {largeur + 48:.1f} {hauteur:.1f}",
    }
    pts = [geo["lieux"][i] for i in LIEUX_BAIE if i in geo["lieux"]]
    if pts:
        bx0 = min(p[0] for p in pts)
        bx1 = max(p[0] for p in pts)
        by0 = min(p[1] for p in pts)
        by1 = max(p[1] for p in pts)
        m = 0.30 * max(bx1 - bx0, by1 - by0)     # de l'air pour les noms
        bx0, bx1 = bx0 - m, bx1 + m
        by0, by1 = by0 - m, by1 + m
        geo["cadres"]["baie"] = (f"{bx0:.1f} {by0:.1f} "
                                 f"{bx1-bx0:.1f} {by1-by0:.1f}")
        print(f"cadre baie : {geo['cadres']['baie']}")

    ecrire(geo)
    total = os.path.getsize(SORTIE)
    print(f"OK -> {SORTIE} ({total//1024} Ko, {time.time()-t0:.1f}s)")


def ecrire(geo):
    entete = (
        "// geo.js — geometrie de Westeros, GENERE par scripts/carte_geo.py\n"
        "// Ne pas editer a la main : relancer le generateur.\n"
        "// Source : donnees de carte du mod AGOT (provinces, titres, mers).\n"
        '"use strict";\n'
        "window.Geo = "
    )
    corps = json.dumps(geo, ensure_ascii=False, separators=(",", ":"))
    with open(SORTIE, "w", encoding="utf-8") as fh:
        fh.write(entete + corps + ";\n")


def main():
    ap = argparse.ArgumentParser(
        description="Genere ecrans/modules/geo.js depuis le mod AGOT")
    ap.add_argument("--hauteur", type=float, default=620.0,
                    help="hauteur du viewBox en unites SVG (defaut 620)")
    ap.add_argument("--tolerance", type=float, default=0.45,
                    help="simplification Douglas-Peucker, en unites SVG")
    args = ap.parse_args()
    generer(args.hauteur, args.tolerance)


if __name__ == "__main__":
    main()
