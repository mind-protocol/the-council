# -*- coding: utf-8 -*-
"""Relief physique de la couronne de Port-Réal.

Produit ``monde/portreal.region-terrain.json`` sur l'emprise définie dans
``scripts/ville/port-real-region.json``. Le cœur urbain conserve son raster de
10 m : la grille régionale de 30 m le recopie exactement, puis s'y raccorde sur
900 m. On obtient ainsi un terrain jouable au recul sans déplacer une maison,
une rue ni une altitude canonique des trois collines.
"""
import io
import json
import math
import os

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
REGION_CHEM = os.path.join(RACINE, "scripts", "ville", "port-real-region.json")
COEUR_CHEM = os.path.join(RACINE, "monde", "portreal.terrain.json")
SORTIE = os.path.join(RACINE, "monde", "portreal.region-terrain.json")
MU = 12.0


def lire(p):
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def monde(p):
    return p[0] * MU, (300.0 - p[1]) * MU


def masque_polygone(X, Y, points):
    poly = [monde(p) for p in points]
    dedans = np.zeros(X.shape, dtype=bool)
    j = len(poly) - 1
    for i, (ax, ay) in enumerate(poly):
        bx, by = poly[j]
        coupe = (ay > Y) != (by > Y)
        if by != ay:
            abscisse = (bx - ax) * (Y - ay) / (by - ay) + ax
            dedans ^= coupe & (X < abscisse)
        j = i
    return dedans


def distance_segments(X, Y, suites):
    """Distance euclidienne aux polylignes, en mètres."""
    dmin = np.full(X.shape, np.inf, dtype=np.float32)
    for points in suites:
        pts = [monde(p) for p in points]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            dx, dy = bx - ax, by - ay
            q = dx * dx + dy * dy
            if q == 0:
                d = np.hypot(X - ax, Y - ay)
            else:
                t = np.clip(((X - ax) * dx + (Y - ay) * dy) / q, 0.0, 1.0)
                d = np.hypot(X - ax - t * dx, Y - ay - t * dy)
            np.minimum(dmin, d, out=dmin)
    return dmin


def bruit_valeur(nx, ny, res, pas_m, graine):
    """Bruit de valeur bilinéaire, déterministe et sans dépendance SciPy."""
    gx = int(math.ceil((nx - 1) * res / pas_m)) + 3
    gy = int(math.ceil((ny - 1) * res / pas_m)) + 3
    g = np.random.default_rng(graine).random((gy, gx), dtype=np.float32)
    fx = np.arange(nx, dtype=np.float32) * res / pas_m
    fy = np.arange(ny, dtype=np.float32) * res / pas_m
    ix, iy = fx.astype(np.int32), fy.astype(np.int32)
    tx, ty = fx - ix, fy - iy
    tx = tx * tx * (3.0 - 2.0 * tx)
    ty = ty * ty * (3.0 - 2.0 * ty)
    a = g[iy[:, None], ix[None, :]]
    b = g[iy[:, None], ix[None, :] + 1]
    c = g[iy[:, None] + 1, ix[None, :] + 1]
    d = g[iy[:, None] + 1, ix[None, :]]
    haut = a * (1.0 - tx[None, :]) + b * tx[None, :]
    bas = d * (1.0 - tx[None, :]) + c * tx[None, :]
    return haut * (1.0 - ty[:, None]) + bas * ty[:, None]


def echantillon(grille, res, X, Y):
    """Interpolation bilinéaire d'une grille dont l'origine est (0, 0)."""
    ny, nx = grille.shape
    fx = np.clip(X / res, 0.0, nx - 1.000001)
    fy = np.clip(Y / res, 0.0, ny - 1.000001)
    i, j = fx.astype(np.int32), fy.astype(np.int32)
    i = np.minimum(i, nx - 2)
    j = np.minimum(j, ny - 2)
    tx, ty = fx - i, fy - j
    a, b = grille[j, i], grille[j, i + 1]
    d, c = grille[j + 1, i], grille[j + 1, i + 1]
    return (a * (1.0 - tx) + b * tx) * (1.0 - ty) + \
           (d * (1.0 - tx) + c * tx) * ty


