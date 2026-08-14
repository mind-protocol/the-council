# -*- coding: utf-8 -*-
"""Port-Réal, densification métrique — les blocs se coupent, puis se remplissent.

    python scripts/monde/densifier.py

Le graphe issu de la carte 2D est un SQUELETTE : 61 m de rue par hectare, là où
une ville médiévale dense en porte 400 à 600. On ne redessine pas la carte pour
autant — on subdivise, en mètres, ce que le squelette a déjà découpé :

  1. on rastérise la voirie existante          (le vide qui reste = les blocs)
  2. on coupe chaque bloc trop profond          (perpendiculairement à son grand
     axe, en suivant la pente et le bruit — jamais au cordeau)
  3. on recommence jusqu'à ce qu'aucun point ne soit loin d'une voie
  4. on pose les parcelles À FAÇADE SUR RUE, rang par rang
  5. ce qui reste au cœur d'un bloc devient une COUR, avec son porche : c'est
     la couche L3, et elle tombe toute seule de la structure.

Chaque coupe garde sa raison : profondeur, accès aux cours, ou pente.
"""
import json, math, io, os, sys, random
from collections import deque

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, ICI)
from echelle import (METRE_PAR_UNITE as MU, mx, my, ux, uy, LARGEUR, gabarit, BATI, GRAIN,
                     polygone_reel, grain, rangs, recul, BLOC_MIN, RECUL, ENTRE_RANGS,
                     TROTTOIR, MARGE_RECUL, ilot_min, ilot_cible, dos, ANNEAU,
                     hors_anneau, loin_du_mur)

R = random.Random(129032301)
MONDE = os.path.join(RACINE, "monde")
G = json.load(io.open(os.path.join(MONDE, "portreal.graph.json"), encoding="utf-8"))
T = json.load(io.open(os.path.join(MONDE, "portreal.terrain.json"), encoding="utf-8"))
CARTE = json.load(io.open(os.path.join(RACINE, "etat", "villes", "port-real.json"), encoding="utf-8"))

# Ce script AJOUTE au graphe et le réécrit : le relancer sur sa propre sortie
# empilerait une seconde fois toutes les voies engendrées. On le dit ici plutôt
# que de le laisser mourir sur un KeyError trois minutes plus tard.
if "_densifie" in G or "batiments" not in G:
    sys.exit("Ce graphe est déjà densifié. Relance d'abord "
             "« python scripts/monde/graphe.py » pour repartir du squelette.")

CEL = 3.0                       # la grille de travail, en mètres
LX = int(T["nx"]*T["res_m"]/CEL)+1
LY = int(T["ny"]*T["res_m"]/CEL)+1
RES, Zg = T["res_m"], T["z"]
NXg, NYg = T["nx"], T["ny"]

def zsol(x, y):
    i, j = min(NXg-2, max(0, int(x/RES))), min(NYg-2, max(0, int(y/RES)))
    tx, ty = (x-i*RES)/RES, (y-j*RES)/RES
    a = Zg[j][i]*(1-tx) + Zg[j][i+1]*tx
    b = Zg[j+1][i]*(1-tx) + Zg[j+1][i+1]*tx
    return a*(1-ty) + b*ty

def boite_de(poly):
    return (min(p[0] for p in poly), min(p[1] for p in poly),
            max(p[0] for p in poly), max(p[1] for p in poly))
def dans_liste(polys, x, y):
    """la boîte englobante d'abord : elle écarte 95 % des cas sans calcul"""
    for (b, p) in polys:
        if b[0] <= x <= b[2] and b[1] <= y <= b[3] and dedans(p, x, y): return True
    return False

def dedans(poly, x, y):
    r = False; j = len(poly)-1
    for i in range(len(poly)):
        if (poly[i][1] > y) != (poly[j][1] > y) and \
           x < (poly[j][0]-poly[i][0])*(y-poly[i][1])/(poly[j][1]-poly[i][1])+poly[i][0]:
            r = not r
        j = i
    return r

# --- le domaine constructible : dans les murs, hors de l'eau et du bâti -----
print("… le domaine")
MURS_U = [p for s in CARTE["sol"] if s["genre"] == "mur" and "largeur" not in s for p in s["points"]]
# L'anneau vit dans `echelle.py` : `graphe.py` en a besoin aussi, et un mur
# recopié à deux endroits est un mur qui finit par passer à deux endroits.
EAU_U = [s["points"] for s in CARTE["sol"] if s["genre"] == "eau"]
BATI_U = [polygone_reel(s.get("nom",""), s["points"]) for s in CARTE["sol"]
          if s["genre"] == "mur" and 0 < s.get("largeur", 0) <= 4]
PLACES_U = [polygone_reel(s.get("nom",""), s["points"]) for s in CARTE["sol"]
            if s["genre"] == "champ" and s.get("nom", "").startswith(("La grande place", "Le march", "L'aire"))]
GREVE_U = [s["points"] for s in CARTE["sol"] if s["genre"] in ("greve", "marais")]

EXCLU = [(boite_de(p), p) for p in (EAU_U + BATI_U + PLACES_U + GREVE_U)]
BA = boite_de(ANNEAU)
LIBRE = bytearray(LX*LY)        # 1 = on peut y bâtir ou y passer une rue
DANS  = bytearray(LX*LY)        # 1 = intra-muros
def idx(i, j): return j*LX + i
for j in range(LY):
    for i in range(LX):
        wx, wy = (i+0.5)*CEL, (j+0.5)*CEL
        cx, cy = ux(wx), uy(wy)
        if dans_liste(EXCLU, cx, cy): continue
        LIBRE[idx(i, j)] = 1
        DANS[idx(i, j)] = 1 if (BA[0] <= cx <= BA[2] and BA[1] <= cy <= BA[3]
                                and dedans(ANNEAU, cx, cy)) else 0
print("   %d × %d cases de %.0f m" % (LX, LY, CEL))

# --- LE MUR, ET LUI SEUL, EST INFRANCHISSABLE -------------------------------
# On bouclait sur les pans de mur en SAUTANT tout ce qui portait une `largeur`,
# c'est-à-dire les sept portes. Or une porte du dessin ne couvre pas une
# ouverture de cinq mètres : elle couvre TOUT L'INTERVALLE entre deux pans,
# soit cent quatre-vingt-dix à deux cent vingt mètres. La muraille avait donc
# sept brèches de deux cents mètres — et une de QUATRE CENT CINQUANTE-NEUF
# entre le mur de la rivière et le mur du midi, que nulle porte ne comble.
# Près de deux kilomètres de rien, par où la ville coulait dehors.
#
# On prend donc l'ANNEAU, qui est le même tracé mais FERMÉ (c'est déjà lui qui
# dit le dedans du dehors, quelques lignes plus haut), on le mure d'un bout à
# l'autre, et l'on reperce ensuite chaque porte à sa vraie ouverture.
def _murer(A, B, libre):
    n = max(1, int(math.dist(A, B)/1.5))
    for k in range(n+1):
        t = k/n
        wx, wy = A[0]+(B[0]-A[0])*t, A[1]+(B[1]-A[1])*t
        for di in range(-2, 3):
            for dj in range(-2, 3):
                i, j = int(wx/CEL)+di, int(wy/CEL)+dj
                if 0 <= i < LX and 0 <= j < LY: LIBRE[idx(i, j)] = libre

ANNEAU_M = [(mx(p[0]), my(p[1])) for p in ANNEAU]
for a, b in zip(ANNEAU_M, ANNEAU_M[1:] + ANNEAU_M[:1]):
    _murer(a, b, 0)

# …et l'on reperce les portes. `PORTE_OUVERTURE` est ce par quoi passe une
# charrette ; on ouvre un peu plus large que la charrette pour que la voirie
# engendrée trouve où passer, mais deux cents mètres, non.
OUVERTURE = 11.0
perces = 0
for s in CARTE["sol"]:
    if s["genre"] != "mur" or s.get("largeur") != 6: continue
    ps = s["points"]
    cx = sum(mx(q[0]) for q in ps)/len(ps)
    cy = sum(my(q[1]) for q in ps)/len(ps)
    r = int(OUVERTURE/CEL)+1
    ci, cj = int(cx/CEL), int(cy/CEL)
    for di in range(-r, r+1):
        for dj in range(-r, r+1):
            i, j = ci+di, cj+dj
            if 0 <= i < LX and 0 <= j < LY and                math.hypot((i+.5)*CEL-cx, (j+.5)*CEL-cy) <= OUVERTURE:
                LIBRE[idx(i, j)] = 1
    perces += 1
print("   muraille fermée, %d portes percées à %.0f m" % (perces, OUVERTURE))

# --- la voirie existante ----------------------------------------------------
RUE = bytearray(LX*LY)
def poser(trace, larg):
    r = max(larg/2, CEL*0.5)
    for a, b in zip(trace, trace[1:]):
        n = max(1, int(math.dist((a[0],a[1]), (b[0],b[1]))/(CEL*0.5)))
        for k in range(n+1):
            t = k/n
            wx, wy = a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t
            ri = int(r/CEL)+1
            ci, cj = int(wx/CEL), int(wy/CEL)
            for di in range(-ri, ri+1):
                for dj in range(-ri, ri+1):
                    i, j = ci+di, cj+dj
                    if 0 <= i < LX and 0 <= j < LY and \
                       math.hypot((i+.5)*CEL-wx, (j+.5)*CEL-wy) <= r:
                        RUE[idx(i, j)] = 1
