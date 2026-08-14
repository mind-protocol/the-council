# -*- coding: utf-8 -*-
"""Donner un métier à chaque feu du bourg de Peyredragon — le pendant de usages.py.

    python scripts/monde/peyredragon_usages.py     (après peyredragon.py)

Même principe qu'à Port-Réal : un métier choisit son sol pour des motifs qu'on
peut nommer. Mais ce n'est pas la même ville, et la table ne se recopie pas —
Peyredragon n'a ni marché, ni rue d'Acier, ni faubourgs. Ce qu'elle a :

    le QUAI       tout le bourg en vit ; la barque, le filet, le poisson, le sel
    l'ESCALIER    le pied du grand escalier est la seule « porte » du village :
                  ce qui monte au château et ce qui en descend passe par là
    l'EAU         la grève, l'estran, les ruisseaux de la caldeira
    le VENT       il descend du Dragonmont vers la rade ; ce qui pue va sous lui,
                  c'est-à-dire au large du pied de l'escalier
    la PENTE      plus on monte vers les murs, moins on est un pêcheur
    l'ÉCART       deux fumoirs ne se posent pas à vingt pas l'un de l'autre

Le château et la muraille ne sont PAS redistribués : leurs volumes viennent des
salles du plan (`scripts/materialisation/lieux.py`), et leur usage est un fait,
pas un choix de site. Ce script ne touche qu'au bourg — il lui donne son métier,
son élévation et sa catégorie, puis pose les colonnes `cat` et `toit` sur tout le
fichier pour que `ecrans/modules/monde/bati.js` colore la scène comme Port-Réal.
"""
import io
import json
import math
import os
import random
from collections import Counter, defaultdict

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
MONDE = os.path.join(RACINE, "monde")

B = json.load(io.open(os.path.join(MONDE, "peyredragon.bati.json"), encoding="utf-8"))
G = json.load(io.open(os.path.join(MONDE, "peyredragon.graph.json"), encoding="utf-8"))
T = json.load(io.open(os.path.join(MONDE, "peyredragon.terrain.json"), encoding="utf-8"))

# Rejouable : si l'on a déjà tourné, on retire ce qu'on avait ajouté avant de
# recommencer. Un script de dispatch qui se compose avec lui-même ment au
# deuxième passage.
BASE = ["x", "y", "z", "cap", "facade_m", "profondeur_m", "etages", "hauteur_m",
        "quartier", "usage", "cave"]
if B["_colonnes"] != BASE:
    n = len(BASE)
    B["bati"] = [b[:n] for b in B["bati"]]
    B["_colonnes"] = list(BASE)
C = {n: k for k, n in enumerate(B["_colonnes"])}
BAT = B["bati"]

# --- ce qui est du château, et ce qui ne l'est pas ---------------------------
# Ces usages-là ne se redistribuent jamais : ce sont des salles et des murs.
DUR = {
    "logis": ("civique", "long"), "caserne": ("civique", "long"),
    "office": ("civique", "plat"), "culte": ("culte", "tour"),
    "forge": ("artisanat", "plat"), "muraille": ("civique", "plat"),
    "tour": ("civique", "tour"), "donjon": ("civique", "tour"),
}


# ---------------------------------------------------------------------------
# les lieux qui attirent ou repoussent
# ---------------------------------------------------------------------------
def noeuds(genres):
    return [n["xyz"] for n in G["noeuds"] if n["genre"] in genres]


QUAIS = noeuds(("quai",))
PORTES = noeuds(("porte",))
CHATEAU = noeuds(("forteresse",))
SOMMET = noeuds(("sommet",))


def d_min(p, liste):
    if not liste:
        return 9e9
    return min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in liste)


# le pied du grand escalier : c'est LA porte du village, celle par où le château
# descend et remonte. On le prend à l'extrémité basse du tracé.
ESC = [a for a in G["aretes"] if a["genre"] == "escalier"]
if ESC:
    tr = ESC[0]["trace"]
    PIED = [tr[0] if d_min(tr[0], QUAIS) < d_min(tr[-1], QUAIS) else tr[-1]]
else:
    PIED = list(QUAIS)

# Le vent : il descend du Dragonmont vers la rade — c'est la brise de montagne,
# et elle décide de tout le sale. Ce qui empeste se met SOUS le vent, jamais au
# nez de l'escalier par où descend la maison de la reine.
if SOMMET and QUAIS:
    vx, vy = QUAIS[0][0] - SOMMET[0][0], QUAIS[0][1] - SOMMET[0][1]
    lv = math.hypot(vx, vy) or 1.0
    VENT = (vx / lv, vy / lv)
else:
    VENT = (1.0, 0.0)

