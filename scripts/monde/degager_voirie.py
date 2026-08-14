# -*- coding: utf-8 -*-
"""L'axe des rues sort des façades — pour qu'un chemin n'en traverse jamais.

    python scripts/monde/degager_voirie.py    (après usages.py)

POURQUOI. Le pathfinding suit l'axe des voies. Tant que cet axe passe dans une
emprise bâtie, un trajet traverse une maison, quelle que soit la finesse du
Dijkstra. La pose exacte de `densifier.py` a ramené le mal de 17,9 % des arêtes
à 0,7 % — il reste une poignée de tronçons dont l'axe rase ou coupe un mur,
là où la voie a été tracée avant que la maison ne soit posée.

CE QU'ON FAIT. On rééchantillonne chaque tracé au mètre, et l'on POUSSE
LATÉRALEMENT les points qui tombent dans du bâti, jusqu'au libre, sans jamais
dépasser trois mètres. Le résultat est simplifié (Douglas-Peucker) pour ne pas
alourdir le graphe d'un point par mètre.

CE QU'ON NE TOUCHE PAS. Les EXTRÉMITÉS : ce sont des nœuds, partagés avec les
arêtes voisines et avec les portes. Les bouger décollerait le réseau. Une
extrémité prise dans un mur se signale et se laisse ; il y en a peu, et c'est un
défaut de pose, pas de tracé.

C'est le tirage de corde d'un moteur de jeu — corridor puis funnel — payé UNE
FOIS hors ligne au lieu d'être refait à chaque trajet. La ville ne bouge qu'à la
régénération : autant que le chemin soit propre par construction.
"""
import json, io, math, os, sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
MONDE = os.path.join(RACINE, "monde")
PREFIXE = sys.argv[1] if len(sys.argv) > 1 else "portreal"

CHEMIN = os.path.join(MONDE, PREFIXE + ".graph.json")
G = json.load(io.open(CHEMIN, encoding="utf-8"))
B = json.load(io.open(os.path.join(MONDE, PREFIXE + ".bati.json"), encoding="utf-8"))
C = {n: i for i, n in enumerate(B["_colonnes"])}

CEL = 0.5                       # la trame du bâti, en mètres
ECART_MAX = 3.0                 # au-delà, ce n'est plus un écart mais un détour
PAS = 1.0                       # le rééchantillonnage du tracé

# --- la trame des emprises ---------------------------------------------------
print("… les emprises")
xs = [r[C["x"]] for r in B["bati"]]
ys = [r[C["y"]] for r in B["bati"]]
X0, Y0 = min(xs) - 60, min(ys) - 60
NX = int((max(xs) + 60 - X0) / CEL) + 1
NY = int((max(ys) + 60 - Y0) / CEL) + 1
BAT = bytearray(NX * NY)
for r in B["bati"]:
    a = math.radians(r[C["cap"]] or 0.)
    ca, sa = math.cos(a), math.sin(a)
    f, p = r[C["facade_m"]] / 2., r[C["profondeur_m"]] / 2.
    nf = max(2, int(r[C["facade_m"]] / CEL)) + 1
    np_ = max(2, int(r[C["profondeur_m"]] / CEL)) + 1
    for u in range(nf + 1):
        for v in range(np_ + 1):
            dx = -f + 2 * f * u / nf
            dy = -p + 2 * p * v / np_
            x = r[C["x"]] + dx * ca - dy * sa
            y = r[C["y"]] + dx * sa + dy * ca
            i, j = int((x - X0) / CEL), int((y - Y0) / CEL)
            if 0 <= i < NX and 0 <= j < NY:
                BAT[j * NX + i] = 1
print("   %d × %d cases de %.1f m" % (NX, NY, CEL))


def dedans(x, y):
    i, j = int((x - X0) / CEL), int((y - Y0) / CEL)
    return 0 <= i < NX and 0 <= j < NY and BAT[j * NX + i]


