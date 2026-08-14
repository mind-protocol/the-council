# -*- coding: utf-8 -*-
"""POSE ORGANIQUE — on remplit l'espace, et la rue est ce qui reste.

    python scripts/monde/organique.py                     tout intra-muros
    python scripts/monde/organique.py --quartier "Le Culpucier"
    python scripts/monde/organique.py --sortie monde/essai.bati.json

CE QUI CHANGE, ET POURQUOI. `densifier.py` est l'algorithme d'une BASTIDE : on
trace la voirie, on découpe des îlots réguliers, on aligne des parcelles
calibrées le long des rues. Port-Réal n'est pas une bastide, et ça se voyait au
seul chiffre qui compte — la moitié du sol restait en friche au cœur des îlots,
parce qu'un modèle qui BORDE des rues ne peut pas remplir un cœur.

Ici, l'occupation est première et la rue est le reste. C'est l'ordre historique :
personne n'a tracé les ruelles de Culpucier, elles sont ce que personne n'a
bâti.

    1. LES ARTÈRES SONT INTANGIBLES. Le squelette nommé de la carte 2D — la rue
       des Sœurs, la porte de la Gadoue, les quais — ne bouge pas d'un pouce.
       Sans lui la ville devient une tache illisible où l'on ne peut plus
       donner un itinéraire à personne, et c'est un jeu, pas une maquette.
    2. LE CHAMP. Une désirabilité par cellule, tirée des mêmes hotspots que
       `usages.py` lit déjà dans le graphe : portes, marchés, quais, donjon,
       eau, et la distance à une voie. On bâtit d'abord là où l'on veut être.
    3. L'ACCRÉTION. On plante en partant du réseau vers le dedans, chaque
       parcelle TAILLÉE sur le vide réel (`pose.tailler`) et COLLÉE à ses
       voisines. Une maison de coin est courte, pas rejetée.
    4. LA VENELLE SE PERCE QUAND ELLE MANQUE. Quand il ne reste que du vide
       hors de portée d'une voie, on creuse un passage depuis la voie la plus
       proche jusqu'au fond, et l'on reprend. C'est ainsi qu'une cour finit
       percée, et c'est ce qui garantit qu'aucune parcelle n'est enclavée.
    5. ON S'ARRÊTE AU COMPTE D'ÂMES. `DENSITE` d'`usages.py` dit les mètres
       carrés de plancher par âme, quartier par quartier ; la cible est celle
       que le dépôt se donne déjà (400 000 âmes, cf. peupler.py). Un
       remplissage a besoin d'une condition d'arrêt qui ne soit pas un réglage.

Écrit `monde/portreal.bati.json` et les voies percées dans le graphe, exactement
comme `densifier.py` — les deux sont donc comparables sur les mêmes mesures.
"""
import json, math, io, os, sys, random, heapq
from collections import deque

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, ICI)
from echelle import (mx, my, ux, uy, LARGEUR, gabarit, polygone_reel, grain,
                     recul, TROTTOIR, MARGE_RECUL)
from pose import Occupation, F_MINI, P_MINI

R = random.Random(90210)
MONDE = os.path.join(RACINE, "monde")

# --- ce qu'on vise, et d'où ça vient ---------------------------------------
# Les mêmes mètres carrés par âme que `usages.py`, qui les tient depuis qu'il
# déduit la population du plancher. On ne les recopie pas : on les importera le
# jour où usages.py les exposera. En attendant ils sont ici, à l'identique.
DENSITE = {"Le Culpucier": 11.0, "La ville": 24.0, "La ville haute": 70.0,
           "Le Crochet": 45.0, "La rue d'Acier": 28.0, "Les tanneries": 30.0,
           "Le port et ses hangars": 200.0}
def m2_par_ame(q): return DENSITE.get(q, 30.0)
AMES_CIBLE = 400000.0          # cf. peupler.py : « Port-Réal, quatre cent mille âmes »

CEL = 3.0                      # la maille de travail, en mètres
PORTEE_VOIE = float(os.environ.get("PORTEE_VOIE", "34.0"))

