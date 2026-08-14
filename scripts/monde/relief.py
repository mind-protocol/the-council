# -*- coding: utf-8 -*-
"""Le relief de Port-Réal — la sous-couche de tout le reste.

    python scripts/monde/relief.py   →   monde/portreal.terrain.json

Jusqu'ici le terrain était trois dômes gaussiens sur une plaine à 11 m : lisible,
et parfaitement faux. Un terrain se lit comme vrai quand on y voit COULER l'eau —
des vallons qui se rejoignent, des crêtes entre eux, des versants raides d'un
côté et doux de l'autre. Ce n'est pas une texture, c'est une histoire d'eau.

    1. le socle          : une pente régionale vers le fleuve et la baie
    2. les trois collines: canoniques, elles décident de la ville — on les garde
    3. le fractal        : cinq octaves, pour que rien ne soit lisse
    4. l'hydrologie      : D8, accumulation de flux, incision des thalwegs
    5. l'érosion thermique : aucun versant ne tient au-delà de son angle de repos
    6. la côte           : estran au sud, à-pic sous la colline d'Aegon
    7. on redresse les sommets : le Donjon Rouge doit rester à sa hauteur

Le résultat est l'AUTORITÉ : graphe.py, densifier.py, coudre.py et batir.py
n'ont pas d'autre source d'altitude.
"""
import json, math, io, os, sys, random
from collections import defaultdict

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, ICI)
from echelle import (METRE_PAR_UNITE as MU, MONDE_L, MONDE_H, COLLINES,
                     SOL_VILLE, PROFONDEUR_FLEUVE, ux, uy)

R = random.Random(1290322)
MONDE = os.path.join(RACINE, "monde")
CARTE = json.load(io.open(os.path.join(RACINE, "etat", "villes", "port-real.json"),
                          encoding="utf-8"))
EAU_U = [s["points"] for s in CARTE["sol"] if s["genre"] == "eau"]