for e in G["aretes"]:
    if e["couche"] == "L1-surface":
        poser(e["trace"], e["largeur_m"])

# --- le quartier d'un point : on hérite de la carte 2D ---------------------
CASES_Q = {}
for s in CARTE["sol"]:
    if s["genre"] != "village": continue
    for p in s["points"]:
        wx, wy = mx(p[0]), my(p[1])
        CASES_Q.setdefault((int(wx//120), int(wy//120)), []).append((wx, wy, s["nom"]))
def quartier(wx, wy):
    meil, best = "La ville", 1e18
    ci, cj = int(wx//120), int(wy//120)
    for di in range(-2, 3):
        for dj in range(-2, 3):
            for (x, y, n) in CASES_Q.get((ci+di, cj+dj), ()):
                d = (x-wx)**2 + (y-wy)**2
                if d < best: best, meil = d, n
    return meil

# ---------------------------------------------------------------------------
# 2. LES BLOCS, ET LEURS COUPES
# ---------------------------------------------------------------------------
print("… les blocs")
def blocs():
    vu = bytearray(LX*LY)
    out = []
    for j0 in range(LY):
        for i0 in range(LX):
            k0 = idx(i0, j0)
            if vu[k0] or not LIBRE[k0] or RUE[k0] or not DANS[k0]: continue
            q, cells = deque([(i0, j0)]), []
            vu[k0] = 1
            while q:
                i, j = q.popleft()
                cells.append((i, j))
                for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
                    a, b = i+di, j+dj
                    if 0 <= a < LX and 0 <= b < LY:
                        k = idx(a, b)
                        if not vu[k] and LIBRE[k] and not RUE[k] and DANS[k]:
                            vu[k] = 1; q.append((a, b))
            if len(cells) >= 4: out.append(cells)
    return out

def axe(cells):
    """PCA : le grand axe du bloc, et son étendue de part et d'autre"""
    n = len(cells)
    mx_, my_ = sum(c[0] for c in cells)/n, sum(c[1] for c in cells)/n
    sxx = syy = sxy = 0.0
    for i, j in cells:
        dx, dy = i-mx_, j-my_
        sxx += dx*dx; syy += dy*dy; sxy += dx*dy
    sxx /= n; syy /= n; sxy /= n
    th = 0.5*math.atan2(2*sxy, sxx-syy)
    ux_, uy_ = math.cos(th), math.sin(th)
    proj = [( (i-mx_)*ux_ + (j-my_)*uy_ , (i-mx_)*(-uy_) + (j-my_)*ux_ ) for i, j in cells]
    l = (max(p[0] for p in proj) - min(p[0] for p in proj)) * CEL
    w = (max(p[1] for p in proj) - min(p[1] for p in proj)) * CEL
    return (mx_, my_), (ux_, uy_), l, w

# La profondeur d'îlot ne vient plus d'une constante : elle vient du QUARTIER,
# comme le gabarit des maisons (echelle.GRAIN). C'est ce qui fait qu'un plan de
# Port-Réal se lit sans légende — la trame du Culpucier n'est pas celle de la
# ville haute, et c'est visible avant qu'on ait lu un seul nom.
MAX_BLOC_DEF = 42.0        # pour un bloc dont on ne sait pas dire le quartier
TRAVERSE = 125.0           # au-delà, un îlot se traverse : c'est ce qui casse les lanières
# Une coupe DIVISE LA LARGEUR PAR DEUX. Pour que les deux moitiés portent
# encore deux fronts et une cour, il faut donc entrer dans la coupe avec plus
# du double de l'îlot minimal — et une marge, parce qu'un îlot réel n'est pas
# un rectangle. Mesuré : c'est le réglage qui remplit le mieux le front de rue
# (51 %) sans vider le cœur des îlots.
AISANCE = 1.6              # ce qu'il reste à chaque moitié, en îlots minimaux
NEUVES = []                # les voies engendrées ici

def composantes(cells):
    """Après une coupe, un « côté » peut contenir plusieurs blocs bien distincts.
    Les mesurer ensemble donne un grand axe qui n'existe nulle part, et l'on
    recoupe indéfiniment un bloc déjà assez petit. On les sépare d'abord."""
    dedans_ = set(cells)
    out = []
    while dedans_:
        d0 = dedans_.pop()
        q, comp = deque([d0]), [d0]
        while q:
            i, j = q.popleft()
            for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
                v = (i+di, j+dj)
                if v in dedans_:
                    dedans_.discard(v); comp.append(v); q.append(v)
        out.append(comp)
    return out

def couper(cells, prof=0):
    for comp in composantes(cells):
        couper_un(comp, prof)

RENONCE = __import__("collections").Counter()
LARG_FIN = __import__("collections").Counter()
LARG_AIRE = __import__("collections").Counter()
AIRE_NON = __import__("collections").Counter()

def profondeur_coeur(cells):
    """La distance, en mètres, du point le plus ENFONCÉ du bloc à son bord, et
    ce point. C'est la seule mesure qui dise si un îlot a un cœur.

    LA LARGEUR MOYENNE MENT, et c'est elle qui a laissé les terrains vagues.
    `aire/L` répartit la surface sur toute la longueur : un îlot en coin, deux
    cents mètres de base et une pointe, sort à soixante-dix de moyenne et passe
    le test — pendant que sa base, elle, n'est desservie par rien. Mesuré sur
    Port-Réal : cent dix-neuf hectares intra-muros à plus de seize mètres de
    toute rue, c'est-à-dire hors d'atteinte de la moindre façade. Trois de ces
    cœurs faisaient à eux seuls vingt-quatre, dix-huit et dix-sept hectares —
    les trous qu'on voyait sur le plan.

    On ne mesure donc plus une moyenne, on cherche le point le plus loin de
    tout bord : c'est lui qui décide, et c'est par lui qu'on coupera."""
    dedans_ = set(cells)
    d = {}
    q = deque()
    for c in cells:
        if any((c[0]+a, c[1]+b) not in dedans_
               for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            d[c] = 0; q.append(c)
    loin = (0, cells[0])
    while q:
        c = q.popleft()
        if d[c] > loin[0]: loin = (d[c], c)
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = (c[0]+a, c[1]+b)
            if v in dedans_ and v not in d:
                d[v] = d[c]+1; q.append(v)
    return loin[0]*CEL, loin[1]


def couper_un(cells, prof=0):
    """coupe un bloc perpendiculairement à son grand axe, et recommence"""
    def _non(motif):
        RENONCE[motif] += 1
        AIRE_NON[motif] += len(cells)*CEL*CEL
    if len(cells) < 10 or prof > 16:
        _non("trop petit / trop profond"); return
    (cx, cy), (ax, ay), L, W = axe(cells)
    # le quartier se lit AU CENTRE du bloc, une fois — pas à chaque case
    q_ = quartier((cx+0.5)*CEL, (cy+0.5)*CEL)
    _, bloc_max = grain(q_)
    # ON NE COUPE QUE SI LES DEUX MOITIÉS RESTENT HABITABLES. Couper divise la
    # largeur par deux : un seuil posé sur la largeur AVANT la coupe laisse donc
    # des îlots deux fois trop minces. Le seuil est ici sur le RÉSULTAT.
    bloc_max = max(BLOC_MIN, 2*AISANCE*ilot_min(q_))
    # …et la largeur se mesure par l'AIRE SUR LA LONGUEUR, pas par l'étendue de
    # l'ACP. Après deux ou trois coupes un îlot n'est plus un rectangle : son
    # étendue en travers compte le plus large redan et surestime la largeur
    # moyenne de moitié — donc on recoupait des îlots déjà trop minces.
    aire = len(cells)*CEL*CEL
    if L > 1: W = min(W, aire/L)

    # SUR QUEL AXE ON COUPE. C'était le trou de toute la ville : on comparait
    # `bloc_max` au GRAND axe, alors que la constante parle de la profondeur —
    # « au-delà, le fond du bloc n'est plus accessible ». Un îlot de deux cents
    # mètres de long sur trente de large est l'îlot médiéval par excellence ;
    # l'ancien test le débitait en quatre. D'où 530 m de rue par hectare, deux
    # rues distantes de dix-neuf mètres, et un front sur trois seulement
    # constructible — le reste de la façade donnait dans le vide.
    #
    #   trop PROFOND (W)  → on fend DANS LA LONGUEUR : une venelle de fond
    #   trop LONG (L)     → on TRAVERSE, et bien plus rarement : c'est une
    #                       affaire de circulation, pas d'accès aux cours
    # ON NE COUPE PAS TOUJOURS DANS LE MÊME SENS, et c'était toute la
    # prévisibilité du plan. `fendre` suit le GRAND AXE ; chaque moitié hérite
    # du même grand axe, donc les coupes successives sortent PARALLÈLES, à
    # intervalle presque constant — et des quartiers entiers se peignent en
    # bandes. Une ville qui s'est faite toute seule ne se lit pas au peigne.
    #
    # Trois grains de sable, et ils suffisent :
    #   • le seuil varie d'un îlot à l'autre, donc les bandes n'ont plus toutes
    #     la même largeur ;
    #   • la traverse tombe bien plus tôt, et au hasard : c'est elle qui casse
    #     les longues lanières en pâtés ;
    #   • quand les deux coupes sont possibles, on TIRE laquelle, au lieu de
    #     toujours fendre en premier.
    bloc_max *= 0.72 + R.random()*0.56
    traverse = TRAVERSE * (0.7 + R.random()*0.6)
    # …ET LE CŒUR, qui prime sur la moyenne. `ilot_cible` dit la largeur qu'un
    # îlot doit AVOIR : deux reculs, deux fronts complets dos à dos, et la cour
    # au milieu. Sa moitié est donc, exactement, ce qu'une façade peut atteindre
    # depuis la rue. Au-delà, le sol n'est plus bâtissable par personne : c'est
    # un terrain vague, et il faut le percer. Ce seuil-là ne se moyenne pas.
    # …MAIS ON NE PERCE PAS UN CŒUR SI LES DEUX MOITIÉS N'EN VALENT PLUS RIEN.
    # Le point le plus enfoncé est à `coeur_m` de chaque bord : couper par lui
    # laisse donc deux bandes d'environ `coeur_m` de large. Sous `ilot_min`,
    # elles ne portent plus deux fronts dos à dos, et l'on retombe exactement
    # dans le défaut que le fichier a déjà connu — cinq cents mètres de rue par
    # hectare, des rues à dix-neuf mètres l'une de l'autre, et un front sur
    # trois seulement bâtissable. Mesuré en le faisant : dix mille maisons
    # perdues d'un coup. Ce qui reste hors d'atteinte sous ce seuil n'est pas un
    # terrain vague, c'est une cour — et `cours()` la ramassera plus bas.
    # …MAIS UN ÎLOT ORDINAIRE A LE DROIT D'AVOIR UNE COUR. `GRAIN` donne la
    # profondeur de la trame du quartier — cinquante-six mètres en ville, vingt-
    # six au Culpucier —, et un îlot bien formé de cette profondeur a donc un
    # cœur à la moitié, que nulle façade n'atteint. C'est une cour, pas un
    # terrain vague, et `cours()` la ramasse plus bas. Percer là, c'est percer
    # TOUS les îlots de la ville : mesuré en le faisant, la voirie passe de 366
    # à 445 m par hectare et dix mille maisons s'en vont en chaussée.
    #
    # Ce qu'on cherche est l'ANORMAL : le cœur une fois et demie plus profond
    # que celui de la trame. Ceux-là ne sont pas des cours, ce sont les vingt-
    # quatre, dix-huit et dix-sept hectares qu'on voyait en blanc sur le plan.
    _, trame = grain(q_)
    coeur_m, loin = profondeur_coeur(cells)
    creux = coeur_m > max(trame*0.75, ilot_min(q_))
    fendre = W >= bloc_max or creux
    croiser = L >= traverse and not creux
    if fendre and croiser:
        # on fend plus souvent qu'on ne traverse : une traverse coûte une rue
        # de plus, et à 50/50 la ville passait de 333 à 622 m de voirie par
        # hectare — vingt et un bâtiments à l'hectare perdus en chaussée.
        fendre = R.random() < 0.78
        croiser = not fendre
    if fendre:
        ux_, uy_ = -ay, ax          # on avance en travers…
        vx_, vy_ = ax, ay           # …et la coupe suit le grand axe
        etendue, portee = L, W
    elif croiser:
        ux_, uy_ = ax, ay
        vx_, vy_ = -ay, ax
        etendue, portee = W, L
    else:
        _non("ni trop large ni trop long")
        LARG_FIN[min(200, int(W/10)*10)] += 1
        LARG_AIRE[min(200, int(W/10)*10)] += len(cells)*CEL*CEL
        return
    imin = min((i-cx)*ux_ + (j-cy)*uy_ for i, j in cells)
    imax = max((i-cx)*ux_ + (j-cy)*uy_ for i, j in cells)
    # ±11 % autour du milieu ne casse pas une trame : les bandes restent
    # jumelles. À ±23 %, deux venelles voisines n'ont plus la même largeur et
    # l'œil cesse de lire une régularité.
    t = 0.5 + (R.random()-0.5)*0.46
    s = imin + (imax-imin)*t
    # QUAND C'EST LE CŒUR QUI COMMANDE, LA COUPE PASSE PAR LUI. Une coupe tirée
    # au milieu statistique du bloc peut très bien longer le terrain vague sans
    # jamais l'ouvrir, et l'on recoupe alors trois fois pour rien.
    if creux:
        s = (loin[0]-cx)*ux_ + (loin[1]-cy)*uy_
    px, py = cx + ux_*s, cy + uy_*s
    nx, ny = vx_, vy_
    ax, ay = ux_, uy_               # l'axe d'avance, pour le serpentement
    W = portee                      # ce que la coupe doit franchir
    # on courbe la coupe : bruit + attirance pour la courbe de niveau
    demi = etendue/CEL/2 + 4
    # Le serpentement se compte en MÈTRES, pas en cases : sinon il change d'échelle
    # avec la trame, et une ruelle de vingt mètres gribouille sur cinq.
    # …et elle se mesure sur CE QUE LA COUPE PARCOURT, pas sur la largeur qu'elle
    # franchit. `min(4,5 ; W·0,11)` plafonnait l'écart à quatre mètres cinquante
    # — sur un tracé de trois cents mètres, c'est un fil à plomb. D'où le défaut
    # qu'on voit sur le plan : des quartiers entiers peignés en droites
    # parallèles, la signature d'une machine. Une rue qui contourne un enclos
    # s'en écarte de quinze mètres, pas de quatre.
    ampl_m = min(4.5, W*0.11)
    ampl = ampl_m/CEL
    # L'ARC SE MESURE SUR CE QUE LA COUPE PARCOURT, LE GRAIN NON. Tout tirer de
    # `ampl` était le nœud : monter l'amplitude pour que la rue cesse d'être un
    # fil à plomb montait AUSSI le tremblement par point, et un front posé sur
    # une chaussée qui frissonne s'évente — les parcelles se refusent l'une
    # l'autre. Mesuré : dix bâtiments à l'hectare perdus, pour une courbure qui
    # ne se voyait qu'à la loupe.
    #
    # On sépare donc les deux. Le grain fin reste ce qu'il était, local et
    # petit. L'ARC, lui, se prend sur la longueur : seize mètres d'écart sur
    # trois cents, c'est un rayon de sept cents mètres — l'œil voit une rue qui
    # tourne, la maison ne voit qu'une droite.
    courbe = min(2.5 + 0.05*etendue, 16.0)/CEL
    # UN C, PAS UN S. Le serpentement était `sin(k·CEL·0,055 + …)` : une
    # sinusoïde de période 2π/0,055, soit CENT QUATORZE MÈTRES, la même pour
    # toutes les coupes de la ville. Toutes les venelles ondulaient donc à la
    # même longueur d'onde, en S réguliers — la signature d'un générateur, pas
    # d'une ville. Une rue qui s'est faite à pied ne serpente pas : elle
    # contourne UNE chose — un rocher, un enclos, un jardin de couvent — et ce
    # qu'elle en garde est un arc unique, tenu sur toute sa longueur.
    #
    # On tire donc, par coupe et non plus une fois pour toutes : un ARC dominant
    # (une demi-onde d'un bout à l'autre, sens et amplitude au hasard), une
    # harmonique faible et déphasée pour qu'il ne soit pas un arc de compas, et
    # un grain fin par-dessus.
    arc = (R.random()*2 - 1) * courbe
    h2 = (R.random()*2 - 1) * ampl * 0.4
    ph2 = R.random() * 6.283
    per2 = 1.3 + R.random()*1.9          # une à trois ondes sur toute la coupe
    ks = list(range(-int(demi), int(demi)+1))
    pts = []
    for kk, k in enumerate(ks):
        t = kk / max(1, len(ks)-1)
        wob = (arc*math.sin(math.pi*t)
               + h2*math.sin(2*math.pi*per2*t + ph2)
               + (R.random()-0.5)*ampl*0.3)
        i = px + nx*k + ax*wob
        j = py + ny*k + ay*wob
        pts.append(((i+0.5)*CEL, (j+0.5)*CEL))
    # une coupe qui sort du domaine ou qui ne touche aucune rue aux deux bouts
    # n'est pas une rue : c'est une impasse, on la refuse
    def dansdom(p):
        i, j = int(p[0]/CEL), int(p[1]/CEL)
        return 0 <= i < LX and 0 <= j < LY and LIBRE[idx(i, j)]
    # ON NE PERCE QUE DANS L'ÎLOT QU'ON COUPE. Le tracé n'était borné que par le
    # DOMAINE — or le domaine, c'est toute la carte hors eau : une coupe partait
    # donc du cœur d'un îlot, ressortait de l'autre côté de la rue d'en face,
    # traversait la muraille et courait dans la campagne. Mesuré : 3,2 km de
    # ruelles entièrement hors les murs, et c'est ce qu'on voyait sur le plan —
    # les peignes de droites qui ne s'arrêtaient pas au rempart.
    #
    # Une coupe est une rue INTÉRIEURE. Elle part du cœur, elle avance tant
    # qu'elle est dans le bloc, et elle s'arrête un pas après en être sortie —
    # ce pas est ce qui lui fait toucher la chaussée qui borde l'îlot.
    du_bloc = set(cells)
    def dansbloc(p):
        return (int(p[0]/CEL), int(p[1]/CEL)) in du_bloc
    mid = len(pts)//2
    if not dansbloc(pts[mid]):
        pres = [k for k in range(len(pts)) if dansbloc(pts[k])]
        if not pres:
            _non("coupe hors du bloc"); return
        mid = min(pres, key=lambda k: abs(k-mid))
    # …et « un pas après » veut dire JUSQU'À LA CHAUSSÉE, pas deux cases au
    # jugé. Une coupe qui s'arrête à la dernière case du bloc ne débouche sur
    # rien : les deux moitiés restent cousues par le bout, le remplissage les
    # revoit comme un seul îlot, et le trou revient. On sort donc du bloc
    # jusqu'à toucher la rue qui le borde — et guère plus loin, sans quoi l'on
    # repart dans la campagne.
    DEBORD = 8                       # vingt-quatre mètres : de quoi franchir une rue
    def sortie(k, sens):
        for n in range(1, DEBORD+1):
            v = k + sens*n
            if not (0 <= v < len(pts)): return k + sens*(n-1)
            i, j = int(pts[v][0]/CEL), int(pts[v][1]/CEL)
            if not (0 <= i < LX and 0 <= j < LY) or not LIBRE[idx(i, j)]:
                return v                       # le mur, ou l'eau : on s'arrête là
            if RUE[idx(i, j)]: return v        # la chaussée : on l'a touchée
        return k + sens*DEBORD
    g_ = d_ = mid
    while g_ > 0 and dansbloc(pts[g_-1]): g_ -= 1
    while d_ < len(pts)-1 and dansbloc(pts[d_+1]): d_ += 1
    g_, d_ = sortie(g_, -1), sortie(d_, +1)
    pts = pts[max(0, g_):d_+1]
    # ON TRONQUE, ON NE FILTRE PAS. Retirer les points hors domaine au lieu de
    # couper la polyligne laisse un SAUT : le dernier point dedans se relie en
    # ligne droite au premier point de l'autre côté, et la venelle traverse la
    # muraille d'un trait pour finir dans les champs. C'était ça, les tronçons
    # rectilignes qui sortent de la ville et ne mènent nulle part — et c'était
    # aussi une bonne part de ce qui paraissait « trop droit » : un saut est
    # toujours une droite. On garde donc la plus longue suite CONTINUE.
    suites, cur = [], []
    for q in pts:
        if dansdom(q):
            cur.append(q)
        else:
            if cur: suites.append(cur)
            cur = []
    if cur: suites.append(cur)
    pts = max(suites, key=len) if suites else []
    if len(pts) < 3:
        _non("coupe hors du domaine"); return
    # le rang se lit à la longueur RÉELLEMENT percée, pas au compteur
    rang = "rue" if etendue > 130 else "ruelle"
    larg = LARGEUR["rue"] if etendue > 130 else (2.6 if etendue > 75 else 2.0)
    raison = ("Une traverse : l'îlot courait trop loin sans qu'on puisse le franchir."
              if not fendre else
              "Le bloc était trop profond pour qu'on en atteigne le fond."
              if etendue > 75 else
              "Passage percé à la longue par ceux qui coupaient au plus court.")
    pente = abs(zsol(pts[0][0], pts[0][1]) - zsol(pts[-1][0], pts[-1][1])) / max(1, math.dist(pts[0], pts[-1]))
    if pente > 0.18:
        rang, larg = "escalier", 3.0
        raison = "La pente y interdit la charrette : le passage s'est marché en degrés."
    # on regarde d'abord si la coupe sépare vraiment : une coupe qui laisse un
    # côté presque intact n'a rien coupé, et la relancer tourne en rond
    # De part et d'autre de la coupe : on projette sur l'axe D'AVANCE, pas sur
    # la direction de la coupe — projeter le long de la ligne trie les cases
    # par leur position SUR la coupe, ce qui ne sépare rien.
    g, d = [], []
    for i, j in cells:
        c = (i-px)*ax + (j-py)*ay
        (g if c < 0 else d).append((i, j))
    if min(len(g), len(d)) < 6 or max(len(g), len(d)) > len(cells)*0.88:
        _non("la coupe ne separe pas"); return
    NEUVES.append({"trace": [[round(p[0],1), round(p[1],1)] for p in pts],
                   "largeur_m": larg, "genre": rang, "raison": raison, "prof": prof})
    poser([(p[0], p[1]) for p in pts], larg)
    g = [c for c in g if not RUE[idx(c[0], c[1])]]
    d = [c for c in d if not RUE[idx(c[0], c[1])]]
    couper(g, prof+1); couper(d, prof+1)

B = blocs()
print("   %d blocs au départ (le plus gros : %d cases)" % (len(B), max(len(b) for b in B)))
for b in sorted(B, key=len, reverse=True):
    couper(b)
print("   %d voies engendrées" % len(NEUVES))
print("   largeur des ilots NON coupes :")
for w in sorted(LARG_FIN):
    print("      %3d-%3d m : %5d ilots, %6.0f ha" % (w, w+10, LARG_FIN[w], LARG_AIRE[w]/1e4))
for m, n in RENONCE.most_common():
    print("   renonce: %-28s %6d fois, %8.0f ha concernes"
          % (m, n, AIRE_NON[m]/1e4))

# ---------------------------------------------------------------------------
# 3. LES PARCELLES — façade sur rue, obligatoire
# ---------------------------------------------------------------------------
print("… les parcelles")
# UN FAUBOURG S'ÉTEINT, IL NE COURT PAS JUSQU'AU BORD DU DESSIN. Les routes de
# la carte sortent de la ville et vont au cadre : la route de la Rose, la route
# royale, celle de Rosby. On bordait de maisons TOUTE leur longueur, des deux
# côtés, à quatre mètres de façade — d'où onze cents mètres de rue continue en
# rase campagne, qui s'arrêtaient net sur le bord du plan. C'est ce qu'on voyait
# dépasser du rempart.
#
# Un faubourg se serre contre sa porte, parce que c'est la porte qui le fait
# vivre, et il se défait ensuite. Intra-muros, rien ne change : on bâtit partout.
FAUBOURG_PLEIN = 150.0     # jusque-là, un faubourg est un faubourg
FAUBOURG_FIN = 450.0       # au-delà, c'est la campagne, et elle est vide
def faubourg_tient(wx, wy):
    """Ce point, en mètres, porte-t-il encore une maison ?"""
    cx, cy = ux(wx), uy(wy)
    if not hors_anneau(cx, cy): return True
    d = loin_du_mur(cx, cy)
    if d <= FAUBOURG_PLEIN: return True
    if d >= FAUBOURG_FIN: return False
    return R.random() > ((d-FAUBOURG_PLEIN)/(FAUBOURG_FIN-FAUBOURG_PLEIN))**0.75

# --- l'encombrement, dans le repère de la parcelle -------------------------
# LE PIÈGE, et il tenait toute la ville : le test d'avant était un DISQUE de
# rayon 0,30·(t+t'), avec t = max(façade, profondeur). Or la parcelle voulue ici
# est étroite et PROFONDE — donc t était la profondeur, et le disque interdisait
# le voisin le long de la façade, là précisément où on le veut collé. Au
# Culpucier (façade 4,4 m, profondeur 7,5 m) le rayon valait 4,5 m pour un pas
# de 4,4 : le quartier le plus dense était le seul où le voisin était refusé.
#
# On teste donc les deux emprises dans le repère DU CANDIDAT : quasi rien le
# long de la façade (le mur est mitoyen), un vrai écart en travers (il faut
# pouvoir passer entre deux rangs dos à dos).
# Ce qui sépare deux rangs qui se tournent le dos n'est PAS une constante : il
# vaut zéro au Culpucier et six mètres au faubourg. Voir `echelle.dos()`. La
# valeur ci-dessous ne sert plus que de garde-fou quand on n'a pas de quartier.
DOS = 0.8
TOL = 0.05                 # deux maisons qui se touchent JUSTE ne se refusent pas
BOITE = 12.0               # le pas du casier de recherche, en mètres
COLLAGE = 1.2              # au-delà de ce jour, on n'étire plus : c'est une venelle

OCC = {}
def _casiers(x, y, r):
    for i in range(int((x-r)//BOITE), int((x+r)//BOITE)+1):
        for j in range(int((y-r)//BOITE), int((y+r)//BOITE)+1):
            yield (i, j)

def case_libre(x, y):
    i, j = int(x/CEL), int(y/CEL)
    return 0 <= i < LX and 0 <= j < LY and LIBRE[idx(i, j)] and not RUE[idx(i, j)]

F_MINI, P_MINI = 2.5, 3.5  # sous quoi ce n'est plus une maison mais un appentis

def _voisins(x, y, f, p, cap, dos_=DOS):
    """Les emprises voisines qui peuvent gêner, dans MON repère.

    Rend, par voisin, l'écart le long de la façade et vers le fond, et sa
    demi-emprise projetée sur mes axes — un voisin peut être de biais, deux
    rues qui se croisent n'ayant pas le même cap.
    """
    a = math.radians(cap)
    vx, vy = math.cos(a), math.sin(a)
    r = 0.5*math.hypot(f, p) + dos_ + 2.0
    for c in _casiers(x, y, r):
        for (ox, oy, ohf, ohp, wx, wy) in OCC.get(c, ()):
            dl = (ox-x)*vx + (oy-y)*vy
            dt = (oy-y)*vx - (ox-x)*vy
            co = abs(wx*vx + wy*vy)
            si = abs(wy*vx - wx*vy)
            yield dl, dt, ohf*co + ohp*si, ohf*si + ohp*co

# --- LA CHAUSSÉE, AU CENTIMÈTRE ---------------------------------------------
# La grille de travail fait TROIS MÈTRES, et le sondage ne prenait que six
# points à ±0,48 de l'emprise : jamais les vrais coins, et une résolution plus
# grosse qu'une ruelle. Une façade débordait donc couramment d'un mètre sur la
# chaussée — 17,9 % des arêtes de surface ont leur axe qui clippe une maison, et
# un trajet passe 3 % de sa longueur DANS du bâti pour cette seule raison.
#
# On double donc le test de grille par un test EXACT contre les tronçons de
# voirie voisins : distance du segment au rectangle, comparée au demi-gabarit
# de la chaussée. Les deux ensembles sont convexes, donc s'ils sont disjoints le
# couple le plus proche met en jeu un sommet de l'un — il suffit de prendre le
# minimum sur les quatre coins et les deux bouts, après avoir écarté le cas où
# ils se croisent.
# UNE FAÇADE MÉDIÉVALE MORD LA RUE, et c'est ce qui fait une ruelle étroite :
# les murs débordent, les encorbellements avancent au premier, les étals
# colonisent le pas de porte. La tolérance zéro est un règlement moderne — elle
# a coûté 4 600 maisons et six points d'occupation. Trente centimètres sur une
# chaussée dont on ne conteste que le bord laissent l'AXE parfaitement dégagé,
# et c'est l'axe qui porte les chemins.
DEBORD = 0.3
MAILLE_V = 16.0
VOIE_G = {}                   # (i, j) → [(ax, ay, bx, by, demi-gabarit)]

def _d_point_seg(px, py, ax, ay, bx, by):
    dx, dy = bx-ax, by-ay
    q = dx*dx + dy*dy
    t = 0.0 if q < 1e-12 else max(0.0, min(1.0, ((px-ax)*dx + (py-ay)*dy)/q))
    return math.hypot(px-ax-t*dx, py-ay-t*dy)

def _seg_coupe_boite(ax, ay, bx, by, hx, hy):
    """le segment entre-t-il dans la boîte [-hx,hx]×[-hy,hy] ? (Liang-Barsky)"""
    t0, t1 = 0.0, 1.0
    dx, dy = bx-ax, by-ay
    for p, q in ((-dx, ax+hx), (dx, hx-ax), (-dy, ay+hy), (dy, hy-ay)):
        if abs(p) < 1e-12:
            if q < 0: return False
            continue
        r = q/p
        if p < 0:
            if r > t1: return False
            if r > t0: t0 = r
        else:
            if r < t0: return False
            if r < t1: t1 = r
    return t0 <= t1

def mord_la_rue(x, y, f, p, cap):
    """l'emprise empiète-t-elle sur une chaussée ?"""
    a = math.radians(cap)
    ca, sa = math.cos(a), math.sin(a)
    hx, hy = f*0.5, p*0.5
    r = math.hypot(hx, hy)
    vus = set()
    for i in range(int((x-r-8)//MAILLE_V), int((x+r+8)//MAILLE_V)+1):
        for j in range(int((y-r-8)//MAILLE_V), int((y+r+8)//MAILLE_V)+1):
            for s in VOIE_G.get((i, j), ()):
                if id(s) in vus: continue
                vus.add(id(s))
                ax, ay, bx, by, w = s
                # dans le repère de la maison
                ux_, uy_ = ax-x, ay-y
                wx_, wy_ = bx-x, by-y
                pax, pay = ux_*ca + uy_*sa, -ux_*sa + uy_*ca
                pbx, pby = wx_*ca + wy_*sa, -wx_*sa + wy_*ca
                if (min(pax, pbx) > hx+w or max(pax, pbx) < -hx-w or
                        min(pay, pby) > hy+w or max(pay, pby) < -hy-w):
                    continue
                if _seg_coupe_boite(pax, pay, pbx, pby, hx, hy):
                    return True   # l'axe DANS la maison : jamais, sans tolérance
                d = min(_d_point_seg(sx, sy, pax, pay, pbx, pby)
                        for sx, sy in ((-hx,-hy), (hx,-hy), (hx,hy), (-hx,hy)))
                for qx, qy in ((pax, pay), (pbx, pby)):
                    d = min(d, math.hypot(max(0.0, abs(qx)-hx), max(0.0, abs(qy)-hy)))
                if d < w - DEBORD:
                    return True
    return False

def _pose_nue(x, y, f, p, cap, joint, dos_=DOS):
    """l'emprise tient-elle ici, sans rien toucher ?"""
    a = math.radians(cap)
    vx, vy = math.cos(a), math.sin(a)
    for sf, sp in ((-.48,-.48), (.48,-.48), (.48,.48), (-.48,.48), (0,-.48), (0,.48)):
        if not case_libre(x + vx*f*sf - vy*p*sp, y + vy*f*sf + vx*p*sp):
            return False   # jamais dans la rue, jamais hors du sol bâtissable
    if VOIE_G and mord_la_rue(x, y, f, p, cap):
        return False
    hf, hp = f*0.5, p*0.5
    for dl, dt, ef, ep in _voisins(x, y, f, p, cap, dos_):
        if abs(dl) < hf + ef + joint - TOL and abs(dt) < hp + ep + dos_ - TOL:
            return False
    return True

def tailler(xf, yf, f, p, cap, joint, dos_=DOS):
    """La parcelle réellement posable ici — ROGNÉE sur ce qui est libre.

    C'ÉTAIT LE DÉFAUT DE FOND, et il ne se voyait pas dans les chiffres. Le
    test d'avant était tout ou rien : une parcelle entrait à sa taille tirée,
    ou elle était jetée. Or une ville n'est pas bâtie de gabarits — elle est
    bâtie de ce qui rentre. Un reste de sept mètres ne peut pas recevoir une
    parcelle de onze, donc il restait vide ; c'est ainsi que la moitié du sol
    de Port-Réal était du terrain vague au cœur des îlots, et que trente-six
    pour cent des tentatives mouraient sur le voisin.

    On rogne donc, dans cet ordre : la PROFONDEUR d'abord (une maison de coin
    est courte, elle n'est pas étroite), la façade ensuite. Sous `F_MINI` par
    `P_MINI`, ce n'est plus une maison et l'on renonce pour de bon.

    `(xf, yf)` est le MILIEU DE LA FAÇADE, pas le centre : c'est lui qui doit
    rester sur la rue quand la profondeur se raccourcit.
    """
    a = math.radians(cap)
    vx, vy = math.cos(a), math.sin(a)
    nx2, ny2 = -vy, vx
    for kp in (1.0, .82, .66, .52, .40, .30):
        p2 = p*kp
        if p2 < P_MINI: break
        for kf in (1.0, .84, .70, .56, .44, .34):
            f2 = f*kf
            if f2 < F_MINI: break
            x = xf + nx2*p2*0.5
            y = yf + ny2*p2*0.5
            if _pose_nue(x, y, f2, p2, cap, joint, dos_):
                return coller(x, y, f2, p2, cap, joint, dos_)
    return None

def coller(x, y, f, p, cap, joint, dos_=DOS):
    """Ferme le jour qui reste avec le voisin : le mur devient mitoyen.

    Rogner laisse forcément des lisières — deux ou trois décimètres qu'aucune
    ville ne tolère et qu'aucun maçon ne laisse. On étire donc chaque côté de
    la façade jusqu'au contact quand le voisin est à portée de main. C'est la
    mitoyenneté comme GESTE, au lieu de l'espérer d'un pas de progression.
    """
    a = math.radians(cap)
    vx, vy = math.cos(a), math.sin(a)
    hf, hp = f*0.5, p*0.5
    gains = [0.0, 0.0]                    # ce qu'on gagne à droite, à gauche
    for dl, dt, ef, ep in _voisins(x, y, f, p, cap, dos_):
        if abs(dt) >= hp + ep + dos_ - TOL: continue   # pas au même rang
        jeu = abs(dl) - hf - ef                        # le jour qui nous sépare
        if 0.0 <= jeu <= COLLAGE:
            k = 0 if dl > 0 else 1
            gains[k] = max(gains[k], jeu)
    if gains[0] or gains[1]:
        f2 = f + gains[0] + gains[1]
        # le centre glisse de la moitié de la différence des deux gains
        d = (gains[0] - gains[1])*0.5
        x2, y2 = x + vx*d, y + vy*d
        if _pose_nue(x2, y2, f2 - 2*TOL, p, cap, 0.0, dos_):
            return x2, y2, f2, p
    return x, y, f, p

def occuper(x, y, f, p, cap):
    a = math.radians(cap)
    e = (x, y, f*0.5, p*0.5, math.cos(a), math.sin(a))
    for c in _casiers(x, y, 0.5*math.hypot(f, p)): OCC.setdefault(c, []).append(e)

USAGE = {"Le port et ses hangars": "entrepot", "Les tanneries": "atelier",
         "La rue d'Acier": "forge", "Le Crochet": "maison d'officier",
         "La ville haute": "hôtel", "Le Culpucier": "taudis"}
BATIMENTS = []
COURS = []
# Diagnostic de pose : sans lui on devine. `NQ` = ce que l'îlot autorise,
# `TENTE`/`POSE` = ce qui a été tenté et obtenu, par rang.
from collections import Counter as _C
DIAG_NQ, DIAG_TENTE, DIAG_POSE, DIAG_PROF = _C(), _C(), _C(), _C()

TOUTES = [{"trace": e["trace"], "largeur_m": e["largeur_m"], "genre": e["genre"]}
          for e in G["aretes"] if e["couche"] == "L1-surface"] + NEUVES
RANGS = {"artere": 2, "quai": 2, "rue": 2, "escalier": 2, "ruelle": 1}

# On indexe la voirie AVANT de poser quoi que ce soit : `mord_la_rue` s'en sert
# à chaque tentative. Le demi-gabarit est celui de la classe, trottoir compris,
# et l'on garde le plus large des deux quand le tracé est plus généreux que sa
# classe — même arbitrage qu'à la pose du recul, sans quoi le test refuserait
# ce que le recul vient d'autoriser.
for _v in TOUTES:
    _w = max(recul(_v["genre"]),
             _v["largeur_m"]*0.5 + TROTTOIR.get(_v["genre"], 0.5)) - MARGE_RECUL
    _t = _v["trace"]
    for _a, _b in zip(_t, _t[1:]):
        _s = (_a[0], _a[1], _b[0], _b[1], _w)
        _i0, _i1 = sorted((int(_a[0]//MAILLE_V), int(_b[0]//MAILLE_V)))
        _j0, _j1 = sorted((int(_a[1]//MAILLE_V), int(_b[1]//MAILLE_V)))
        for _i in range(_i0-1, _i1+2):
            for _j in range(_j0-1, _j1+2):
                VOIE_G.setdefault((_i, _j), []).append(_s)
print("   voirie indexée : %d cases" % len(VOIE_G))

# --- LA PROFONDEUR DE L'ÎLOT, MESURÉE ET NON SUPPOSÉE -----------------------
# Combien de rangs tiennent derrière une façade ? La question n'a pas de réponse
# de QUARTIER, elle a une réponse par ENDROIT. Un même quartier porte des îlots
# de vingt-cinq mètres et des îlots de quatre-vingt-dix ; la table qui répondait
# « deux » pour les deux laissait le second creux. Mesuré : 26 % du vide enclavé
# de la ville est à plus de trente mètres de toute rue — c'est-à-dire au cœur
# d'îlots qu'on n'a jamais fini de bâtir.
#
# On sonde donc perpendiculairement à la voie jusqu'à rencontrer la chaussée
# suivante : c'est la profondeur du bloc ICI. On en garde la moitié — l'autre
# revient au front d'en face —, on réserve la cour, et l'on compte ce qui tient.
SONDE = 96.0                 # au-delà, ce n'est plus un îlot mais un terrain

def profond_ici(x, y, ux_, uy_):
    """Jusqu'où va le bloc dans cette direction, en mètres.

    ON SAUTE D'ABORD SA PROPRE CHAUSSÉE. La sonde part de l'AXE de la voie, et
    la trame de travail fait trois mètres — donc les premières cases sont la
    rue dont on vient, marquée plus large que son gabarit. Sans ce saut, DEUX
    SONDES SUR SEPT rendaient zéro au Culpucier : l'îlot était réputé
    inexistant, un seul rang se posait, et tout le cœur restait en friche.
    C'est de là que venait le vide qu'on voyait derrière les rangs.
    """
    s = CEL
    while s < SONDE:                      # 1. sortir de la chaussée de départ
        i, j = int((x + ux_*s)/CEL), int((y + uy_*s)/CEL)
        if not (0 <= i < LX and 0 <= j < LY) or not LIBRE[idx(i, j)]:
            return s
        if not RUE[idx(i, j)]:
            break
        s += CEL
    while s < SONDE:                      # 2. courir jusqu'à la suivante
        i, j = int((x + ux_*s)/CEL), int((y + uy_*s)/CEL)
        if not (0 <= i < LX and 0 <= j < LY):
            return s
        k = idx(i, j)
        if RUE[k] or not LIBRE[k]:
            return s
        s += CEL
    return SONDE

def rangs_ici(x, y, ux_, uy_, d0, prof, dos_=DOS):
    """Combien de rangs poser depuis cette façade.

    ON NE RÉSERVE PAS LA COUR, ON LA LAISSE TOMBER. Retrancher `COEUR` avant
    de compter coûtait un rang entier : les îlots sont coupés à cinquante et
    un mètres, qui tiennent deux rangs par côté et presque rien au milieu — en
    prélevant six mètres d'avance, il n'en tenait plus qu'un, et la ville a
    perdu treize cents maisons au lieu d'en gagner. La cour est ce qui RESTE
    quand les rangs sont posés, et l'étape suivante la ramasse justement comme
    telle. Ce qui ne tient pas se rogne, ce qui reste devient une cour.
    """
    dispo = profond_ici(x, y, ux_, uy_)*0.5 - d0
    if dispo < prof:
        return 1
    # Le plafond n'est pas une opinion sur la ville, c'est un garde-fou contre
    # une sonde folle. À quatre, il MORDAIT : 1 447 sondes du Culpucier le
    # touchaient, sur des îlots qui en portaient davantage.
    return max(1, min(6, int((dispo + dos_)/(prof + dos_))))

def point_a(segs, s):
    """le point de la polyligne à l'abscisse curviligne `s`"""
    lo, hi = 0, len(segs)-1
    while lo < hi:                       # le segment qui porte cette abscisse
        mi = (lo+hi+1)//2
        if segs[mi][0] <= s: lo = mi
        else: hi = mi-1
    s0, L, ax_, ay_, vx, vy = segs[lo]
    t = max(0.0, min(L, s-s0))
    return ax_ + vx*t, ay_ + vy*t

for v in sorted(TOUTES, key=lambda w: -w["largeur_m"]):
    tr, larg = v["trace"], v["largeur_m"]
    nmax = RANGS.get(v["genre"], 2)
    # ON PARCOURT LA POLYLIGNE D'UN SEUL TENANT, et c'était là le vrai mal.
    # Les tracés engendrés par les coupes portent un point tous les 3 m (la
    # maille de travail) ; en repartant de s = 0 à chaque segment, on tentait
    # une maison de 7 m tous les 3 m. Le pas réel n'était donc pas le joint du
    # quartier mais l'ÉCHANTILLONNAGE DE LA POLYLIGNE — d'où deux candidats sur
    # trois refusés, des trous de la largeur d'une maison, et, du temps du test
    # isotrope, une maison sur deux bâtie dans sa voisine.
    segs, total = [], 0.0
    for a, b in zip(tr, tr[1:]):
        L = math.dist((a[0],a[1]), (b[0],b[1]))
        if L < 1e-6: continue
        segs.append((total, L, a[0], a[1], (b[0]-a[0])/L, (b[1]-a[1])/L))
        total += L
    if total >= 1.5:
        si, s = 0, 0.0
        while s < total:
            while si+1 < len(segs) and s >= segs[si][0] + segs[si][1]: si += 1
            s0, L, ax_, ay_, vx, vy = segs[si]
            x0, y0 = ax_ + vx*(s-s0), ay_ + vy*(s-s0)
            if not faubourg_tient(x0, y0):
                s += 6.0                 # la campagne : on passe son chemin
                continue
            q = quartier(x0, y0)
            fmin, fmax, prof, etages, he = gabarit(q)
            joint, _ = grain(q)
            dos_ = dos(q)
            f = fmin + R.random()*(fmax-fmin)
            # LE CAP SE LIT SUR LA CORDE DE LA FAÇADE, pas sur le segment.
            # Les ruelles engendrées portent un point tous les 3 m et tournent
            # de 13° en moyenne d'un segment au suivant (le bruit par point de
            # `couper_un`). Un mur de huit mètres ne suit pas un frisson de
            # trois : posé sur le segment, il héritait du tremblement, et tout
            # le front s'éventait. La corde [s, s+f] donne la direction que la
            # maison voit vraiment.
            #
            # `s` compte donc le BORD de la parcelle, jamais son milieu. Avec le
            # milieu on avançait de f+joint là où il faut (f_précédente+f)/2 +
            # joint : les façades étant tirées au hasard entre fmin et fmax, une
            # fois sur deux le pas était trop court — le voisin refusé, et un
            # TROU large comme une maison.
            xe, ye = point_a(segs, min(total, s + f))
            dx, dy = xe - x0, ye - y0
            n_ = math.hypot(dx, dy)
            if n_ > 0.5: vx, vy = dx/n_, dy/n_
            nx, ny = -vy, vx
            cap = math.degrees(math.atan2(vy, vx))
            x0, y0 = (x0 + xe)*0.5, (y0 + ye)*0.5
            usage = USAGE.get(q, "maison")
            if q.startswith(("Le faubourg", "Les baraques", "Le bourg")): usage = "cabane"
            pose = False
            # une ruelle ne porte qu'un rang, quel que soit le quartier ; et un
            # quartier dont l'îlot ne tient pas deux rangs n'en porte qu'un,
            # quelle que soit la rue. C'est le plus contraignant qui gagne.
            #
            # LES RANGS SE COMPTENT, ILS NE SE TENTENT PAS — et ils se comptent
            # ICI, pas dans une table de quartier : voir `rangs_ici`. On en
            # tentait trois ou quatre partout, en laissant « la place
            # disponible décider », mais la pose ne sait pas où finit l'îlot,
            # elle sait seulement si la case est libre : le troisième rang
            # tombait de l'autre côté du cœur, dans le front de la rue d'en
            # face, s'y rattachait, et présentait sa façade au mauvais côté.
            for cote in (1, -1):
                # le recul se prend sur la CLASSE de la voie, comme le fait la
                # cuisson du plan — et l'on garde le plus grand des deux quand
                # la voie engendrée est plus large que sa classe.
                d = max(recul(v["genre"]),
                        larg*0.5 + TROTTOIR.get(v["genre"], 0.5) + MARGE_RECUL)
                # `d` est le FRONT du rang, pas son milieu : c'est lui qui reste
                # sur la rue quand la parcelle se raccourcit.
                _pf = profond_ici(x0, y0, nx*cote, ny*cote)
                nq = rangs_ici(x0, y0, nx*cote, ny*cote, d, prof, dos_)
                if q == "Le Culpucier":
                    DIAG_NQ[nq] += 1
                    DIAG_PROF[min(90, int(_pf//10)*10)] += 1
                # LE CAP EST CELUI DE LA MAISON, PAS CELUI DE LA RUE. Du côté
                # gauche, la façade regarde à l'opposé du tracé : on TAILLAIT
                # bien avec `cap+180`, mais on ÉCRIVAIT `cap`. Un côté de rue
                # sur deux sortait donc orienté à l'envers — cour sur la rue,
                # mur aveugle sur l'arrière —, ce que la cuisson du plan
                # rattrapait après coup (`redresser`, geste 1) au prix d'un
                # écart de cap moyen de 56°.
                cap_pose = cap if cote > 0 else cap + 180.0
                cap_pose = (cap_pose + 180.0) % 360.0 - 180.0
                for rang in range(nq):
                    xf, yf = x0 + nx*d*cote, y0 + ny*d*cote
                    taillee = tailler(xf, yf, f, prof, cap_pose, joint, dos_)
                    if q == "Le Culpucier":
                        DIAG_TENTE[rang] += 1
                        if taillee: DIAG_POSE[rang] += 1
                    if taillee:
                        x, y, f2, p2 = taillee
                        occuper(x, y, f2, p2, cap_pose)
                        et = R.randint(*etages)
                        BATIMENTS.append([round(x,1), round(y,1), round(zsol(x,y),1),
                                          round(cap_pose,1), round(f2,1), round(p2,1),
                                          et, round(et*he+1.2,1), q, usage,
                                          1 if (usage in ("entrepot","forge","hôtel","maison d'officier")
                                                or R.random() < 0.25) else 0])
                        pose = True
                    # LE FRONT DU RANG SUIVANT NE DÉPEND PAS DE CE QU'ON VIENT
                    # DE POSER. On avançait de `p2`, la profondeur ROGNÉE : deux
                    # voisines rognées différemment ouvraient deux fronts
                    # différents au rang d'après, et de proche en proche l'îlot
                    # cessait de se lire comme un îlot. Le pas est donc le
                    # gabarit du quartier, le même pour toute la rue. Ce qui a
                    # été rogné laisse une arrière-cour, et c'est juste.
                    d += prof + dos_
            # le pas le long de la rue EST la façade plus le joint du quartier :
            # mitoyen au Culpucier, un mètre quatre-vingts au faubourg. Quand
            # rien ne s'est posé, on force l'avance, sans quoi on repique au
            # même endroit.
            s += f + joint + (0.8 if not pose else 0)
print("   %d bâtiments" % len(BATIMENTS))
print("   CULPUCIER — profondeur d'îlot sondée :",
      " ".join("%dm:%d" % (k, v) for k, v in sorted(DIAG_PROF.items())))
print("   CULPUCIER — rangs autorisés :",
      " ".join("%d:%d" % (k, v) for k, v in sorted(DIAG_NQ.items())))
print("   CULPUCIER — posés/tentés par rang :",
      " ".join("r%d %d/%d" % (k, DIAG_POSE[k], DIAG_TENTE[k])
               for k in sorted(DIAG_TENTE)))

# ---------------------------------------------------------------------------
# 4. L3 — LES COURS : ce que les parcelles n'ont pas mangé
# ---------------------------------------------------------------------------
print("… les cours et leurs porches")
PRIS = bytearray(LX*LY)
for b in BATIMENTS:
    r = max(b[4], b[5])/2
    ci, cj = int(b[0]/CEL), int(b[1]/CEL)
    rr = int(r/CEL)+1
    for di in range(-rr, rr+1):
        for dj in range(-rr, rr+1):
            i, j = ci+di, cj+dj
            if 0 <= i < LX and 0 <= j < LY: PRIS[idx(i, j)] = 1

vu = bytearray(LX*LY)
ARETES_L3 = []
NOEUDS_L3 = []
PORTAILS_L3 = []
for j0 in range(LY):
    for i0 in range(LX):
        k0 = idx(i0, j0)
        if vu[k0] or not LIBRE[k0] or RUE[k0] or PRIS[k0] or not DANS[k0]: continue
        q, cells = deque([(i0, j0)]), []
        vu[k0] = 1
        while q:
            i, j = q.popleft(); cells.append((i, j))
            for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
                a, b = i+di, j+dj
                if 0 <= a < LX and 0 <= b < LY:
                    k = idx(a, b)
                    if not vu[k] and LIBRE[k] and not RUE[k] and not PRIS[k]:
                        vu[k] = 1; q.append((a, b))
        aire = len(cells)*CEL*CEL
        if not (45 <= aire <= 2600): continue
        cx = sum(c[0] for c in cells)/len(cells)*CEL + CEL/2
        cy = sum(c[1] for c in cells)/len(cells)*CEL + CEL/2
        # le porche : la case de la cour la plus proche d'une rue
        meil, best = None, 1e18
        for (i, j) in cells:
            for di in range(-4, 5):
                for dj in range(-4, 5):
                    a, b = i+di, j+dj
                    if 0 <= a < LX and 0 <= b < LY and RUE[idx(a, b)]:
                        d = di*di + dj*dj
                        if d < best:
                            best, meil = d, ((i+.5)*CEL, (j+.5)*CEL, (a+.5)*CEL, (b+.5)*CEL)
        if not meil: continue
        cid = "cour:%d.%d" % (i0, j0)
        NOEUDS_L3.append({"id": cid, "genre": "cour", "niveau": 0,
                          "xyz": [round(cx,1), round(cy,1), round(zsol(cx,cy),1)],
                          "nom": "Cour intérieure", "aire_m2": round(aire),
                          "quartier": quartier(cx, cy),
                          "raison": "Ce que les parcelles n'ont pas mangé au cœur du bloc : "
                                    "on y puise, on y range, on y étend le linge."})
        ARETES_L3.append({"id": "porche:%d.%d" % (i0, j0), "de": cid, "vers": None,
                          "genre": "porche", "couche": "L3-interieurs",
                          "largeur_m": 2.2, "longueur_m": round(math.dist(meil[:2], meil[2:]), 1),
                          "pente": 0.0,
                          "raison": "Le seul accès de la cour à la rue : un porche sous une maison. "
                                    "Qui le tient tient la cour.",
                          "trace": [[round(meil[0],1), round(meil[1],1), round(zsol(meil[0],meil[1]),1)],
                                    [round(meil[2],1), round(meil[3],1), round(zsol(meil[2],meil[3]),1)]],
                          "visibilite": "semi-privee", "acces": "prive", "etat": "ouvert"})
print("   %d cours" % len(NOEUDS_L3))

# ---------------------------------------------------------------------------
# 4bis. L3, la suite — halls, arcades, passages entre cours, escaliers de cave
# ---------------------------------------------------------------------------
print("… les intérieurs structurants")
def l3_noeud(nid, x, y, z, genre, nom, raison, **kw):
    n = {"id": nid, "genre": genre, "niveau": kw.pop("niveau", 0),
         "xyz": [round(x,1), round(y,1), round(z,1)], "nom": nom, "raison": raison}
    n.update(kw); NOEUDS_L3.append(n); return nid
def l3_arete(aid, na, nb, genre, pa, pb, larg, raison, **kw):
    e = {"id": aid, "de": na, "vers": nb, "genre": genre, "couche": "L3-interieurs",
         "largeur_m": larg, "longueur_m": round(math.dist(pa[:2], pb[:2]), 1),
         "pente": 0.0, "raison": raison,
         "trace": [[round(pa[0],1), round(pa[1],1), round(pa[2],1)],
                   [round(pb[0],1), round(pb[1],1), round(pb[2],1)]]}
    e.update(kw); ARETES_L3.append(e); return e

# --- a) les HALLS : tout bâtiment assez grand a un dedans qui compte --------
# On ne modélise pas l'intérieur d'une échoppe. On modélise celui des bâtiments
# où l'on ENTRE pour autre chose que dormir : entrepôts, hôtels, forges,
# maisons d'officier. Un hall, sa porte sur rue, et sa descente en cave.
cellier = 0
halls = 0
cx_, cy_, cz_ = 0, 1, 2
for k, b in enumerate(BATIMENTS):
    x, y, z, cap, f, prof, et, haut, q, usage, cave = b
    if usage not in ("entrepot", "hôtel", "maison d'officier", "forge", "atelier"): continue
    if f*prof < 90: continue
    a = math.radians(cap)
    vx, vy = math.cos(a), math.sin(a)
    nxx, nyy = -vy, vx
    hid = l3_noeud("hall:%d" % k, x, y, z, "hall",
                   {"entrepot": "Salle de l'entrepôt", "hôtel": "Le grand hall",
                    "maison d'officier": "Le vestibule", "forge": "L'atelier",
                    "atelier": "L'atelier"}[usage],
                   "On y entre pour autre chose que dormir : c'est là que la chose se traite.",
                   quartier=q, usage=usage, aire_m2=round(f*prof))
    halls += 1
    # la porte donne sur la façade, du côté de la rue
    px, py = x - nxx*prof*0.52, y - nyy*prof*0.52
    l3_arete("entree:%d" % k, hid, None, "entree", (x, y, z), (px, py, z), 1.6,
             "La porte : elle donne sur la rue que la façade borde, et pas ailleurs.",
             visibilite="publique", acces="public", etat="ouvert")
    if cave:
        vid = l3_noeud("cave:%d" % k, x, y, z-4.5, "cave", "La cave",
                       "Sous le hall : ce qui craint le gel, ce qui craint les yeux.",
                       niveau=-1, quartier=q)
        l3_arete("degre:%d" % k, hid, vid, "escalier", (x, y, z), (x, y, z-4.5), 1.2,
                 "L'escalier de cave : quatre mètres et demi, et l'on n'est plus dans la ville.",
                 visibilite="privee", acces="prive", etat="ouvert")
        PORTAILS_L3.append({"id": "pt:cave:%d" % k, "haut": hid, "bas": vid,
                            "genre": "escalier", "cache": False, "ferme": True,
                            "cout": 1.0,
                            "raison": "Du hall à la cave : le premier degré vers tout ce qui est dessous."})
        cellier += 1
print("   %d halls, %d caves" % (halls, cellier))

# --- b) les PASSAGES ENTRE COURS -------------------------------------------
# Deux cours voisines séparées par une seule maison finissent toujours percées :
# les gens de service ne ressortent pas dans la rue pour faire trente pas.
cours = [n for n in NOEUDS_L3 if n["genre"] == "cour"]
seau = {}
for n in cours:
    seau.setdefault((int(n["xyz"][0]//40), int(n["xyz"][1]//40)), []).append(n)
perces = 0
faits = set()
for n in cours:
    ci, cj = int(n["xyz"][0]//40), int(n["xyz"][1]//40)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for m2 in seau.get((ci+di, cj+dj), ()):
                if m2 is n: continue
                paire = tuple(sorted((n["id"], m2["id"])))
                if paire in faits: continue
                d = math.dist(n["xyz"][:2], m2["xyz"][:2])
                if not (10 < d < 34): continue
                faits.add(paire)
                l3_arete("entrecour:%d" % perces, n["id"], m2["id"], "passage",
                         n["xyz"], m2["xyz"], 1.1,
                         "Deux cours à trente pas l'une de l'autre, séparées par une seule "
                         "maison : on a fini par la percer plutôt que de ressortir en rue.",
                         visibilite="semi-privee", acces="prive", etat="ouvert")
                perces += 1
print("   %d passages entre cours" % perces)

# --- c) les ARCADES : on vend à couvert au bord d'une place -----------------
arcades = 0
for s_ in CARTE["sol"]:
    if s_["genre"] != "champ" or not s_.get("nom", "").startswith(("La grande place", "Le march")):
        continue
    pts = [(mx(p[0]), my(p[1])) for p in polygone_reel(s_["nom"], s_["points"])]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        lg = math.dist(a, b)
        if lg < 18: continue
        ux2, uy2 = (b[0]-a[0])/lg, (b[1]-a[1])/lg
        nx2, ny2 = -uy2, ux2
        # l'arcade se range CONTRE le bâti, en retrait du bord de la place
        A = (a[0] + nx2*3.5 + ux2*2, a[1] + ny2*3.5 + uy2*2)
        B = (b[0] + nx2*3.5 - ux2*2, b[1] + ny2*3.5 - uy2*2)
        if not (case_libre(A[0], A[1]) or case_libre(B[0], B[1])):
            A = (a[0] - nx2*3.5 + ux2*2, a[1] - ny2*3.5 + uy2*2)
            B = (b[0] - nx2*3.5 - ux2*2, b[1] - ny2*3.5 - uy2*2)
        za, zb = zsol(A[0], A[1]), zsol(B[0], B[1])
        nid_a = l3_noeud("arc:%s:%d:a" % (s_["nom"][:6], arcades), A[0], A[1], za,
                         "arcade", "Arcade de " + s_["nom"],
                         "Au bord de la place : on y vend à couvert, et l'on y attend la pluie.")
        nid_b = l3_noeud("arc:%s:%d:b" % (s_["nom"][:6], arcades), B[0], B[1], zb,
                         "arcade", "Arcade de " + s_["nom"], "L'autre bout de la galerie.")
        l3_arete("arcade:%d" % arcades, nid_a, nid_b, "arcade",
                 (A[0], A[1], za), (B[0], B[1], zb), 3.4,
                 "Galerie couverte au bord de la place : le commerce s'y tient les jours de pluie, "
                 "et l'on y traîne les jours de soleil.",
                 visibilite="publique", acces="public", etat="ouvert")
        arcades += 1
print("   %d arcades" % arcades)

# ---------------------------------------------------------------------------
# on réécrit le graphe
# ---------------------------------------------------------------------------
def noeud_bout(p, suff):
    nid = "d%d.%d" % (round(p[0]), round(p[1]))
    return nid
for k, v in enumerate(NEUVES):
    tr = [[p[0], p[1], round(zsol(p[0], p[1]), 1)] for p in v["trace"]]
    na, nb = noeud_bout(tr[0], "a"), noeud_bout(tr[-1], "b")
    for nid, p in ((na, tr[0]), (nb, tr[-1])):
        if not any(n["id"] == nid for n in G["noeuds"]):
            G["noeuds"].append({"id": nid, "genre": "carrefour", "niveau": 0, "xyz": p})
    lg = sum(math.dist(a[:2], b[:2]) for a, b in zip(tr, tr[1:]))
    G["aretes"].append({"id": "dn%d" % k, "de": na, "vers": nb, "genre": v["genre"],
                        "couche": "L1-surface", "largeur_m": v["largeur_m"],
                        "longueur_m": round(lg, 1),
                        "pente": round(abs(tr[0][2]-tr[-1][2])/max(1, lg), 3),
                        "raison": v["raison"], "trace": tr,
                        "visibilite": "publique", "acces": "public", "etat": "ouvert",
                        "engendre": "densification"})
G["noeuds"] += NOEUDS_L3
G["aretes"] += ARETES_L3
# une cave assez proche d'un drain finit toujours par s'y ouvrir : c'est comme
# ça qu'on entre dans une maison sans passer par sa porte.
EGOUTS_TR = [p for e in G["aretes"] if e["genre"] == "egout" for p in e["trace"]]
ouvertes = 0
for n in NOEUDS_L3:
    if n["genre"] != "cave": continue
    for p in EGOUTS_TR:
        if (n["xyz"][0]-p[0])**2 + (n["xyz"][1]-p[1])**2 < 26**2:
            PORTAILS_L3.append({"id": "pt:cave-egout:" + n["id"], "haut": n["id"],
                "bas": "egout:aegon:tete", "genre": "percement", "cache": True,
                "ferme": False, "cout": 2.5,
                "raison": "Le mur de cette cave touche le drain, et quelqu'un l'a su avant vous."})
            ouvertes += 1
            break
G["portails"] += PORTAILS_L3
print("   %d caves ouvertes sur un drain" % ouvertes)
G["couches"]["L3-interieurs"] = "Cours intérieures et leurs porches : le dedans des blocs"
G["_densifie"] = ("Voirie subdivisée en mètres : chaque bloc a été coupé en travers de son "
                  "grand axe dès qu'il dépassait la profondeur d'îlot de SON quartier "
                  "(echelle.GRAIN : %s), jusqu'à ce qu'aucun fond ne soit inatteignable. "
                  "Les parcelles suivent les rues (façade obligatoire) et se touchent selon "
                  "le joint du quartier — nul au Culpucier, où le mur est mitoyen ; ce qui "
                  "reste au cœur d'un bloc est une cour, et son porche est le seul accès."
                  % ", ".join("%s %.0f m" % (q, b) for q, (j, b) in sorted(GRAIN.items())))
del G["batiments"]
io.open(os.path.join(MONDE, "portreal.graph.json"), "w", encoding="utf-8").write(
    json.dumps(G, ensure_ascii=False, indent=1))
io.open(os.path.join(MONDE, "portreal.bati.json"), "w", encoding="utf-8").write(
    json.dumps({"_colonnes": ["x", "y", "z", "cap", "facade_m", "profondeur_m",
                              "etages", "hauteur_m", "quartier", "usage", "cave"],
                "bati": BATIMENTS}, ensure_ascii=False, separators=(",", ":")))

aire_ha = 7.02*100
km = sum(e["longueur_m"] for e in G["aretes"] if e["couche"] == "L1-surface")/1000
print()
print("  %d nœuds, %d arêtes, %d bâtiments, %d cours" %
      (len(G["noeuds"]), len(G["aretes"]), len(BATIMENTS), len(NOEUDS_L3)))
print("  voirie de surface : %.1f km — %.0f m/ha" % (km, km*1000/aire_ha))
print("  bâtiments         : %.0f /ha" % (len(BATIMENTS)/aire_ha))
