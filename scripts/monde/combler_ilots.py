# -*- coding: utf-8 -*-
"""COMBLER LES ÎLOTS — ajouter du vrai tissu sans renuméroter la ville.

Le semis réglé borde les rues puis laisse des poches blanches au milieu des
blocs. Ce script travaille APRÈS la couture, les portes et le dégagement : il
cherche ces poches, protège les places et les monuments, y mène une venelle
depuis le réseau existant, puis bâtit des parcelles de part et d'autre.

Les bâtiments existants ne sont jamais déplacés. Les nouveaux sont ajoutés à
la fin de ``bati`` ; leurs portes, nœuds et arêtes sont ajoutés au graphe.

Essai sans écriture :
    python scripts/monde/combler_ilots.py --analyse

Candidate isolée :
    python scripts/monde/combler_ilots.py \
      --sortie-bati monde/portreal-candidat.bati.json \
      --sortie-graphe monde/portreal-candidat.graph.json
"""
import argparse
import heapq
import io
import json
import math
import os
import random
import sys
from collections import Counter, deque

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
MONDE = os.path.join(RACINE, "monde")
sys.path.insert(0, ICI)

from echelle import (ANNEAU, METRE_PAR_UNITE, gabarit, hors_anneau,
                     mx, my, ux, uy)
from pose import Occupation

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CEL = 3.0
PORTEE = 180                 # cases : 540 m au plus pour rejoindre le réseau
PROFOND = 6.0                # au-delà d'un premier rang commence le fond constructible
POCHE_MIN = 150.0            # on garde les micro-cours ; les cours communes plus vastes se bâtissent
MAX_POCHES = 2200
R = random.Random(0xC0A7)


def lire(p):
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def ecrire(p, v):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(v, f, ensure_ascii=False, separators=(",", ":"))


def dedans_poly(poly, x, y):
    oui = False
    j = len(poly) - 1
    for i in range(len(poly)):
        if ((poly[i][1] > y) != (poly[j][1] > y)
                and x < (poly[j][0] - poly[i][0]) * (y - poly[i][1])
                / (poly[j][1] - poly[i][1]) + poly[i][0]):
            oui = not oui
        j = i
    return oui


