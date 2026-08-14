# -*- coding: utf-8 -*-
"""Donner un métier à chaque bâtiment — et le mettre là où il a une raison d'être.

    python scripts/monde/usages.py     (après coudre.py, avant batir.py)

Jusqu'ici l'usage d'un bâtiment était une copie de son quartier : sept usages
pour douze quartiers, et rien d'autre. Une ville ne se répartit pas comme ça.
Un métier choisit son sol pour des motifs qu'on peut nommer :

    la RUE        une échoppe veut une artère ; un taudis se contente d'une ruelle
    le CLIENT     le boulanger va où sont les bouches, l'aubergiste où sont les portes
    l'EAU         tanneur, teinturier et boucher en ont besoin — et la salissent
    le VENT       ce qui pue va SOUS LE VENT, jamais au nez du Donjon
    le FEU        potiers et fondeurs sortent des murs, ou s'en approchent le moins
    la PENTE      les forges montent la rue d'Acier ; plus haut, plus cher
    le RANG       le noble prend la hauteur et la vue ; le portefaix prend le fond
    l'ÉCART       deux boulangers ne s'installent pas à trente pas l'un de l'autre

Chaque type porte donc un score de site et un écart minimal. On sert les métiers
rares et exigeants d'abord, les logements remplissent ce qui reste.
"""
import json, math, io, os, sys
from collections import defaultdict, Counter

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, ICI)

MONDE = os.path.join(RACINE, "monde")
B = json.load(io.open(os.path.join(MONDE, "portreal.bati.json"), encoding="utf-8"))
G = json.load(io.open(os.path.join(MONDE, "portreal.graph.json"), encoding="utf-8"))
# Rejouable : si l'on a déjà tourné, on retire ce qu'on avait ajouté avant de
# recommencer. Un script de dispatch qui se compose avec lui-même ment au
# deuxième passage.
BASE = ["x","y","z","cap","facade_m","profondeur_m","etages","hauteur_m",
        "quartier","usage","cave"]
if B["_colonnes"] != BASE:
    n = len(BASE)
    B["bati"] = [b[:n] for b in B["bati"]]
    B["_colonnes"] = list(BASE)
C = {n: k for k, n in enumerate(B["_colonnes"])}
BAT = B["bati"]

# --- le vent et le courant : deux règles qui décident de tout le sale ---------
# La Néra coule d'ouest en est ; le vent dominant vient du nord-ouest. Ce qui
# souille l'eau se met donc en AVAL, et ce qui empeste se met SOUS LE VENT —
# c'est-à-dire au sud-est. Aucune ville n'a jamais fait autrement.
VENT = (0.62, -0.78)             # vers où le vent porte (sud-est), en monde

# ---------------------------------------------------------------------------
# les lieux qui attirent ou repoussent
# ---------------------------------------------------------------------------
def noeuds(genres):
    return [n["xyz"] for n in G["noeuds"] if n["genre"] in genres]
MARCHES = noeuds(("marche",))
PORTES = noeuds(("porte",))
QUAIS = noeuds(("quai",))
DONJON = noeuds(("forteresse",)) or [[3432, 1224, 47]]
SOMMETS = noeuds(("sommet",))
# Les cinq institutions nommées du graphe. Elles portaient un nom et un point et
# rien d'autre : ni bâtiment, ni un seul habitant. On s'y colle par la distance,
# exactement comme un boulanger se colle à son marché.
FOSSE = noeuds(("monument",))
VIEUX_SEPTUAIRE = noeuds(("septuaire",))
GUILDE = noeuds(("guilde",))
CASERNES = noeuds(("caserne",))
OFFICE_PORT = noeuds(("office",))

def d_min(p, liste):
    if not liste: return 9e9
    return min(math.hypot(p[0]-q[0], p[1]-q[1]) for q in liste)