# TROIS RÉGIMES, PAS UN. Percer partout la même fente de deux mètres donnait
# quatre cent soixante-six culs-de-sac par quartier et aucun itinéraire qui
# traverse — pour une partie où l'on s'enfuit à pied avec une malle, c'est
# disqualifiant. La largeur se prend donc sur ce que le passage DESSERT.
def largeur_venelle(aire_m2):
    if aire_m2 > 3000: return LARGEUR["rue"], "rue"
    if aire_m2 > 800:  return 2.6, "ruelle"
    return 2.0, "ruelle"
FUSION = float(os.environ.get("FUSION", "9.0"))   # on se raccorde à un passage voisin
DERIVE = float(os.environ.get("DERIVE", "0.35"))  # combien la courbe s'écarte de la corde

USAGE = {"Le port et ses hangars": "entrepot", "Les tanneries": "atelier",
         "La rue d'Acier": "forge", "Le Crochet": "maison d'officier",
         "La ville haute": "hôtel", "Le Culpucier": "taudis"}


def dedans(poly, x, y):
    r = False; j = len(poly)-1
    for i in range(len(poly)):
        if (poly[i][1] > y) != (poly[j][1] > y) and \
           x < (poly[j][0]-poly[i][0])*(y-poly[i][1])/(poly[j][1]-poly[i][1])+poly[i][0]:
            r = not r
        j = i
    return r

def boite_de(poly):
    return (min(p[0] for p in poly), min(p[1] for p in poly),
            max(p[0] for p in poly), max(p[1] for p in poly))


def lisser(trace, tours=3):
    """Défait l'escalier d'un chemin tracé de case en case.

    UNE VENELLE PERCÉE SUIT LA GRILLE, et c'est un piège en deux temps. On
    redescend le gradient à quatre voisins, donc chaque segment fait trois
    mètres et vaut 0° ou 90°. Tant que la maison prenait son cap sur la grille,
    ça ne se voyait pas — les deux erreurs se compensaient. Le jour où la
    maison prend honnêtement le cap DE SA RUE, elle hérite de l'escalier, et
    tout le quartier devient orthogonal.

    Trois passages de moyenne (le coin coupé de Chaikin, en plus court), puis
    on jette les points qui ne disent plus rien : une ruelle rendue à des
    angles continus, ce qui est ce qu'elle a toujours été sur le terrain.
    """
    if len(trace) < 3: return trace
    pts = list(trace)
    for _ in range(tours):
        out = [pts[0]]
        for a, b, c in zip(pts, pts[1:], pts[2:]):
            out.append(((a[0] + 2*b[0] + c[0])*0.25, (a[1] + 2*b[1] + c[1])*0.25))
        out.append(pts[-1])
        pts = out
    # décimation : un point tous les cinq mètres suffit à porter la courbe
    garde = [pts[0]]
    for p in pts[1:-1]:
        if math.dist(p, garde[-1]) >= 5.0: garde.append(p)
    garde.append(pts[-1])
    return garde


def charger(chemin=None):
    # Le squelette peut être passé à part : trois essais en parallèle ne
    # doivent pas se disputer le graphe du monde vivant.
    G = json.load(io.open(chemin or os.path.join(MONDE, "portreal.graph.json"),
                          encoding="utf-8"))
    T = json.load(io.open(os.path.join(MONDE, "portreal.terrain.json"), encoding="utf-8"))
    C = json.load(io.open(os.path.join(RACINE, "etat", "villes", "port-real.json"),
                          encoding="utf-8"))
    if "_densifie" in G or "batiments" not in G:
        sys.exit("Ce graphe est déjà semé. Relance d'abord "
                 "« python scripts/monde/graphe.py » pour repartir du squelette.")
    return G, T, C


