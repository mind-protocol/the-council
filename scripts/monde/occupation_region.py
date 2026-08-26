# -*- coding: utf-8 -*-
"""Occupation rurale de la couronne de Port-Réal.

Le relief est une contrainte, pas un décor. Ce générateur place des parcelles,
des taillis, des fermes et leurs chemins de desserte à partir du raster
``portreal.region-terrain.json``. Les cinq grandes routes et les lieux nommés
restent écrits à la main dans ``port-real-region.json`` ; le semis secondaire
est déterministe et peut donc être recuit sans dérive.
"""
import heapq
import io
import json
import math
import os
import random

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
REGION_CHEM = os.path.join(RACINE, "scripts", "ville", "port-real-region.json")
TERRAIN_CHEM = os.path.join(RACINE, "monde", "portreal.region-terrain.json")
SORTIE = os.path.join(RACINE, "monde", "portreal.region-occupation.json")
MU = 12.0


def lire(p):
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def monde(p):
    return float(p[0]) * MU, (300.0 - float(p[1])) * MU


def distance_segment(p, a, b):
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    q = dx * dx + dy * dy
    t = 0.0 if q == 0 else max(0.0, min(1.0,
        ((px - ax) * dx + (py - ay) * dy) / q))
    x, y = ax + t * dx, ay + t * dy
    return math.hypot(px - x, py - y), (x, y), math.atan2(dy, dx)


def route_proche(p, routes):
    meilleur = (float("inf"), None, 0.0, None)
    for route in routes:
        pts = route["monde"]
        for a, b in zip(pts, pts[1:]):
            d, q, cap = distance_segment(p, a, b)
            if d < meilleur[0]:
                meilleur = (d, q, cap, route["id"])
    return meilleur


class Terrain:
    def __init__(self, paquet):
        self.x0 = float(paquet["x0_m"])
        self.y0 = float(paquet["y0_m"])
        self.res = float(paquet["res_m"])
        self.z = np.asarray(paquet["z"], dtype=np.float32)
        self.eau = np.asarray(paquet["eau"], dtype=np.uint8) > 0
        self.ny, self.nx = self.z.shape
        gy, gx = np.gradient(self.z, self.res, self.res)
        self.pente = np.hypot(gx, gy)

    def indice(self, x, y):
        i = int(round((x - self.x0) / self.res))
        j = int(round((y - self.y0) / self.res))
        return max(0, min(self.nx - 1, i)), max(0, min(self.ny - 1, j))

    def info(self, x, y):
        i, j = self.indice(x, y)
        return float(self.z[j, i]), float(self.pente[j, i]), bool(self.eau[j, i])

    def sec(self, points):
        return all(not self.info(x, y)[2] for x, y in points)


def distance_coeur(x, y):
    """Distance au rectangle du raster urbain 0..5280 × 0..3600 m."""
    dx = max(0.0, -x, x - 5280.0)
    dy = max(0.0, -y, y - 3600.0)
    return math.hypot(dx, dy)


def polygone_parcelle(cx, cy, cap, longueur, largeur, alea):
    ux, uy = math.cos(cap), math.sin(cap)
    vx, vy = -uy, ux
    # Six sommets légèrement gauchis : une lanière cadastrale, pas un rectangle
    # de lotissement moderne.
    l = longueur / 2.0
    w = largeur / 2.0
    gau = alea.uniform(-.11, .11) * largeur
    return [
        [cx - ux*l - vx*w, cy - uy*l - vy*w],
        [cx + vx*(-w + gau), cy + vy*(-w + gau)],
        [cx + ux*l - vx*w*.82, cy + uy*l - vy*w*.82],
        [cx + ux*l + vx*w, cy + uy*l + vy*w],
        [cx + vx*(w + gau), cy + vy*(w + gau)],
        [cx - ux*l + vx*w*.86, cy - uy*l + vy*w*.86],
    ]


def dans_disque(p, centres, marge=1.0):
    return any(math.hypot(p[0] - x, p[1] - y) < r * marge
               for x, y, r in centres)


