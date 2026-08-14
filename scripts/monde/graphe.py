# -*- coding: utf-8 -*-
"""Port-Réal en graphe 3D multi-couches — mètres, nœuds, arêtes, portails.

    python scripts/monde/graphe.py   →   monde/portreal.graph.json

La carte 2D donne la géométrie de surface (elle a déjà été engendrée par la
circulation) ; ici on la MÉTRISE, on la coupe en arêtes à chaque carrefour, on
lui donne son profil en z, puis on empile les couches que le dessin ne peut pas
porter : intérieurs, réseau caché, sous-sol, et les portails qui les cousent.

Règle d'or, tenue partout : aucune arête sans `raison`. Une ruelle qui ne relie
rien à rien n'est pas tracée ; un tunnel sans motif n'est pas creusé.
"""
import json, math, io, os, sys, random

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, ICI)
from echelle import (METRE_PAR_UNITE as MU, m, mx, my, ux, uy, mcap,
                     hors_anneau, loin_du_mur, MONDE_L, MONDE_H, LARGEUR, PENTE_MAX,
                     hauteur_sol, gabarit, NIVEAUX, HAUTEUR_SOUS_PLAFOND,
                     MUR_HAUTEUR, MUR_EPAISSEUR, QUAI_HAUTEUR, SOL_VILLE)

R = random.Random(51290323)
CARTE = json.load(io.open(os.path.join(RACINE, "etat", "villes", "port-real.json"), encoding="utf-8"))

# ---------------------------------------------------------------------------
# le sol, repris de la carte : elle est l'autorité géographique
# ---------------------------------------------------------------------------
EAU   = [s["points"] for s in CARTE["sol"] if s["genre"] == "eau"]
MURS  = [s for s in CARTE["sol"] if s["genre"] == "mur" and "largeur" not in s]
PORTES= [s for s in CARTE["sol"] if s["genre"] == "mur" and s.get("largeur") == 6]
BATIS = [s for s in CARTE["sol"] if s["genre"] == "mur" and 0 < s.get("largeur", 0) <= 4]
VOIES = [s for s in CARTE["sol"] if s["genre"] == "route"]
TOITS = [s for s in CARTE["sol"] if s["genre"] == "village"]
QUAIS = [s for s in CARTE["sol"] if s["genre"] == "quai"]
COLLINES_SOL = [s for s in CARTE["sol"] if s["genre"] == "colline"]

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
def d_ligne(pts, x, y):
    return min(d_seg(x, y, a, b) for a, b in zip(pts, pts[1:]))

# L'altitude ne se recalcule PAS ici : elle est lue dans le relief engendré par
# scripts/monde/relief.py. Deux formules de terrain dans un même monde, c'est un
# monde où les rues flottent au-dessus du sol.
_REL = json.load(io.open(os.path.join(RACINE, "monde", "portreal.terrain.json"),
                         encoding="utf-8"))
_RES, _NX, _NY, _Z = _REL["res_m"], _REL["nx"], _REL["ny"], _REL["z"]
def sol(x, y):
    """altitude du terrain, en mètres, au point de CARTE (x, y)"""
    wx, wy = mx(x), my(y)
    i = min(_NX-2, max(0, int(wx/_RES)))
    j = min(_NY-2, max(0, int(wy/_RES)))
    tx, ty = (wx - i*_RES)/_RES, (wy - j*_RES)/_RES
    a = _Z[j][i]*(1-tx) + _Z[j][i+1]*tx
    b = _Z[j+1][i]*(1-tx) + _Z[j+1][i+1]*tx
    return a*(1-ty) + b*ty

# ---------------------------------------------------------------------------
# 1. LES NŒUDS
# ---------------------------------------------------------------------------
NOEUDS = {}
def noeud(nid, x, y, genre, nom=None, niveau=0, z=None, **kw):
    if nid in NOEUDS: return nid
    zz = sol(x, y) if z is None else z
    n = {"id": nid, "genre": genre, "niveau": niveau,
         "xyz": [round(mx(x), 1), round(my(y), 1), round(zz, 1)]}
    if nom: n["nom"] = nom
    n.update(kw)
    NOEUDS[nid] = n
    return nid