# le rang de la voie devant laquelle le bâtiment a sa façade
print("… le rang de voie de chaque façade")
SEAU = defaultdict(list)
for e in G["aretes"]:
    if e["couche"] != "L1-surface":
        continue
    for a, b in zip(e["trace"], e["trace"][1:]):
        for t in (0.0, 0.5, 1.0):
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            SEAU[(int(x // 50), int(y // 50))].append((x, y, e["genre"],
                                                       e.get("largeur_m", 3)))


def voie_devant(x, y):
    ci, cj = int(x // 50), int(y // 50)
    meil = (9e9, "sentier", 2.0)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for (qx, qy, g, w) in SEAU.get((ci + di, cj + dj), ()):
                d = (x - qx) ** 2 + (y - qy) ** 2
                if d < meil[0]:
                    meil = (d, g, w)
    return meil[1], meil[2]


# l'eau : on reprend le masque du relief
RES, NX, NY, EAUM = T["res_m"], T["nx"], T["ny"], T["eau"]
BORD_EAU = []
for j in range(1, NY - 1):
    for i in range(1, NX - 1):
        if EAUM[j][i] and not (EAUM[j][i - 1] and EAUM[j][i + 1]
                               and EAUM[j - 1][i] and EAUM[j + 1][i]):
            BORD_EAU.append((i * RES, j * RES))
SEAU_EAU = defaultdict(list)
for (x, y) in BORD_EAU:
    SEAU_EAU[(int(x // 120), int(y // 120))].append((x, y))


def d_eau(x, y):
    ci, cj = int(x // 120), int(y // 120)
    meil = 9e9
    for r in range(1, 8):
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                for (qx, qy) in SEAU_EAU.get((ci + di, cj + dj), ()):
                    meil = min(meil, math.hypot(x - qx, y - qy))
        if meil < 9e8:
            return meil
    return meil


print("… les traits de site")
F = []
for k, b in enumerate(BAT):
    if b[C["usage"]] in DUR:
        continue                       # le château et ses murs ne se rejouent pas
    x, y, z = b[C["x"]], b[C["y"]], b[C["z"]]
    rang, larg = voie_devant(x, y)
    F.append({
        "i": k, "x": x, "y": y, "z": z, "q": b[C["quartier"]],
        "rang": rang, "larg": larg,
        "quai": d_min((x, y), QUAIS), "pied": d_min((x, y), PIED),
        "porte": d_min((x, y), PORTES), "chateau": d_min((x, y), CHATEAU),
        "eau": d_eau(x, y),
        # « sous le vent » : la projection sur la direction du vent, en mètres,
        # comptée depuis le pied de l'escalier
        "aval": (x - PIED[0][0]) * VENT[0] + (y - PIED[0][1]) * VENT[1],
        # l'EMPRISE, pas le plancher : le nombre d'étages est justement ce que ce
        # script réécrit, et une population qui en dépendrait changerait à chaque
        # passage — donc le compte des métiers avec elle.
        "emprise": b[C["facade_m"]] * b[C["profondeur_m"]],
    })

# --- la population, déduite du plancher -------------------------------------
# Un bourg de pêche s'entasse : une pièce, un feu, une famille. Le diviseur
# n'est pas un réglage d'ambiance : il est calé sur `etat/ville.json`, qui dit
# « trois cent quarante âmes sous les murs ». C'est l'état qui a raison — 67
# feux pour 340 âmes, cinq par foyer, ce qui est le compte d'un village.
POP = sum(f["emprise"] / 11.0 for f in F)
print("   population du bourg déduite de l'emprise : %d âmes" % int(POP))


# ---------------------------------------------------------------------------
# LA TABLE DES MÉTIERS — celle d'un bourg de pêche sous une forteresse
# ---------------------------------------------------------------------------
def pres(d, portee):
    return max(0.0, 1.0 - d / portee)


def loin(d, portee):
    return min(1.0, d / portee)


TYPES = [
 # --- ce qui ne souffre aucun voisin : on sert ces métiers d'abord -----------
 dict(id="septuaire-bourg", nom="Petit septuaire", cat="culte", nombre=1, ecart=0,
      toit="tour", etages=(2, 2), gabarit_h=13.0,
      score=lambda f: 2.0 * (f["rang"] == "rue") + 1.2 * pres(f["pied"], 300)
                      + 0.8 * loin(f["eau"], 200)),
 dict(id="corps-de-garde", nom="Corps de garde", cat="civique", nombre=2, ecart=180,
      toit="tour", etages=(2, 2), gabarit_h=11.0,
      score=lambda f: 3.0 * pres(f["pied"], 140) + 1.0 * pres(f["quai"], 200)),
 dict(id="auberge", nom="Auberge du quai", cat="service", nombre=2, ecart=120,
      toit="long", etages=(2, 2), gabarit_h=12.0,
      score=lambda f: 2.4 * pres(f["pied"], 220) + 1.6 * pres(f["quai"], 260)
                      + 0.8 * (f["rang"] == "rue")),
 dict(id="forge-bourg", nom="Forge du bourg", cat="artisanat", nombre=1, ecart=0,
      toit="plat", etages=(1, 1), gabarit_h=7.0,
      score=lambda f: 2.0 * pres(f["pied"], 260) + 1.0 * loin(f["eau"], 160)),

 # --- ce qui pue : sous le vent et au bord de l'eau, sans exception ----------
 dict(id="boucanerie", nom="Boucanerie", cat="nuisance", pour=70, ecart=45,
      toit="long", etages=(1, 1), gabarit_h=6.0,
      refuse=lambda f: f["eau"] > 140 or f["pied"] < 90,
      score=lambda f: 2.4 * pres(f["eau"], 110) + 2.0 * (f["aval"] / 260.0)),
 dict(id="saline", nom="Saline", cat="nuisance", nombre=3, ecart=60,
      toit="plat", etages=(1, 1), gabarit_h=4.5,
      refuse=lambda f: f["eau"] > 120,
      score=lambda f: 2.6 * pres(f["eau"], 90) + 1.2 * (f["aval"] / 260.0)),
 dict(id="tannerie", nom="Tannerie", cat="nuisance", nombre=2, ecart=90,
      toit="long", etages=(1, 1), gabarit_h=6.5,
      refuse=lambda f: f["eau"] > 160 or f["pied"] < 140,
      score=lambda f: 2.2 * pres(f["eau"], 120) + 2.2 * (f["aval"] / 260.0)),

 # --- le quai : des métiers qui n'existent qu'au bord de l'eau --------------
 dict(id="sechoir", nom="Séchoir à filets", cat="artisanat", pour=45, ecart=30,
      toit="long", etages=(1, 1), gabarit_h=3.2,
      refuse=lambda f: f["eau"] > 150,
      score=lambda f: 2.8 * pres(f["eau"], 110) + 0.8 * pres(f["quai"], 400)),
 dict(id="hangar", nom="Hangar à barques", cat="commerce", pour=60, ecart=35,
      toit="long", etages=(1, 1), gabarit_h=6.0,
      refuse=lambda f: f["quai"] > 320,
      score=lambda f: 3.0 * pres(f["quai"], 240) + 1.0 * pres(f["eau"], 120)),
 dict(id="corderie", nom="Corderie", cat="artisanat", nombre=1, ecart=0,
      toit="long", etages=(1, 1), gabarit_h=5.5,
      refuse=lambda f: f["quai"] > 380,
      score=lambda f: 2.4 * pres(f["quai"], 280)),
 dict(id="voilerie", nom="Voilerie", cat="artisanat", nombre=1, ecart=0,
      toit="long", etages=(1, 1), gabarit_h=6.5,
      refuse=lambda f: f["quai"] > 380,
      score=lambda f: 2.4 * pres(f["quai"], 280)),
 dict(id="entrepot", nom="Entrepôt de la garnison", cat="commerce", nombre=3, ecart=60,
      toit="long", etages=(1, 1), gabarit_h=8.0,
      refuse=lambda f: f["quai"] > 340,
      score=lambda f: 2.2 * pres(f["quai"], 240) + 1.4 * pres(f["pied"], 300)),

 # --- le commerce d'un village : il suit le chemin et le client -------------
 dict(id="taverne", nom="Taverne", cat="plaisir", pour=110, ecart=60,
      toit="pignon", etages=(2, 2), gabarit_h=9.0,
      score=lambda f: 1.8 * (f["rang"] == "rue") + 1.4 * pres(f["quai"], 260)
                      + 1.2 * pres(f["pied"], 260)),
 dict(id="echoppe", nom="Échoppe", cat="commerce", pour=80, ecart=35,
      toit="pignon", etages=(2, 2), gabarit_h=8.5,
      score=lambda f: 2.0 * (f["rang"] == "rue") + 1.2 * pres(f["pied"], 320)
                      + 0.6 * pres(f["quai"], 320)),
 dict(id="boulangerie", nom="Four à pain", cat="artisanat", nombre=2, ecart=140,
      toit="pignon", etages=(1, 2), gabarit_h=8.0,
      score=lambda f: 1.6 * (f["rang"] == "rue") + 1.0 * loin(f["eau"], 160)),
 dict(id="brasserie", nom="Brasserie", cat="artisanat", nombre=1, ecart=0,
      toit="long", etages=(1, 2), gabarit_h=8.0,
      score=lambda f: 1.4 * loin(f["quai"], 300) + 1.0 * (f["rang"] == "rue")),

 # --- l'habitat : il prend ce qui reste -------------------------------------
 dict(id="maison-pecheur", nom="Maison de pêcheur", cat="habitat", remplit="_reste",
      toit="pignon", etages=(1, 2), gabarit_h=6.0),
 dict(id="cabane", nom="Cabane", cat="habitat", remplit="_ecart",
      toit="pignon", etages=(1, 1), gabarit_h=4.6),
]

# ---------------------------------------------------------------------------
# LE DISPATCH — les exigeants d'abord, l'habitat en dernier
# ---------------------------------------------------------------------------
print("… on attribue les métiers")
libre = {f["i"]: True for f in F}
attrib = {}


def choisir(t):
    n = t.get("nombre")
    if n is None and t.get("pour"):
        n = max(1, int(POP / t["pour"]))
    if not n:
        return
    ref = t.get("refuse")
    sc = t["score"]
    cands = []
    for f in F:
        if not libre[f["i"]]:
            continue
        if ref and ref(f):
            continue
        s = sc(f)
        if s > 0.15:
            cands.append((-s, f["i"], f["x"], f["y"]))
    cands.sort()
    ecart = t.get("ecart", 0)
    pris = []
    k = 0
    for (ms, i, x, y) in cands:
        if k >= n:
            break
        if ecart and any((x - px) ** 2 + (y - py) ** 2 < ecart * ecart
                         for (px, py) in pris):
            continue
        if ecart:
            pris.append((x, y))
        libre[i] = False
        attrib[i] = t
        k += 1
    manque = n - k
    print("   %-24s %4d posés%s" % (t["nom"], k,
          ("  (%d de moins que voulu : le bourg n'a pas le sol)" % manque)
          if manque > 0 else ""))


for t in TYPES:
    if "remplit" in t:
        continue
    choisir(t)

# l'habitat ramasse le reste : les feux isolés, loin de tout chemin, sont des
# cabanes — le reste, des maisons de pêcheur
REMPLIT = {t["remplit"]: t for t in TYPES if "remplit" in t}
for f in F:
    if not libre[f["i"]]:
        continue
    t = REMPLIT["_ecart"] if (f["rang"] == "sentier" or f["pied"] > 420) \
        else REMPLIT["_reste"]
    attrib[f["i"]] = t
    libre[f["i"]] = False

# ---------------------------------------------------------------------------
# on réécrit le bâti : le métier impose l'ÉLÉVATION, jamais l'emprise
# ---------------------------------------------------------------------------
R = random.Random(1293)
for f in F:
    t = attrib[f["i"]]
    b = BAT[f["i"]]
    e0, e1 = t["etages"]
    et = R.randint(e0, e1)
    ha = t["gabarit_h"]
    # La PARCELLE décide de l'emprise — un saleur n'élargit pas son terrain en
    # changeant de métier. Le MÉTIER décide de l'élévation. Les deux ne se
    # mélangent pas, et c'est ce qui rend ce script rejouable.
    b[C["etages"]] = et
    b[C["hauteur_m"]] = round(ha / max(1.0, (e0 + e1) / 2.0) * et
                              * (0.88 + 0.24 * R.random()), 1)
    b[C["usage"]] = t["id"]

# les colonnes de rendu, sur TOUT le fichier — château compris
B["_colonnes"] = B["_colonnes"] + ["cat", "toit"]
CATS = dict(DUR)
CATS.update({t["id"]: (t["cat"], t["toit"]) for t in TYPES})
for b in BAT:
    c, to = CATS[b[C["usage"]]]
    b.append(c)
    b.append(to)
B["_types"] = {t["id"]: {"nom": t["nom"], "cat": t["cat"], "toit": t["toit"]}
               for t in TYPES}
B["_lisez_moi"] = ("Une ligne par volume, en mètres, dans le repère du monde. "
                   "Les feux du bourg portent un MÉTIER choisi par leur site — "
                   "quai, pied du grand escalier, eau, vent descendu du "
                   "Dragonmont, et un écart minimal entre deux du même métier. "
                   "Le château et la muraille gardent leur usage : ce sont des "
                   "salles et des murs, pas un choix de site. Table et règles "
                   "dans scripts/monde/peyredragon_usages.py.")

io.open(os.path.join(MONDE, "peyredragon.bati.json"), "w", encoding="utf-8").write(
    json.dumps(B, ensure_ascii=False, separators=(",", ":")))

print()
print("  %d volumes, dont %d feux du bourg" % (len(BAT), len(F)))
par = Counter(BAT[f["i"]][C["usage"]] for f in F)
for t in TYPES:
    n = par[t["id"]]
    if n:
        print("   %-24s %-10s %4d  (%.1f %%)" % (t["nom"], t["cat"], n,
                                                 100.0 * n / len(F)))