def choisir_fermes(terrain, routes, alea, nombre_par_route=3):
    candidats = []
    x1 = terrain.x0 + (terrain.nx - 1) * terrain.res
    y1 = terrain.y0 + (terrain.ny - 1) * terrain.res
    for _ in range(14000):
        x, y = alea.uniform(terrain.x0 + 500, x1 - 500), \
               alea.uniform(terrain.y0 + 500, y1 - 500)
        z, pente, eau = terrain.info(x, y)
        droute, _, _, route_id = route_proche((x, y), routes)
        if eau or not (4.0 < z < 72.0) or pente > .052:
            continue
        if distance_coeur(x, y) < 900 or droute > 2300:
            continue
        score = droute / 2300 + pente * 8 + abs(z - 25) / 100
        score += alea.random() * .32
        candidats.append((score, x, y, route_id))
    candidats.sort()
    fermes = []
    # Chaque grande route nourrit sa propre campagne. Sans quota, la plaine
    # occidentale — la plus plate — gagnait toutes les fermes et le nord
    # redevenait un vide malgré un relief parfaitement valable.
    for route in routes:
        pris = 0
        for _, x, y, route_id in candidats:
            if route_id != route["id"]:
                continue
            if all(math.hypot(x - a, y - b) > 1200 for a, b in fermes):
                fermes.append((x, y))
                pris += 1
                if pris == nombre_par_route:
                    break
    return fermes


def choisir_bois(terrain, routes, fermes, alea, nombre=19):
    x1 = terrain.x0 + (terrain.nx - 1) * terrain.res
    y1 = terrain.y0 + (terrain.ny - 1) * terrain.res
    candidats = []
    for _ in range(12000):
        x, y = alea.uniform(terrain.x0 + 700, x1 - 700), \
               alea.uniform(terrain.y0 + 700, y1 - 700)
        z, pente, eau = terrain.info(x, y)
        droute, _, _, _ = route_proche((x, y), routes)
        if eau or distance_coeur(x, y) < 950 or droute < 280:
            continue
        if z < 35 or (pente < .018 and z < 58):
            continue
        if any(math.hypot(x-a, y-b) < 520 for a, b in fermes):
            continue
        candidats.append((-(z + pente * 420) + alea.random() * 18, x, y))
    candidats.sort()
    centres = []
    for _, x, y in candidats:
        if all(math.hypot(x-a, y-b) > 1050 for a, b, _ in centres):
            centres.append((x, y, alea.uniform(380, 760)))
            if len(centres) == nombre:
                break
    bois = []
    gardes = []
    for cx, cy, r in centres:
        pts = []
        n = alea.randint(11, 16)
        ellipt = alea.uniform(.58, .92)
        cap = alea.random() * math.tau
        for k in range(n):
            a = k * math.tau / n
            rr = r * alea.uniform(.72, 1.18)
            u, v = math.cos(a) * rr, math.sin(a) * rr * ellipt
            x = cx + u * math.cos(cap) - v * math.sin(cap)
            y = cy + u * math.sin(cap) + v * math.cos(cap)
            pts.append([x, y])
        if terrain.sec(pts + [[cx, cy]]):
            bois.append(pts)
            gardes.append((cx, cy, r))
    return bois, gardes


def choisir_parcelles(terrain, routes, fermes, bois_centres, alea):
    parcelles = {"cereale": [], "pature": [], "verger": []}
    blocs = []
    for nf, (fx, fy) in enumerate(fermes):
        faits = 0
        for _ in range(320):
            if faits >= 3:
                break
            a = alea.random() * math.tau
            d = alea.uniform(420, 1420)
            cx, cy = fx + math.cos(a) * d, fy + math.sin(a) * d
            z, pente, eau = terrain.info(cx, cy)
            droute, _, cap_route, _ = route_proche((cx, cy), routes)
            if eau or distance_coeur(cx, cy) < 620 or pente > .057 or z > 75:
                continue
            if droute > 2900 or dans_disque((cx, cy), bois_centres, .84):
                continue
            if any(math.hypot(cx-x, cy-y) < 650 for x, y in blocs):
                continue
            dzx = terrain.info(cx + 75, cy)[0] - terrain.info(cx - 75, cy)[0]
            dzy = terrain.info(cx, cy + 75)[0] - terrain.info(cx, cy - 75)[0]
            cap_contour = math.atan2(dzy, dzx) + math.pi / 2
            # Près d'une route, les limites lui répondent ; ailleurs elles
            # suivent surtout la courbe de niveau.
            poids_route = max(0.0, 1.0 - droute / 900.0) * .42
            cap = cap_contour * (1.0 - poids_route) + cap_route * poids_route
            genre = "pature" if z < 12 or pente > .038 else \
                    "verger" if (nf + faits) % 8 == 0 and z < 48 else "cereale"
            nombre = alea.randint(8, 14)
            larg = alea.uniform(42, 72)
            intervalle = larg + alea.uniform(8, 20)
            vx, vy = -math.sin(cap), math.cos(cap)
            ux, uy = math.cos(cap), math.sin(cap)
            lanières = []
            for k in range(nombre):
                # Une ou deux lanières manquent dans chaque sole : jachère,
                # pré enclavé ou limite de tenure. Le groupe reste lisible.
                if nombre > 9 and k not in (0, nombre-1) and alea.random() < .09:
                    continue
                travers = (k - (nombre-1)/2) * intervalle
                avance = alea.uniform(-55, 55)
                px = cx + vx*travers + ux*avance
                py = cy + vy*travers + uy*avance
                longueur = alea.uniform(390, 720)
                poly = polygone_parcelle(px, py, cap + alea.uniform(-.025, .025),
                                         longueur, larg, alea)
                if terrain.sec(poly + [[px, py]]) and \
                        not dans_disque((px, py), bois_centres, .78):
                    lanières.append(poly)
            if len(lanières) >= 5:
                parcelles[genre].extend(lanières)
                blocs.append((cx, cy))
                faits += 1
    return parcelles, len(blocs)