def cle(x, y, niveau=0, pref="c"):
    return "%s%d.%d_%d" % (pref, round(x*2), round(y*2), niveau)

print("… les nœuds obligatoires")
for p in PORTES:
    a, b = p["points"][0], p["points"][-1]
    x, y = (a[0]+b[0])/2, (a[1]+b[1])/2
    noeud("porte:" + p["nom"], x, y, "porte", p["nom"],
          raison="Le seul passage de la muraille en ce point : tout ce qui entre y est vu.")
LANDMARKS = [
    ("donjon", 286, 198, "forteresse", "Le Donjon Rouge", "Le siège du pouvoir : la ville entière y monte ou en descend."),
    ("fosse", 272, 130, "monument", "La Fosse aux Dragons", "On ne monte Rhaenys que pour les bêtes."),
    ("septuaire", 148, 198, "septuaire", "Le vieux septuaire", "Le sept de la colline de Visenya, et sa crypte."),
    ("guilde", 236, 146, "guilde", "La Guilde des Alchimistes", "Ils fabriquent ce qu'on ne veut pas voir traverser une rue."),
    ("casernes", 234, 180, "caserne", "Les casernes du Guet", "D'ici sortent les rondes, et par où elles sortent compte."),
    ("grand-marche", 198, 148, "marche", "La grande place", "Cinq rues y versent : c'est le cœur du commerce."),
    ("marche-chevaux", 120, 149, "marche", "Le marché aux chevaux", "Ce qui vient par la route de la Rose se vend là."),
    ("marche-poissons", 288, 225, "marche", "Le marché aux poissons", "Le premier prix de la ville qui bouge."),
    ("quai-amont", 288, 268, "quai", "Le quai d'amont", "Où l'on décharge le grain."),
    ("quai-aval", 344, 258, "quai", "Le quai d'aval", "Où mouillent les coques de guerre quand il y en a."),
    ("bureau-port", 333, 251, "office", "Le bureau du maître de port", "Les rôles d'entrée."),
    ("aire-bris", 232, 260, "chantier", "L'aire de bris", "Le chantier de Marlo Vasse, hors la porte."),
    ("sommet-visenya", 150, 182, "sommet", "Le sommet de Visenya", None),
    ("sommet-aegon", 318, 193, "sommet", "Le sommet d'Aegon", None),
    ("sommet-rhaenys", 276, 94, "sommet", "Le sommet de Rhaenys", None),
]
for nid, x, y, genre, nom, raison in LANDMARKS:
    noeud(nid, x, y, genre, nom, **({"raison": raison} if raison else {}))

# ---------------------------------------------------------------------------
# 2. LES ARÊTES DE SURFACE — la carte, coupée à chaque carrefour
# ---------------------------------------------------------------------------
print("… on coupe les voies aux carrefours")
def croise(a1, a2, b1, b2):
    d = (a2[0]-a1[0])*(b2[1]-b1[1]) - (a2[1]-a1[1])*(b2[0]-b1[0])
    if abs(d) < 1e-9: return None
    t = ((b1[0]-a1[0])*(b2[1]-b1[1]) - (b1[1]-a1[1])*(b2[0]-b1[0])) / d
    u = ((b1[0]-a1[0])*(a2[1]-a1[1]) - (b1[1]-a1[1])*(a2[0]-a1[0])) / d
    if 0 <= t <= 1 and 0 <= u <= 1:
        return [a1[0]+t*(a2[0]-a1[0]), a1[1]+t*(a2[1]-a1[1])]
    return None

def rang_de(v):
    lg = v.get("largeur", 4)
    if v.get("nom", "").startswith("La route"): return "artere"
    if lg >= 4.5: return "artere"
    if lg >= 2.6: return "rue"
    return "ruelle"