def ligne_cases(a, b):
    """Cases traversées par un segment, à un pas inférieur à la demi-maille."""
    d = math.dist(a, b)
    n = max(1, int(d / (CEL * .45)))
    for k in range(n + 1):
        t = k / n
        yield int((a[0] + (b[0] - a[0]) * t) / CEL), \
              int((a[1] + (b[1] - a[1]) * t) / CEL)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Combler les poches des îlots")
    ap.add_argument("--prefixe", default="portreal")
    ap.add_argument("--source-bati")
    ap.add_argument("--source-graphe")
    ap.add_argument("--analyse", action="store_true")
    ap.add_argument("--reprendre", action="store_true",
                    help="ajouter une passe à un graphe déjà comblé")
    ap.add_argument("--sortie-bati")
    ap.add_argument("--sortie-graphe")
    ap.add_argument("--poche-min", type=float, default=POCHE_MIN)
    ap.add_argument("--profondeur-min", type=float, default=PROFOND,
                    help="distance minimale à la voirie en mètres (défaut: %(default)s)")
    ap.add_argument("--max-poches", type=int, default=MAX_POCHES)
    ap.add_argument("--details", action="store_true",
                    help="afficher les centres des plus grandes poches")
    a = ap.parse_args(argv)

    pb = (os.path.abspath(a.source_bati) if a.source_bati
          else os.path.join(MONDE, a.prefixe + ".bati.json"))
    pg = (os.path.abspath(a.source_graphe) if a.source_graphe
          else os.path.join(MONDE, a.prefixe + ".graph.json"))
    pt = os.path.join(MONDE, a.prefixe + ".terrain.json")
    B, G, T = lire(pb), lire(pg), lire(pt)
    precedent = G.get("_infill") or {}
    if precedent and not a.analyse and not a.reprendre:
        sys.exit("Ce graphe porte déjà son comblement d'îlots.")
    C = {n: i for i, n in enumerate(B["_colonnes"])}
    requis = ("x", "y", "z", "cap", "facade_m", "profondeur_m",
              "etages", "hauteur_m", "quartier", "usage", "cave", "cat",
              "toit", "porte_x", "porte_y", "voie")
    manque = [n for n in requis if n not in C]
    if manque:
        sys.exit("Colonnes manquantes : " + ", ".join(manque))

    larg = 5280.0
    haut = 3600.0
    nx, ny = int(larg / CEL), int(haut / CEL)
    ncase = nx * ny
    def idx(i, j): return j * nx + i
    def monde(i, j): return (i + .5) * CEL, (j + .5) * CEL
    def valide(i, j): return 0 <= i < nx and 0 <= j < ny

    # Relief : même interpolation que les autres générateurs.
    res, zt, ntx, nty = T["res_m"], T["z"], T["nx"], T["ny"]
    def zsol(x, y):
        i = min(ntx - 2, max(0, int(x / res)))
        j = min(nty - 2, max(0, int(y / res)))
        tx, ty = (x - i * res) / res, (y - j * res) / res
        za = zt[j][i] * (1 - tx) + zt[j][i + 1] * tx
        zb = zt[j + 1][i] * (1 - tx) + zt[j + 1][i + 1] * tx
        return za * (1 - ty) + zb * ty

    print("… le domaine et les protections")
    DANS = bytearray(ncase)
    for j in range(ny):
        wy = (j + .5) * CEL
        for i in range(nx):
            wx = (i + .5) * CEL
            if not hors_anneau(ux(wx), uy(wy)) and zsol(wx, wy) > -0.5:
                DANS[idx(i, j)] = 1

    BAT = bytearray(ncase)
    RUE = bytearray(ncase)
    PROTEGE = bytearray(ncase)

    def disque(buf, x, y, r):
        ci, cj, rr = int(x / CEL), int(y / CEL), int(math.ceil(r / CEL))
        for dj in range(-rr, rr + 1):
            for di in range(-rr, rr + 1):
                ii, jj = ci + di, cj + dj
                if valide(ii, jj):
                    wx, wy = monde(ii, jj)
                    if math.hypot(wx - x, wy - y) <= r:
                        buf[idx(ii, jj)] = 1

    def rectangle(buf, x, y, f, p, cap):
        ang = math.radians(cap or 0.)
        ca, sa = math.cos(ang), math.sin(ang)
        hf, hp = f / 2., p / 2.
        rayon = math.hypot(hf, hp) + CEL
        i0, i1 = max(0, int((x - rayon) / CEL)), min(nx - 1, int((x + rayon) / CEL))
        j0, j1 = max(0, int((y - rayon) / CEL)), min(ny - 1, int((y + rayon) / CEL))
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                wx, wy = monde(i, j)
                dx, dy = wx - x, wy - y
                u, v = dx * ca + dy * sa, -dx * sa + dy * ca
                if abs(u) <= hf + .35 and abs(v) <= hp + .35:
                    buf[idx(i, j)] = 1

    # Les rectangles de base, plus les prises de fond et de flanc déjà cuites.
    iaf = C.get("ann_f"); iag = C.get("ann_g"); iad = C.get("ann_d")
    for r in B["bati"]:
        x, y, cap = r[C["x"]], r[C["y"]], r[C["cap"]] or 0.
        f, p = r[C["facade_m"]], r[C["profondeur_m"]]
        rectangle(BAT, x, y, f, p, cap)
        ang = math.radians(cap); ca, sa = math.cos(ang), math.sin(ang)
        fo = (r[iaf] or 0.) if iaf is not None else 0.
        ga = (r[iag] or 0.) if iag is not None else 0.
        da = (r[iad] or 0.) if iad is not None else 0.
        if fo:
            rectangle(BAT, x - sa * (p / 2 + fo / 2),
                      y + ca * (p / 2 + fo / 2), f * .8, fo, cap)
        if ga:
            rectangle(BAT, x - ca * (f / 2 + ga / 2),
                      y - sa * (f / 2 + ga / 2), ga, p * .6, cap)
        if da:
            rectangle(BAT, x + ca * (f / 2 + da / 2),
                      y + sa * (f / 2 + da / 2), da, p * .6, cap)

    # La chaussée existante.
    surface = [e for e in G["aretes"] if e.get("couche") == "L1-surface"
               and len(e.get("trace") or ()) >= 2]
    for e in surface:
        w = (e.get("largeur_m") or 2.) / 2. + .7
        tr = e["trace"]
        for u, v in zip(tr, tr[1:]):
            d = math.dist(u[:2], v[:2]); pas = max(1, int(d / (CEL * .5)))
            for k in range(pas + 1):
                t = k / pas
                disque(RUE, u[0] + (v[0] - u[0]) * t,
                       u[1] + (v[1] - u[1]) * t, w)

    # Places nommées : un vide nommé est une place, pas une erreur de semis.
    topo_path = os.path.join(RACINE, "scripts", "ville", "port-real-toponymie.json")
    topo = lire(topo_path) if os.path.exists(topo_path) else {"reperes": []}
    noeuds = {n.get("id"): n for n in G["noeuds"] if n.get("id")}
    proteges = 0
    for p in topo.get("reperes", []):
        if p.get("genre") not in ("place", "marche", "parvis"):
            continue
        n = noeuds.get(p.get("ancre_noeud"))
        if not n or not n.get("xyz"):
            continue
        rayon = 72. if p.get("importance", 1) >= 2 else 45.
        disque(PROTEGE, n["xyz"][0], n["xyz"][1], rayon); proteges += 1
    for n in G["noeuds"]:
        if n.get("genre") in ("marche", "monument", "forteresse", "septuaire", "guilde"):
            if n.get("xyz"):
                disque(PROTEGE, n["xyz"][0], n["xyz"][1], 48.); proteges += 1
    print("   %d bâtiments existants, %d espaces publics protégés" %
          (len(B["bati"]), proteges))

    # Distance à la voirie. Une poche n'est pas tout ce qui est blanc : c'est
    # le blanc que n'atteint plus aucune façade depuis une voie.
    print("… la profondeur des vides")
    INF = 65535
    DIST = [INF] * ncase
    q = deque()
    for k, v in enumerate(RUE):
        if v and DANS[k]:
            DIST[k] = 0; q.append(k)
    while q:
        k = q.popleft(); i, j = k % nx, k // nx
        nd = DIST[k] + 1
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ii, jj = i + di, j + dj
            if valide(ii, jj):
                z = idx(ii, jj)
                if DANS[z] and nd < DIST[z]:
                    DIST[z] = nd; q.append(z)

    profond_cases = int(math.ceil(a.profondeur_min / CEL))
    VU = bytearray(ncase)
    poches = []
    for k0 in range(ncase):
        if (VU[k0] or not DANS[k0] or BAT[k0] or RUE[k0] or PROTEGE[k0]
                or DIST[k0] < profond_cases):
            continue
        cells = []; qq = deque([k0]); VU[k0] = 1
        while qq:
            k = qq.popleft(); cells.append(k)
            i, j = k % nx, k // nx
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ii, jj = i + di, j + dj
                if not valide(ii, jj): continue
                z = idx(ii, jj)
                if (not VU[z] and DANS[z] and not BAT[z] and not RUE[z]
                        and not PROTEGE[z] and DIST[z] >= profond_cases):
                    VU[z] = 1; qq.append(z)
        aire = len(cells) * CEL * CEL
        if aire >= a.poche_min:
            poches.append((aire, cells))
    poches.sort(reverse=True, key=lambda x: x[0])
    hist = Counter(min(5000, int(aire // 500) * 500) for aire, _ in poches)
    print("   %d poches de plus de %.0f m² à au moins %.0f m des voies, %.1f ha" %
          (len(poches), a.poche_min, profond_cases * CEL,
           sum(x[0] for x in poches) / 10000.))
    for s in sorted(hist)[:12]:
        print("      %4d–%4d m² : %4d" % (s, s + 499, hist[s]))
    if a.details:
        print("   plus grandes poches (x, y, aire, profondeur) :")
        for aire, cells in poches[:20]:
            ci = sum(k % nx for k in cells) / len(cells)
            cj = sum(k // nx for k in cells) / len(cells)
            prof = max(DIST[k] for k in cells) * CEL
            print("      %7.1f %7.1f  %6.0f m²  fond %4.0f m" %
                  ((ci+.5)*CEL, (cj+.5)*CEL, aire, prof))
    if a.analyse:
        return 0

    # Le quartier d'un point, depuis les polygones de village de la carte.
    carte = lire(os.path.join(RACINE, "etat", "villes", "port-real.json"))
    villages = []
    for s in carte.get("sol", []):
        if s.get("genre") == "village" and len(s.get("points") or ()) >= 3:
            villages.append(([(mx(p[0]), my(p[1])) for p in s["points"]], s["nom"]))
    def quartier(x, y):
        for poly, nom in villages:
            if dedans_poly(poly, x, y): return nom
        return "La ville"

    # Occupation géométrique exacte pour la pose, initialisée avec l'existant.
    def case_libre(x, y):
        i, j = int(x / CEL), int(y / CEL)
        return valide(i, j) and bool(DANS[idx(i, j)]) \
            and not RUE[idx(i, j)] and not PROTEGE[idx(i, j)]
    OCC = Occupation(case_libre)
    for r in B["bati"]:
        x, y = r[C["x"]], r[C["y"]]
        f, p, cap = r[C["facade_m"]], r[C["profondeur_m"]], r[C["cap"]] or 0.
        OCC.occuper(x, y, f, p, cap)
        ang = math.radians(cap); ca, sa = math.cos(ang), math.sin(ang)
        fo = (r[iaf] or 0.) if iaf is not None else 0.
        ga = (r[iag] or 0.) if iag is not None else 0.
        da = (r[iad] or 0.) if iad is not None else 0.
        if fo:
            OCC.occuper(x - sa*(p/2+fo/2), y + ca*(p/2+fo/2), f*.8, fo, cap)
        if ga:
            OCC.occuper(x - ca*(f/2+ga/2), y - sa*(f/2+ga/2), ga, p*.6, cap)
        if da:
            OCC.occuper(x + ca*(f/2+da/2), y + sa*(f/2+da/2), da, p*.6, cap)

    # Nœuds de surface réellement connectés, indexés sur la grille.
    ids_surface = set()
    for e in surface:
        ids_surface.add(e.get("de")); ids_surface.add(e.get("vers"))
    cibles = {}
    for n in G["noeuds"]:
        if n.get("id") in ids_surface and n.get("xyz"):
            i, j = int(n["xyz"][0] / CEL), int(n["xyz"][1] / CEL)
            if valide(i, j): cibles.setdefault(idx(i, j), n["id"])

    def chemin_vers_reseau(depart):
        """BFS dans le sol libre : retourne le réseau → fond de l'îlot."""
        qq = deque([depart]); prec = {depart: None}; trouve = None
        while qq:
            k = qq.popleft()
            if k in cibles:
                trouve = k; break
            i, j = k % nx, k // nx
            di0, dj0 = depart % nx, depart // nx
            if abs(i - di0) + abs(j - dj0) > PORTEE:
                continue
            for di, dj in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)):
                ii, jj = i + di, j + dj
                if not valide(ii, jj): continue
                z = idx(ii, jj)
                if z in prec or not DANS[z] or BAT[z] or PROTEGE[z]: continue
                prec[z] = k; qq.append(z)
        if trouve is None: return None, None
        cells = []
        k = trouve
        while k is not None:
            cells.append(k); k = prec[k]
        # `cells` va déjà du réseau vers le fond.
        return cibles[trouve], cells

    def simplifier(points):
        if len(points) <= 2: return points
        garde = [points[0]]
        for p in points[1:-1]:
            if math.dist(p, garde[-1]) >= 7.5: garde.append(p)
        garde.append(points[-1])
        # Deux passages de moyenne cassent l'escalier de la grille.
        for _ in range(2):
            if len(garde) < 3: break
            garde = [garde[0]] + [((a[0] + 2*b[0] + c[0]) / 4,
                                    (a[1] + 2*b[1] + c[1]) / 4)
                                   for a, b, c in zip(garde, garde[1:], garde[2:])] + [garde[-1]]
        return garde

    def usage_de(q, tirage):
        if q == "Le Culpucier": return ("taudis", "habitat", "pignon")
        if q == "La ville haute":
            return ("manse", "habitat", "long") if tirage < .22 else ("maison", "habitat", "pignon")
        if q == "Le Crochet":
            return ("maison-officier", "habitat", "pignon") if tirage < .28 else ("maison", "habitat", "pignon")
        if q == "Le port et ses hangars": return ("entrepot", "commerce", "long")
        if q == "Les tanneries":
            return ("tannerie", "nuisance", "long") if tirage < .30 else ("maison", "habitat", "pignon")
        if q == "La rue d'Acier":
            return ("forge", "artisanat", "plat") if tirage < .25 else ("maison", "habitat", "pignon")
        return ("echoppe", "commerce", "pignon") if tirage < .10 else ("maison", "habitat", "pignon")

    def ligne_longueur(tr):
        return sum(math.dist(p, q) for p, q in zip(tr, tr[1:]))

    def point_a(tr, s):
        reste = s
        for u, v in zip(tr, tr[1:]):
            d = math.dist(u, v)
            if reste <= d:
                t = reste / d if d else 0.
                return (u[0] + (v[0]-u[0])*t, u[1] + (v[1]-u[1])*t), \
                       math.degrees(math.atan2(v[1]-u[1], v[0]-u[0]))
            reste -= d
        u, v = tr[-2], tr[-1]
        return tr[-1], math.degrees(math.atan2(v[1]-u[1], v[0]-u[0]))

    def row(valeurs):
        return [valeurs.get(n, 0) for n in B["_colonnes"]]

    print("… les venelles et les nouvelles parcelles")
    branches = []
    nouveaux = 0
    aire_prise = 0.0
    vus_fonds = set()
    branche_no = int(precedent.get("venelles", 0))
    for no, (aire, cells) in enumerate(poches[:a.max_poches]):
        # Un hectare de cœur ne se dessert pas par la même impasse qu'une cour
        # de cinq cents mètres. On prend plusieurs fonds, espacés d'au moins
        # trente mètres, et chacun doit retrouver le réseau sans traverser ce
        # que les branches précédentes viennent de bâtir.
        nb_voulu = min(5, 1 + int(aire // 1200.))
        candidats = sorted(cells, key=lambda k: DIST[k], reverse=True)
        fonds = []
        for fond in candidats:
            fi, fj = fond % nx, fond // nx
            if any((fi-x)**2 + (fj-y)**2 < 100 for x, y in fonds): continue
            if any(abs(fi-x) + abs(fj-y) < 7 for x, y in vus_fonds): continue
            fonds.append((fi,fj))
            if len(fonds) >= nb_voulu: break

        for fno, (fi, fj) in enumerate(fonds):
            fond = idx(fi, fj)
            nid0, chemin = chemin_vers_reseau(fond)
            if not chemin or len(chemin) < 5: continue
            vus_fonds.add((fi, fj))
            n0 = noeuds.get(nid0)
            if not n0 or not n0.get("xyz"): continue
            pts = [(n0["xyz"][0], n0["xyz"][1])]
            pts += [monde(k % nx, k // nx) for k in chemin[1:]]
            pts = simplifier(pts)
            longueur = ligne_longueur(pts)
            if longueur < 12.: continue
            genre = "rue" if aire >= 3000. and fno == 0 else "ruelle"
            largeur = 4.2 if genre == "rue" else (2.6 if aire >= 1000. else 2.0)

            # La branche devient immédiatement du sol interdit à la pose.
            for u, v in zip(pts, pts[1:]):
                d = math.dist(u, v); pas = max(1, int(d / (CEL * .5)))
                for k in range(pas + 1):
                    t = k / pas
                    disque(RUE, u[0] + (v[0]-u[0])*t,
                           u[1] + (v[1]-u[1])*t, largeur/2 + .55)

            maisons = []
            s = 4.0 + R.random() * 2.0
            while s < longueur - 3.0:
                (px, py), cap = point_a(pts, s)
                qn = quartier(px, py)
                fmin, fmax, prof, etages, he = gabarit(qn)
                facade = fmin + (fmax-fmin) * R.random()
                profondeur = prof * (.82 + .32 * R.random())
                for cote in (1, -1):
                    ccap = cap if cote > 0 else cap + 180.
                    ang = math.radians(ccap); nxp, nyp = -math.sin(ang), math.cos(ang)
                    # La maille de chaussée fait trois mètres : un recul d'un
                    # mètre tombait encore dans sa case et refusait la façade.
                    xf = px + nxp * (largeur/2 + 2.15)
                    yf = py + nyp * (largeur/2 + 2.15)
                    joint = 0.0 if qn == "Le Culpucier" else .18
                    t = OCC.tailler(xf, yf, facade, profondeur, ccap, joint)
                    if not t: continue
                    x, y, f2, p2 = t
                    OCC.occuper(x, y, f2, p2, ccap)
                    rectangle(BAT, x, y, f2, p2, ccap)
                    usage, cat, toit = usage_de(qn, R.random())
                    et = R.randint(etages[0], etages[1])
                    kbat = len(B["bati"])
                    valeurs = {
                        "x":round(x,1), "y":round(y,1), "z":round(zsol(x,y),1),
                        "cap":round(ccap % 360,1), "facade_m":round(f2,1),
                        "profondeur_m":round(p2,1), "etages":et,
                        "hauteur_m":round(et*he+1.2,1), "quartier":qn,
                        "usage":usage, "cave":1 if R.random() < .22 else 0,
                        "cat":cat, "toit":toit, "porte_x":round(px,1),
                        "porte_y":round(py,1), "voie":"",
                        "ann_f":0., "ann_g":0., "ann_d":0., "mur_d":0.,
                    }
                    B["bati"].append(row(valeurs))
                    maisons.append((s, kbat))
                    nouveaux += 1; aire_prise += f2*p2
                s += max(3.0, facade * (.76 + .16 * R.random()))
            if maisons:
                branches.append({"no":branche_no, "de":nid0, "trace":pts,
                                 "genre":genre, "largeur":largeur,
                                 "maisons":maisons, "aire":aire})
                # Le fond atteint devient le départ possible de la prochaine
                # branche. Sans cela, chaque rameau tentait de retraverser le
                # premier rang de maisons pour revenir jusqu'à l'ancienne rue.
                # Le nœud sera réellement écrit lors de la segmentation, plus
                # bas ; ici on le rend seulement visible au chercheur de route.
                fin_id = "infill:%03d:fond" % branche_no
                ex, ey = pts[-1]
                noeuds[fin_id] = {"id":fin_id, "xyz":[ex,ey,zsol(ex,ey)]}
                ei, ej = int(ex/CEL), int(ey/CEL)
                if valide(ei, ej): cibles[idx(ei,ej)] = fin_id
                branche_no += 1

    # Les branches sont segmentées aux portes : chaque nouvelle maison devient
    # une vraie destination du graphe, comme celles créées par portes.py.
    def coupe(tr, s0, s1):
        out = []; s = 0.
        for u, v in zip(tr, tr[1:]):
            d = math.dist(u, v); a0, a1 = s, s+d
            if a1 >= s0 and a0 <= s1 and d:
                for cible in (max(a0,s0), min(a1,s1)):
                    t = (cible-a0)/d
                    p = [round(u[0]+(v[0]-u[0])*t,2),
                         round(u[1]+(v[1]-u[1])*t,2)]
                    if not out or math.dist(p,out[-1]) > 1e-6: out.append(p)
            s = a1
        return out

    portes = G.setdefault("portes_bat", {})
    for br in branches:
        base = "infill:%03d" % br["no"]
        tr = br["trace"]; total = ligne_longueur(tr)
        fin = base + ":fond"
        fx, fy = tr[-1]
        G["noeuds"].append({"id":fin, "genre":"cour", "niveau":0,
                            "xyz":[round(fx,1),round(fy,1),round(zsol(fx,fy),1)],
                            "raison":"Le fond de la venelle : ici commence la cour commune."})
        groupes = []
        for s, kbat in sorted(br["maisons"]):
            s = min(total-.25,max(.25,s))
            if groupes and s-groupes[-1][0] < .5:
                groupes[-1][1].append(kbat)
            else:
                groupes.append([s,[kbat]])
        bornes = [(0.,br["de"])]
        for gi,(s,ks) in enumerate(groupes):
            nid = base + ":porte:%03d" % gi
            (px,py),_ = point_a(tr,s)
            G["noeuds"].append({"id":nid,"genre":"porte-maison","niveau":0,
                                "xyz":[round(px,1),round(py,1),round(zsol(px,py),1)],
                                "bat":ks,"raison":"La porte des maisons nouvelles donne sur la venelle."})
            for kbat in ks: portes[str(kbat)] = nid
            bornes.append((s,nid))
        bornes.append((total,fin))
        ids_segments = []
        for si,((s0,n0),(s1,n1)) in enumerate(zip(bornes,bornes[1:])):
            seg2 = coupe(tr,s0,s1)
            if len(seg2) < 2: continue
            seg = [[x,y,round(zsol(x,y),1)] for x,y in seg2]
            eid = base + ":s%03d" % si; ids_segments.append((s0,s1,eid,n0,n1))
            lg = sum(math.dist(x[:2],y[:2]) for x,y in zip(seg,seg[1:]))
            G["aretes"].append({"id":eid,"de":n0,"vers":n1,
                                "genre":br["genre"],"couche":"L1-surface",
                                "largeur_m":br["largeur"],"longueur_m":round(lg,2),
                                "pente":round(abs(seg[-1][2]-seg[0][2])/max(1,lg),3),
                                "raison":"Le cœur de l'îlot était hors d'atteinte ; la venelle l'a rendu habitable.",
                                "trace":seg,"visibilite":"publique","acces":"public","etat":"ouvert"})
        for s,kbat in br["maisons"]:
            voisin = next((x for x in ids_segments if x[0]-1e-6 <= s <= x[1]+1e-6),None)
            if voisin: B["bati"][kbat][C["voie"]] = voisin[2]

    G["_infill"] = {
        "version":int(precedent.get("version", 0)) + 1,
        "anciens":int(precedent.get("anciens", len(B["bati"])-nouveaux)),
        "nouveaux":int(precedent.get("nouveaux", 0)) + nouveaux,
        "venelles":int(precedent.get("venelles", 0)) + len(branches),
        "emprise_m2":round(float(precedent.get("emprise_m2", 0)) + aire_prise),
        "regle":"append-only ; places nommées protégées ; aucune maison sans porte",
    }
    # Contrat avant écriture : pas de destination fantôme, pas d'identifiant
    # dupliqué, et chaque maison ajoutée possède à la fois une voie et un nœud
    # de porte. C'est ce qui sépare un comblement urbain d'un décor peint.
    ids_n = [n.get("id") for n in G["noeuds"] if n.get("id")]
    ids_e = [e.get("id") for e in G["aretes"] if e.get("id")]
    if len(ids_n) != len(set(ids_n)):
        raise RuntimeError("identifiant de nœud dupliqué après comblement")
    if len(ids_e) != len(set(ids_e)):
        raise RuntimeError("identifiant d'arête dupliqué après comblement")
    ens_n, ens_e = set(ids_n), set(ids_e)
    for e in G["aretes"]:
        if e.get("id") and (e.get("de") not in ens_n or e.get("vers") not in ens_n):
            raise RuntimeError("arête sans nœud : " + e["id"])
    ancien_n = len(B["bati"]) - nouveaux
    for kbat in range(ancien_n, len(B["bati"])):
        voie = B["bati"][kbat][C["voie"]]
        if voie not in ens_e or str(kbat) not in portes:
            raise RuntimeError("maison nouvelle sans adresse : %d" % kbat)
    print("   contrat graphe : %d/%d nouvelles adresses reliées" %
          (nouveaux, nouveaux))
    sb = os.path.join(RACINE, a.sortie_bati) if a.sortie_bati else pb
    sg = os.path.join(RACINE, a.sortie_graphe) if a.sortie_graphe else pg
    ecrire(sb,B); ecrire(sg,G)
    print()
    print("   %d venelles, %d bâtiments nouveaux, %.2f ha d'emprise" %
          (len(branches), nouveaux, aire_prise/10000.))
    print("   rangs existants conservés : 0–%d ; nouveaux : %d–%d" %
          (len(B["bati"])-nouveaux-1, len(B["bati"])-nouveaux, len(B["bati"])-1))
    print("   écrit — %s" % os.path.relpath(sb,RACINE))
    print("   écrit — %s" % os.path.relpath(sg,RACINE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
