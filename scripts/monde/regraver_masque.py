# -*- coding: utf-8 -*-
"""REGRAVER LES MURS DANS LE MASQUE, SANS RECUIRE LA VILLE.

    python scripts/monde/regraver_masque.py --lieu port-real
    python scripts/monde/regraver_masque.py --lieu port-real --mesurer

POURQUOI CE SCRIPT PLUTÔT QUE `plan_ville.py`. Le masque est cuit au milieu de
`cuire()`, entre le bâti redressé et les quartiers : le refaire par la voie
normale, c'est recuire `portreal.plan2d.json` en entier — donc repasser la
rectification sur le bâti, donc bouger des bâtiments. Or `etat/corps.json`
attache des lieux du jeu à des bâtiments par leurs coordonnées : une
régénération du monde rend les affectations cohérentes et mortes.

On ne touche donc QUE `monde/<prefixe>.masque.bin`. Le bâti déjà gravé reste
mot pour mot ce qu'il était ; on ajoute les murs manquants et l'on perce les
passages. C'est additif partout sauf aux portes, et le perçage ne mord que sur
les cases que la courtine vient de poser (voir `graver_courtine`).

`--mesurer` ne réécrit rien : il parcourt chaque mur au demi-mètre et dit
combien de mètres ne sont pas dans le masque. C'est la mesure qui a montré les
trente-six pour cent de trous, et c'est celle qui doit rester à zéro.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan_ville as PV

RACINE = PV.RACINE


def _bin(prefixe):
    return os.path.join(RACINE, "monde", prefixe + ".masque.bin")


def _meta(prefixe):
    chem = os.path.join(RACINE, "monde", prefixe + ".plan2d.json")
    with open(chem, encoding="utf-8") as f:
        return (json.load(f) or {}).get("masque") or {}


def mesurer(prefixe, lieu):
    """Combien de mètres de mur ne sont pas dans le masque, mur par mur."""
    m = _meta(prefixe)
    nx, ny, pas = m["nx"], m["ny"], m["pas"]
    with open(_bin(prefixe), "rb") as f:
        bits = f.read()

    def dedans(x, y):
        i, j = int(x / pas), int(y / pas)
        if i < 0 or j < 0 or i >= nx or j >= ny:
            return False
        k = j * nx + i
        return (bits[k >> 3] >> (k & 7)) & 1

    chem = os.path.join(RACINE, "etat", "villes", lieu + ".json")
    if not os.path.exists(chem):
        print("pas de carte de ville pour « %s »" % lieu)
        return
    with open(chem, encoding="utf-8") as f:
        sol = [s for s in (json.load(f).get("sol") or [])
               if s.get("genre") == "mur"]
    # LES CONTOURS DE LIEUX NE SONT PAS DES MURS, et les compter comme tels
    # ferait mentir la mesure de cinq kilomètres. Même critère que
    # `graver_courtine` et que `remparts()` : voir la note qui y est écrite.
    murs = [s for s in sol if s.get("largeur") in (None, 6)]
    autres = [s.get("nom") or "sans nom" for s in sol if s not in murs]
    total = trous = 0.
    for s in murs:
        pts = [PV._du_plan(p) for p in s["points"]]
        L = manque = 0.
        runs, cur = [], 0.
        for a, b in zip(pts, pts[1:]):
            lg = math.hypot(b[0] - a[0], b[1] - a[1])
            n = max(1, int(lg / .5))
            for i in range(n):
                t = (i + .5) / n
                L += lg / n
                if dedans(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t):
                    if cur:
                        runs.append(cur)
                    cur = 0.
                else:
                    manque += lg / n
                    cur += lg / n
        if cur:
            runs.append(cur)
        runs = sorted((r for r in runs if r > 1.), reverse=True)[:5]
        total += L
        trous += manque
        print("  %-30s larg=%-5s %6.0f m  ouvert %5.0f m (%3.0f %%)  %s"
              % ((s.get("nom") or "(sans nom)")[:30], s.get("largeur"), L,
                 manque, 100. * manque / L if L else 0.,
                 " ".join("%.0f" % r for r in runs)))
    print("  ---- %.0f m de mur, %.0f m ouverts (%.0f %%)"
          % (total, trous, 100. * trous / total if total else 0.))
    if autres:
        print("  (contours de lieux, non gravés : %s)" % ", ".join(autres))


def regraver(prefixe, lieu):
    m = _meta(prefixe)
    nx, ny = m["nx"], m["ny"]
    if m.get("pas") != PV.MASQUE_PAS:
        raise SystemExit("le masque cuit est au pas de %s m, le script au pas "
                         "de %s m — on ne mélange pas les deux"
                         % (m.get("pas"), PV.MASQUE_PAS))
    with open(_bin(prefixe), "rb") as f:
        bits = bytearray(f.read())
    if len(bits) != (nx * ny + 7) // 8:
        raise SystemExit("le .bin ne fait pas la taille annoncée par le plan2d")
    avant = sum(bin(o).count("1") for o in bits)
    PV.PREFIXE[0] = prefixe
    PV.graver_courtine(bits, nx, ny, lieu)
    apres = sum(bin(o).count("1") for o in bits)
    with open(_bin(prefixe), "wb") as f:
        f.write(bits)
    print("  masque      %d m² bâtis avant, %d après (%+d)"
          % (avant, apres, apres - avant))


def main():
    ap = argparse.ArgumentParser(description="Regraver les murs dans le masque")
    ap.add_argument("--lieu", default="port-real")
    ap.add_argument("--mesurer", action="store_true",
                    help="ne rien réécrire : dire seulement où sont les trous")
    a = ap.parse_args()
    prefixe = PV.PREFIXES.get(a.lieu)
    if not prefixe:
        raise SystemExit("lieu inconnu : " + a.lieu)
    if a.mesurer:
        mesurer(prefixe, a.lieu)
        return
    print("avant :")
    mesurer(prefixe, a.lieu)
    regraver(prefixe, a.lieu)
    print("après :")
    mesurer(prefixe, a.lieu)


if __name__ == "__main__":
    main()