def alleger(pts, tol=0.25):
    """Douglas-Peucker : un tracé n'a pas besoin d'un point par mètre"""
    if len(pts) < 3:
        return pts
    ax, ay = pts[0][0], pts[0][1]
    bx, by = pts[-1][0], pts[-1][1]
    dx, dy = bx - ax, by - ay
    q = dx * dx + dy * dy
    dmax, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i][0], pts[i][1]
        t = 0.0 if q < 1e-12 else max(0., min(1., ((px - ax) * dx + (py - ay) * dy) / q))
        d = math.hypot(px - ax - t * dx, py - ay - t * dy)
        if d > dmax:
            dmax, idx = d, i
    if dmax > tol:
        return alleger(pts[:idx + 1], tol)[:-1] + alleger(pts[idx:], tol)
    return [pts[0], pts[-1]]


# --- on écarte ---------------------------------------------------------------
print("… on écarte les axes des façades")
touchees = pousses = bouts = 0
for a in G["aretes"]:
    if a.get("couche") != "L1-surface":
        continue
    t = a.get("trace") or []
    if len(t) < 2:
        continue
    # rééchantillonnage au mètre
    fin = []
    for u, v in zip(t, t[1:]):
        L = math.hypot(v[0] - u[0], v[1] - u[1])
        n = max(1, int(L / PAS))
        for k in range(n):
            s = k / n
            fin.append([u[0] + (v[0] - u[0]) * s, u[1] + (v[1] - u[1]) * s,
                        (u[2] + (v[2] - u[2]) * s) if len(u) > 2 and len(v) > 2 else 0.])
    fin.append(list(t[-1]))
    if not any(dedans(p[0], p[1]) for p in fin):
        continue
    touchees += 1
    if dedans(fin[0][0], fin[0][1]) or dedans(fin[-1][0], fin[-1][1]):
        bouts += 1
    for i in range(1, len(fin) - 1):          # jamais les extrémités : ce sont des nœuds
        if not dedans(fin[i][0], fin[i][1]):
            continue
        ax, ay = fin[i - 1][0], fin[i - 1][1]
        bx, by = fin[i + 1][0], fin[i + 1][1]
        L = math.hypot(bx - ax, by - ay)
        if L < 1e-9:
            continue
        nx, ny = -(by - ay) / L, (bx - ax) / L     # la normale au tracé
        mieux = None
        e = CEL
        while e <= ECART_MAX:
            for s in (1, -1):
                qx, qy = fin[i][0] + nx * e * s, fin[i][1] + ny * e * s
                if not dedans(qx, qy):
                    mieux = (qx, qy)
                    break
            if mieux:
                break
            e += CEL
        if mieux:
            fin[i][0], fin[i][1] = mieux
            pousses += 1
    neuf = alleger([[round(p[0], 2), round(p[1], 2), round(p[2], 2)] for p in fin])
    lg = sum(math.dist(p[:2], q[:2]) for p, q in zip(neuf, neuf[1:]))
    if lg < 1e-3:
        continue
    a["trace"] = neuf
    a["longueur_m"] = round(lg, 2)
    dz = abs(neuf[-1][2] - neuf[0][2])
    a["pente"] = round(dz / lg, 3)

G["_degage"] = True
io.open(CHEMIN, "w", encoding="utf-8").write(json.dumps(G, ensure_ascii=False))

L1 = [e for e in G["aretes"] if e.get("couche") == "L1-surface"]
reste = 0
for a in L1:
    t = a["trace"]
    mauv = 0
    for u, v in zip(t, t[1:]):
        L = math.hypot(v[0] - u[0], v[1] - u[1])
        n = max(1, int(L))
        for k in range(n + 1):
            s = k / n
            if dedans(u[0] + (v[0] - u[0]) * s, u[1] + (v[1] - u[1]) * s):
                mauv += 1
    if mauv > 2:
        reste += 1
print()
print("  %s" % os.path.relpath(CHEMIN, RACINE))
print("  %d aretes touchaient du bati, %d points pousses" % (touchees, pousses))
print("  %d dont une EXTREMITE est dans un mur (laissees : ce sont des noeuds)" % bouts)
print("  restent %d aretes qui traversent (%.2f %%)" % (reste, 100. * reste / len(L1)))
print("  voirie de surface : %.1f km" % (sum(e["longueur_m"] for e in L1) / 1000))
print()
print("  puis : python scripts/marche.py --cache")