coupes = [[] for _ in VOIES]            # (indice de segment, t, point)
for i, v in enumerate(VOIES):
    for j, w in enumerate(VOIES):
        if j <= i: continue
        for si, (a1, a2) in enumerate(zip(v["points"], v["points"][1:])):
            for sj, (b1, b2) in enumerate(zip(w["points"], w["points"][1:])):
                p = croise(a1, a2, b1, b2)
                if p:
                    t = math.dist(a1, p) / (math.dist(a1, a2) or 1)
                    u = math.dist(b1, p) / (math.dist(b1, b2) or 1)
                    coupes[i].append((si, t, p)); coupes[j].append((sj, u, p))

def morceaux(v, cs):
    """découpe la polyligne aux points de coupe, en gardant l'ordre"""
    pts = v["points"]
    cs = sorted(cs)
    bouts, cur = [], [pts[0]]
    ic = 0
    for si in range(len(pts)-1):
        while ic < len(cs) and cs[ic][0] == si:
            p = cs[ic][2]
            if math.dist(cur[-1], p) > 1.2:
                cur.append(p); bouts.append(cur); cur = [p]
            ic += 1
        if math.dist(cur[-1], pts[si+1]) > 0.05:
            cur.append(pts[si+1])
    if len(cur) > 1: bouts.append(cur)
    return [b for b in bouts if len(b) > 1 and
            sum(math.dist(x, y) for x, y in zip(b, b[1:])) > 2.0]

ARETES = []
def arete(aid, na, nb, genre, couche, points, largeur, raison, **kw):
    zs = [sol(p[0], p[1]) for p in points]
    lg = sum(math.dist(a, b) for a, b in zip(points, points[1:])) * MU
    pente = 0.0
    for (pa, pb), (za, zb) in zip(zip(points, points[1:]), zip(zs, zs[1:])):
        d = math.dist(pa, pb) * MU
        if d > 1: pente = max(pente, abs(zb-za)/d)
    e = {"id": aid, "de": na, "vers": nb, "genre": genre, "couche": couche,
         "largeur_m": round(largeur, 2), "longueur_m": round(lg, 1),
         "pente": round(pente, 3), "raison": raison,
         "trace": [[round(mx(p[0]),1), round(my(p[1]),1), round(z,1)] for p, z in zip(points, zs)]}
    e.update(kw)
    ARETES.append(e)
    return e

for i, v in enumerate(VOIES):
    rang = rang_de(v)
    for k, b in enumerate(morceaux(v, coupes[i])):
        na = noeud(cle(b[0][0], b[0][1]), b[0][0], b[0][1], "carrefour")
        nb = noeud(cle(b[-1][0], b[-1][1]), b[-1][0], b[-1][1], "carrefour")
        if na == nb: continue
        larg = LARGEUR[rang]
        genre = rang
        raison = v.get("detail") or "Desserte locale."
        e = arete("v%d.%d" % (i, k), na, nb, genre, "L1-surface", b, larg, raison,
                  nom=v.get("nom"), visibilite="publique", acces="public", etat="ouvert")
        # une voie trop raide n'est plus une rue : c'est un escalier
        if e["pente"] > PENTE_MAX.get(rang, 0.2):
            e["genre"] = "escalier"
            e["largeur_m"] = LARGEUR["escalier"]
            e["raison"] = (e["raison"] or "") + " La pente y interdit la charrette : on l'a marchée."
print("   ", len(ARETES), "arêtes de surface")

# les quais : une arête à part, parce qu'on y décharge
for k, q in enumerate(QUAIS):
    p = q["points"]
    na = noeud(cle(p[0][0], p[0][1]), p[0][0], p[0][1], "carrefour")
    nb = noeud(cle(p[-1][0], p[-1][1]), p[-1][0], p[-1][1], "carrefour")
    arete("q%d" % k, na, nb, "quai", "L1-surface", p, LARGEUR["quai"],
          q.get("detail") or "Le bord de l'eau : on y pose ce qui arrive.",
          nom=q.get("nom"), visibilite="publique", acces="public", etat="ouvert")