def generer():
    src, coeur = lire(REGION_CHEM), lire(COEUR_CHEM)
    cfg = src["topographie"]
    res = float(cfg.get("resolution_m", 30))
    (x0, y1), (x1, y0) = monde(src["repere"][:2]), monde(src["repere"][2:])
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    nx = int(round((x1 - x0) / res)) + 1
    ny = int(round((y1 - y0) / res)) + 1
    xs = x0 + np.arange(nx, dtype=np.float32) * res
    ys = y0 + np.arange(ny, dtype=np.float32) * res
    X, Y = np.meshgrid(xs, ys)
    print("relief régional : %d × %d à %.0f m (%.1f × %.1f km)" %
          (nx, ny, res, (x1 - x0) / 1000, (y1 - y0) / 1000))

    eaux = [masque_polygone(X, Y, e["points"]) for e in src.get("eau", [])]
    eau = np.logical_or.reduce(eaux) if eaux else np.zeros(X.shape, dtype=bool)
    contours_eau = [e["points"] + [e["points"][0]] for e in src.get("eau", [])]
    dist_rive = distance_segments(X, Y, contours_eau)
    dist_nera = distance_segments(X, Y, [contours_eau[0]]) if contours_eau \
        else dist_rive

    graine = int(cfg.get("graine", 1290322))
    n_grand = bruit_valeur(nx, ny, res, 2400, graine + 11)
    n_moyen = bruit_valeur(nx, ny, res, 900, graine + 22)
    n_fin = bruit_valeur(nx, ny, res, 360, graine + 33)
    gauchi_x = bruit_valeur(nx, ny, res, 3100, graine + 101)
    gauchi_y = bruit_valeur(nx, ny, res, 2700, graine + 202)
    bruit = ((n_grand - .5) * 14.0 + (n_moyen - .5) * 6.0 +
             (n_fin - .5) * 2.4)
    # Le socle monte lentement loin de l'eau ; le bruit ne commande jamais la
    # géographie, il casse seulement les surfaces trop parfaites.
    H = 3.0 + 17.0 * (1.0 - np.exp(-dist_rive / 1700.0)) + bruit

    for m in cfg.get("massifs", []):
        cx, cy = monde(m["centre"])
        rx, ry = m["rayons"][0] * MU, m["rayons"][1] * MU
        a = math.radians(-float(m.get("cap_deg", 0)))
        ca, sa = math.cos(a), math.sin(a)
        dx, dy = X - cx, Y - cy
        u0 = (dx * ca + dy * sa) / rx
        v0 = (-dx * sa + dy * ca) / ry
        # Les rayons donnent l'échelle du massif, pas un compas. Deux champs
        # lents gauchissent chaque versant et décentrent les épaules : les
        # isolignes gardent une structure lisible sans former des ovales
        # concentriques de maquette.
        u = u0 + (gauchi_x - .5) * .26 + v0 * .055
        v = v0 + (gauchi_y - .5) * .22 - u0 * .035
        q2 = u * u + v * v
        profil = np.where(q2 < 1.0, np.maximum(0.0, 1.0 - q2) ** 1.75, 0.0)
        sommet = float(m["sommet_m"])
        forme = 8.0 + (sommet - 8.0) * profil + bruit * .22
        H = np.maximum(H, forme)

    for v in cfg.get("vallons", []):
        d = distance_segments(X, Y, [v["points"]])
        largeur = float(v["largeur_m"])
        profil = np.maximum(0.0, 1.0 - d / largeur) ** 2
        H -= float(v["profondeur_m"]) * profil

    # La Néra possède une vraie plaine d'inondation : même sous un massif, le
    # fond alluvial ne remonte pas soudain en colline. La côte de la baie, elle,
    # ne s'aplatit que dans l'étroite bande d'estran.
    plafond_nera = 2.2 + dist_nera * .018 + np.maximum(0.0, bruit * .18)
    H = np.where((~eau) & (dist_nera < 1350), np.minimum(H, plafond_nera), H)
    plafond_rive = 1.2 + dist_rive * .075
    H = np.where((~eau) & (dist_rive < 180), np.minimum(H, plafond_rive), H)

    # Trois passes thermiques très douces retirent les marches numériques sans
    # effacer les vallons décidés à la main.
    for _ in range(3):
        voisin = (np.roll(H, 1, 0) + np.roll(H, -1, 0) +
                   np.roll(H, 1, 1) + np.roll(H, -1, 1)) * .25
        H = np.where(~eau, H * .78 + voisin * .22, H)

    coeur_z = np.asarray(coeur["z"], dtype=np.float32)
    coeur_eau = np.asarray(coeur["eau"], dtype=np.uint8)
    coeur_l = (coeur["nx"] - 1) * coeur["res_m"]
    coeur_h = (coeur["ny"] - 1) * coeur["res_m"]
    CX, CY = np.clip(X, 0, coeur_l), np.clip(Y, 0, coeur_h)
    z_bord = echantillon(coeur_z, float(coeur["res_m"]), CX, CY)
    dx = np.maximum(0.0, np.maximum(-X, X - coeur_l))
    dy = np.maximum(0.0, np.maximum(-Y, Y - coeur_h))
    dcoeur = np.hypot(dx, dy)
    raccord = float(cfg.get("raccord_coeur_m", 900))
    t = np.clip(dcoeur / raccord, 0.0, 1.0)
    t = t * t * (3.0 - 2.0 * t)
    H = np.where(dcoeur < raccord, z_bord * (1.0 - t) + H * t, H)

    dans_coeur = (X >= 0) & (X <= coeur_l) & (Y >= 0) & (Y <= coeur_h)
    H = np.where(dans_coeur, echantillon(coeur_z, float(coeur["res_m"]), X, Y), H)
    eau_coeur = echantillon(coeur_eau.astype(np.float32),
                            float(coeur["res_m"]), X, Y) > .5
    eau = np.where(dans_coeur, eau_coeur, eau)

    profondeur = np.minimum(16.0, .8 + dist_rive / 160.0)
    H = np.where(eau, -profondeur, np.maximum(.35, H))
    # La bathymétrie régionale ne doit pas réécrire celle du port : après le
    # calcul de profondeur au large, le cœur entier — terre ET eau — revient à
    # la valeur exacte du raster de 10 m.
    H = np.where(dans_coeur,
                 echantillon(coeur_z, float(coeur["res_m"]), X, Y), H)
    H = np.round(H, 2).astype(np.float32)

    gy, gx = np.gradient(H, res, res)
    pente = np.hypot(gx, gy)
    terre = H[~eau]
    meta = {
        "min_m": round(float(H.min()), 1),
        "max_m": round(float(H.max()), 1),
        "mediane_terre_m": round(float(np.median(terre)), 1),
        "pente_p95_pct": round(float(np.percentile(pente[~eau], 95) * 100), 1),
        "pente_p99_pct": round(float(np.percentile(pente[~eau], 99) * 100), 1),
        "cellules_eau": int(eau.sum()),
    }
    paquet = {
        "x0_m": x0, "y0_m": y0, "res_m": res, "nx": nx, "ny": ny,
        "bornes_m": [x0, y0, x1, y1],
        "z": H.tolist(), "eau": eau.astype(np.uint8).tolist(),
        "statistiques": meta,
        "_lisez_moi": "Relief régional engendré par scripts/monde/relief_region.py. "
        "Le raster urbain de 10 m est recopié dans le cœur et raccordé sur "
        "900 m; les massifs et vallons nommés viennent de port-real-region.json.",
    }
    tmp = SORTIE + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(paquet, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, SORTIE)
    print("monde/portreal.region-terrain.json écrit —", meta)
    return paquet


def assurer():
    sources = [__file__, REGION_CHEM, COEUR_CHEM]
    if os.path.exists(SORTIE) and os.path.getmtime(SORTIE) >= \
            max(os.path.getmtime(p) for p in sources):
        return lire(SORTIE)
    return generer()


if __name__ == "__main__":
    generer()
