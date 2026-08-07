# -*- coding: utf-8 -*-
"""Port-Réal : la ville s'engendre par la CIRCULATION, pas par les maisons.

    nœuds → artères → rues → ruelles → parcelles → façades

Chaque tracé porte sa `raison` : la forme de la ville dit son fonctionnement.
Rien d'aléatoire dans la structure ; le hasard ne sert qu'à froisser les tracés
pour qu'aucune rue ne soit droite au cordeau.
"""
import json, math, heapq, io, os, random

R = random.Random(112900323)
SP = os.path.dirname(os.path.abspath(__file__))

L, H = 440, 300          # le repère
PAS = 2                  # la grille de calcul : 2 unités par case
GL, GH = L // PAS, H // PAS

# ---------------------------------------------------------------------------
# 0. LE SOL — ce qui décide de tout le reste
# ---------------------------------------------------------------------------
MURS = [[90,132],[96,112],[118,80],[170,58],[232,48],[292,52],[336,74],[364,112],
        [374,158],[370,204],[356,236],[310,246],[246,252],[186,250],[150,244],
        [130,238],[100,206],[89,174],[88,160]]

EAU = [
    [[0,282],[70,276],[150,272],[228,274],[296,276],[348,268],[386,250],[398,300],[0,300]],
    [[386,250],[398,300],[440,300],[440,0],[404,8],[392,74],[386,150],[380,200]],
]
COLLINES = [                       # centre, rayon, hauteur
    ((318,193), 46, 30),           # la colline d'Aegon
    ((276, 94), 43, 26),           # la colline de Rhaenys
    ((150,182), 41, 28),           # la colline de Visenya
]
BATI = {   # ce qu'on ne perce pas : une rue s'arrête à la porte
    "donjon":  [[300,176],[344,170],[352,200],[330,220],[300,214],[292,194]],
    "fosse":   [[262,80],[292,84],[300,102],[286,118],[262,116],[252,98]],
    "septuaire":[[140,166],[166,162],[172,180],[152,190],[136,182]],
    "guilde":  [[224,124],[248,122],[250,140],[226,142]],
    "casernes":[[222,158],[244,156],[246,174],[224,176]],
}

def dedans(poly, x, y):
    r = False; j = len(poly) - 1
    for i in range(len(poly)):
        if (poly[i][1] > y) != (poly[j][1] > y) and \
           x < (poly[j][0]-poly[i][0])*(y-poly[i][1])/(poly[j][1]-poly[i][1])+poly[i][0]:
            r = not r
        j = i
    return r

def dist_seg(px, py, a, b):
    ax, ay = a; bx, by = b
    dx, dy = bx-ax, by-ay
    q = dx*dx + dy*dy
    t = 0 if q == 0 else max(0, min(1, ((px-ax)*dx + (py-ay)*dy)/q))
    return math.hypot(px-ax-t*dx, py-ay-t*dy)

def dist_ligne(pts, x, y):
    return min(dist_seg(x, y, a, b) for a, b in zip(pts, pts[1:]))

def hauteur(x, y):
    h = 0.0
    for (cx, cy), r, ht in COLLINES:
        d = math.hypot(x-cx, y-cy)
        if d < r: h += ht * (1 - (d/r)**2)**1.4
    return h