# ---------------------------------------------------------------------------
# LA PORTE — le point où le bâtiment touche la chaussée
# ---------------------------------------------------------------------------
# On cherchait ici le RANG de la rue devant la façade, pour savoir ce qu'un
# métier vaut à cet endroit. On garde en même temps le POINT, et c'est ce qui
# fait la différence entre une ville habitée et une ville peuplée : sans porte,
# un habitant naît au milieu de son mur et n'a aucun moyen d'en sortir.
#
# Le graphe câble déjà 3 702 bâtiments (les arêtes `entree`, de `hall:<index>`
# vers la rue) — un sur treize. Les 44 675 autres n'ont rien, alors que la
# projection était calculée ici depuis toujours et jetée aussitôt. On la garde.
#
# On projette sur le SEGMENT, pas sur des points échantillonnés : trois points
# par segment suffisent à classer une rue, pas à poser une porte — l'erreur
# atteindrait plusieurs mètres, et la porte tomberait dans la chaussée ou dans
# le mur d'en face.
print("… la rue devant chaque façade, et le point où l'on en sort")
SEAU = defaultdict(list)
for e in G["aretes"]:
    if e["couche"] != "L1-surface": continue
    larg = e.get("largeur_m", 3)
    for a, b in zip(e["trace"], e["trace"][1:]):
        seg = (a[0], a[1], b[0], b[1], e["genre"], larg, e["id"])
        # un segment s'inscrit dans TOUTES les cases qu'il traverse, sinon un
        # long segment droit reste invisible depuis son milieu
        n = max(1, int(math.hypot(b[0]-a[0], b[1]-a[1]) // 50) + 1)
        for k in range(n + 1):
            t = k / n
            x, y = a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t
            SEAU[(int(x//50), int(y//50))].append(seg)

def rue_devant(x, y):
    """(genre, largeur, px, py, id de la voie) — la chaussée la plus proche."""
    ci, cj = int(x//50), int(y//50)
    meil = (9e9, "ruelle", 2.0, x, y, None)
    vus = set()
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for seg in SEAU.get((ci+di, cj+dj), ()):
                if id(seg) in vus: continue
                vus.add(id(seg))
                ax, ay, bx, by, g, w, vid = seg
                dx, dy = bx-ax, by-ay
                q = dx*dx + dy*dy
                t = 0.0 if q == 0 else max(0.0, min(1.0, ((x-ax)*dx + (y-ay)*dy)/q))
                px, py = ax + dx*t, ay + dy*t
                d = (x-px)**2 + (y-py)**2
                if d < meil[0]: meil = (d, g, w, px, py, vid)
    return meil[1], meil[2], meil[3], meil[4], meil[5]

# l'eau : on reprend le masque du relief
T = json.load(io.open(os.path.join(MONDE, "portreal.terrain.json"), encoding="utf-8"))
RES, NX, NY, EAUM = T["res_m"], T["nx"], T["ny"], T["eau"]
BORD_EAU = []
for j in range(1, NY-1):
    for i in range(1, NX-1):
        if EAUM[j][i] and not (EAUM[j][i-1] and EAUM[j][i+1] and EAUM[j-1][i] and EAUM[j+1][i]):
            BORD_EAU.append((i*RES, j*RES))
SEAU_EAU = defaultdict(list)
for (x, y) in BORD_EAU: SEAU_EAU[(int(x//120), int(y//120))].append((x, y))
def d_eau(x, y):
    ci, cj = int(x//120), int(y//120)
    meil = 9e9
    for r in range(1, 6):
        for di in range(-r, r+1):
            for dj in range(-r, r+1):
                for (qx, qy) in SEAU_EAU.get((ci+di, cj+dj), ()):
                    meil = min(meil, math.hypot(x-qx, y-qy))
        if meil < 9e8: return meil
    return meil

print("… les traits de site")
CENTRE = (2640.0, 1800.0)
F = []
for k, b in enumerate(BAT):
    x, y, z = b[C["x"]], b[C["y"]], b[C["z"]]
    rang, larg, px, py, voie = rue_devant(x, y)
    q = b[C["quartier"]]
    F.append({
        "i": k, "x": x, "y": y, "z": z, "q": q,
        "rang": rang, "larg": larg,
        # la porte : le point de chaussée le plus proche, et la voie qui le
        # porte. C'est par là qu'on entre et qu'on sort, pour tout le monde.
        "px": round(px, 1), "py": round(py, 1), "voie": voie,
        "marche": d_min((x, y), MARCHES), "porte": d_min((x, y), PORTES),
        "quai": d_min((x, y), QUAIS), "donjon": d_min((x, y), DONJON),
        "eau": d_eau(x, y), "sommet": d_min((x, y), SOMMETS),
        "fosse": d_min((x, y), FOSSE), "vieux_septuaire": d_min((x, y), VIEUX_SEPTUAIRE),
        "guilde": d_min((x, y), GUILDE), "caserne": d_min((x, y), CASERNES),
        "office": d_min((x, y), OFFICE_PORT),
        # « sous le vent » : la projection sur la direction du vent, en mètres
        "aval": (x-CENTRE[0])*VENT[0] + (y-CENTRE[1])*VENT[1],
        "dehors": q.startswith(("Le faubourg", "Les baraques", "Le bourg")),
        "surface": b[C["facade_m"]]*b[C["profondeur_m"]]*b[C["etages"]],
    })

# --- la population, déduite du plancher ------------------------------------
DENSITE = {"Le Culpucier": 11.0, "La ville": 24.0, "La ville haute": 70.0,
           "Le Crochet": 45.0, "La rue d'Acier": 28.0, "Les tanneries": 30.0,
           "Le port et ses hangars": 200.0}
def m2_par_ame(q):
    if q in DENSITE: return DENSITE[q]
    return 30.0
POP = sum(f["surface"]/m2_par_ame(f["q"]) for f in F)
print("   population déduite du plancher : %s âmes" % format(int(POP), ",d").replace(",", " "))

# ---------------------------------------------------------------------------
# LA TABLE DES MÉTIERS
# ---------------------------------------------------------------------------
# `pour` : une pour tant d'âmes.  `nombre` : compte fixe.  `ecart` : mètres
# minimum entre deux du même type.  `score` : ce qui fait un bon emplacement.
# `refuse` : un emplacement qu'aucun score ne rachète.
def pres(d, portee):  return max(0.0, 1.0 - d/portee)
def loin(d, portee):  return min(1.0, d/portee)

# `pres` est un CÔNE : il vaut zéro net au-delà de sa portée. Pour un besoin qui
# a un rayon vrai — le seau d'un puits, la garnison d'un donjon — c'est juste.
# Pour une ATTIRANCE, c'est faux, et ça se voit sur la carte : tous les sites du
# disque battent tous ceux du dehors, donc le métier remplit le disque à ras
# bord et s'arrête au cordeau. Mesuré autour des marchés : 65 % de commerces à
# cent vingt mètres, 47 % à trois cents, puis 6 % — une falaise, et un rond
# orange sur le plan.
#
# Une attirance décroît sans jamais s'annuler : on veut la moitié de l'effet à
# la portée, un quart au double, et une queue qui laisse une échoppe s'installer
# sur une bonne artère à l'autre bout de la ville. C'est ce que fait une
# lorentzienne, et elle ne coûte pas une division de plus.
def attire(d, portee):  return 1.0/(1.0 + (d/portee)**2)

TYPES = [
 # --- LES INSTITUTIONS : on les sert avant tout le monde -------------------
 # Le graphe nommait ces cinq lieux depuis le début ; aucun n'avait de mur ni
 # une seule âme. Chacun se colle à son nœud, et `nombre` dit sur combien de
 # bâtiments il s'étale — un donjon n'est pas une maison, c'est une enceinte.
 dict(id="donjon-rouge", nom="Le Donjon Rouge", cat="institution", nombre=9, ecart=0,
      toit="tour", etages=(3,4), gabarit=(20,28,26),
      # existe par le besoin de gouverner : garnison, offices, domesticité.
      score=lambda f: 3.0*pres(f["donjon"], 300)),
 dict(id="fosse-dragons", nom="La Fosse aux Dragons", cat="institution", nombre=1, ecart=0,
      toit="tour", etages=(2,2), gabarit=(60,60,40),
      # existe par les dragons : on les nourrit, on les enchaîne, on les veille.
      score=lambda f: 3.0*pres(f["fosse"], 220)),
 dict(id="vieux-septuaire", nom="Le vieux septuaire", cat="institution", nombre=1, ecart=0,
      toit="tour", etages=(2,2), gabarit=(30,44,30),
      # existe par le culte : c'est le grand septuaire de la ville en 129 AC.
      score=lambda f: 3.0*pres(f["vieux_septuaire"], 200)),
 dict(id="guilde-alchimistes", nom="La Guilde des Alchimistes", cat="institution",
      nombre=2, ecart=0, toit="plat", etages=(2,3), gabarit=(18,24,16),
      # existe par le feu grégeois : on le cuit, on le pot, on le garde.
      score=lambda f: 3.0*pres(f["guilde"], 200)),
 dict(id="caserne", nom="Caserne du Guet", cat="institution", nombre=6, ecart=0,
      toit="long", etages=(2,3), gabarit=(24,34,17),
      # existe par le Guet : deux mille manteaux d'or logent et s'arment ici.
      score=lambda f: 3.0*pres(f["caserne"], 300)),
 dict(id="bureau-port", nom="Le bureau du maître de port", cat="institution",
      nombre=1, ecart=0, toit="plat", etages=(2,2), gabarit=(16,20,13),
      # existe par la douane : rien n'est déchargé sans que ce bureau le sache.
      score=lambda f: 3.0*pres(f["office"], 200)),

 # --- ce qui ne souffre aucun voisin : on sert ces métiers d'abord ----------
 dict(id="septuaire-quartier", nom="Septuaire de quartier", cat="culte", pour=7000,
      ecart=260, toit="tour", etages=(2,2), gabarit=(14,20,18),
      refuse=lambda f: f["dehors"],
      score=lambda f: 2.0*(f["rang"] in ("artere","rue")) + 1.4*pres(f["marche"],450)
                      + 0.8*pres(f["z"]*0+f["donjon"], 2500)),
 dict(id="grenier", nom="Grenier public", cat="civique", nombre=8, ecart=420,
      toit="long", etages=(2,2), gabarit=(22,30,26),
      refuse=lambda f: f["dehors"] or f["quai"] > 900,
      score=lambda f: 2.4*pres(f["quai"],500) + 1.2*pres(f["porte"],600)
                      + 1.0*(f["rang"]=="artere")),
 # Deux corps de garde par porte, un de chaque côté du passage : l'écart valait
 # 300 m pour une portée de 260, si bien qu'on en réclamait quatorze et qu'on en
 # posait sept — le second était toujours refusé par son voisin.
 dict(id="corps-de-garde", nom="Corps de garde", cat="civique", nombre=14, ecart=150,
      toit="tour", etages=(2,3), gabarit=(12,14,14),
      score=lambda f: 3.0*pres(f["porte"], 300)),
 dict(id="geole", nom="Geôle", cat="civique", nombre=3, ecart=900,
      toit="plat", etages=(2,2), gabarit=(18,22,16),
      refuse=lambda f: f["dehors"],
      score=lambda f: 1.6*pres(f["donjon"],900) + 1.0*loin(f["marche"],700)),
 dict(id="auberge", nom="Auberge", cat="service", pour=3200, ecart=190,
      toit="long", etages=(2,3), gabarit=(14,18,16),
      score=lambda f: 3.0*pres(f["porte"],380) + 1.0*(f["rang"]=="artere")
                      + 0.6*pres(f["quai"],500)),
 dict(id="ecurie", nom="Écurie de louage", cat="service", pour=4200, ecart=200,
      toit="long", etages=(1,1), gabarit=(16,22,9),
      score=lambda f: 2.6*pres(f["porte"],320) + 0.8*(f["rang"] in ("artere","rue"))),

 # --- ce qui pue, ce qui salit : sous le vent et à l'eau, sans exception ----
 dict(id="tannerie", nom="Tannerie", cat="nuisance", pour=4500, ecart=110,
      toit="long", etages=(1,2), gabarit=(12,18,10),
      refuse=lambda f: f["eau"] > 420 or f["donjon"] < 700,
      score=lambda f: 2.6*pres(f["eau"],300) + 2.2*(f["aval"]/900.0)
                      + 1.4*(f["q"]=="Les tanneries")),
 dict(id="abattoir", nom="Abattoir", cat="nuisance", pour=9000, ecart=260,
      toit="long", etages=(1,1), gabarit=(14,20,9),
      refuse=lambda f: f["eau"] > 520 or f["donjon"] < 800,
      score=lambda f: 2.4*pres(f["eau"],320) + 1.8*(f["aval"]/900.0)
                      + 0.8*pres(f["marche"],600)),
 dict(id="teinturerie", nom="Teinturerie", cat="nuisance", pour=7000, ecart=140,
      toit="long", etages=(1,2), gabarit=(11,16,10),
      refuse=lambda f: f["eau"] > 380,
      score=lambda f: 2.4*pres(f["eau"],280) + 1.2*(f["aval"]/900.0)),
 # Le déchet du foyer partait jusqu'ici NULLE PART. Il part d'ici : la fosse est
 # le bout de la chaîne, et sa géographie est celle de la tannerie — en aval,
 # sous le vent, et hors de vue du Donjon.
 dict(id="fosse-vidange", nom="Fosse de vidange", cat="nuisance", pour=18000, ecart=340,
      toit="plat", etages=(1,1), gabarit=(10,16,6),
      refuse=lambda f: f["donjon"] < 900,
      score=lambda f: 2.4*(f["aval"]/900.0) + 1.6*float(f["dehors"])
                      + 1.2*loin(f["marche"], 800) + 0.8*pres(f["eau"], 400)),
 dict(id="poterie", nom="Four de potier", cat="nuisance", pour=11000, ecart=300,
      toit="plat", etages=(1,1), gabarit=(11,14,8),
      score=lambda f: 2.2*float(f["dehors"]) + 1.4*loin(f["marche"],900)
                      + 1.0*(f["aval"]/900.0)),

 # --- le port : des métiers qui n'existent qu'au bord de l'eau -------------
 dict(id="entrepot", nom="Entrepôt", cat="commerce", pour=1400, ecart=0,
      toit="long", etages=(1,1), gabarit=(18,26,11),
      refuse=lambda f: f["quai"] > 420,
      score=lambda f: 3.0*pres(f["quai"],300)),
 dict(id="corderie", nom="Corderie", cat="artisanat", nombre=7, ecart=120,
      toit="long", etages=(1,1), gabarit=(9,34,8),
      refuse=lambda f: f["quai"] > 500,
      score=lambda f: 2.6*pres(f["quai"],340)),
 dict(id="voilerie", nom="Voilerie", cat="artisanat", nombre=6, ecart=110,
      toit="long", etages=(2,2), gabarit=(12,20,12),
      refuse=lambda f: f["quai"] > 500,
      score=lambda f: 2.4*pres(f["quai"],340)),
 dict(id="bordel", nom="Maison close", cat="plaisir", pour=2600, ecart=90,
      toit="pignon", etages=(2,3), gabarit=(9,13,13),
      score=lambda f: 2.0*pres(f["quai"],420) + 1.4*pres(f["porte"],420)
                      + 1.0*pres(f["marche"],350) + 0.8*(f["rang"]=="ruelle")),

 # --- le feu : forges et fours, groupés, et jamais chez les nobles ---------
 dict(id="forge", nom="Forge", cat="artisanat", pour=700, ecart=45,
      toit="plat", etages=(1,2), gabarit=(8,13,10),
      refuse=lambda f: f["q"] in ("La ville haute", "Le Crochet"),
      score=lambda f: 3.0*(f["q"]=="La rue d'Acier") + 0.8*pres(f["marche"],500)
                      + 0.6*(f["z"]/60.0)),
 dict(id="boulangerie", nom="Boulangerie", cat="artisanat", pour=430, ecart=58,
      toit="pignon", etages=(2,3), gabarit=(8,12,12),
      score=lambda f: 1.6*(f["rang"] in ("artere","rue")) + 1.0*pres(f["marche"],700)
                      + 0.6*(f["q"] in ("La ville","Le Culpucier"))),
 dict(id="brasserie", nom="Brasserie", cat="artisanat", pour=2400, ecart=170,
      toit="long", etages=(2,2), gabarit=(12,18,13),
      score=lambda f: 1.4*pres(f["eau"],500) + 1.0*(f["rang"] in ("artere","rue"))),

 # Entre le grain et les neuf cent soixante boulangeries, il n'y avait rien.
 # Le moulin est ce rien : à vent sur les trois collines et hors les murs où
 # l'air passe, à eau sur la Néra. Peu nombreux, et visibles de toute la ville.
 dict(id="moulin", nom="Moulin", cat="artisanat", pour=16000, ecart=280,
      toit="tour", etages=(2,3), gabarit=(9,9,17),
      score=lambda f: 1.8*float(f["dehors"]) + 1.6*(f["z"]/70.0)
                      + 1.4*pres(f["sommet"], 500) + 1.6*pres(f["eau"], 130)),
 # Le deuxième tonnage de la ville après le grain : tout foyer, tout four, toute
 # forge en brûle, et le bois entre par les portes ou par le fleuve.
 dict(id="chantier-bois", nom="Chantier à bois et charbon", cat="commerce",
      pour=5500, ecart=160, toit="long", etages=(1,1), gabarit=(15,22,8),
      score=lambda f: 2.2*pres(f["porte"], 380) + 2.0*pres(f["quai"], 400)
                      + 0.8*(f["rang"] in ("artere", "rue"))),

 # --- le commerce : il suit la rue et le client ----------------------------
 # Trois marchés pour quatre cent mille âmes faisaient un pour cent trente-trois
 # mille, et une lieue de marche pour trois oignons. Les marchés de quartier
 # existent par ce trajet-là : on les pose LOIN des trois grands, exprès.
 dict(id="marche-quartier", nom="Marché de quartier", cat="commerce", pour=28000,
      ecart=420, toit="long", etages=(1,1), gabarit=(18,24,8),
      score=lambda f: 2.2*loin(f["marche"], 900) + 1.4*(f["rang"] == "artere")
                      + 0.8*(f["rang"] == "rue")),
 dict(id="taverne", nom="Taverne", cat="plaisir", pour=330, ecart=42,
      toit="pignon", etages=(2,3), gabarit=(8,13,13),
      score=lambda f: 1.8*(f["rang"]=="artere") + 1.2*pres(f["marche"],450)
                      + 1.0*pres(f["porte"],400) + 1.0*pres(f["quai"],400)),
 dict(id="echoppe", nom="Échoppe", cat="commerce", pour=115, ecart=0,
      toit="pignon", etages=(2,3), gabarit=(7,12,12),
      refuse=lambda f: f["dehors"],
      # LA RUE PASSE AVANT LE MARCHÉ. C'était 2,2 contre 1,6 avec un cône de
      # 400 m : dans le disque, la somme écrasait tout le reste de la ville et
      # les trois mille cinq cents échoppes s'y entassaient. On garde l'artère
      # au même poids, on desserre l'attirance, et le commerce redevient un
      # RUBAN le long des grandes rues au lieu d'une tache autour des places.
      score=lambda f: 2.2*(f["rang"]=="artere") + 1.1*(f["rang"]=="rue")
                      + 0.25*(f["rang"]=="ruelle") + 1.15*attire(f["marche"],320)),
 dict(id="change", nom="Table de change", cat="commerce", pour=14000, ecart=280,
      toit="plat", etages=(2,3), gabarit=(10,14,14),
      refuse=lambda f: f["dehors"],
      score=lambda f: 2.4*pres(f["marche"],260) + 1.0*(f["rang"]=="artere")),
 dict(id="etuve", nom="Étuve", cat="service", pour=9000, ecart=250,
      toit="plat", etages=(1,2), gabarit=(11,15,10),
      score=lambda f: 1.6*pres(f["eau"],450) + 1.2*pres(f["marche"],450)),

 # --- l'eau : le flux dominant de la ville, et il n'avait aucun bâtiment ---
 # Deux à trois allers par jour et par foyer : deux cent mille trajets par jour,
 # loin devant le pain, le bois ou le marché. La portée d'un puits est celle du
 # seau plein — cent mètres, guère plus —, d'où le grand nombre et l'écart
 # serré. On vise une bouche d'eau pour mille âmes environ.
 #
 # LE CHOIX DISCUTABLE, dit en clair : un puits occupe quand même une parcelle,
 # faute d'une couche « mobilier de rue » dans le bâti. On le sert donc en
 # DERNIER, après tous les métiers, pour qu'il ne prenne jamais l'échoppe
 # d'angle d'un carrefour ; et il refuse les grandes parcelles, si bien qu'il
 # mange un recoin de logement et non un commerce. Son gabarit est minuscule et
 # il n'a qu'un étage : à l'écran c'est une margelle, pas une maison.
 dict(id="puits", nom="Puits", cat="civique", pour=1000, ecart=95,
      toit="plat", etages=(1,1), gabarit=(3,3,2),
      refuse=lambda f: f["surface"] > 240,
      score=lambda f: 1.6*(f["rang"] in ("artere", "rue", "ruelle"))
                      + 1.0*pres(f["marche"], 900) + 0.6*loin(f["eau"], 400)),

 # --- l'habitat : il prend ce qui reste, selon son quartier ---------------
 dict(id="manse", nom="Manse noble", cat="habitat", remplit="La ville haute",
      toit="long", etages=(2,3), gabarit=(16,20,15)),
 dict(id="maison-officier", nom="Maison d'officier", cat="habitat", remplit="Le Crochet",
      toit="pignon", etages=(2,3), gabarit=(11,14,13)),
 dict(id="taudis", nom="Taudis", cat="habitat", remplit="Le Culpucier",
      toit="pignon", etages=(3,4), gabarit=(4,7,11)),
 dict(id="cabane", nom="Cabane de faubourg", cat="habitat", remplit="_dehors",
      toit="pignon", etages=(1,2), gabarit=(6,8,7)),
 dict(id="maison", nom="Maison", cat="habitat", remplit="_reste",
      toit="pignon", etages=(2,3), gabarit=(8,11,11)),
]

# ---------------------------------------------------------------------------
# LE DISPATCH — les exigeants d'abord, l'habitat en dernier
# ---------------------------------------------------------------------------
print("… on attribue les métiers")
libre = [True]*len(BAT)
attrib = [None]*len(BAT)
poses = Counter()

def _bruit(i):
    """un tirage stable par emplacement : même bâtiment, même sort"""
    h = (i*2654435761 + 1013904223) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h*1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFFFF)/4294967296.0

def choisir(t):
    n = t.get("nombre")
    if n is None and t.get("pour"): n = max(1, int(POP/t["pour"]))
    if not n: return
    cands = []
    ref = t.get("refuse")
    sc = t["score"]
    for f in F:
        if not libre[f["i"]]: continue
        if ref and ref(f): continue
        s = sc(f)
        # UN CLASSEMENT STRICT SUR UN CHAMP LISSE DONNE UN BORD NET. Prendre les
        # N meilleurs, c'est découper une COURBE DE NIVEAU — et la courbe de
        # niveau d'une attirance ponctuelle est un ROND. D'où les taches orange
        # autour des marchés : 62 % de commerces à cent vingt mètres, 33 % à
        # trois cents, 2 % à trois cent cinquante. Adoucir la portée n'y change
        # rien, parce que ce n'est pas la portée qui tranche : c'est le quota,
        # qui s'épuise avant d'atteindre la queue.
        #
        # Le monde, lui, ne trie pas. Deux emplacements comparables se
        # départagent par qui est arrivé le premier, qui avait l'argent, à qui
        # appartenait le mur. On brouille donc le rang de ±18 %, stablement, et
        # le bord redevient une frange au lieu d'un trait de compas.
        if s > 0.15:
            s *= 0.82 + 0.36*_bruit(f["i"])
            cands.append((-s, f["i"], f["x"], f["y"]))
    cands.sort()
    ecart = t.get("ecart", 0)
    pris = defaultdict(list)
    pas = max(ecart, 1)
    k = 0
    for (ms, i, x, y) in cands:
        if k >= n: break
        if ecart:
            ci, cj = int(x//pas), int(y//pas)
            trop = False
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    for (px, py) in pris.get((ci+di, cj+dj), ()):
                        if (x-px)**2 + (y-py)**2 < ecart*ecart: trop = True; break
                    if trop: break
                if trop: break
            if trop: continue
            pris[(ci, cj)].append((x, y))
        libre[i] = False
        attrib[i] = t
        k += 1
    poses[t["id"]] = k
    manque = n - k
    print("   %-20s %5d posés%s" % (t["nom"], k,
          ("  (%d de moins que voulu : la ville n'a pas le sol)" % manque) if manque > 0 else ""))

for t in TYPES:
    if "remplit" in t: continue
    choisir(t)

# l'habitat ramasse le reste, selon le quartier
REMPLIT = {t["remplit"]: t for t in TYPES if "remplit" in t}
for f in F:
    if not libre[f["i"]]: continue
    q = f["q"]
    t = REMPLIT.get(q)
    if t is None and f["dehors"]: t = REMPLIT["_dehors"]
    if t is None: t = REMPLIT["_reste"]
    attrib[f["i"]] = t
    libre[f["i"]] = False
    poses[t["id"]] += 1

# ---------------------------------------------------------------------------
# on réécrit le bâti : le type impose aussi son gabarit
# ---------------------------------------------------------------------------
import random
R = random.Random(90210)
for f in F:
    t = attrib[f["i"]]
    b = BAT[f["i"]]
    fa, pr, ha = t["gabarit"]
    e0, e1 = t["etages"]
    et = R.randint(e0, e1)
    # La PARCELLE décide de l'emprise — un boulanger n'élargit pas son terrain
    # en changeant de métier. Le MÉTIER décide de l'élévation : combien d'étages
    # on monte, et quelle hauteur on se donne. Les deux ne se mélangent pas, et
    # c'est ce qui rend ce script rejouable sans qu'il se compose avec lui-même.
    b[C["etages"]] = et
    b[C["hauteur_m"]] = round(ha/max(1.0, (e0+e1)/2.0) * et * (0.88 + 0.24*R.random()), 1)
    b[C["usage"]] = t["id"]

# `porte_x`, `porte_y`, `voie` : là où le bâtiment touche la chaussée, et par
# quelle arête du graphe. Trois colonnes qui coûtent une projection déjà faite
# et qui rendent toute la circulation possible — un trajet, c'est porte, voie,
# graphe, voie, porte.
B["_colonnes"] = B["_colonnes"] + ["cat", "toit", "porte_x", "porte_y", "voie"]
CATS = {t["id"]: (t["cat"], t["toit"]) for t in TYPES}
PORTES_BAT = {f["i"]: (f["px"], f["py"], f["voie"]) for f in F}
for k, b in enumerate(BAT):
    c, to = CATS[b[C["usage"]]]
    px, py, voie = PORTES_BAT[k]
    b.append(c); b.append(to); b.append(px); b.append(py); b.append(voie)
B["_types"] = {t["id"]: {"nom": t["nom"], "cat": t["cat"], "toit": t["toit"]} for t in TYPES}
B["_lisez_moi"] = ("Chaque bâtiment porte un MÉTIER choisi par son site, pas par son "
                   "quartier : rue devant lui, distance au marché, à la porte, au quai, "
                   "à l'eau, position sous le vent, pente, et un écart minimal entre "
                   "deux du même métier. Table et règles dans scripts/monde/usages.py.")
io.open(os.path.join(MONDE, "portreal.bati.json"), "w", encoding="utf-8").write(
    json.dumps(B, ensure_ascii=False, separators=(",", ":")))

print()
print("  %d bâtiments, %d métiers" % (len(BAT), len(poses)))
par_cat = Counter()
for b in BAT: par_cat[b[C["usage"]]] += 1
for t in TYPES:
    n = par_cat[t["id"]]
    if n: print("   %-22s %-10s %6d  (%.1f %%)" % (t["nom"], t["cat"], n, 100*n/len(BAT)))