# ---------------------------------------------------------------------------
# 3. L2 — LE TISSU BÂTI : une parcelle de la carte vaut plusieurs maisons
# ---------------------------------------------------------------------------
print("… les parcelles et les bâtiments")
BATIMENTS = []
USAGE = {
    "Le port et ses hangars": "entrepot", "Les tanneries": "atelier",
    "La rue d'Acier": "forge", "Le Crochet": "maison d'officier",
    "La ville haute": "hôtel", "Le Culpucier": "taudis",
}
# UN FAUBOURG S'ÉTEINT, IL NE COURT PAS JUSQU'AU BORD DU DESSIN. La carte
# d'origine tire ses faubourgs le long des routes jusqu'au cadre : au douzième
# de mètre près, ça donne onze cents mètres de maisons continues le long de la
# route de la Rose, qui s'arrêtent net sur le bord du plan. Sur un schéma ça se
# lit comme « il y a du monde par là » ; métré, c'est une ville qui déborde de
# son cadre, et c'est ce qu'on voyait dépasser.
#
# Un faubourg réel se serre contre sa porte, parce que c'est la porte qui le
# fait vivre, et il se défait ensuite : plein jusqu'à cent cinquante pas,
# clairsemé jusqu'à quatre cent cinquante, plus rien au-delà. On n'ampute que
# les faubourgs — la ville, le port et ses quais gardent tout ce qu'ils ont.
FAUBOURG_PLEIN = 150.0     # jusque-là, le faubourg est un faubourg
FAUBOURG_FIN = 450.0       # au-delà, c'est la campagne, et elle est vide
def _tenue(x, y):
    """Ce qu'il reste d'un faubourg à cette distance de la porte : 1 ou 0."""
    if not hors_anneau(x, y): return True
    d = loin_du_mur(x, y)
    if d <= FAUBOURG_PLEIN: return True
    if d >= FAUBOURG_FIN: return False
    t = (d-FAUBOURG_PLEIN)/(FAUBOURG_FIN-FAUBOURG_PLEIN)
    return R.random() > t**0.75