# un bruit lisse et reproductible : c'est lui qui empêche les rues d'être droites
BR = [[R.random() for _ in range(GH//4 + 3)] for _ in range(GL//4 + 3)]
def bruit(gx, gy):
    fx, fy = gx/4.0, gy/4.0
    i, j = int(fx), int(fy)
    tx, ty = fx-i, fy-j
    tx = tx*tx*(3-2*tx); ty = ty*ty*(3-2*ty)
    a = BR[i][j]*(1-tx) + BR[i+1][j]*tx
    b = BR[i][j+1]*(1-tx) + BR[i+1][j+1]*tx
    return a*(1-ty) + b*ty

print("… le sol")
HT   = [[0.0]*GH for _ in range(GL)]
LIBRE= [[False]*GH for _ in range(GL)]   # constructible / carrossable
DEDANS=[[False]*GH for _ in range(GL)]   # dans les murs
for gx in range(GL):
    for gy in range(GH):
        x, y = gx*PAS + 1, gy*PAS + 1
        HT[gx][gy] = hauteur(x, y)
        if any(dedans(e, x, y) for e in EAU): continue
        LIBRE[gx][gy] = True
        DEDANS[gx][gy] = dedans(MURS, x, y)

def bloque(poly, marge=0):
    for gx in range(GL):
        for gy in range(GH):
            x, y = gx*PAS+1, gy*PAS+1
            if dedans(poly, x, y): LIBRE[gx][gy] = False
for p in BATI.values(): bloque(p)

# le mur : infranchissable sauf aux portes
PORTES = {
    "dieux":  (89,140), "lion": (90,183), "roi": (159,245), "gadoue": (282,249),
    "fer":    (370,134), "dragons": (262,49), "vieille": (146,68),
}
MUR_PTS = MURS + [MURS[0]]
for gx in range(GL):
    for gy in range(GH):
        x, y = gx*PAS+1, gy*PAS+1
        if dist_ligne(MUR_PTS, x, y) < 3.2 and \
           all(math.hypot(x-px, y-py) > 6 for px, py in PORTES.values()):
            LIBRE[gx][gy] = False

# ---------------------------------------------------------------------------
# 1. LES NŒUDS — les destinations obligatoires
# ---------------------------------------------------------------------------
CX = sum(p[0] for p in MURS)/len(MURS)
CY = sum(p[1] for p in MURS)/len(MURS)
def en_dedans(p, d=9.0):
    vx, vy = CX-p[0], CY-p[1]
    n = math.hypot(vx, vy)
    return (p[0]+vx/n*d, p[1]+vy/n*d)
N = {k: en_dedans(v) for k, v in PORTES.items()}
N_PORTE = dict(PORTES)
N.update({
    "quai-amont": (286,258), "quai-aval": (344,250),
    "donjon":     (286,198),                       # la porte du Donjon, côté ville
    "grand-marche": (196,150),                     # la grande place
    "marche-chevaux": (120,150),                   # sous la porte des Dieux
    "marche-poissons": (288,228),                  # dedans, sous la Gadoue
    "guilde":     (236,146), "casernes": (234,180),
    "septuaire":  (148,198), "fosse": (272,130),
    "col-soeurs": (216,138),                       # le col entre Visenya et Rhaenys
    "col-crochet":(276,168),                       # le col au pied d'Aegon
})

# ---------------------------------------------------------------------------
# 2-4. LE GRAPHE — un A* dont le coût dit pourquoi une rue tourne
# ---------------------------------------------------------------------------
for k, (x, y) in N.items():
    gx, gy = int(x)//PAS, int(y)//PAS
    if not (LIBRE[gx][gy] and DEDANS[gx][gy]):
        print("   ! noeud injoignable :", k, (x, y))

RUE = [[0.0]*GH for _ in range(GL)]      # 0 = vierge, sinon largeur posée

def chemin_a(dep, arr, dedans_seul=True, pente=1.0, reprise=0.55, sinuosite=1.0):
    """coût = distance + pente + bruit − reprise d'une voie existante"""
    d0 = (int(dep[0])//PAS, int(dep[1])//PAS)
    a0 = (int(arr[0])//PAS, int(arr[1])//PAS)
    def ok(g):
        gx, gy = g
        if not (0 <= gx < GL and 0 <= gy < GH): return False
        if not LIBRE[gx][gy]: return False
        return DEDANS[gx][gy] if dedans_seul else True
    if not ok(d0) or not ok(a0): return None
    vu = {d0: 0.0}
    prec = {}
    tas = [(0.0, d0)]
    VOISINS = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    while tas:
        f, g = heapq.heappop(tas)
        if g == a0: break
        gx, gy = g
        cg = vu[g]
        for dx, dy in VOISINS:
            n = (gx+dx, gy+dy)
            if not ok(n): continue
            longueur = math.hypot(dx, dy) * PAS
            dh = abs(HT[n[0]][n[1]] - HT[gx][gy])
            c = longueur * (1 + sinuosite * 0.9 * bruit(n[0], n[1])) + pente * 3.2 * dh
            if RUE[n[0]][n[1]]:              # récupérer une vieille voie coûte moins
                c *= reprise
            nc = cg + c
            if n not in vu or nc < vu[n] - 1e-9:
                vu[n] = nc; prec[n] = g
                heapq.heappush(tas, (nc + math.dist(n, a0)*PAS*0.92, n))
    if a0 not in prec and a0 != d0: return None
    ch, cur = [a0], a0
    while cur in prec:
        cur = prec[cur]; ch.append(cur)
    ch.reverse()
    return [[c[0]*PAS+1, c[1]*PAS+1] for c in ch]

def alleger(pts, tol=1.6):
    """Douglas-Peucker : une rue n'a pas besoin d'un point tous les deux pas"""
    if len(pts) < 3: return pts
    dmax, idx = 0, 0
    for i in range(1, len(pts)-1):
        d = dist_seg(pts[i][0], pts[i][1], pts[0], pts[-1])
        if d > dmax: dmax, idx = d, i
    if dmax > tol:
        return alleger(pts[:idx+1], tol)[:-1] + alleger(pts[idx:], tol)
    return [pts[0], pts[-1]]

def lisser(pts, n=2):
    """Chaikin : on coupe les angles, une rue de terre n'en a pas"""
    for _ in range(n):
        if len(pts) < 3: break
        q = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            q.append([a[0]*.75+b[0]*.25, a[1]*.75+b[1]*.25])
            q.append([a[0]*.25+b[0]*.75, a[1]*.25+b[1]*.75])
        q.append(pts[-1])
        pts = q
    return pts

def poser(pts, larg):
    """marque la voie dans la grille : les suivantes la retrouveront"""
    r = larg/2 + 1.2
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.dist(a, b)/1.5))
        for i in range(n+1):
            t = i/n
            x, y = a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t
            for gx in range(max(0,int((x-r)//PAS)), min(GL, int((x+r)//PAS)+1)):
                for gy in range(max(0,int((y-r)//PAS)), min(GH, int((y+r)//PAS)+1)):
                    if math.hypot(gx*PAS+1-x, gy*PAS+1-y) <= r:
                        RUE[gx][gy] = max(RUE[gx][gy], larg)

VOIES = []      # {points, largeur, nom?, raison, rang}
def tracer(dep, arr, larg, raison, nom=None, rang="artere", **kw):
    ch = chemin_a(N.get(dep, dep), N.get(arr, arr), **kw)
    if not ch or len(ch) < 3:
        print("   ! pas de chemin", dep, "->", arr); return None
    ch = lisser(alleger(ch, 1.8), 2)
    for bout, cle in ((0, dep), (-1, arr)):
        if cle in N_PORTE:
            p = list(N_PORTE[cle])
            ch = ([p] + ch) if bout == 0 else (ch + [p])
    ch = [[round(p[0],1), round(p[1],1)] for p in ch]
    poser(ch, larg)
    v = {"points": ch, "largeur": larg, "raison": raison, "rang": rang}
    if nom: v["nom"] = nom
    VOIES.append(v)
    return v

print("… les artères")
# Ce que des centaines de gens font chaque jour. Rien d'autre n'est une artère.
ARTERES = [
    ("gadoue","marche-poissons", 6.5, "Tout ce qui débarque entre par là : la Gadoue au marché", "La rue de la Gadoue"),
    ("marche-poissons","grand-marche", 6.0, "Du marché au poisson à la grande place : le ventre de la ville", "La rue du Fleuve"),
    ("grand-marche","donjon", 5.5, "De la place au Donjon Rouge : la voie des robes et des ordres", "La rue de la Soie"),
    ("dieux","marche-chevaux", 6.0, "La route de la Rose entre par les Dieux et s'arrête au marché aux chevaux", "La rue du Marché"),
    ("marche-chevaux","grand-marche", 5.5, "Les deux marchés se tiennent par la main", None),
    ("roi","grand-marche", 5.0, "La porte du Roi monte droit à la place", "La rue du Roi"),
    ("lion","marche-chevaux", 4.8, "La porte du Lion se rabat sur le marché aux chevaux", None),
    ("dragons","col-soeurs", 5.0, "La descente de la Fosse : on n'y monte que pour les bêtes", "La descente des Dragons"),
    ("col-soeurs","septuaire", 5.0, "Du septuaire à la Fosse, de colline à colline", "La rue des Sœurs"),
    ("col-soeurs","grand-marche", 5.0, "Le col verse sur la place", None),
    ("fer","donjon", 5.2, "La porte de Fer sert le Donjon avant de servir la ville", "La rue de Fer"),
    ("vieille","grand-marche", 4.8, "La Vieille Porte, et ce qui vient encore du nord", "La rue de la Vieille Porte"),
    ("donjon","col-crochet", 5.0, "Le Crochet contourne le pied de la colline d'Aegon", "Le Crochet"),
    ("col-crochet","marche-poissons", 4.8, "Du Crochet au poisson : les cuisines du Donjon", None),
    ("grand-marche","septuaire", 4.6, "La rue d'Acier monte droit : les forges veulent la pente", "La rue d'Acier"),
]
for a, b, w, why, nom in ARTERES:
    kw = {"pente": 0.35, "sinuosite": 0.7} if nom == "La rue d'Acier" else {}
    tracer(a, b, w, why, nom, "artere", **kw)

print("… les rues secondaires")
# Elles ne relient plus des lieux : elles relient les artères entre elles.
def point_sur(v, t):
    pts = v["points"]
    tot = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    cible, cur = tot*t, 0
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        if cur + d >= cible:
            u = (cible-cur)/d if d else 0
            return [a[0]+(b[0]-a[0])*u, a[1]+(b[1]-a[1])*u]
        cur += d
    return pts[-1]

def trop_pres(pts, mini):
    """une rue qui longe une autre de bout en bout n'a pas lieu d'être"""
    n = 0
    for p in pts:
        gx, gy = int(p[0])//PAS, int(p[1])//PAS
        if 0 <= gx < GL and 0 <= gy < GH and RUE[gx][gy]: n += 1
    return n > len(pts)*mini

arteres = [v for v in VOIES if v["rang"] == "artere"]
secondaires = 0
for v in arteres:
    pts = v["points"]
    tot = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    n = max(1, int(tot // 15))
    for i in range(1, n+1):
        dep = point_sur(v, i/(n+1))
        # on cherche l'artère voisine la plus proche, mais pas la sienne
        cands = []
        for w in arteres:
            if w is v: continue
            for t in (0.2, 0.4, 0.6, 0.8):
                q = point_sur(w, t)
                d = math.dist(dep, q)
                if 13 < d < 70: cands.append((d, q))
        if not cands: continue
        cands.sort()
        arr = cands[R.randrange(min(3, len(cands)))][1]
        ch = chemin_a(dep, arr, pente=1.5, reprise=1.35, sinuosite=1.5)
        if not ch or len(ch) < 4: continue
        ch = lisser(alleger(ch, 1.4), 2)
        if trop_pres(ch, 0.72): continue
        ch = [[round(p[0],1), round(p[1],1)] for p in ch]
        larg = 3.2
        poser(ch, larg)
        VOIES.append({"points": ch, "largeur": larg, "rang": "rue",
                      "raison": "Rue de desserte : elle tient deux artères ensemble"})
        secondaires += 1
print("   ", secondaires, "rues")

print("… les ruelles")
# Là où un bloc est trop profond pour qu'on atteigne le fond, un passage se fait.
def profondeur(gx, gy):
    """distance à la rue la plus proche, en unités, par balayage local"""
    for r in range(1, 12):
        for dx in range(-r, r+1):
            for dy in (-r, r):
                for a, b in ((gx+dx, gy+dy), (gx+dy, gy+dx)):
                    if 0 <= a < GL and 0 <= b < GH and RUE[a][b]: return r*PAS
    return 24

ruelles = 0
candidats = []
for gx in range(2, GL-2):
    for gy in range(2, GH-2):
        if not (LIBRE[gx][gy] and DEDANS[gx][gy]) or RUE[gx][gy]: continue
        if profondeur(gx, gy) >= 10:
            candidats.append((gx*PAS+1, gy*PAS+1))
R.shuffle(candidats)
for (x, y) in candidats:
    gx, gy = int(x)//PAS, int(y)//PAS
    if RUE[gx][gy] or profondeur(gx, gy) < 9: continue
    # on cherche les deux bouts de rue les plus proches, de part et d'autre
    meil = None
    for ang in range(0, 180, 15):
        a = math.radians(ang)
        bouts = []
        for s in (1, -1):
            for d in range(4, 46, 2):
                px, py = x + math.cos(a)*d*s, y + math.sin(a)*d*s
                g2 = (int(px)//PAS, int(py)//PAS)
                if not (0 <= g2[0] < GL and 0 <= g2[1] < GH): break
                if not (LIBRE[g2[0]][g2[1]] and DEDANS[g2[0]][g2[1]]): break
                if RUE[g2[0]][g2[1]]: bouts.append([px, py]); break
        if len(bouts) == 2:
            lg = math.dist(bouts[0], bouts[1])
            if meil is None or lg < meil[0]: meil = (lg, bouts)
    if not meil or meil[0] > 48: continue
    ch = chemin_a(meil[1][0], meil[1][1], pente=2.2, reprise=1.0, sinuosite=2.2)
    if not ch or len(ch) < 3: continue
    ch = lisser(alleger(ch, 1.2), 1)
    ch = [[round(p[0],1), round(p[1],1)] for p in ch]
    poser(ch, 2.0)
    VOIES.append({"points": ch, "largeur": 2.0, "rang": "ruelle",
                  "raison": "Ruelle : le fond du bloc s'est percé un passage"})
    ruelles += 1
print("   ", ruelles, "ruelles")

# ---------------------------------------------------------------------------
# LE PORT — une grammaire à part, parce qu'on y décharge
# ---------------------------------------------------------------------------
print("… le port")
QUAI = [[278,270],[314,266],[350,258]]
VOIES.append({"points": [[276,265],[312,261],[350,253]], "largeur": 5.5,
              "nom": "La rue des Quais", "rang": "artere",
              "raison": "Le long de l'eau : tout ce qu'on débarque doit filer quelque part"})
poser(VOIES[-1]["points"], 5.5)
TRAVERSES = []
for i in range(6):
    t = i/5.0
    x = 280 + t*62
    a = [x, 262 - t*8]
    b = list(a)
    for k in range(1, 20):                      # on monte jusqu'à sentir le mur
        q = [a[0] - k*0.25, a[1] - k]
        if dist_ligne(MUR_PTS, q[0], q[1]) < 4.0 or any(dedans(e, q[0], q[1]) for e in EAU):
            break
        b = q
    if math.dist(a, b) < 5: continue
    TRAVERSES.append((a, b))
    VOIES.append({"points": [a, b], "largeur": 2.4, "rang": "ruelle",
                  "raison": "Traverse d'entrepôt : du quai au mur, entre deux hangars"})
    poser([a, b], 2.4)

# ---------------------------------------------------------------------------
# 5. LES BÂTIMENTS — façade sur rue, obligatoire
# ---------------------------------------------------------------------------
print("… les façades")
OCC = []                 # occupation, en dur
def libre_pour(x, y, taille):
    if not (0 <= x < L and 0 <= y < H): return False
    gx, gy = int(x)//PAS, int(y)//PAS
    if not (0 <= gx < GL and 0 <= gy < GH): return False
    if not LIBRE[gx][gy]: return False
    if RUE[gx][gy]: return False
    for ox, oy, ot in OCC:
        if (x-ox)**2 + (y-oy)**2 < ((taille+ot)*0.46)**2: return False
    return True

def quartier_de(x, y):
    """trois grammaires : la ville haute, la ville basse, le dehors"""
    if not dedans(MURS, x, y): return "faubourg"
    if hauteur(x, y) > 7.5: return "haute"
    return "basse"

TAILLE = {"haute": (4.2, 5.6), "basse": (2.4, 3.4), "faubourg": (2.6, 3.8)}
ECART  = {"haute": 1.5, "basse": 0.5, "faubourg": 2.2}
RANGS  = {"artere": 3, "rue": 2, "ruelle": 2}

quartiers = {}
def poser_toit(zone, x, y, ang, t):
    quartiers.setdefault(zone, []).append(
        [round(x,1), round(y,1), int(ang) % 180 - (180 if int(ang) % 180 > 90 else 0), round(t,1)])
    OCC.append((x, y, t))


# les entrepôts du port : perpendiculaires au quai, gros, et posés les premiers
PORT_ZONE = [[266,246],[312,242],[356,232],[362,248],[352,266],[300,276],[266,270]]
for (a, b) in TRAVERSES:
    lg = math.dist(a, b) or 1
    ang = math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))
    for cote in (1, -1):
        for k in range(3):
            t = 5.4
            u = (k+0.55)/3.1
            x = a[0]+(b[0]-a[0])*u - (b[1]-a[1])/lg*(3.6)*cote
            y = a[1]+(b[1]-a[1])*u + (b[0]-a[0])/lg*(3.6)*cote
            if libre_pour(x, y, t): poser_toit("port", x, y, ang+90, t)

for v in sorted(VOIES, key=lambda w: -w["largeur"]):
    pts, larg = v["points"], v["largeur"]
    nrangs = RANGS.get(v["rang"], 2)
    for a, b in zip(pts, pts[1:]):
        seg = math.dist(a, b)
        if seg < 0.6: continue
        ux, uy = (b[0]-a[0])/seg, (b[1]-a[1])/seg
        nx, ny = -uy, ux
        ang = math.degrees(math.atan2(uy, ux))
        s = 0.0
        while s < seg:
            x0, y0 = a[0]+ux*s, a[1]+uy*s
            if dedans(PORT_ZONE, x0, y0): s += 3; continue
            zone = quartier_de(x0, y0)
            t0, t1 = TAILLE[zone]
            t = t0 + R.random()*(t1-t0)
            pose = False
            for cote in (1, -1):
                d = larg/2 + t*0.55
                for rang in range(nrangs):
                    x = x0 + nx*d*cote
                    y = y0 + ny*d*cote
                    if libre_pour(x, y, t):
                        poser_toit(zone, x, y, ang, t)
                        pose = True
                    d += t*0.86 + 0.5
            s += t + ECART[zone] + (0.6 if not pose else 0)
# les faubourgs : ils poussent LE LONG des routes, pas autour de la ville
DEHORS = [
    ([[89,140],[46,132],[0,124]], "route de la Rose", 26),
    ([[262,49],[266,22],[258,0]], "route royale", 18),
    ([[370,134],[404,122],[440,108]], "route de Rosby", 16),
    ([[159,245],[136,264],[104,278]], "route du gué", 18),
    ([[90,183],[54,196],[20,214]], "chemin du Lion", 12),
]
for pts, nom, n in DEHORS:
    tot = sum(math.dist(p, q) for p, q in zip(pts, pts[1:]))
    for i in range(n*3):
        u = (i/(n*3.0))**0.7          # serré près de la porte, clairsemé au loin
        p = point_sur({"points": pts}, min(0.99, u))
        seg_a, seg_b = pts[0], pts[1]
        ang = math.degrees(math.atan2(pts[-1][1]-pts[0][1], pts[-1][0]-pts[0][0]))
        for cote in (1, -1):
            if R.random() > 0.62 - u*0.35: continue
            a = math.radians(ang)
            x = p[0] - math.sin(a)*(5.5+R.random()*3)*cote
            y = p[1] + math.cos(a)*(5.5+R.random()*3)*cote
            if dedans(MURS, x, y): continue
            t = 2.6 + R.random()*1.4
            if libre_pour(x, y, t): poser_toit("faubourg", x, y, ang, t)

for z, p in quartiers.items(): print("   ", z, len(p), "toits")
json.dump({"voies": VOIES, "toits": quartiers}, io.open(os.path.join(SP, "tissu.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("total", sum(len(p) for p in quartiers.values()), "toits |", len(VOIES), "voies")
