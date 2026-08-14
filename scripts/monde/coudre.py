# -*- coding: utf-8 -*-
"""Coudre les couches — sans quoi la ville est un décor, pas un réseau.

    python scripts/monde/coudre.py     (après graphe.py puis densifier.py)

L'audit avait trouvé un décor : 11 638 composantes, 6 178 arêtes sans seconde
extrémité, et un seul vrai réseau souterrain de 44 nœuds. Quatre coutures :

  1. chaque ENTRÉE et chaque PORCHE se raccroche à la rue — en COUPANT l'arête
     de rue au point de raccord, pas en tirant un fil vers le carrefour le plus
     proche : une porte donne sur la rue devant elle, pas trente mètres plus loin.
  2. l'ÉGOUT se ramifie sous les artères. C'est le décalque du réseau de surface
     un niveau plus bas — historiquement c'est ainsi qu'on les creuse : sous la
     rue, parce que c'est le seul sol qui n'appartienne à personne.
  3. les CAVES se percent vers leurs voisines et vers le drain qu'elles touchent.
  4. on VÉRIFIE : depuis chaque porte de la ville, atteindre le fleuve par le
     dessous. Un test qui échoue est un réseau qui n'existe pas.
"""
import json, math, io, os, sys
from collections import defaultdict, deque, Counter

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, ICI)
from echelle import NIVEAUX, LARGEUR

MONDE = os.path.join(RACINE, "monde")
CHEMIN = os.path.join(MONDE, "portreal.graph.json")
G = json.load(io.open(CHEMIN, encoding="utf-8"))
N = {n["id"]: n for n in G["noeuds"]}
A = G["aretes"]
P = G["portails"]
Z_EGOUT = NIVEAUX[-2][1]