def main(argv):
    quartier_seul = None
    if "--quartier" in argv: quartier_seul = argv[argv.index("--quartier")+1]
    sortie = (argv[argv.index("--sortie")+1] if "--sortie" in argv
              else os.path.join("monde", "portreal.bati.json"))

    graphe = argv[argv.index("--graphe")+1] if "--graphe" in argv else None
    G, T, CARTE = charger(graphe)
    RES, Zg, NXg, NYg = T["res_m"], T["z"], T["nx"], T["ny"]
    LX = int(NXg*RES/CEL)+1
    LY = int(NYg*RES/CEL)+1
    def idx(i, j): return j*LX + i
    def zsol(x, y):
        i, j = min(NXg-2, max(0, int(x/RES))), min(NYg-2, max(0, int(y/RES)))
        tx, ty = (x-i*RES)/RES, (y-j*RES)/RES
        a = Zg[j][i]*(1-tx) + Zg[j][i+1]*tx
        b = Zg[j+1][i]*(1-tx) + Zg[j+1][i+1]*tx
        return a*(1-ty) + b*ty

    # ---------------------------------------------------------------- le sol
    print("… le sol")
    ANNEAU = [[90,132],[96,112],[118,80],[170,58],[232,48],[292,52],[336,74],[364,112],
              [374,158],[370,204],[356,236],[310,246],[246,252],[186,250],[150,244],
              [130,238],[100,206],[89,174],[88,160]]
    EAU_U = [s["points"] for s in CARTE["sol"] if s["genre"] == "eau"]
    BATI_U = [polygone_reel(s.get("nom",""), s["points"]) for s in CARTE["sol"]
              if s["genre"] == "mur" and 0 < s.get("largeur", 0) <= 4]
    PLACES_U = [polygone_reel(s.get("nom",""), s["points"]) for s in CARTE["sol"]
                if s["genre"] == "champ"
                and s.get("nom", "").startswith(("La grande place", "Le march", "L'aire"))]
    GREVE_U = [s["points"] for s in CARTE["sol"] if s["genre"] in ("greve", "marais")]
    EXCLU = [(boite_de(p), p) for p in (EAU_U + BATI_U + PLACES_U + GREVE_U)]
    BA = boite_de(ANNEAU)

    LIBRE = bytearray(LX*LY)       # 1 = bâtissable ou franchissable
    DANS = bytearray(LX*LY)        # 1 = intra-muros
    for j in range(LY):
        for i in range(LX):
            cx, cy = ux((i+0.5)*CEL), uy((j+0.5)*CEL)
            hit = False
            for (b, p) in EXCLU:
                if b[0] <= cx <= b[2] and b[1] <= cy <= b[3] and dedans(p, cx, cy):
                    hit = True; break
            if hit: continue
            LIBRE[idx(i, j)] = 1
            DANS[idx(i, j)] = 1 if (BA[0] <= cx <= BA[2] and BA[1] <= cy <= BA[3]
                                    and dedans(ANNEAU, cx, cy)) else 0
    for s in CARTE["sol"]:
        if s["genre"] != "mur" or "largeur" in s: continue
        for a, b in zip(s["points"], s["points"][1:]):
            A, B = (mx(a[0]), my(a[1])), (mx(b[0]), my(b[1]))
            n = max(1, int(math.dist(A, B)/3))
            for k in range(n+1):
                t = k/n
                wx, wy = A[0]+(B[0]-A[0])*t, A[1]+(B[1]-A[1])*t
                for di in range(-1, 2):
                    for dj in range(-1, 2):
                        i, j = int(wx/CEL)+di, int(wy/CEL)+dj
                        if 0 <= i < LX and 0 <= j < LY: LIBRE[idx(i, j)] = 0

    # ------------------------------------------------- les artères, intangibles
    RUE = bytearray(LX*LY)
    # LA ROUTE SE PROPAGE AVEC SA DIRECTION, pas seulement avec sa distance.
    # Une distance entière sur grille ne connaît que huit directions : c'est
    # elle qui donnait des files rectilignes et des plaques en chevrons à 45°.
    # On garde donc, par case, le POINT de voirie le plus proche et le CAP de
    # la voie à cet endroit — deux flottants et un angle, propagés par le même
    # parcours. La maison prend alors le cap de sa rue, continûment, et se
    # tourne vers elle.
    SRCX = [0.0]*(LX*LY)
    SRCY = [0.0]*(LX*LY)
    SRCA = [0.0]*(LX*LY)

    def poser(trace, larg):
        """rastérise une voie, et sème son point et son cap sur ce qu'elle touche"""
        r = max(larg/2, CEL*0.5)
        touchees = []
        for a, b in zip(trace, trace[1:]):
            seg = math.dist((a[0],a[1]), (b[0],b[1]))
            if seg < 1e-9: continue
            ang = math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))
            n = max(1, int(seg/(CEL*0.5)))
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
                            k2 = idx(i, j)
                            RUE[k2] = 1
                            SRCX[k2], SRCY[k2], SRCA[k2] = wx, wy, ang
                            touchees.append(k2)
        return touchees
    for e in G["aretes"]:
        if e["couche"] == "L1-surface":
            poser(e["trace"], e["largeur_m"])
    print("   %d × %d cases de %.0f m — %d en voirie"
          % (LX, LY, CEL, sum(RUE)))

    # ------------------------------------------------------------ le quartier
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

    # ------------------------------------------------------- l'emprise de travail
    # Sur un essai d'un quartier, on ne balaie pas les sept cents hectares : on
    # se borne à la boîte du quartier, prise sur son polygone de la carte 2D.
    I0, I1, J0, J1 = 0, LX, 0, LY
    if quartier_seul:
        pts = [(mx(p[0]), my(p[1])) for s in CARTE["sol"]
               if s["genre"] == "village" and s.get("nom") == quartier_seul
               for p in s["points"]]
        if not pts: sys.exit("Quartier inconnu : %s" % quartier_seul)
        MARGE = 200.0
        I0 = int((min(p[0] for p in pts)-MARGE)/CEL); I1 = int((max(p[0] for p in pts)+MARGE)/CEL)
        J0 = int((min(p[1] for p in pts)-MARGE)/CEL); J1 = int((max(p[1] for p in pts)+MARGE)/CEL)
        I0, J0 = max(0, I0), max(0, J0); I1, J1 = min(LX, I1), min(LY, J1)
        print("   emprise d'essai : %d × %d cases" % (I1-I0, J1-J0))

    # ------------------------------------------------------------- LE CHAMP
    # Les hotspots viennent du graphe, comme dans usages.py — on ne les invente
    # pas ici, sans quoi les deux scripts diraient deux villes différentes.
    print("… le champ")
    def noeuds(genres):
        return [n["xyz"] for n in G["noeuds"] if n["genre"] in genres]
    FOYERS = ([(p, 520.0, 1.00) for p in noeuds(("marche",))] +
              [(p, 420.0, 0.85) for p in noeuds(("porte",))] +
              [(p, 380.0, 0.70) for p in noeuds(("quai",))] +
              [(p, 600.0, 0.55) for p in (noeuds(("forteresse",)) or [[3432, 1224, 47]])])
    if not FOYERS:
        FOYERS = [[(2640, 1800, 0), 900.0, 1.0]]
    print("   %d foyers d'attraction" % len(FOYERS))

    DESIR = [0.0]*(LX*LY)
    for j in range(J0, J1):
        wy = (j+0.5)*CEL
        for i in range(I0, I1):
            k = idx(i, j)
            if not (LIBRE[k] and DANS[k]) or RUE[k]: continue
            wx = (i+0.5)*CEL
            v = 0.0
            for (p, portee, poids) in FOYERS:
                d = math.hypot(p[0]-wx, p[1]-wy)
                if d < portee: v += poids*(1.0 - d/portee)
            DESIR[k] = v

    # ------------------------------------------- la distance à une voie, vivante
    # Elle sert deux fois : à ordonner l'accrétion (on bâtit d'abord au bord de
    # la rue, comme on l'a toujours fait), et à savoir quand percer.
    INF = 1 << 30
    DIST = [INF]*(LX*LY)
    def refaire_dist():
        """le BFS complet — une seule fois, au départ"""
        q = deque()
        for k in range(LX*LY):
            if RUE[k]: DIST[k] = 0; q.append(k)
            else: DIST[k] = INF
        while q:
            k = q.popleft()
            i, j = k % LX, k // LX
            d1 = DIST[k] + 1
            for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
                a, b = i+di, j+dj
                if 0 <= a < LX and 0 <= b < LY:
                    n = idx(a, b)
                    if LIBRE[n] and DIST[n] > d1:
                        DIST[n] = d1
                        SRCX[n], SRCY[n], SRCA[n] = SRCX[k], SRCY[k], SRCA[k]
                        q.append(n)

    def maj_dist(graines):
        """LA MISE À JOUR LOCALE, et c'est elle qui change tout. Percer une
        venelle ne modifie les distances que dans son voisinage : refaire le
        BFS sur les deux millions de cases de la ville pour cinquante mètres
        de passage, c'était le gros du temps de calcul. On repart des seules
        cases percées, et l'on ne relâche que ce qui s'améliore — la vague
        s'arrête d'elle-même là où l'ancien chemin était déjà meilleur."""
        q = deque()
        for k in graines:
            if DIST[k] != 0:
                DIST[k] = 0; q.append(k)
        while q:
            k = q.popleft()
            i, j = k % LX, k // LX
            d1 = DIST[k] + 1
            for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
                a, b = i+di, j+dj
                if 0 <= a < LX and 0 <= b < LY:
                    n = idx(a, b)
                    if LIBRE[n] and DIST[n] > d1:
                        DIST[n] = d1
                        SRCX[n], SRCY[n], SRCA[n] = SRCX[k], SRCY[k], SRCA[k]
                        q.append(n)
    refaire_dist()

    # ----------------------------------------------------------- l'accrétion
    print("… l'accrétion")
    PRIS = bytearray(LX*LY)
    # LES CASES ENCORE LIBRES, TENUES À JOUR. Les rebalayer à chaque passe,
    # c'était relire la grille entière pour retrouver le peu qui reste ; ici
    # l'ensemble ne fait que rétrécir, et il rétrécit vite.
    LIBRES_RESTANTS = set()
    for j in range(J0, J1):
        for i in range(I0, I1):
            k = idx(i, j)
            if LIBRE[k] and DANS[k] and not RUE[k]: LIBRES_RESTANTS.add(k)
    def case_libre(x, y):
        i, j = int(x/CEL), int(y/CEL)
        if not (0 <= i < LX and 0 <= j < LY): return False
        k = idx(i, j)
        return bool(LIBRE[k]) and not RUE[k] and not PRIS[k]
    OCC = Occupation(case_libre)

    BATIMENTS = []
    NEUVES = []
    plancher = {}                      # m² de plancher posés, par quartier
    ames = {}                          # et les âmes que ça porte

    def marquer(x, y, f, p, cap):
        """noircir les cases que la parcelle occupe"""
        a = math.radians(cap)
        vx, vy = math.cos(a), math.sin(a)
        nx, ny = -vy, vx
        n_f = max(2, int(f/CEL)+2); n_p = max(2, int(p/CEL)+2)
        for u in range(-n_f, n_f+1):
            for w in range(-n_p, n_p+1):
                du, dw = u*CEL*0.5, w*CEL*0.5
                if abs(du) > f*0.5 or abs(dw) > p*0.5: continue
                px = x + vx*du + nx*dw
                py = y + vy*du + ny*dw
                i, j = int(px/CEL), int(py/CEL)
                if 0 <= i < LX and 0 <= j < LY:
                    k = idx(i, j)
                    PRIS[k] = 1
                    LIBRES_RESTANTS.discard(k)

    def cap_vers_voie(i, j):
        """LE CAP DE LA RUE, pris sur la rue elle-même — et la façade tournée
        vers elle. On ne lit plus un gradient de grille (huit directions, d'où
        les files et les chevrons) : on lit le cap de la voie la plus proche,
        qui est un angle de polyligne, donc continu. Puis on choisit entre ce
        cap et son opposé celui qui met le FOND de la parcelle du côté opposé
        à la rue : une maison tourne le dos à la cour, pas à la rue.
        """
        k = idx(i, j)
        if DIST[k] >= INF: return None
        ang = SRCA[k]
        wx, wy = (i+0.5)*CEL, (j+0.5)*CEL
        vers_rue = (SRCX[k]-wx, SRCY[k]-wy)
        a = math.radians(ang)
        nx, ny = -math.sin(a), math.cos(a)        # le fond de la parcelle
        # si le fond pointe vers la rue, on retourne la maison
        if nx*vers_rue[0] + ny*vers_rue[1] > 0: ang += 180.0
        return ang

    # LE PIÈGE DE PERFORMANCE, et il a fallu le payer une fois : reconstruire
    # le tas à chaque tour, c'est balayer deux millions de cases quatre cents
    # fois. On le construit UNE fois sur l'emprise utile, on le vide, et l'on
    # n'y réinjecte que les abords d'une venelle fraîchement percée.
    def cases_de(*_):
        seuil = PORTEE_VOIE/CEL
        for k in LIBRES_RESTANTS:
            if PRIS[k] or RUE[k] or DIST[k] > seuil: continue
            yield (DIST[k], -DESIR[k], k % LX, k // LX)

    def semer(h, ijs):
        for c in ijs: heapq.heappush(h, c)

    def _corde(a, b, libre_ok):
        """Une courbe libre entre deux points, qui dérive au lieu d'aller droit.

        LA GRILLE SERT À VÉRIFIER, PAS À DESSINER. Suivre le gradient d'un BFS
        à quatre voisins donne des couloirs rectilignes à 0° et 90° : les
        lignes de niveau d'une distance de grille sont alignées sur la grille,
        et lisser une droite laisse une droite. Quatre-vingt-deux pour cent du
        quartier tombait à l'équerre. On tire donc une corde entre les deux
        bouts, on la fait dériver de son milieu, et l'on ne demande à la grille
        que de dire si ça passe.
        """
        lg = math.dist(a, b)
        if lg < 6.0: return [a, b]
        ux_, uy_ = (b[0]-a[0])/lg, (b[1]-a[1])/lg
        nx_, ny_ = -uy_, ux_
        n = max(3, int(lg/7.0))
        for essai in range(3):
            amp = lg*DERIVE*(R.random()-0.5)*(1.0 - 0.3*essai)
            ph = R.random()*math.pi
            pts = []
            for k in range(n+1):
                t = k/n
                d = math.sin(math.pi*t + ph*0)*amp
                pts.append((a[0] + ux_*lg*t + nx_*d, a[1] + uy_*lg*t + ny_*d))
            if all(libre_ok(px, py) for (px, py) in pts): return pts
        return None

    def _venelle(cible):
        """redescend le gradient de DIST jusqu'à la rue, et perce"""
        trace = []
        i, j = cible
        garde = 0
        while DIST[idx(i, j)] > 0 and garde < 4000:
            garde += 1
            trace.append(((i+0.5)*CEL, (j+0.5)*CEL))
            bd, nxt = DIST[idx(i, j)], None
            for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
                a, b = i+di, j+dj
                if 0 <= a < LX and 0 <= b < LY and DIST[idx(a, b)] < bd:
                    bd, nxt = DIST[idx(a, b)], (a, b)
            if nxt is None: break
            i, j = nxt
        trace.append(((i+0.5)*CEL, (j+0.5)*CEL))
        if len(trace) < 2: return None
        trace.reverse()
        # `_venelle` ne fait que RENDRE le tracé : c'est l'appelant qui décide
        # de sa largeur et qui l'inscrit. L'inscrire ici aussi doublait chaque
        # passage de secours dans le graphe.
        return lisser(trace)

    def percer():
        """Perce toutes les poches enclavées — en PASSAGES, pas en fentes.

        Trois choses que l'ancienne version ne faisait pas, et qui décidaient
        de la jouabilité bien plus que de l'allure :

        LE RACCORD. Chaque poche était percée jusqu'à l'artère la plus proche,
        indépendamment des autres : quatre cent soixante-six culs-de-sac dans
        un seul quartier, aucun itinéraire qui traverse. On vise maintenant
        d'abord un passage déjà percé s'il court à moins de `FUSION` — c'est
        ainsi qu'un réseau se forme au lieu d'un peigne.

        LA TRAVERSÉE. Quand la poche est grande, on ressort de l'autre côté :
        un passage qui débouche aux deux bouts est une rue, un passage borgne
        est un piège.

        LA LARGEUR. Elle se prend sur ce que le passage dessert. Une poche de
        trois mille mètres carrés mérite une rue où deux hommes se croisent ;
        un fond de cour mérite deux mètres et pas davantage.
        """
        seuil = PORTEE_VOIE/CEL
        candidates = set()
        for k in LIBRES_RESTANTS:
            if PRIS[k] or RUE[k]: continue
            if DIST[k] < INF and DIST[k] > seuil: candidates.add(k)
        if not candidates: return 0

        def libre_ok(px, py):
            i, j = int(px/CEL), int(py/CEL)
            if not (0 <= i < LX and 0 <= j < LY): return False
            k = idx(i, j)
            return bool(LIBRE[k]) and not PRIS[k]

        perces, vu = 0, set()
        for k0 in list(candidates):
            if k0 in vu: continue
            pile, poche = [k0], []
            vu.add(k0)
            while pile:
                k = pile.pop(); poche.append(k)
                i, j = k % LX, k // LX
                for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
                    a, b = i+di, j+dj
                    if 0 <= a < LX and 0 <= b < LY:
                        n = idx(a, b)
                        if n in candidates and n not in vu:
                            vu.add(n); pile.append(n)
            aire = len(poche)*CEL*CEL
            larg, genre = largeur_venelle(aire)
            fond = max(poche, key=lambda k: DIST[k])
            A = ((fond % LX + 0.5)*CEL, (fond // LX + 0.5)*CEL)

            # LE POINT VISÉ : un passage déjà percé s'il est à portée de main,
            # l'artère sinon. C'est le raccord qui fait le réseau.
            B, motif = (SRCX[fond], SRCY[fond]), "l'artère la plus proche"
            meilleur = FUSION
            for v in NEUVES:
                for (px, py) in v["trace"]:
                    d = math.hypot(px-A[0], py-A[1])
                    if d < meilleur: meilleur, B, motif = d, (px, py), "un passage voisin"

            tr = _corde(A, B, libre_ok)
            if tr is None:
                tr = _venelle((fond % LX, fond // LX))     # la grille, en secours
                if not tr: continue
            NEUVES.append({"trace": [[round(p[0],1), round(p[1],1)] for p in tr],
                           "largeur_m": larg, "genre": genre,
                           "raison": "Le fond de l'îlot était hors de portée ; le passage "
                                     "a été percé vers %s, et il est resté." % motif})
            maj_dist(poser(tr, larg))
            perces += 1

            # LA TRAVERSÉE : si la poche est grande, on ressort de l'autre bord
            if aire > 2200 and len(poche) > 12:
                loin_ = max(poche, key=lambda k: (k % LX - A[0]/CEL)**2 + (k // LX - A[1]/CEL)**2)
                C2 = ((loin_ % LX + 0.5)*CEL, (loin_ // LX + 0.5)*CEL)
                if math.hypot(C2[0]-A[0], C2[1]-A[1]) > 24.0:
                    tr2 = _corde(A, C2, libre_ok)
                    if tr2:
                        NEUVES.append({"trace": [[round(p[0],1), round(p[1],1)] for p in tr2],
                                       "largeur_m": larg, "genre": genre,
                                       "raison": "On ne s'arrête pas au fond : le passage "
                                                 "ressort de l'autre côté, et l'on traverse."})
                        maj_dist(poser(tr2, larg))
                        perces += 1
        return perces

    # LE QUOTA, PAR QUARTIER. L'arrêt comparait chaque quartier aux quatre cent
    # mille âmes de la ville entière : il ne s'arrêtait donc jamais, et le
    # premier quartier servi avalait tout le budget. On répartit la cible au
    # prorata de ce que chaque sol peut porter — sa surface libre divisée par
    # ses mètres carrés par âme, ce qui donne sa capacité, et non sa taille.
    aire_q = {}
    for k in LIBRES_RESTANTS:
        q = quartier((k % LX + 0.5)*CEL, (k // LX + 0.5)*CEL)
        aire_q[q] = aire_q.get(q, 0.0) + CEL*CEL
    capacite = dict((q, a/m2_par_ame(q)) for q, a in aire_q.items())
    somme = sum(capacite.values()) or 1.0
    QUOTA = dict((q, AMES_CIBLE*c/somme) for q, c in capacite.items())
    if quartier_seul:
        # sur un essai d'un seul quartier, la cible est SA part de la ville
        print("   quota du quartier : %d âmes" % int(QUOTA.get(quartier_seul, 0)))

    pose_tot = 0
    h = []
    semer(h, cases_de())
    print("   %d cases candidates au départ" % len(h))
    for tour in range(60):
        if not h:
            if not percer(): break
            semer(h, cases_de())
            continue
        avance = 0
        while h:
            _, _, i, j = heapq.heappop(h)
            k = idx(i, j)
            if PRIS[k] or RUE[k]: continue
            q = quartier((i+0.5)*CEL, (j+0.5)*CEL)
            if quartier_seul and q != quartier_seul: continue
            if ames.get(q, 0.0) >= QUOTA.get(q, 1e18): continue
            cap = cap_vers_voie(i, j)
            if cap is None: continue
            fmin, fmax, prof, etages, he = gabarit(q)
            joint, _ = grain(q)
            f = fmin + R.random()*(fmax-fmin)
            xf, yf = (i+0.5)*CEL, (j+0.5)*CEL
            t = OCC.tailler(xf, yf, f, prof, cap, joint)
            if not t: continue
            x, y, f2, p2 = t
            OCC.occuper(x, y, f2, p2, cap)
            marquer(x, y, f2, p2, cap)
            et = R.randint(*etages)
            usage = USAGE.get(q, "maison")
            if q.startswith(("Le faubourg", "Les baraques", "Le bourg")): usage = "cabane"
            BATIMENTS.append([round(x,1), round(y,1), round(zsol(x,y),1),
                              round(cap,1), round(f2,1), round(p2,1),
                              et, round(et*he+1.2,1), q, usage,
                              1 if (usage in ("entrepot","forge","hôtel","maison d'officier")
                                    or R.random() < 0.25) else 0])
            s = f2*p2*et
            plancher[q] = plancher.get(q, 0.0) + s
            ames[q] = ames.get(q, 0.0) + s/m2_par_ame(q)
            avance += 1; pose_tot += 1
        # On ne refait la carte des distances QUE si l'on a percé : c'est la
        # seule chose qui la change. La refaire à chaque tour, c'était un BFS
        # de deux millions de cases pour rien.
        n_perce = percer()
        print("   passe %2d — %6d parcelles, %6d âmes, %d venelles (+%d), %d cases libres"
              % (tour, pose_tot, int(sum(ames.values())), len(NEUVES), n_perce,
                 len(LIBRES_RESTANTS)))
        sys.stdout.flush()
        if not n_perce: break
        semer(h, cases_de())

    # ------------------------------------------------------------- le compte
    total_ames = sum(ames.values())
    emprise = sum(b[4]*b[5] for b in BATIMENTS)
    print()
    print("   %d parcelles — %d âmes portées (cible %d)"
          % (len(BATIMENTS), int(total_ames), int(AMES_CIBLE)))
    print("   %d venelles percées" % len(NEUVES))
    print("   emprise bâtie : %.0f m²" % emprise)
    for q in sorted(ames, key=lambda z: -ames[z])[:8]:
        print("     %-26s %7d âmes  %9.0f m² de plancher"
              % (q, int(ames[q]), plancher[q]))

    io.open(os.path.join(RACINE, sortie), "w", encoding="utf-8").write(
        json.dumps({"_colonnes": ["x", "y", "z", "cap", "facade_m", "profondeur_m",
                                  "etages", "hauteur_m", "quartier", "usage", "cave"],
                    "bati": BATIMENTS}, ensure_ascii=False, separators=(",", ":")))
    print("   écrit — %s" % sortie)
    return NEUVES


if __name__ == "__main__":
    main(sys.argv[1:])