ecartes = 0
for q in TOITS:
    nom = q["nom"]
    fmin, fmax, prof, etages, he = gabarit(nom)
    usage = USAGE.get(nom, "maison")
    faubourg = nom.startswith(("Le faubourg", "Les baraques", "Le bourg"))
    if faubourg: usage = "cabane"
    for pi, p in enumerate(q["points"]):
        x, y = p[0], p[1]
        if faubourg and not _tenue(x, y):
            ecartes += 1
            continue
        ang = math.radians(p[2] if len(p) > 2 else 0)
        larg_parcelle = m(p[3] if len(p) > 3 else 3.0)
        z = sol(x, y)
        # on subdivise la façade de la parcelle en maisons réelles
        n = max(1, int(larg_parcelle // ((fmin+fmax)/2)))
        f = larg_parcelle / n
        vx, vy = math.cos(ang), math.sin(ang)
        for k in range(n):
            d = (k + 0.5 - n/2) * f
            bx, by = mx(x) + vx*d, my(y) - vy*d
            et = R.randint(*etages)
            BATIMENTS.append({
                "id": "b%s.%d.%d" % (nom[:3].lower().replace(" ", ""), pi, k),
                "quartier": nom, "usage": usage,
                "xyz": [round(bx,1), round(by,1), round(z,1)],
                "cap": round(mcap(math.degrees(ang)), 1),
                "facade_m": round(f, 2), "profondeur_m": round(prof, 1),
                "etages": et, "hauteur_m": round(et*he + 1.2, 1),
                "cave": usage in ("entrepot", "forge", "hôtel", "maison d'officier") or R.random() < 0.22,
            })
print("   ", len(BATIMENTS), "bâtiments sur", sum(len(q["points"]) for q in TOITS), "parcelles")
print("   ", ecartes, "parcelles de faubourg écartées : au-delà de %.0f m, ce n'est plus un faubourg" % FAUBOURG_FIN)

# ---------------------------------------------------------------------------
# 4. L5 — LE SOUS-SOL : quatre familles, à quatre profondeurs
# ---------------------------------------------------------------------------
print("… le sous-sol")
def sous(nid, x, y, niveau, genre, nom=None, **kw):
    z = sol(x, y) + NIVEAUX[niveau][1]
    return noeud(nid, x, y, genre, nom, niveau=niveau, z=z, **kw)

# A — infrastructure : l'égout SUIT LA PENTE. On descend depuis chaque colline.
def descendre(x, y, pas=6.0, n=60):
    """on suit la ligne de plus grande pente jusqu'à l'eau"""
    ch = [[x, y]]
    for _ in range(n):
        meil, best = None, sol(x, y)
        for a in range(0, 360, 15):
            r = math.radians(a)
            nx, ny = x + math.cos(r)*pas, y + math.sin(r)*pas
            if not (0 <= nx < 440 and 0 <= ny < 300): continue
            h = sol(nx, ny)
            if h < best: best, meil = h, (nx, ny)
        if not meil: break
        x, y = meil
        ch.append([round(x,1), round(y,1)])
        if any(dedans(e, x, y) for e in EAU): break
    return ch

EGOUTS = [
    ("visenya", 150, 190, "Le grand drain de Visenya : la colline se vide vers la Néra, et la ville a bâti dessus."),
    ("aegon",   300, 210, "Le drain d'Aegon : il part sous le Donjon et sort au fleuve, sous le quai."),
    ("rhaenys", 268, 122, "Le drain de Rhaenys : il descend la Fosse, traverse la ville basse et rejoint le Boyau."),
]
for nom, x, y, raison in EGOUTS:
    ch = descendre(x, y)
    if len(ch) < 3: continue
    na = sous("egout:%s:tete" % nom, ch[0][0], ch[0][1], -2, "regard",
              "Tête du drain de " + nom, raison="Le point haut : c'est là que l'eau prend.")
    nb = sous("egout:%s:bouche" % nom, ch[-1][0], ch[-1][1], -2, "bouche",
              "Bouche du drain de " + nom, raison="Il crache au fleuve — et par là, on entre.")
    arete("eg:" + nom, na, nb, "egout", "L5-sous-sol", ch, LARGEUR["egout"], raison,
          niveau=-2, visibilite="cachee", acces="technique", etat="ouvert",
          humidite="courante", nom="Le drain de " + nom)

# B — stockage : les caves du port, reliées entre elles sous les hangars
cav = [b for b in BATIMENTS if b["quartier"] == "Le port et ses hangars"]
for i, b in enumerate(cav):
    sous("cave:port:%d" % i, ux(b["xyz"][0]), uy(b["xyz"][1]), -1, "cave",
         "Cave d'entrepôt", raison="Sous un hangar : ce qui ne doit pas rester sur le quai.")
for i in range(len(cav)-1):
    a, b = "cave:port:%d" % i, "cave:port:%d" % (i+1)
    if a in NOEUDS and b in NOEUDS:
        pa = [ux(NOEUDS[a]["xyz"][0]), uy(NOEUDS[a]["xyz"][1])]
        pb = [ux(NOEUDS[b]["xyz"][0]), uy(NOEUDS[b]["xyz"][1])]
        if math.dist(pa, pb) < 6:
            arete("cv:port:%d" % i, a, b, "galerie", "L5-sous-sol", [pa, pb], LARGEUR["galerie"],
                  "Les caves du port ont été percées les unes vers les autres : on décharge la nuit sans repasser au quai.",
                  niveau=-1, visibilite="cachee", acces="prive", etat="ouvert")

# C — ancien / oublié
ANCIEN = [
    ("crypte-septuaire", 150, 190, "La crypte du vieux septuaire",
     "Les septons y couchent leurs morts depuis Aegon : la ville a été bâtie par-dessus."),
    ("fondations-fosse", 274, 118, "Les fondations de la Fosse",
     "Ce que Maegor a coulé sous la colline pour tenir le dôme — plus vaste que le dôme."),
    ("grotte-aegon", 322, 214, "La grotte de la colline d'Aegon",
     "Naturelle, antérieure à la ville : c'est elle qui a décidé de l'emplacement du Donjon."),
]
for nid, x, y, nom, raison in ANCIEN:
    sous("ancien:" + nid, x, y, -3, "salle", nom, raison=raison)
arete("an:crypte-grotte", "ancien:crypte-septuaire", "ancien:grotte-aegon", "galerie", "L5-sous-sol",
      [[150,190],[186,196],[228,206],[268,212],[322,214]], 2.6,
      "Une galerie d'avant la ville, retrouvée en creusant : elle joint les deux collines sans passer par le fond.",
      niveau=-3, visibilite="secrete", acces="secret", etat="partiellement effondre",
      nom="La galerie ancienne")

# D — clandestin et militaire
MILITAIRE = [
    ("fuite-maegor", "Le tunnel de Maegor",
     [[300,200],[308,214],[318,228],[326,244],[332,256]],
     "Sortie de siège du Donjon Rouge vers l'eau. Maegor l'a fait creuser, puis fait tuer les creuseurs.",
     "praticable", "secret", ["aegon-ii", "larys"]),
    ("armes-casernes", "La cache d'armes du Guet",
     [[234,180],[238,190],[236,200]],
     "Sous les casernes : de quoi armer trois cents hommes sans ouvrir l'arsenal du Donjon.",
     "praticable", "militaire", ["criston"]),
    ("contrebande-gadoue", "Le boyau du chantier",
     [[232,258],[248,252],[262,248],[272,244]],
     "Un vieux drain sous le mur, élargi à la main : le bris — et ce qui n'est pas du bris — passe sans voir la porte.",
     "praticable", "secret", ["marlo-vasse", "hann-bourbe", "nel-bec"]),
]
for nid, nom, ch, raison, etat, acces, connu in MILITAIRE:
    na = sous("sous:%s:a" % nid, ch[0][0], ch[0][1], -2, "acces", nom + " (entrée)")
    nb = sous("sous:%s:b" % nid, ch[-1][0], ch[-1][1], -2, "acces", nom + " (issue)")
    arete("ss:" + nid, na, nb, "tunnel", "L5-sous-sol", ch, LARGEUR["tunnel"], raison,
          niveau=-2, visibilite="secrete", acces=acces, etat=etat, connu_de=connu, nom=nom)

# ---------------------------------------------------------------------------
# 5. L4 — LES PASSAGES SECRETS : peu, asymétriques, et chacun sait pourquoi
# ---------------------------------------------------------------------------
print("… les passages secrets")
PASSAGES = [
    dict(id="ps:donjon-fosse", nom="Le couloir des montures",
         trace=[[292,186],[288,168],[282,146],[276,130]],
         bati_par="Jaehaerys I, quand la Fosse a été agrandie",
         pour="Que la famille royale atteigne ses bêtes sans traverser la ville",
         connu_de=["aegon-ii", "helaena", "aemond", "criston"],
         dissimule_par="une remise à harnais, derrière la cour des écuries",
         largeur_m=1.6, etat="praticable", niveau=-1),
    dict(id="ps:guilde-egout", nom="La descente des Sagesses",
         trace=[[236,146],[240,156],[236,166]],
         bati_par="La Guilde des Alchimistes, il y a soixante ans",
         pour="Sortir les jarres sans qu'elles traversent une rue ni croisent une torche",
         connu_de=["les Sagesses de la Guilde"],
         dissimule_par="une citerne à double fond, sous la salle des fours",
         largeur_m=1.3, etat="praticable", niveau=-2),
    dict(id="ps:septuaire-acier", nom="Le pas du septon",
         trace=[[150,188],[158,180],[168,172],[176,166]],
         bati_par="Les septons, pour porter les morts sans passer par la rue",
         pour="Alors : les morts. Aujourd'hui : ce qu'un forgeron ne veut pas déclarer",
         connu_de=["le septon de Visenya", "deux forgerons de la rue d'Acier"],
         dissimule_par="une dalle de la crypte, sous le septième autel",
         largeur_m=1.1, etat="praticable", niveau=-1),
    dict(id="ps:casernes-culpucier", nom="Le couloir du Guet",
         trace=[[234,182],[236,196],[232,210],[228,220]],
         bati_par="Le Guet, après les émeutes du pain",
         pour="Faire sortir une ronde au milieu du Culpucier, et non à sa lisière",
         connu_de=["les sergents du Guet"],
         dissimule_par="une remise à fourrage qui n'a jamais eu de fourrage",
         largeur_m=1.8, etat="surveille", niveau=-1),
    dict(id="ps:crochet-cuisines", nom="Le passage des plats",
         trace=[[286,196],[292,190],[298,186]],
         bati_par="Les intendants du Donjon",
         pour="Que les livraisons du Crochet n'entrent pas par la porte du Roi",
         connu_de=["les cuisines du Donjon", "trois marchands du Crochet"],
         dissimule_par="une arcade murée du Crochet, rouverte côté cour",
         largeur_m=2.2, etat="praticable", niveau=0),
    dict(id="ps:mur-gadoue", nom="Le trou de Nel",
         trace=[[272,250],[268,254],[262,256]],
         bati_par="Personne : c'est un drain du mur que l'eau a élargi",
         pour="Ce que les gosses de la grève font passer sans payer Waltyr",
         connu_de=["nel-bec", "trente gosses", "marlo-vasse"],
         dissimule_par="la vase, à basse mer seulement",
         largeur_m=0.8, etat="praticable a basse mer", niveau=-1),
    dict(id="ps:tour-main", nom="L'escalier creux de la tour de la Main",
         trace=[[341,178],[336,186],[330,196]],
         bati_par="Maegor le Cruel",
         pour="Écouter. Il ne mène nulle part d'utile — il longe trois murs et s'arrête",
         connu_de=["larys"],
         dissimule_par="l'épaisseur du mur lui-même, derrière la cheminée du solar",
         largeur_m=0.7, etat="praticable", niveau=0),
]
for p in PASSAGES:
    ch = p["trace"]
    lvl = p["niveau"]
    na = sous(p["id"] + ":a", ch[0][0], ch[0][1], lvl if lvl else -1, "acces", p["nom"] + " (entrée)")
    nb = sous(p["id"] + ":b", ch[-1][0], ch[-1][1], lvl if lvl else -1, "acces", p["nom"] + " (issue)")
    arete(p["id"], na, nb, "passage", "L4-cache", ch, p["largeur_m"],
          p["pour"], nom=p["nom"], niveau=lvl, visibilite="secrete", acces="secret",
          etat=p["etat"], bati_par=p["bati_par"], connu_de=p["connu_de"],
          dissimule_par=p["dissimule_par"])

# ---------------------------------------------------------------------------
# 6. LES PORTAILS — ce qui coud les couches ensemble
# ---------------------------------------------------------------------------
print("… les portails")
PORTAILS = []
def portail(pid, haut, bas, genre, cache=False, ferme=False, cout=1.0, raison=""):
    if haut not in NOEUDS or bas not in NOEUDS:
        print("   ! portail sans nœud :", pid); return
    PORTAILS.append({"id": pid, "haut": haut, "bas": bas, "genre": genre,
                     "cache": cache, "ferme": ferme, "cout": cout, "raison": raison})

# les égouts s'ouvrent à leurs bouches, et par les regards des places
for nom, x, y, _ in EGOUTS:
    ns = noeud(cle(x, y, 0, "p"), x, y, "regard-surface", "Regard de " + nom)
    portail("pt:regard:" + nom, ns, "egout:%s:tete" % nom, "puits", cache=False, ferme=True,
            cout=2.0, raison="Un regard de drain : scellé, et le Guet a la clef.")
    portail("pt:bouche:" + nom, "quai-amont" if nom == "aegon" else ns,
            "egout:%s:bouche" % nom, "conduit", cache=True, ferme=False, cout=3.0,
            raison="La bouche au fleuve : praticable à basse mer, à quatre pattes.")
portail("pt:donjon-maegor", "donjon", "sous:fuite-maegor:a", "escalier", cache=True, ferme=True,
        cout=1.0, raison="L'escalier de fuite : il part d'une cave du Donjon que trois hommes savent nommer.")
portail("pt:maegor-neva", "quai-aval", "sous:fuite-maegor:b", "porte", cache=True, ferme=True,
        cout=1.5, raison="La poterne au bord de l'eau : sous le quai, invisible à marée haute.")
portail("pt:casernes-cache", "casernes", "sous:armes-casernes:a", "trappe", cache=False, ferme=True,
        cout=1.0, raison="La trappe de l'arsenal : sous les dalles de la salle d'armes.")
portail("pt:aire-boyau", "aire-bris", "sous:contrebande-gadoue:a", "trappe", cache=True, ferme=False,
        cout=1.2, raison="Sous le hangar du chantier, entre deux cales : on soulève, on descend.")
portail("pt:boyau-gadoue", "marche-poissons", "sous:contrebande-gadoue:b", "escalier", cache=True,
        ferme=False, cout=1.2, raison="Il débouche dans une cave du marché — ce qui explique que le poisson n'y soit pas toujours du poisson.")
portail("pt:crypte", "septuaire", "ancien:crypte-septuaire", "escalier", cache=False, ferme=True,
        cout=1.0, raison="L'escalier de la crypte : ouvert aux fidèles, fermé la nuit.")
portail("pt:grotte", "sommet-aegon", "ancien:grotte-aegon", "puits", cache=True, ferme=True,
        cout=4.0, raison="Un puits sec du Donjon tombe dans la grotte : personne n'a jamais voulu le descendre.")
portail("pt:fosse-fondations", "fosse", "ancien:fondations-fosse", "escalier", cache=False, ferme=True,
        cout=1.5, raison="Les fondations s'ouvrent sous la fosse : c'est par là qu'on sort les carcasses.")
for p in PASSAGES:
    portail("pt:" + p["id"], p["id"] + ":a", p["id"] + ":b", "porte dissimulee",
            cache=True, ferme=(p["etat"] == "surveille"), cout=1.4,
            raison="Dissimulé par : " + p["dissimule_par"])

# ---------------------------------------------------------------------------
MONDE = {
    "_lisez_moi": "Port-Réal, 1:1, en mètres. La carte 2D donne la géométrie de surface ; "
        "ce fichier la métrise, la coupe en graphe, et empile les couches. Le z 0 est l'étale "
        "de la Néra. AUCUNE arête sans `raison` : une ruelle qui ne relie rien n'existe pas, "
        "un tunnel sans motif n'est pas creusé. Se rebâtit par scripts/monde/graphe.py.",
    "echelle": {"metre_par_unite_carte": MU, "monde_m": [MONDE_L, MONDE_H],
                "z0": "étale de la Néra", "unite": "mètre"},
    "couches": {
        "L1-surface": "Artères, rues, ruelles, escaliers, quais, places",
        "L2-bati": "Parcelles et bâtiments : usage, façade, profondeur, étages, cave",
        "L3-interieurs": "Cours, arcades, passages entre cours (à venir)",
        "L4-cache": "Passages secrets, portes dissimulées, corridors de service",
        "L5-sous-sol": "Égouts et drains, caves, ancien, clandestin et militaire",
    },
    "niveaux": {str(k): {"nom": v[0], "z_m": v[1], "quoi": v[2]} for k, v in NIVEAUX.items()},
    "noeuds": list(NOEUDS.values()),
    "aretes": ARETES,
    "batiments": BATIMENTS,
    "portails": PORTAILS,
}
os.makedirs(os.path.join(RACINE, "monde"), exist_ok=True)

sortie = os.path.join(RACINE, "monde", "portreal.graph.json")
io.open(sortie, "w", encoding="utf-8").write(json.dumps(MONDE, ensure_ascii=False, indent=1))

par_couche = {}
for e in ARETES: par_couche[e["couche"]] = par_couche.get(e["couche"], 0) + 1
print()
print("monde/portreal.graph.json")
print("  %d nœuds, %d arêtes, %d bâtiments, %d portails" %
      (len(NOEUDS), len(ARETES), len(BATIMENTS), len(PORTAILS)))
for c, n in sorted(par_couche.items()): print("   ", c, n)
print("  escaliers (pente > seuil) :", sum(1 for e in ARETES if e["genre"] == "escalier"))
print("  voirie de surface : %.1f km" % (sum(e["longueur_m"] for e in ARETES if e["couche"] == "L1-surface")/1000))
print("  souterrain        : %.1f km" % (sum(e["longueur_m"] for e in ARETES if e["couche"] != "L1-surface")/1000))
