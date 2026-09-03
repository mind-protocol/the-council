# -*- coding: utf-8 -*-
"""Le relief d'une emprise OSM — les tuiles Terrarium, assemblées en mètres.

    python bataille/outils/osm/03_relief.py --nom gelibolu [--pas 15] [--zoom 13]

Lit l'emprise dans <donnees>/osm/<nom>.osm.json, tire les tuiles d'altitude
Terrarium (AWS `elevation-tiles-prod`, héritage Mapzen, bâties sur SRTM ; sans
clé ; PNG où h = R·256 + G + B/256 − 32768) et les rééchantillonne sur le MÊME
repère que la couche nettoyée : mètres depuis le coin sud-ouest, x vers l'est,
y vers le nord. Les tuiles sont gardées dans <donnees>/osm/terrarium/ : une
relance ne touche plus le réseau.

Sortie, sur le modèle du masque cuit : <nom>.relief.bin (int16, décimètres,
k = j*nx + i, ligne j = sud en premier) et <nom>.relief.json (nx, ny, pas,
origine, min/max, source). La mer vaut 0 dans la source.

Zoom 13 ≈ 14,5 m/px à cette latitude ; la donnée native est à 30 m, plus haut
n'apporte rien. Le pas de sortie par défaut, 15 m, suit la source.
"""
import argparse, io, json, math, os, sys
import numpy as np
import requests
from PIL import Image
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _travail import dossier_travail  # les intermédiaires vivent hors du dépôt

MOTEUR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # bataille/
TUILES = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
ENTETE = {"User-Agent": "la-companie/0.1 (jeu ; reynolds.nicorr@gmail.com)"}


def merc(lon, lat, z):
    """Pixel Web-Mercator (256 px par tuile) à ce zoom, en flottants."""
    n = 2 ** z * 256
    px = (lon + 180) / 360 * n
    py = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return px, py


def tuile(z, x, y, cache):
    p = os.path.join(cache, f"{z}-{x}-{y}.png")
    if not os.path.exists(p):
        r = requests.get(TUILES.format(z=z, x=x, y=y), headers=ENTETE, timeout=60)
        if r.status_code != 200: sys.exit(f"tuile {z}/{x}/{y} : {r.status_code}")
        io.open(p, "wb").write(r.content)
    a = np.asarray(Image.open(p).convert("RGB"), dtype=np.float64)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nom", required=True)
    ap.add_argument("--pas", type=float, default=15.0, help="mètres par case en sortie")
    ap.add_argument("--zoom", type=int, default=13)
    ap.add_argument("--donnees", help="dossier de travail (défaut : bataille/donnees/osm/<nom>/)")
    a = ap.parse_args()
    a.donnees = a.donnees or dossier_travail(a.nom)
    src = json.load(io.open(os.path.join(a.donnees, f"{a.nom}.osm.json"), encoding="utf-8"))
    sud, ouest, nord, est = src["bbox"]
    kx = 111320 * math.cos(math.radians((sud + nord) / 2)); ky = 111320
    largeur, hauteur = (est - ouest) * kx, (nord - sud) * ky
    nx, ny = int(math.ceil(largeur / a.pas)) + 1, int(math.ceil(hauteur / a.pas)) + 1

    # La mosaïque des tuiles qui couvrent l'emprise.
    z = a.zoom
    px0, py1 = merc(ouest, sud, z); px1, py0 = merc(est, nord, z)
    tx0, tx1 = int(px0 // 256), int(px1 // 256); ty0, ty1 = int(py0 // 256), int(py1 // 256)
    cache = os.path.join(a.donnees, "terrarium"); os.makedirs(cache, exist_ok=True)
    mosaique = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256))
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            mosaique[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = tuile(z, tx, ty, cache)
    n_tuiles = (ty1 - ty0 + 1) * (tx1 - tx0 + 1)

    # Chaque case de sortie -> lon/lat -> pixel mosaïque, bilinéaire.
    i = np.arange(nx) * a.pas; j = np.arange(ny) * a.pas
    X, Y = np.meshgrid(i, j)                       # Y[j] : ligne j = sud en premier
    lon = ouest + X / kx; lat = sud + Y / ky
    n = 2 ** z * 256
    PX = (lon + 180) / 360 * n - tx0 * 256
    PY = (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / np.pi) / 2 * n - ty0 * 256
    x0 = np.clip(np.floor(PX).astype(int), 0, mosaique.shape[1] - 2); y0 = np.clip(np.floor(PY).astype(int), 0, mosaique.shape[0] - 2)
    fx, fy = PX - x0, PY - y0
    H = (mosaique[y0, x0] * (1 - fx) * (1 - fy) + mosaique[y0, x0 + 1] * fx * (1 - fy)
         + mosaique[y0 + 1, x0] * (1 - fx) * fy + mosaique[y0 + 1, x0 + 1] * fx * fy)

    bin_ = os.path.join(a.donnees, f"{a.nom}.relief.bin")
    np.round(H * 10).astype("<i2").tofile(bin_)
    meta = {"_lisez_moi": "Relief Terrarium (SRTM) rééchantillonné par bataille/outils/osm/03_relief.py. int16 en décimètres, k = j*nx + i, ligne 0 = sud. Même repère que <nom>.propre.json.",
            "nom": a.nom, "source": "AWS elevation-tiles-prod / terrarium", "zoom": z, "tuiles": n_tuiles,
            "bbox": src["bbox"], "origine": {"lat": sud, "lon": ouest}, "nx": nx, "ny": ny, "pas": a.pas,
            "largeur_m": round(largeur), "hauteur_m": round(hauteur),
            "min_m": round(float(H.min()), 1), "max_m": round(float(H.max()), 1), "unite": "decimetre", "format": "<i2"}
    json.dump(meta, io.open(os.path.join(a.donnees, f"{a.nom}.relief.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{n_tuiles} tuiles, grille {nx} x {ny} au pas {a.pas} m, altitudes {meta['min_m']} à {meta['max_m']} m -> {os.path.relpath(bin_, os.path.dirname(MOTEUR))} ({os.path.getsize(bin_)//1024} Ko)")


if __name__ == "__main__":
    main()
