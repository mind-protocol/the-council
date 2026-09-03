# -*- coding: utf-8 -*-
"""L'ombrage du relief — le volume de la carte, cuit une fois en PNG.

    python bataille/outils/osm/07_ombrage.py --nom gelibolu --id gallipoli

Lit `<nom>.relief.bin` (int16 décimètres, ligne 0 = sud) et écrit
`bataille/donnees/ville/<id>.ombrage.png` — un calque RGBA au repère EXACT du
plan cuit (y vers le SUD, mètre pour mètre, l'image couvre `largeur_m` x
`hauteur_m`), que 🖥️ terrain.js pose sous le sol.

Pourquoi une image et pas un calcul dans le moteur : l'ombrage ne change
jamais entre deux parties — le relief est de la géographie. Le cuire ici
coûte une seconde et rend au navigateur un `drawImage`, au lieu d'un demi-
million de dérivées par changement de zoom.

Ce que l'image porte, et rien d'autre :
- l'image a DEUX FACES, et c'est ce qui la rend visible : la pente qui prend
  la lumière est BLANCHE, celle qui lui tourne le dos est NOIRE, l'alpha porte
  l'écart au plat. Un ombrage seulement noir ne rend rien sur cette carte —
  mesuré le 2 septembre : le sol vaut déjà #1b1712, il n'a pas de marge vers
  le bas, et la péninsule entière restait une masse plate. Le plat, lui, est
  transparent : là où le terrain ne penche pas, la palette passe intacte.
- une lumière rasante du NORD-OUEST à 45°, la convention des cartes
  topographiques — c'est ce qui fait qu'un talus se lit comme un talus et non
  comme un creux.
- la MER n'est pas ombrée (altitude <= 0) : elle est plate, et une ride de
  SRTM sur l'eau est du bruit de mesure, pas une vague.
"""
import argparse, io, json, math, os
import numpy as np
from PIL import Image
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _travail import dossier_travail  # les intermédiaires vivent hors du dépôt

MOTEUR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # bataille/
RACINE = os.path.dirname(MOTEUR)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nom", required=True, help="cache du relief (donnees/osm/<nom>.relief.*)")
    ap.add_argument("--id", required=True, help="id de la ville cuite (donnees/ville/<id>.plan.json)")
    ap.add_argument("--azimut", type=float, default=315.0, help="d'où vient la lumière, en degrés (315 = nord-ouest)")
    ap.add_argument("--hauteur", type=float, default=45.0, help="hauteur du soleil, en degrés")
    ap.add_argument("--exagere", type=float, default=2.0, help="facteur z : le relief d'ici est doux, on l'appuie")
    ap.add_argument("--force", type=float, default=0.55, help="opacité maximale de l'ombre (0-1)")
    ap.add_argument("--lumiere", type=float, default=0.30, help="opacité maximale du versant éclairé (0-1)")
    ap.add_argument("--donnees", help="dossier de travail (défaut : bataille/donnees/osm/<nom>/)")
    a = ap.parse_args()
    a.donnees = a.donnees or dossier_travail(a.nom)

    meta = json.load(io.open(os.path.join(a.donnees, f"{a.nom}.relief.json"), encoding="utf-8"))
    plan_p = os.path.join(MOTEUR, "donnees", "ville", f"{a.id}.plan.json")
    plan = json.load(io.open(plan_p, encoding="utf-8"))
    if abs(plan["largeur_m"] - meta["largeur_m"]) > 5 or abs(plan["hauteur_m"] - meta["hauteur_m"]) > 5:
        raise SystemExit(f"le plan ({plan['largeur_m']}x{plan['hauteur_m']} m) et le relief "
                         f"({meta['largeur_m']}x{meta['hauteur_m']} m) ne couvrent pas la même emprise : "
                         "un ombrage décalé est pire que pas d'ombrage")

    nx, ny, pas = meta["nx"], meta["ny"], meta["pas"]
    z = np.fromfile(os.path.join(a.donnees, f"{a.nom}.relief.bin"), dtype="<i2")
    z = z.reshape(ny, nx).astype(np.float32) / 10.0     # décimètres -> mètres, ligne 0 = sud
    z = z[::-1]                                          # -> ligne 0 = nord, le repère du plan

    # La pente, par différences centrées (Horn). dzdy est déjà dans le repère
    # y-vers-le-sud : une ligne de plus, c'est un pas vers le sud.
    dzdx = np.gradient(z, pas, axis=1) * a.exagere
    dzdy = np.gradient(z, pas, axis=0) * a.exagere
    pente = np.arctan(np.hypot(dzdx, dzdy))
    # aspect : la direction de la plus grande pente, en repère compas
    aspect = np.arctan2(dzdy, -dzdx)
    az, h = math.radians(90.0 - a.azimut), math.radians(a.hauteur)
    lum = np.sin(h) * np.cos(pente) + np.cos(h) * np.sin(pente) * np.cos(az - aspect)
    lum = np.clip(lum, 0.0, 1.0)

    # L'écart au PLAT, signé : négatif à l'ombre, positif à la lumière. Le plat
    # vaut zéro et reste transparent — la carte est intacte là où elle ne penche pas.
    plat = math.sin(h)
    ecart = (lum - plat) / max(plat, 1e-6)
    ombre = np.clip(-ecart, 0.0, 1.0) * a.force
    clair = np.clip(ecart, 0.0, 1.0) * a.lumiere
    ombre[z <= 0.0] = 0.0                                # la mer ne porte ni ombre
    clair[z <= 0.0] = 0.0                                # ni reflet : elle est plate

    # Une seule couche : le versant le plus marqué gagne le pixel. Blanc à la
    # lumière, noir à l'ombre, l'alpha porte l'intensité.
    gagne_clair = clair > ombre
    alpha = np.where(gagne_clair, clair, ombre)
    img = np.zeros((z.shape[0], z.shape[1], 4), dtype=np.uint8)
    img[..., 0] = img[..., 1] = img[..., 2] = np.where(gagne_clair, 255, 0).astype(np.uint8)
    img[..., 3] = np.round(alpha * 255).astype(np.uint8)
    dst = os.path.join(MOTEUR, "donnees", "ville", f"{a.id}.ombrage.png")
    Image.fromarray(img, "RGBA").save(dst, optimize=True)
    print(f"ombrage {z.shape[1]} x {z.shape[0]} au pas {pas} m, lumiere {a.azimut}° a {a.hauteur}°, "
          f"z x{a.exagere} ; {float((ombre > .02).mean())*100:.0f} % a l'ombre, "
          f"{float((clair > .02).mean())*100:.0f} % au clair, {float((alpha <= .02).mean())*100:.0f} % de plat intact")
    print(f"  -> {os.path.relpath(dst, RACINE)} ({os.path.getsize(dst)//1024} Ko)")


if __name__ == "__main__":
    main()
