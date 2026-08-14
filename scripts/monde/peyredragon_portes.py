# -*- coding: utf-8 -*-
"""La porte de chaque bâtiment de Peyredragon — le point où il touche la rue.

    python scripts/monde/peyredragon_portes.py
        (après peyredragon_chateau.py --vraiment, avant peupler.py)

Sans porte, un habitant naît au milieu de son mur et n'a aucun moyen d'en
sortir. C'est le même geste qu'à Port-Réal, où `usages.py` le fait au passage
(voir `rue_devant`) : on projette le centre du volume sur la chaussée la plus
proche, on garde le POINT et l'ID DE LA VOIE, et toute la circulation devient
possible — un trajet, c'est porte, voie, graphe, voie, porte.

Trois colonnes s'ajoutent au bâti : `porte_x`, `porte_y`, `voie`. Elles sont
exactement celles de `portreal.bati.json`, et c'est voulu : `besoins.py` et
`journee.js` ne doivent pas avoir à savoir de quel lieu ils parlent.

On projette sur le SEGMENT et non sur des points échantillonnés : trois points
par tronçon suffisent à classer une rue, pas à poser une porte — l'erreur
atteindrait plusieurs mètres, et la porte tomberait dans la chaussée ou dans le
mur d'en face.

Rejouable : si les trois colonnes sont déjà là, on les retire avant de
recommencer.
"""
import io
import json
import math
import os
from collections import defaultdict

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
MONDE = os.path.join(RACINE, "monde")

CHEMIN = os.path.join(MONDE, "peyredragon.bati.json")
B = json.load(io.open(CHEMIN, encoding="utf-8"))
G = json.load(io.open(os.path.join(MONDE, "peyredragon.graph.json"),
                      encoding="utf-8"))

AJOUT = ["porte_x", "porte_y", "voie"]
if B["_colonnes"][-3:] == AJOUT:
    n = len(B["_colonnes"]) - 3
    B["_colonnes"] = B["_colonnes"][:n]
    B["bati"] = [b[:n] for b in B["bati"]]
C = {n: k for k, n in enumerate(B["_colonnes"])}
BAT = B["bati"]

# ---------------------------------------------------------------------------
# LE SEAU — pour ne pas comparer chaque façade aux cent soixante tronçons
# ---------------------------------------------------------------------------
MAILLE = 50.0
SEAU = defaultdict(list)
NVOIES = 0
for e in G["aretes"]:
    if e.get("couche") != "L1-surface":
        continue
    NVOIES += 1
    larg = e.get("largeur_m", 3.0)
    for a, b in zip(e["trace"], e["trace"][1:]):
        seg = (a[0], a[1], b[0], b[1], e["genre"], larg, e["id"])
        # un segment s'inscrit dans TOUTES les cases qu'il traverse, sinon un
        # long segment droit reste invisible depuis son milieu
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) // MAILLE) + 1)
        for k in range(n + 1):
            t = k / n
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            SEAU[(int(x // MAILLE), int(y // MAILLE))].append(seg)


def rue_devant(x, y):
    """(px, py, id de la voie, distance) — la chaussée la plus proche."""
    ci, cj = int(x // MAILLE), int(y // MAILLE)
    meil = (9e18, x, y, None)
    vus = set()
    # on élargit l'anneau tant qu'on n'a rien : une salle du château est loin
    # de sa cour, et un séchoir de bout de grève l'est plus encore.
    for r in range(1, 12):
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                if r > 1 and abs(di) < r and abs(dj) < r:
                    continue
                for seg in SEAU.get((ci + di, cj + dj), ()):
                    if id(seg) in vus:
                        continue
                    vus.add(id(seg))
                    ax, ay, bx, by, _g, _w, vid = seg
                    dx, dy = bx - ax, by - ay
                    qq = dx * dx + dy * dy
                    t = 0.0 if qq == 0 else max(0.0, min(
                        1.0, ((x - ax) * dx + (y - ay) * dy) / qq))
                    px, py = ax + dx * t, ay + dy * t
                    d = (x - px) ** 2 + (y - py) ** 2
                    if d < meil[0]:
                        meil = (d, px, py, vid)
        # un anneau de plus après la première trouvaille : le plus proche en
        # cases n'est pas le plus proche en mètres
        if meil[3] is not None and r > 1:
            break
    return round(meil[1], 1), round(meil[2], 1), meil[3], math.sqrt(meil[0])


print("… la rue devant chaque façade — %d bâtiments, %d tronçons"
      % (len(BAT), NVOIES))
B["_colonnes"] = B["_colonnes"] + AJOUT
ds, sans = [], 0
par_quartier = defaultdict(list)
for b in BAT:
    px, py, voie, d = rue_devant(b[C["x"]], b[C["y"]])
    if voie is None:
        sans += 1
    b.append(px)
    b.append(py)
    b.append(voie)
    ds.append(d)
    par_quartier[b[C["quartier"]]].append(d)

io.open(CHEMIN, "w", encoding="utf-8").write(
    json.dumps(B, ensure_ascii=False, separators=(",", ":")))

ds.sort()
print()
print("  %d bâtiments ont une porte, %d n'en ont pas" % (len(BAT) - sans, sans))
print("  distance à la chaussée : médiane %.1f m, p90 %.1f m, max %.1f m"
      % (ds[len(ds) // 2], ds[int(len(ds) * 0.9)], ds[-1]))
for qu, v in sorted(par_quartier.items()):
    v.sort()
    print("   %-24s %3d  médiane %5.1f m, max %5.1f m"
          % (qu, len(v), v[len(v) // 2], v[-1]))
print("  -> monde/peyredragon.bati.json")