def simplifier(points):
    if len(points) < 3:
        return points
    out = [points[0]]
    for i in range(1, len(points) - 1):
        ax, ay = out[-1]
        bx, by = points[i]
        cx, cy = points[i + 1]
        croix = abs((bx-ax)*(cy-by) - (by-ay)*(cx-bx))
        if croix > 2400:
            out.append(points[i])
    out.append(points[-1])
    return out


def chemin_astar(terrain, depart, arrivee, graine):
    pas = 120.0
    nx = int((terrain.nx - 1) * terrain.res / pas) + 1
    ny = int((terrain.ny - 1) * terrain.res / pas) + 1

    def cellule(p):
        return (max(0, min(nx-1, int(round((p[0]-terrain.x0)/pas)))),
                max(0, min(ny-1, int(round((p[1]-terrain.y0)/pas)))))

    def point(c):
        return terrain.x0 + c[0]*pas, terrain.y0 + c[1]*pas

    s, but = cellule(depart), cellule(arrivee)
    ouverts = [(0.0, s)]
    cout = {s: 0.0}
    vient = {}
    rng = random.Random(graine)
    phase_x, phase_y = rng.random()*9, rng.random()*9
    voisins = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    while ouverts:
        _, c = heapq.heappop(ouverts)
        if c == but:
            break
        base = cout[c]
        x0, y0 = point(c)
        z0, _, _ = terrain.info(x0, y0)
        for di, dj in voisins:
            v = c[0]+di, c[1]+dj
            if not (0 <= v[0] < nx and 0 <= v[1] < ny):
                continue
            x, y = point(v)
            z, pente, eau = terrain.info(x, y)
            if eau or pente > .16:
                continue
            longueur = pas * (1.41421356 if di and dj else 1.0)
            ondulation = .07 * (1 + math.sin(v[0]*.63 + phase_x) *
                                      math.cos(v[1]*.57 + phase_y))
            nouveau = base + longueur * (1 + pente*22 + abs(z-z0)/pas*8 + ondulation)
            if nouveau < cout.get(v, float("inf")):
                cout[v] = nouveau
                vient[v] = c
                heur = math.hypot(v[0]-but[0], v[1]-but[1]) * pas
                heapq.heappush(ouverts, (nouveau + heur, v))
    if but not in vient and but != s:
        return [list(depart), list(arrivee)]
    chemin = [but]
    while chemin[-1] != s:
        chemin.append(vient[chemin[-1]])
    chemin.reverse()
    pts = [list(depart)] + [list(point(c)) for c in chemin[1:-1]] + [list(arrivee)]
    return simplifier(pts)