RES = 10.0
NX = int(MONDE_L // RES) + 1
NY = int(MONDE_H // RES) + 1
print("relief : %d × %d à %.0f m (%.1f km × %.1f km)"
      % (NX, NY, RES, MONDE_L/1000, MONDE_H/1000))

def dedans(poly, x, y):
    r = False; j = len(poly)-1
    for i in range(len(poly)):
        if (poly[i][1] > y) != (poly[j][1] > y) and \
           x < (poly[j][0]-poly[i][0])*(y-poly[i][1])/(poly[j][1]-poly[i][1])+poly[i][0]:
            r = not r
        j = i
    return r
def d_seg(px, py, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    q = dx*dx+dy*dy
    t = 0 if q == 0 else max(0, min(1, ((px-a[0])*dx+(py-a[1])*dy)/q))
    return math.hypot(px-a[0]-t*dx, py-a[1]-t*dy)

# ---------------------------------------------------------------------------
# le bruit fractal : cinq octaves de bruit de valeur, interpolé en douceur
# ---------------------------------------------------------------------------
def grille_bruit(n, m, graine):
    rr = random.Random(graine)
    return [[rr.random() for _ in range(m+2)] for _ in range(n+2)]

class Octave:
    def __init__(self, taille_m, graine):
        self.pas = taille_m / RES
        self.g = grille_bruit(int(NX/self.pas)+3, int(NY/self.pas)+3, graine)
    def __call__(self, i, j):
        fx, fy = i/self.pas, j/self.pas
        a, b = int(fx), int(fy)
        tx, ty = fx-a, fy-b
        tx = tx*tx*(3-2*tx); ty = ty*ty*(3-2*ty)
        g = self.g
        u = g[a][b]*(1-tx) + g[a+1][b]*tx
        v = g[a][b+1]*(1-tx) + g[a+1][b+1]*tx
        return u*(1-ty) + v*ty

print("… le socle et le fractal")
OCTAVES = [(Octave(900, 11), 16.0), (Octave(420, 22), 8.0), (Octave(190, 33), 4.0),
           (Octave(90, 44), 2.0), (Octave(45, 55), 1.0)]

H = [[0.0]*NX for _ in range(NY)]
EAU = [[0]*NX for _ in range(NY)]
DIST_RIVE = [[999.0]*NX for _ in range(NY)]

# la distance à la rive, une fois pour toutes
BORDS = [(e, [(e[k], e[(k+1) % len(e)]) for k in range(len(e))]) for e in EAU_U]
for j in range(NY):
    for i in range(NX):
        wx, wy = i*RES, j*RES
        cx, cy = ux(wx), uy(wy)
        dedans_eau = any(dedans(e, cx, cy) for e in EAU_U)
        d = min(min(d_seg(cx, cy, a, b) for a, b in segs) for e, segs in BORDS) * MU
        EAU[j][i] = 1 if dedans_eau else 0
        DIST_RIVE[j][i] = d
        # socle : la terre s'incline vers l'eau, doucement, sur toute l'emprise
        socle = 6.0 + min(1.0, d/1400.0) * 16.0
        f = sum(o(i, j)*amp for o, amp in OCTAVES) / sum(a for _, a in OCTAVES)
        H[j][i] = socle + (f - 0.5) * 26.0

print("… les trois collines")
for (cx_u, cy_u), r_u, sommet in COLLINES:
    cx, cy = cx_u*MU, (300 - cy_u)*MU
    r = r_u*MU
    for j in range(NY):
        wy = j*RES
        if abs(wy-cy) > r*1.35: continue
        for i in range(NX):
            wx = i*RES
            d = math.hypot(wx-cx, wy-cy)
            if d >= r*1.3: continue
            # un versant n'est pas un cosinus : on le froisse, et on l'écrase
            # d'un côté pour qu'aucune colline ne soit un chapeau
            t = max(0.0, 1.0 - d/(r*1.3))
            gauchi = 1.0 + 0.30*math.sin(math.atan2(wy-cy, wx-cx)*1.7 + cx*0.001)
            H[j][i] += (sommet - SOL_VILLE) * (t**1.7) * gauchi

# ---------------------------------------------------------------------------
# l'hydrologie : c'est elle qui rend un terrain crédible
# ---------------------------------------------------------------------------
print("… l'écoulement (D8) et l'incision des thalwegs")
VOISINS = [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]

def ecoulement(H, passes=2, k_incision=1.35):
    for tour in range(passes):
        # 1) chaque case s'écoule vers sa voisine la plus basse
        aval = {}
        cases = []
        for j in range(1, NY-1):
            for i in range(1, NX-1):
                if EAU[j][i]: continue
                h = H[j][i]
                meil, pente = None, 0.0
                for dx, dy in VOISINS:
                    hv = H[j+dy][i+dx]
                    p = (h - hv) / (RES*math.hypot(dx, dy))
                    if p > pente: pente, meil = p, (i+dx, j+dy)
                if meil: aval[(i, j)] = meil
                cases.append((h, i, j))
        # 2) on accumule du haut vers le bas : chaque case passe son eau à l'aval
        cases.sort(reverse=True)
        flux = defaultdict(float)
        for h, i, j in cases:
            flux[(i, j)] += 1.0
            a = aval.get((i, j))
            if a: flux[a] += flux[(i, j)]
        # 3) on creuse là où l'eau passe : la vallée se fait par le bas
        creuse = 0.0
        for (i, j), f in flux.items():
            if EAU[j][i]: continue
            d = k_incision * math.sqrt(f) * 0.045
            d = min(d, 9.0)
            H[j][i] -= d
            creuse = max(creuse, d)
        print("     passe %d : %d cases drainées, incision max %.1f m"
              % (tour+1, len(flux), creuse))
    return flux

flux = ecoulement(H)

print("… l'érosion thermique")
TALUS = 0.62                     # au-delà, la pente s'éboule
for tour in range(14):
    bouge = 0.0
    for j in range(1, NY-1):
        for i in range(1, NX-1):
            if EAU[j][i]: continue
            h = H[j][i]
            for dx, dy in VOISINS:
                hv = H[j+dy][i+dx]
                dl = RES*math.hypot(dx, dy)
                if (h - hv)/dl > TALUS:
                    t = ((h-hv) - TALUS*dl) * 0.22
                    H[j][i] -= t; H[j+dy][i+dx] += t
                    bouge = max(bouge, t)
                    h = H[j][i]
    if bouge < 0.05: break
print("     %d passes" % (tour+1))

# ---------------------------------------------------------------------------
# la côte : estran doux au sud, à-pic sous la colline d'Aegon
# ---------------------------------------------------------------------------
print("… la côte")
AEGON = (COLLINES[0][0][0]*MU, (300-COLLINES[0][0][1])*MU)
for j in range(NY):
    for i in range(NX):
        d = DIST_RIVE[j][i]
        if EAU[j][i]:
            H[j][i] = -min(PROFONDEUR_FLEUVE, 0.8 + d/45.0)
            continue
        # à moins de 70 m de l'eau, la terre rejoint le niveau du fleuve
        if d < 70.0:
            # sous Aegon, la berge est une falaise : le Donjon domine l'eau
            pres_aegon = math.hypot(i*RES-AEGON[0], j*RES-AEGON[1]) < 700
            portee = 22.0 if pres_aegon else 70.0
            t = min(1.0, d/portee)
            t = t*t*(3-2*t)
            H[j][i] = 0.6 + (H[j][i] - 0.6) * t

print("… on redresse les sommets canoniques")
# On NE SOUSTRAIT PAS une bosse corrective : retrancher un dôme au point le plus
# haut y creuse un pli, parce que le sommet réel n'est jamais exactement au
# centre géométrique. On RÉÉCHELONNE le relief autour de sa base : la forme
# érodée est conservée telle quelle, seule son amplitude change.
for (cx_u, cy_u), r_u, sommet in COLLINES:
    cx, cy = cx_u*MU, (300-cy_u)*MU
    r = r_u*MU
    cases = []
    for j in range(NY):
        wy = j*RES
        if abs(wy-cy) > r*1.35: continue
        for i in range(NX):
            d = math.hypot(i*RES-cx, wy-cy)
            if d < r*1.3 and not EAU[j][i]:
                cases.append((d, i, j))
    if not cases: continue
    haut = max(H[j][i] for d, i, j in cases if d < r*0.4)
    base = sorted(H[j][i] for d, i, j in cases if d > r*1.1)
    base = base[len(base)//2] if base else SOL_VILLE
    if haut - base < 1.0: continue
    k = (sommet - base) / (haut - base)
    for d, i, j in cases:
        t = max(0.0, 1.0 - d/(r*1.3)) ** 0.8     # on fond vers les bords
        H[j][i] = H[j][i] + (base + (H[j][i]-base)*k - H[j][i]) * t
    print("     sommet %.0f m : base %.0f, avant %.0f, facteur %.2f"
          % (sommet, base, haut, k))

lo = min(min(l) for l in H)
hi = max(max(l) for l in H)
terre = [H[j][i] for j in range(NY) for i in range(NX) if not EAU[j][i]]
print()
print("relief : de %.0f m à %.0f m | terre : moyenne %.0f m, médiane %.0f m"
      % (lo, hi, sum(terre)/len(terre), sorted(terre)[len(terre)//2]))

os.makedirs(MONDE, exist_ok=True)
io.open(os.path.join(MONDE, "portreal.terrain.json"), "w", encoding="utf-8").write(
    json.dumps({"res_m": RES, "nx": NX, "ny": NY,
                "z": [[round(v, 2) for v in l] for l in H], "eau": EAU,
                "_lisez_moi": "Relief engendré par scripts/monde/relief.py : socle + "
                              "collines canoniques + fractal 5 octaves, puis écoulement "
                              "D8 avec incision des thalwegs, érosion thermique, côte, "
                              "et redressement des sommets. C'est L'AUTORITÉ d'altitude : "
                              "aucun autre script ne calcule de hauteur."},
               ensure_ascii=False, separators=(",", ":")))
print("monde/portreal.terrain.json écrit")