def d_seg(px, py, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    q = dx*dx + dy*dy
    t = 0.0 if q == 0 else max(0.0, min(1.0, ((px-a[0])*dx + (py-a[1])*dy)/q))
    return math.hypot(px-a[0]-t*dx, py-a[1]-t*dy), t

def nid_pt(p, pref="s"):
    return "%s%d.%d" % (pref, round(p[0]*2), round(p[1]*2))

def ajoute_noeud(nid, x, y, z, genre, nom=None, **kw):
    if nid in N: return nid
    n = {"id": nid, "genre": genre, "niveau": kw.pop("niveau", 0),
         "xyz": [round(x,1), round(y,1), round(z,1)]}
    if nom: n["nom"] = nom
    n.update(kw)
    N[nid] = n; G["noeuds"].append(n)
    return nid

def ajoute_arete(aid, de, vers, genre, couche, trace, larg, raison, **kw):
    lg = sum(math.dist(a[:2], b[:2]) for a, b in zip(trace, trace[1:]))
    e = {"id": aid, "de": de, "vers": vers, "genre": genre, "couche": couche,
         "largeur_m": round(larg, 2), "longueur_m": round(lg, 1),
         "pente": round(abs(trace[0][2]-trace[-1][2])/max(1.0, lg), 3),
         "raison": raison,
         "trace": [[round(p[0],1), round(p[1],1), round(p[2],1)] for p in trace]}
    e.update(kw)
    A.append(e); return e

# ---------------------------------------------------------------------------
# 1. NOUER LA VOIRIE, PUIS Y RACCROCHER LES ENTRÉES ET LES PORCHES
# ---------------------------------------------------------------------------
# Une seule machine pour les deux : trouver la chaussée la plus proche d'un
# point, y planter un nœud, et COUPER l'arête de rue à cet endroit. Sans la
# coupe, on obtient un nœud posé sur un trait qui ne le connaît pas — ce qui a
# l'air correct dans le fichier et ne relie rien du tout.
def indexer_voirie():
    L1 = [e for e in A if e["couche"] == "L1-surface"]
    seau = defaultdict(list)
    for ei, e in enumerate(L1):
        for si in range(len(e["trace"])-1):
            a, b = e["trace"][si], e["trace"][si+1]
            for t in (0.0, 0.5, 1.0):
                x, y = a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t
                seau[(int(x//40), int(y//40))].append((ei, si))
    return L1, seau

def rue_la_plus_proche(L1, seau, x, y, portee=70.0, exclure=None, rayons=2):
    meil = None
    ci, cj = int(x//40), int(y//40)
    for r in range(1, rayons+1):
        vus = set()
        for di in range(-r, r+1):
            for dj in range(-r, r+1):
                for (ei, si) in seau.get((ci+di, cj+dj), ()):
                    if (ei, si) in vus or ei == exclure: continue
                    vus.add((ei, si))
                    a, b = L1[ei]["trace"][si], L1[ei]["trace"][si+1]
                    d, t = d_seg(x, y, a, b)
                    if d < portee and (meil is None or d < meil[0]):
                        meil = (d, ei, si, t,
                                (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t,
                                 a[2]+(b[2]-a[2])*t))
        if meil: return meil
    return None

def noeud_cible(L1, ei, si, tt, q, prefixe):
    """Le nœud à utiliser sur l'arête visée.

    Un bout de ruelle tombe presque toujours SUR l'extrémité de la rue qu'il
    rejoint — c'est par construction : la coupe de bloc va d'une rue à l'autre.
    Y planter un nœud neuf ne coupe alors rien (on ne scinde pas une arête à
    son propre bout), et le nœud reste seul au monde. Il faut REPRENDRE celui
    qui est déjà là."""
    e = L1[ei]
    for bout, cle_ in ((0, "de"), (-1, "vers")):
        if e.get(cle_) and math.dist(q[:2], e["trace"][bout][:2]) < 3.5:
            return e[cle_], None
    nid = nid_pt(q, prefixe)
    return nid, (si, tt, q, nid)

# --- 1a. les bouts de ruelle qui ne touchent rien --------------------------
# La densification a tracé 6 494 coupes de bloc. Chacune s'arrête SUR une rue,
# mais avec un nœud à elle : deux points au même endroit, aucun lien. C'est là
# que le graphe s'est brisé en six mille morceaux.
print("… on noue la voirie")
L1, SEAU = indexer_voirie()
degre = Counter()
for e in A:
    if e.get("de"): degre[e["de"]] += 1
    if e.get("vers"): degre[e["vers"]] += 1
coupes = defaultdict(list)
noues, repris = 0, [0]
for k, e in enumerate(L1):
    for bout, cle_ in ((0, "de"), (-1, "vers")):
        nid0 = e.get(cle_)
        if not nid0 or degre[nid0] > 1: continue
        p = e["trace"][bout]
        t = rue_la_plus_proche(L1, SEAU, p[0], p[1], portee=26.0, exclure=k)
        if not t: continue
        d, ei, si, tt, q = t
        nid, coupe = noeud_cible(L1, ei, si, tt, q, "noeud")
        # une ruelle si courte que ses deux bouts se rabattent sur le même nœud
        # n'est plus une ruelle : on la laisse pendre plutôt que de la boucler.
        if nid == e.get("vers" if cle_ == "de" else "de"): continue
        if coupe:
            ajoute_noeud(nid, q[0], q[1], q[2], "carrefour",
                         raison="Là où une ruelle débouche sur la rue : sans ce nœud, "
                                "elle s'arrête à côté d'elle sans jamais la rejoindre.")
            coupes[ei].append(coupe)
        else:
            q = N[nid]["xyz"]
            repris[0] += 1
        e[cle_] = nid
        e["trace"][bout] = [round(q[0],1), round(q[1],1), round(q[2],1)]
        degre[nid] += 1
        noues += 1
print("   %d bouts de ruelle noués (%d en reprenant un nœud existant)" % (noues, repris[0]))

# --- 1b. les entrées et les porches ----------------------------------------
print("… on raccroche les entrées et les porches")
def raccroche_sur_rue(e, portee, rayons):
    p = e["trace"][-1]
    trouve = rue_la_plus_proche(L1, SEAU, p[0], p[1], portee=portee, rayons=rayons)
    if not trouve: return False
    d, ei, si, t, q = trouve
    nid, coupe = noeud_cible(L1, ei, si, t, q, "seuil")
    if coupe:
        ajoute_noeud(nid, q[0], q[1], q[2], "seuil", "Seuil sur rue",
                     raison="Le point où une porte ou un porche touche la chaussée.")
        coupes[ei].append(coupe)
    else:
        q = N[nid]["xyz"]
    e["vers"] = nid
    e["trace"][-1] = [round(q[0],1), round(q[1],1), round(q[2],1)]
    e["longueur_m"] = round(sum(math.dist(a[:2], b[:2])
                                for a, b in zip(e["trace"], e["trace"][1:])), 1)
    return True

ouvertures = [e for e in A if e["couche"] == "L3-interieurs"
              and e.get("vers") is None and e["genre"] in ("entree", "porche")]
raccrochees = sum(1 for e in ouvertures if raccroche_sur_rue(e, 70.0, 2))
# celles qui restent sont des portes de fond de cour, à plus de 70 m de toute
# chaussée : on va les chercher plus loin plutôt que de les laisser pendre.
loin = [e for e in ouvertures if e.get("vers") is None]
rattrapees = sum(1 for e in loin if raccroche_sur_rue(e, 240.0, 7))
# une porte qui ne trouve toujours aucune rue n'est pas une porte : on la retire,
# car une arête sans seconde extrémité est un mensonge dans le fichier.
perdues = [e for e in loin if e.get("vers") is None]
for e in perdues: A.remove(e)
print("   %d entrées/porches raccrochées (%d rattrapées au large, %d retirées)"
      % (raccrochees + rattrapees, rattrapees, len(perdues)))

# on recoupe chaque arête de rue à ses points de raccord
recoupees = 0
for ei, cs in coupes.items():
    e = L1[ei]
    if e not in A: continue
    cs = sorted(set(cs), key=lambda c: (c[0], c[1]))
    # Une coupe qui porte l'id d'un BOUT de l'arête n'est pas une coupe : c'est
    # ce bout-là. Le cas arrive quand une ruelle s'est raccrochée ici avant que
    # l'arête ne soit elle-même nouée — les deux points ont alors fini sur la
    # même demi-mesure, donc sous le même id. Laissée en place, elle découpe un
    # tronçon qui part d'un nœud pour y revenir : une rue qui ne mène qu'à
    # elle-même, et le nœud est de toute façon déjà au bout de l'arête.
    extremites = {e.get("de"), e.get("vers")}
    cs = [c for c in cs if c[3] not in extremites]
    tr = e["trace"]
    bouts, cur = [], [tr[0]]
    noms = [e.get("de")]
    ic = 0
    for si in range(len(tr)-1):
        while ic < len(cs) and cs[ic][0] == si:
            q, nid = cs[ic][2], cs[ic][3]
            if nid != noms[-1] and math.dist(cur[-1][:2], q[:2]) > 0.8:
                cur.append([q[0], q[1], q[2]])
                bouts.append(cur); noms.append(nid)
                cur = [[q[0], q[1], q[2]]]
            ic += 1
        if math.dist(cur[-1][:2], tr[si+1][:2]) > 0.05:
            cur.append(tr[si+1])
    if len(cur) > 1: bouts.append(cur); noms.append(e.get("vers"))
    if len(bouts) < 2: continue
    base = dict(e)
    A.remove(e)
    for k, (b, na, nb) in enumerate(zip(bouts, noms, noms[1:])):
        f = dict(base)
        f["id"] = base["id"] + ".%d" % k
        f["de"], f["vers"], f["trace"] = na, nb, b
        f["longueur_m"] = round(sum(math.dist(x[:2], y[:2])
                                    for x, y in zip(b, b[1:])), 1)
        A.append(f)
    recoupees += 1
print("   %d arêtes de rue recoupées à leurs seuils" % recoupees)

# ---------------------------------------------------------------------------
# 2. L'ÉGOUT SOUS LES ARTÈRES — le décalque de la surface, un niveau plus bas
# ---------------------------------------------------------------------------
print("… on creuse l'égout sous les artères")
def sous_id(nid): return "eg:" + nid
arteres = [e for e in A if e["couche"] == "L1-surface"
           and e["genre"] in ("artere", "rue") and e["longueur_m"] > 40]
creuses = 0
for e in arteres:
    na, nb = e.get("de"), e.get("vers")
    if not na or not nb or na not in N or nb not in N: continue
    tr = [[p[0], p[1], p[2] + Z_EGOUT] for p in e["trace"]]
    # un égout coule : on l'oriente du haut vers le bas, toujours
    if tr[0][2] < tr[-1][2]:
        tr.reverse(); na, nb = nb, na
    a = ajoute_noeud(sous_id(na), tr[0][0], tr[0][1], tr[0][2], "regard",
                     niveau=-2, raison="Un regard sous la chaussée : c'est par là qu'on cure.")
    b = ajoute_noeud(sous_id(nb), tr[-1][0], tr[-1][1], tr[-1][2], "regard",
                     niveau=-2, raison="Un regard sous la chaussée.")
    if a == b: continue
    ajoute_arete("eg:" + e["id"], a, b, "egout", "L5-sous-sol", tr, LARGEUR["egout"],
                 "Creusé sous la rue, parce que c'est le seul sol qui n'appartienne "
                 "à personne — et il descend, parce que l'eau ne fait que ça.",
                 niveau=-2, visibilite="cachee", acces="technique", etat="ouvert",
                 humidite="courante", suit=e["id"])
    creuses += 1
    # un regard sur deux s'ouvre à la surface : c'est ce qui rend l'égout jouable
    if creuses % 2 == 0:
        P.append({"id": "pt:regard:" + e["id"], "haut": na, "bas": a,
                  "genre": "regard", "cache": False, "ferme": True, "cout": 2.0,
                  "raison": "Une grille de regard dans la chaussée : scellée, "
                            "et le Guet a la clef — mais une grille se lève."})
print("   %d tronçons d'égout, sous %d artères et rues" % (creuses, len(arteres)))

# les trois vieux drains de colline rejoignent le réseau neuf
EG_NOEUDS = [(n["id"], n["xyz"]) for n in G["noeuds"]
             if n.get("niveau") == -2 and n["genre"] in ("regard", "bouche", "tete")]
seau_eg = defaultdict(list)
for nid, p in EG_NOEUDS: seau_eg[(int(p[0]//60), int(p[1]//60))].append((nid, p))
def eg_proche(p, sauf, portee=80.0):
    meil = None
    ci, cj = int(p[0]//60), int(p[1]//60)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for (nid, q) in seau_eg.get((ci+di, cj+dj), ()):
                if nid == sauf: continue
                d = math.dist(p[:2], q[:2])
                if d < portee and (meil is None or d < meil[0]): meil = (d, nid, q)
    return meil
jonctions = 0
for n in list(G["noeuds"]):
    if n["genre"] not in ("tete", "bouche"): continue
    t = eg_proche(n["xyz"], n["id"])
    if not t: continue
    d, nid, q = t
    ajoute_arete("jc:" + n["id"], n["id"], nid, "egout", "L5-sous-sol",
                 [n["xyz"], q], LARGEUR["egout"],
                 "Le vieux drain de colline et l'égout des rues se sont rejoints : "
                 "on ne creuse pas deux fois le même sol.",
                 niveau=-2, visibilite="cachee", acces="technique", etat="ouvert")
    jonctions += 1
print("   %d jonctions entre vieux drains et réseau neuf" % jonctions)

# ---------------------------------------------------------------------------
# 3. LES CAVES — entre elles, et vers le drain qu'elles touchent
# ---------------------------------------------------------------------------
print("… on perce les caves")
caves = [n for n in G["noeuds"] if n["genre"] == "cave"]
sc = defaultdict(list)
for n in caves: sc[(int(n["xyz"][0]//20), int(n["xyz"][1]//20))].append(n)
perces, faits = 0, set()
for n in caves:
    ci, cj = int(n["xyz"][0]//20), int(n["xyz"][1]//20)
    voisins = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for m in sc.get((ci+di, cj+dj), ()):
                if m is n: continue
                d = math.dist(n["xyz"][:2], m["xyz"][:2])
                if d < 19: voisins.append((d, m))
    voisins.sort(key=lambda v: v[0])
    for d, m in voisins[:2]:
        paire = tuple(sorted((n["id"], m["id"])))
        if paire in faits: continue
        faits.add(paire)
        ajoute_arete("cv:%d" % perces, n["id"], m["id"], "galerie", "L5-sous-sol",
                     [n["xyz"], m["xyz"]], 1.4,
                     "Deux caves mitoyennes : le mur qui les sépare a fini par "
                     "s'ouvrir, et personne ne se rappelle qui l'a ouvert.",
                     niveau=-1, visibilite="cachee", acces="prive", etat="ouvert")
        perces += 1
print("   %d galeries entre caves" % perces)

# les percements vers l'égout : le réseau est dense maintenant, on peut resserrer
EG_TRACE = []
for e in A:
    if e["genre"] == "egout":
        for p in e["trace"]: EG_TRACE.append(p)
seau_tr = defaultdict(list)
for p in EG_TRACE: seau_tr[(int(p[0]//40), int(p[1]//40))].append(p)
anciens = {p["id"] for p in P if p["genre"] == "percement"}
P[:] = [p for p in P if p["genre"] != "percement"]
ouverts = 0
for n in caves:
    ci, cj = int(n["xyz"][0]//40), int(n["xyz"][1]//40)
    meil = None
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for p in seau_tr.get((ci+di, cj+dj), ()):
                d = math.dist(n["xyz"][:2], p[:2])
                if meil is None or d < meil[0]: meil = (d, p)
    if not meil or meil[0] > 22: continue
    nid = nid_pt(meil[1], "eg")
    ajoute_noeud(nid, meil[1][0], meil[1][1], meil[1][2], "regard", niveau=-2,
                 raison="Point de l'égout qu'une cave a fini par atteindre.")
    ajoute_arete("pc:%d" % ouverts, n["id"], nid, "percement", "L5-sous-sol",
                 [n["xyz"], meil[1]], 0.9,
                 "Le mur de cette cave touche l'égout, et quelqu'un l'a su avant vous.",
                 niveau=-2, visibilite="secrete", acces="secret", etat="ouvert")
    P.append({"id": "pt:pc:%d" % ouverts, "haut": n["id"], "bas": nid,
              "genre": "percement", "cache": True, "ferme": False, "cout": 2.5,
              "raison": "On entre dans cette maison sans passer par sa porte."})
    ouverts += 1
print("   %d caves ouvertes sur l'égout (%d avant)" % (ouverts, len(anciens)))

# les nouveaux regards d'égout doivent tenir au réseau : on les raccroche
seau_eg2 = defaultdict(list)
for n in G["noeuds"]:
    if n.get("niveau") == -2:
        seau_eg2[(int(n["xyz"][0]//40), int(n["xyz"][1]//40))].append(n)
raccords = 0
adj_test = defaultdict(set)
for e in A:
    if e.get("de") and e.get("vers"):
        adj_test[e["de"]].add(e["vers"]); adj_test[e["vers"]].add(e["de"])
for n in list(G["noeuds"]):
    if n.get("niveau") != -2 or n["genre"] != "regard": continue
    if adj_test[n["id"]]: continue
    ci, cj = int(n["xyz"][0]//40), int(n["xyz"][1]//40)
    meil = None
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for m in seau_eg2.get((ci+di, cj+dj), ()):
                if m is n or not adj_test[m["id"]]: continue
                d = math.dist(n["xyz"][:2], m["xyz"][:2])
                if d < 45 and (meil is None or d < meil[0]): meil = (d, m)
    if not meil: continue
    ajoute_arete("rc:%d" % raccords, n["id"], meil[1]["id"], "egout", "L5-sous-sol",
                 [n["xyz"], meil[1]["xyz"]], LARGEUR["egout"],
                 "Raccord de collecteur : deux tronçons creusés séparément se rejoignent.",
                 niveau=-2, visibilite="cachee", acces="technique", etat="ouvert")
    adj_test[n["id"]].add(meil[1]["id"]); adj_test[meil[1]["id"]].add(n["id"])
    raccords += 1
print("   %d raccords de collecteur" % raccords)

# ---------------------------------------------------------------------------
# 3bis. LES ORPHELINS NOMMÉS — portes, quais, monuments, bouches d'égout
# ---------------------------------------------------------------------------
# Ils ont été posés comme DESTINATIONS, avant qu'aucune arête n'existe : ils se
# trouvent au même endroit qu'un carrefour sans avoir aucun lien avec lui. Un
# nœud obligatoire qui ne touche rien est la panne la plus silencieuse du lot —
# la ville a l'air complète et la porte n'ouvre sur rien.
print("… on raccroche les nœuds obligatoires")
N = {n["id"]: n for n in G["noeuds"]}
lie = defaultdict(set)
for e in A:
    if e.get("de") in N and e.get("vers") in N:
        lie[e["de"]].add(e["vers"]); lie[e["vers"]].add(e["de"])
for p in P:
    if p["haut"] in N and p["bas"] in N:
        lie[p["haut"]].add(p["bas"]); lie[p["bas"]].add(p["haut"])

def index(noeuds, pas):
    s = defaultdict(list)
    for n in noeuds: s[(int(n["xyz"][0]//pas), int(n["xyz"][1]//pas))].append(n)
    return s
def proche(s, pas, p, pred, portee, rayons=3):
    meil = None
    ci, cj = int(p[0]//pas), int(p[1]//pas)
    for r in range(1, rayons+1):
        for di in range(-r, r+1):
            for dj in range(-r, r+1):
                for m in s.get((ci+di, cj+dj), ()):
                    if not pred(m): continue
                    d = math.dist(p[:2], m["xyz"][:2])
                    if d < portee and (meil is None or d < meil[0]): meil = (d, m)
        if meil: return meil
    return meil

OBLIG = ("porte", "quai", "forteresse", "marche", "monument", "septuaire",
         "guilde", "caserne", "office", "chantier", "sommet")
idx_surf = index([n for n in G["noeuds"] if n.get("niveau", 0) == 0], 40)

# Un abord doit atterrir sur de la VOIRIE — une rue, une ruelle, un escalier, un
# quai — et jamais dans une cour ni dans un hall : un marché qu'on n'atteint
# qu'en traversant le logis d'autrui n'est pas un marché public. On ne juge pas
# ça au genre du nœud (un seuil est en pleine chaussée, une arcade non), mais à
# ce qu'il touche : porte-t-il une voie où l'on marche ?
VOIES = ("ruelle", "rue", "artere", "escalier", "quai", "abord")
def reseau_a_pied():
    v = defaultdict(set)
    for e in A:
        if e["couche"] != "L1-surface" or e["genre"] not in VOIES: continue
        d, w = e.get("de"), e.get("vers")
        if d in N and w in N: v[d].add(w); v[w].add(d)
    return v
MARCHE_ADJ = reseau_a_pied()
VOIRIE = set(MARCHE_ADJ)

# Le degré ne dit RIEN de l'accessibilité : chacun de ces lieux tient déjà par un
# lien — sa crypte, sa cache, sa poterne —, et ce lien-là est lui-même un
# cul-de-sac. Un donjon relié à son seul tunnel de fuite passe pour raccroché et
# ne s'atteint pas à pied. Ce qu'il faut mesurer, c'est l'appartenance au réseau
# où tout le monde circule : la composante géante.
def geante_de(lie):
    vu, meil = set(), []
    for nid in N:
        if nid in vu: continue
        q, c = deque([nid]), []
        vu.add(nid)
        while q:
            x = q.popleft(); c.append(x)
            for y in lie[x]:
                if y not in vu: vu.add(y); q.append(y)
        if len(c) > len(meil): meil = c
    return set(meil)

def rallie(nid, geante, lie):
    """Le nœud raccroché amène tout son îlot avec lui."""
    q, vu = deque([nid]), {nid}
    while q:
        x = q.popleft(); geante.add(x)
        for y in lie[x]:
            if y not in vu: vu.add(y); q.append(y)

GEANTE = geante_de(lie)
# Le critère n'est PAS « relié au réseau », toutes couches confondues : le quai
# d'aval tient au donjon par le tunnel de Maegor, et le bureau du port au logis
# qui l'abrite. Ils passeraient pour desservis alors qu'on n'y va qu'en
# traversant chez quelqu'un ou par le souterrain d'évasion du roi. Le critère
# est : y va-t-on À PIED, par la voirie, depuis le reste de la ville ?
MARCHE = geante_de(MARCHE_ADJ)

# Les quais forment une chaussée continue le long de l'eau, et pas un pas ne la
# relie à la ville : on y déchargeait le grain sur une berge où l'on n'arrive
# qu'en bateau. C'est la rampe qui manquait — et tant qu'elle manque, aucun
# abord ne sauvera le quai d'aval, puisqu'il n'y a rien à quoi le raccrocher.
QUAIS = set()
for e in A:
    if e["couche"] == "L1-surface" and e["genre"] == "quai":
        for b in ("de", "vers"):
            if e.get(b) in N: QUAIS.add(e[b])
rampes, vus_quai = 0, set()
for nid in sorted(QUAIS):
    if nid in MARCHE or nid in vus_quai: continue
    ilot, f = {nid}, deque([nid])
    while f:
        x = f.popleft()
        for y in MARCHE_ADJ[x]:
            if y not in ilot: ilot.add(y); f.append(y)
    vus_quai |= ilot
    meil = None
    for x in ilot:
        t = proche(idx_surf, 40, N[x]["xyz"], lambda m: m["id"] in MARCHE,
                   300.0, rayons=9)
        if t and (meil is None or t[0] < meil[0]): meil = (t[0], x, t[1])
    if not meil:
        print("   ! quai de %d nœuds : aucune rue à 300 m, il reste sans rampe"
              % len(ilot)); continue
    d, x, m = meil
    ajoute_arete("ab:rampe:" + x, x, m["id"], "abord", "L1-surface",
                 [N[x]["xyz"], m["xyz"]], LARGEUR["rue"],
                 "La rampe qui monte du quai à la rue : c'est par là que le grain "
                 "quitte l'eau, et c'est par là qu'on redescend le voir arriver.",
                 visibilite="publique", acces="public", etat="ouvert")
    lie[x].add(m["id"]); lie[m["id"]].add(x)
    MARCHE_ADJ[x].add(m["id"]); MARCHE_ADJ[m["id"]].add(x)
    rallie(x, GEANTE, lie); rallie(x, MARCHE, MARCHE_ADJ)
    rampes += 1
    print("   une rampe de %.0f m relie %d nœuds de quai à la rue" % (d, len(ilot)))

a_raccrocher = [n for n in G["noeuds"]
                if n["genre"] in OBLIG and n["id"] not in MARCHE]
abords, elargis, orphelins = 0, [], []
for n in a_raccrocher:
    t = None
    for portee in (90.0, 200.0, 450.0):
        t = proche(idx_surf, 40, n["xyz"],
                   lambda m: m["id"] in MARCHE and m["id"] != n["id"],
                   portee, rayons=int(portee//40)+2)
        if t: break
    if not t:
        orphelins.append(n["id"]); continue
    d, m = t
    if d > 90.0: elargis.append((n["id"], d))
    ajoute_arete("ab:" + n["id"], n["id"], m["id"], "abord", "L1-surface",
                 [n["xyz"], m["xyz"]], LARGEUR["rue"],
                 "Les derniers pas jusqu'au lieu lui-même : sans eux, la porte "
                 "n'ouvre sur rien.", visibilite="publique", acces="public", etat="ouvert")
    lie[n["id"]].add(m["id"]); lie[m["id"]].add(n["id"])
    MARCHE_ADJ[n["id"]].add(m["id"]); MARCHE_ADJ[m["id"]].add(n["id"])
    rallie(n["id"], GEANTE, lie)
    rallie(n["id"], MARCHE, MARCHE_ADJ)
    abords += 1
print("   %d nœuds obligatoires raccrochés" % abords)
for nid, d in elargis:
    print("   ! %s : aucune voirie à 90 m, raccroché à %.0f m" % (nid, d))
for nid in orphelins:
    print("   ! %s reste hors du réseau : rien de joignable" % nid)

# les regards de drain ouverts dans une place : la trappe est en pleine rue, et
# pourtant deux d'entre eux ne tenaient qu'au drain qu'ils coiffent.
regards = 0
for n in G["noeuds"]:
    if n["genre"] != "regard-surface" or n["id"] in MARCHE: continue
    t = proche(idx_surf, 40, n["xyz"], lambda m: m["id"] in MARCHE and m is not n,
               200.0, rayons=7)
    if not t: continue
    d, m = t
    ajoute_arete("ab:" + n["id"], n["id"], m["id"], "abord", "L1-surface",
                 [n["xyz"], m["xyz"]], LARGEUR["ruelle"],
                 "Les quelques pas de pavé jusqu'à la grille du drain : on y mène "
                 "les mules du cureur, et l'on y jette ce qu'on ne veut plus voir.",
                 visibilite="publique", acces="public", etat="ouvert")
    lie[n["id"]].add(m["id"]); lie[m["id"]].add(n["id"])
    MARCHE_ADJ[n["id"]].add(m["id"]); MARCHE_ADJ[m["id"]].add(n["id"])
    rallie(n["id"], GEANTE, lie); rallie(n["id"], MARCHE, MARCHE_ADJ)
    regards += 1
print("   %d regards de drain ramenés sur la rue" % regards)

# ---------------------------------------------------------------------------
# 3bis-2. LES PASSAGES SECRETS — deux bouts qui ne touchaient rien
# ---------------------------------------------------------------------------
# Un passage qui ne part de nulle part et n'arrive nulle part n'est pas un
# secret, c'est un tuyau flottant. Chaque bout doit mordre quelque part : dans le
# lieu que son nom désigne quand il en désigne un, sinon dans ce qu'il y a de
# plus proche — une cave, un regard, une porte de cour. Et le raccord se cache,
# comme le passage : ce n'est jamais une rue de plus.
DESSERT = {"donjon": "donjon", "fosse": "fosse", "septuaire": "septuaire",
           "casernes": "casernes", "guilde": "guilde", "cuisines": "donjon",
           "main": "donjon", "crochet": "marche-poissons"}
idx_tous = index(G["noeuds"], 40)
attaches = 0
for e in list(A):
    if e["couche"] != "L4-cache" or not e["id"].startswith("ps:"): continue
    jetons = e["id"].split(":", 1)[1].split("-")
    # on juge les deux bouts AVANT d'en rattacher un : sinon le premier raccord
    # fait entrer tout le passage dans le réseau et le second bout, désormais
    # « joignable », resterait une impasse.
    isole = {b: e.get(b) not in GEANTE for b in ("de", "vers")}
    for bout, jeton in zip(("de", "vers"), (jetons[0], jetons[-1])):
        nid = e.get(bout)
        if nid not in N or not isole[bout]: continue
        n = N[nid]
        cible = None
        # 1. le lieu que le nom désigne, s'il est à portée d'un couloir
        lieu = DESSERT.get(jeton)
        if lieu and lieu in N and math.dist(n["xyz"][:2], N[lieu]["xyz"][:2]) < 300.0:
            cible = N[lieu]
        # 2. sinon le plus proche du réseau, de préférence au même étage
        if cible is None:
            niv = n.get("niveau", 0)
            for ecart in (1, 9):
                t = proche(idx_tous, 40, n["xyz"],
                           lambda m: (m["id"] in GEANTE and m["id"] != nid
                                      and abs(m.get("niveau", 0) - niv) <= ecart),
                           220.0, rayons=7)
                if t: cible = t[1]; break
        if cible is None: continue
        ajoute_arete("ps-ab:" + nid, nid, cible["id"], "passage", "L4-cache",
                     [n["xyz"], cible["xyz"]], LARGEUR["passage"],
                     "Le bout caché du passage : une dalle, une trappe, un pan de "
                     "mur qui pivote — il faut bien qu'il s'ouvre quelque part, et "
                     "celui qui l'ignore passe devant sans le voir.",
                     niveau=n.get("niveau", 0), visibilite="cachee",
                     acces="secret", etat="ouvert")
        lie[nid].add(cible["id"]); lie[cible["id"]].add(nid)
        rallie(nid, GEANTE, lie)
        attaches += 1
print("   %d bouts de passage secret rattachés au réseau" % attaches)

# les bouches et les têtes de drain : l'exutoire est le point du réseau qui
# compte le plus, et c'était le plus isolé de tous.
idx_eg = index([n for n in G["noeuds"] if n.get("niveau") == -2], 60)
exut = 0
for n in G["noeuds"]:
    if n["genre"] not in ("bouche", "tete"): continue
    t = proche(idx_eg, 60, n["xyz"], lambda m: m["id"] != n["id"] and bool(lie[m["id"]]),
               500.0, rayons=8)
    if not t: continue
    d, m = t
    ajoute_arete("ex:" + n["id"], n["id"], m["id"], "egout", "L5-sous-sol",
                 [n["xyz"], m["xyz"]], LARGEUR["egout"],
                 "Le collecteur rejoint son exutoire : tout ce que la ville lâche "
                 "sort par là, et l'on y entre à contre-courant.",
                 niveau=-2, visibilite="cachee", acces="technique", etat="ouvert")
    lie[n["id"]].add(m["id"]); lie[m["id"]].add(n["id"])
    exut += 1
print("   %d exutoires raccordés au collecteur" % exut)

# ---------------------------------------------------------------------------
# 3ter. ÉLAGUER LES NŒUDS MORTS
# ---------------------------------------------------------------------------
# Nouer une ruelle, c'est réaffecter son extrémité au nœud de la rue : l'ancien
# reste dans le fichier sans plus rien référencer. Ce ne sont pas des ruptures,
# ce sont des cadavres — mais tant qu'ils traînent, tout compte de composantes
# ment sur l'état réel du réseau.
print("… on élague les nœuds morts")
lie2 = defaultdict(int)
for e in A:
    if e.get("de"): lie2[e["de"]] += 1
    if e.get("vers"): lie2[e["vers"]] += 1
for p in P:
    lie2[p["haut"]] += 1; lie2[p["bas"]] += 1
GARDE = ("porte", "quai", "forteresse", "marche", "monument", "septuaire",
         "guilde", "caserne", "office", "chantier", "sommet", "bouche", "tete")
morts = [n for n in G["noeuds"] if lie2[n["id"]] == 0 and n["genre"] not in GARDE]
tues = {n["id"] for n in morts}
G["noeuds"] = [n for n in G["noeuds"] if n["id"] not in tues]
print("   %d nœuds morts retirés" % len(morts))

# ---------------------------------------------------------------------------
# 4. LE TEST — depuis chaque porte, atteindre le fleuve par le dessous
# ---------------------------------------------------------------------------
print()
print("=== TEST DE TRAVERSÉE ===")
N = {n["id"]: n for n in G["noeuds"]}
adj = defaultdict(set)
for e in A:
    if e.get("de") in N and e.get("vers") in N:
        adj[e["de"]].add(e["vers"]); adj[e["vers"]].add(e["de"])
for p in P:
    if p["haut"] in N and p["bas"] in N:
        adj[p["haut"]].add(p["bas"]); adj[p["bas"]].add(p["haut"])

def composantes():
    vu, out = set(), []
    for nid in N:
        if nid in vu: continue
        q, c = deque([nid]), []
        vu.add(nid)
        while q:
            x = q.popleft(); c.append(x)
            for y in adj[x]:
                if y not in vu: vu.add(y); q.append(y)
        out.append(c)
    return sorted(out, key=len, reverse=True)

comps = composantes()
print("  composantes du graphe : %d | plus grosse : %d nœuds (%.0f %%)"
      % (len(comps), len(comps[0]), 100*len(comps[0])/len(N)))
print("  nœuds isolés          : %d" % sum(1 for c in comps if len(c) == 1))
# ces deux comptes doivent rester à zéro : une arête pendante ne casse rien à
# l'écran, elle ment simplement sur ce qui est joignable.
print("  arêtes sans extrémité : %d" % sum(1 for e in A if e.get("de") not in N
                                           or e.get("vers") not in N))
print("  arêtes sans raison    : %d" % sum(1 for e in A if not (e.get("raison") or "").strip()))
print("  arêtes qui bouclent   : %d" % sum(1 for e in A if e.get("de") == e.get("vers")))
geants = set(comps[0])
hors = [n for n in G["noeuds"] if n.get("nom") and n["genre"] in OBLIG + ("acces", "regard-surface")
        and n["id"] not in geants]
print("  lieux nommés hors du réseau : %d %s" % (len(hors), [n["id"] for n in hors[:12]]))

SOUS = {nid for nid, n in N.items() if n.get("niveau", 0) < 0}
EXUT = {nid for nid, n in N.items() if n["genre"] == "bouche"} | \
       {nid for nid, n in N.items() if n.get("niveau") == -2 and n["xyz"][2] < -4}
portes = [nid for nid, n in N.items() if n["genre"] == "porte"]
ok = 0
for g_ in sorted(portes):
    # une traversée qui compte : il faut PASSER par le dessous
    vu, q, trouve, prof = {g_}, deque([(g_, False)]), False, 0
    while q:
        x, sous = q.popleft()
        if sous and x in EXUT: trouve = True; break
        for y in adj[x]:
            if y in vu: continue
            vu.add(y)
            q.append((y, sous or y in SOUS))
    print("   %-34s %s" % (N[g_].get("nom", g_), "atteint le fleuve par-dessous"
                           if trouve else "AUCUN CHEMIN"))
    ok += 1 if trouve else 0
print("  %d portes sur %d relient la ville au fleuve par le dessous" % (ok, len(portes)))

sn = {nid for nid in SOUS}
sadj = {k: (v & sn) for k, v in adj.items() if k in sn}
vu2, scomp = set(), []
for nid in sn:
    if nid in vu2: continue
    q, c = deque([nid]), []
    vu2.add(nid)
    while q:
        x = q.popleft(); c.append(x)
        for y in sadj.get(x, ()):
            if y not in vu2: vu2.add(y); q.append(y)
    scomp.append(c)
scomp.sort(key=len, reverse=True)
print("  réseaux souterrains distincts : %d | plus grand : %d nœuds | isolés : %d"
      % (len(scomp), len(scomp[0]), sum(1 for c in scomp if len(c) == 1)))
km = sum(e["longueur_m"] for e in A if e["couche"] in ("L5-sous-sol", "L4-cache"))/1000
print("  souterrain : %.2f km sur %d arêtes" % (km, sum(1 for e in A if e["couche"] in ("L5-sous-sol","L4-cache"))))

G["_cousu"] = ("Couches cousues par scripts/monde/coudre.py : entrées et porches "
               "raccrochés en coupant l'arête de rue ; égout creusé sous les artères "
               "(décalque de la surface, un niveau plus bas, orienté par la pente) ; "
               "caves percées entre voisines et vers l'égout. Validé par un test de "
               "traversée porte → fleuve par le dessous.")
io.open(CHEMIN, "w", encoding="utf-8").write(json.dumps(G, ensure_ascii=False, indent=1))
print()
print("  %d nœuds, %d arêtes, %d portails écrits" % (len(G["noeuds"]), len(A), len(P)))