def batiments(centres, routes, alea, tailles):
    toits = []
    for (cx, cy), nombre, rayon in zip(centres, tailles[0], tailles[1]):
        _, _, cap_route, _ = route_proche((cx, cy), routes)
        for _ in range(nombre):
            a = alea.random() * math.tau
            d = (alea.random() ** .62) * rayon
            x, y = cx + math.cos(a)*d, cy + math.sin(a)*d*.62
            cap = cap_route + alea.uniform(-.22, .22)
            lo, la = alea.uniform(7, 16), alea.uniform(4.5, 9)
            ux, uy = math.cos(cap), math.sin(cap)
            vx, vy = -uy, ux
            toits.append([[x+ux*lo*s+vx*la*t, y+uy*lo*s+vy*la*t]
                          for s, t in ((-1,-1),(1,-1),(1,1),(-1,1))])
    return toits


def generer():
    src, brut = lire(REGION_CHEM), lire(TERRAIN_CHEM)
    terrain = Terrain(brut)
    graine = int((src.get("topographie") or {}).get("graine", 1290322)) + 7000
    alea = random.Random(graine)
    routes = [{"id": r["id"], "monde": [monde(p) for p in r["points"]]}
              for r in src.get("routes", [])]

    fermes = choisir_fermes(terrain, routes, alea)
    bois, bois_centres = choisir_bois(terrain, routes, fermes, alea)
    parcelles, nombre_blocs = choisir_parcelles(
        terrain, routes, fermes, bois_centres, alea)

    chemins = []
    pentes_chemins = []
    for i, ferme in enumerate(fermes):
        _, jonction, _, route_id = route_proche(ferme, routes)
        pts = chemin_astar(terrain, ferme, jonction, graine + i * 37)
        chemins.append({"id": "desserte-%02d" % (i+1), "route": route_id,
                         "points": pts})
        for a, b in zip(pts, pts[1:]):
            za = terrain.info(*a)[0]
            zb = terrain.info(*b)[0]
            d = math.hypot(b[0]-a[0], b[1]-a[1])
            if d:
                pentes_chemins.append(abs(zb-za)/d)

    lieux = [(monde(l["point"]), l.get("genre", "hameau"))
             for l in src.get("lieux", []) if l.get("genre") != "gue"]
    centres_bati = [p for p, _ in lieux] + list(fermes)
    nombres = [{"bourg":34, "hameau":13, "relais":8}.get(g, 9)
               for _, g in lieux] + [alea.randint(2, 4) for _ in fermes]
    rayons = [{"bourg":210, "hameau":105, "relais":75}.get(g, 90)
              for _, g in lieux] + [alea.uniform(38, 70) for _ in fermes]
    toits = batiments(centres_bati, routes, alea, (nombres, rayons))

    arbres = []
    for poly, (cx, cy, r) in zip(bois, bois_centres):
        for _ in range(max(8, int(r/42))):
            a = alea.random()*math.tau
            d = math.sqrt(alea.random())*r*.75
            x, y = cx+math.cos(a)*d, cy+math.sin(a)*d*.72
            rr = alea.uniform(7, 15)
            arbres.append([[x+math.cos(k*math.tau/7)*rr,
                             y+math.sin(k*math.tau/7)*rr] for k in range(7)])

    statistiques = {
        "fermes": len(fermes),
        "batiments_regionaux": len(toits),
        "parcelles": {k: len(v) for k, v in parcelles.items()},
        "blocs_parcellaires": nombre_blocs,
        "bois": len(bois),
        "arbres_symboliques": len(arbres),
        "chemins": len(chemins),
        "pente_chemins_max_pct": round(max(pentes_chemins, default=0)*100, 1),
        "pente_chemins_p95_pct": round(float(np.percentile(pentes_chemins, 95))*100, 1)
            if pentes_chemins else 0,
    }
    paquet = {
        "version": 1,
        "parcelles": parcelles,
        "bois": bois,
        "arbres": arbres,
        "fermes": [[x, y] for x, y in fermes],
        "batiments": toits,
        "chemins": chemins,
        "statistiques": statistiques,
        "_lisez_moi": "Occupation dérivée du relief régional. Les routes majeures et lieux "
                       "nommés restent manuels; champs, bois, fermes et dessertes sont recuits.",
    }
    tmp = SORTIE + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(paquet, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, SORTIE)
    print("monde/portreal.region-occupation.json écrit —", statistiques)
    return paquet


def assurer():
    sources = [__file__, REGION_CHEM, TERRAIN_CHEM]
    if os.path.exists(SORTIE) and os.path.getmtime(SORTIE) >= \
            max(os.path.getmtime(p) for p in sources):
        return lire(SORTIE)
    return generer()


if __name__ == "__main__":
    generer()
