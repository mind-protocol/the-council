# -*- coding: utf-8 -*-
"""Assemble etat/villes/port-real.json depuis le tissu engendré."""
import json, io, os, math

SP = os.path.dirname(os.path.abspath(__file__))
CIBLE = os.path.join(os.path.dirname(os.path.dirname(SP)), "etat", "villes", "port-real.json")
T = json.load(io.open(os.path.join(SP, "tissu.json"), encoding="utf-8"))
VOIES, TOITS = T["voies"], T["toits"]

def dedans(poly, x, y):
    r = False; j = len(poly)-1
    for i in range(len(poly)):
        if (poly[i][1] > y) != (poly[j][1] > y) and \
           x < (poly[j][0]-poly[i][0])*(y-poly[i][1])/(poly[j][1]-poly[i][1])+poly[i][0]:
            r = not r
        j = i
    return r
def dist_seg(px, py, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    q = dx*dx+dy*dy
    t = 0 if q == 0 else max(0, min(1, ((px-a[0])*dx+(py-a[1])*dy)/q))
    return math.hypot(px-a[0]-t*dx, py-a[1]-t*dy)
def dist_ligne(pts, x, y):
    return min(dist_seg(x, y, a, b) for a, b in zip(pts, pts[1:]))
def par_nom(n):
    for v in VOIES:
        if v.get("nom") == n: return v["points"]
    return None

EAU = [
    [[0,282],[70,276],[150,272],[228,274],[296,276],[348,268],[386,250],[398,300],[0,300]],
    [[386,250],[398,300],[440,300],[440,0],[404,8],[392,74],[386,150],[380,200]],
]
CULPU    = [[204,196],[252,190],[276,206],[268,236],[224,242],[198,224]]
TANNERIE = [[194,230],[228,226],[232,246],[196,248]]
PORT_ZONE= [[266,246],[312,242],[356,232],[362,248],[352,266],[300,276],[266,270]]
VASE     = [[196,256],[240,252],[276,254],[280,270],[236,276],[194,268]]
AIRE     = [[210,256],[252,254],[256,266],[212,268]]
PLACES = [
    ("La grande place", [[184,138],[212,136],[216,158],[188,162]],
     "Le cœur du commerce : cinq rues y versent et rien n'y pousse."),
    ("Le marché aux chevaux", [[106,138],[132,136],[134,160],[108,162]],
     "Sous la porte des Dieux : ce qui arrive par la route de la Rose se vend ici."),
    ("Le marché aux poissons", [[274,216],[300,214],[302,234],[276,236]],
     "Le premier endroit de la ville où un prix bouge."),
]
ACIER   = par_nom("La rue d'Acier")
CROCHET = par_nom("Le Crochet")
DEHORS_NOM = [
    ([[89,140],[46,132],[0,124]],   "Le faubourg de la Rose"),
    ([[262,49],[266,22],[258,0]],   "Le faubourg royal"),
    ([[370,134],[404,122],[440,108]],"Le faubourg de Rosby"),
    ([[159,245],[136,264],[104,278]],"Les baraques du gué"),
    ([[90,183],[54,196],[20,214]],  "Le faubourg du Lion"),
]

def quartier(p, zone):
    x, y = p[0], p[1]
    if zone == "port": return "Le port et ses hangars"
    if dedans(PORT_ZONE, x, y): return "Le port et ses hangars"
    if dedans(CULPU, x, y): return "Le Culpucier"
    if dedans(TANNERIE, x, y): return "Les tanneries"
    if ACIER and dist_ligne(ACIER, x, y) < 9: return "La rue d'Acier"
    if CROCHET and dist_ligne(CROCHET, x, y) < 9: return "Le Crochet"
    if zone == "haute": return "La ville haute"
    if zone == "faubourg":
        d, nom = min((dist_ligne(pts, x, y), n) for pts, n in DEHORS_NOM)
        return nom if d < 26 else "Le bourg de la Gadoue"
    return "La ville"

# les places et la vase sont du sol nu : on en retire ce qui s'y était posé
VIDES = [p for _, p, _ in PLACES] + [VASE, AIRE]
def sur_du_vide(x, y):
    return any(dedans(v, x, y) for v in VIDES)

QUARTIERS = {}
ote = 0
for zone, pts in TOITS.items():
    for p in pts:
        if sur_du_vide(p[0], p[1]): ote += 1; continue
        QUARTIERS.setdefault(quartier(p, zone), []).append(p)
print("toits ôtés des places :", ote)

DETAIL_Q = {
    "Le Culpucier": "Le fond entre les deux collines : blocs minuscules, ruelles percées à la main, et le ragoût pour tout registre.",
    "Les tanneries": "Sous le vent, contre le mur du midi. On les sent avant de les voir.",
    "La rue d'Acier": "Elle monte droit la colline de Visenya : plus haut on forge, plus cher on vend.",
    "Le Crochet": "La rue qui contourne le pied de la colline d'Aegon : gens de robe, et ceux qui les servent.",
    "La ville haute": "Sur les pentes : parcelles larges, cours fermées, et de la place perdue — ce qui se voit d'en bas.",
    "Le port et ses hangars": "Entre le mur et l'eau : le quai, sa rue, ses traverses, et des hangars en travers pour que tout passe droit.",
    "Le bourg de la Gadoue": "Bâti hors la porte, entre le mur et la vase, sans que personne l'ait permis.",
}
# une étiquette au barycentre du quartier, puis on les écarte les unes des autres
ETIQ_Q = {}
for n, pts in QUARTIERS.items():
    if n == "La ville": ETIQ_Q[n] = [206, 108]; continue
    ETIQ_Q[n] = [round(sum(p[0] for p in pts)/len(pts), 1),
                 round(sum(p[1] for p in pts)/len(pts), 1)]

sol = []
def A(**kw): sol.append(kw)

A(genre="eau", nom="La Néra", etiq=[110, 292], points=EAU[0])
A(genre="eau", nom="La rade", etiq=[416, 176], points=EAU[1])
A(genre="champ", nom="Les champs du dehors", etiq=[38, 76], points=[[0,44],[62,34],[86,66],[80,124],[0,136]])
A(genre="bois", nom="Le bois de la route royale", etiq=[318, 22], points=[[286,26],[338,10],[386,20],[380,52],[326,58],[294,46]])
A(genre="champ", nom="Le champ de tournoi", etiq=[100, 236], points=[[80,214],[122,226],[118,252],[78,244]])
A(genre="marais", nom="Les prés bas de la Néra", etiq=[40, 200], points=[[0,170],[50,178],[74,206],[48,250],[0,246]])
A(genre="greve", nom="La vase", etiq=[248, 274], points=VASE)
A(genre="champ", nom="L'aire de bris", etiq=[218, 250], points=AIRE,
  detail="Le chantier de bris : ce qui reste d'une coque quand vingt et un hommes s'y mettent.")
for nom, pts, det in PLACES:
    A(genre="champ", nom=nom, etiq=[round(sum(p[0] for p in pts)/4), round(sum(p[1] for p in pts)/4) - 14],
      points=pts, detail=det)
A(genre="colline", nom="La colline de Rhaenys", etiq=[248, 66], points=[[246,72],[292,64],[318,84],[314,116],[280,128],[248,112],[236,90]])
A(genre="colline", nom="La colline de Visenya", etiq=[112, 196], points=[[122,158],[168,150],[190,170],[184,204],[150,216],[120,202],[110,178]])
A(genre="colline", nom="La colline d'Aegon", etiq=[344, 216], points=[[288,166],[330,158],[356,178],[358,212],[330,230],[294,220],[280,192]])

# ---- la circulation, du plus gros au plus fin -----------------------------
RANG_ORDRE = {"artere": 0, "rue": 1, "ruelle": 2}
for v in sorted(VOIES, key=lambda w: RANG_ORDRE.get(w["rang"], 3)):
    e = {"genre": "route", "largeur": v["largeur"], "points": v["points"]}
    if v.get("nom"): e["nom"] = v["nom"]
    e["detail"] = v["raison"]
    sol.append(e)
# les routes du dehors : elles existaient avant la ville
for pts, nom in [([[89,140],[46,132],[0,124]], "La route de la Rose"),
                 ([[262,49],[266,22],[258,0]], "La route royale"),
                 ([[370,134],[404,122],[440,108]], "La route de Rosby"),
                 ([[159,245],[136,264],[104,278]], "La route du gué")]:
    A(genre="route", largeur=6, nom=nom, points=pts,
      detail="Route du dehors : la ville s'est bâtie sur elle, pas l'inverse.")

# ---- les toits ------------------------------------------------------------
for n, pts in sorted(QUARTIERS.items(), key=lambda kv: -len(kv[1])):
    e = {"genre": "village", "nom": n, "etiq": ETIQ_Q[n], "points": pts}
    if n in DETAIL_Q: e["detail"] = DETAIL_Q[n]
    sol.append(e)

# ---- le mur, ses portes, et ce qui est bâti à l'équerre -------------------
MUR = [
    ("Le mur du couchant", [104,92], [[90,132],[96,112],[118,80],[138,70]], None),
    ("La Vieille Porte", [146,58], [[138,70],[154,66]], 6),
    ("Le mur du nord", [206,42], [[154,66],[170,58],[232,48],[254,49]], None),
    ("La porte des Dragons", [262,38], [[254,49],[270,49]], 6),
    ("Le mur du levant", [348,80], [[270,49],[292,52],[336,74],[364,112],[369,126]], None),
    ("La porte de Fer", [392,136], [[369,126],[371,142]], 6),
    ("Le mur de la rivière", [390,196], [[371,142],[374,158],[370,204],[356,236],[310,246]], None),
    ("La porte de la Gadoue", [296,238], [[292,248],[272,250]], 6),
    ("Le mur du midi", [216,262], [[272,250],[246,252],[186,250],[168,247]], None),
    ("La porte du Roi", [158,260], [[168,247],[150,244]], 6),
    (None, None, [[150,244],[130,238],[100,206],[92,192]], None),
    ("La porte du Lion", [70,190], [[92,192],[89,174]], 6),
    (None, None, [[89,174],[88,160],[89,148]], None),
    ("La porte des Dieux", [64,124], [[89,148],[90,132]], 6),
]
for nom, etiq, pts, larg in MUR:
    e = {"genre": "mur", "points": pts}
    if larg: e["largeur"] = larg
    if nom: e["nom"] = nom; e["etiq"] = etiq
    if larg: e["detail"] = "Une des sept portes : tout ce qui entre y est vu, compté, ou payé."
    sol.append(e)

BATI = [
    ("Le Donjon Rouge", [322,186], 4, [[300,176],[344,170],[352,200],[330,220],[300,214],[292,194],[300,176]], None),
    ("La tour de la Main", [352,164], 2.5, [[336,174],[346,172],[347,182],[337,184],[336,174]], None),
    ("La Fosse aux Dragons", [276,74], 4, [[262,80],[292,84],[300,102],[286,118],[262,116],[252,98],[262,80]],
     "Rhaenys porte la fosse : on ne monte cette colline que pour les bêtes."),
    ("Le vieux septuaire", [156,158], 3, [[140,166],[166,162],[172,180],[152,190],[136,182],[140,166]], None),
    ("La Guilde des Alchimistes", [238,116], 3, [[224,124],[248,122],[250,140],[226,142],[224,124]],
     "Sur la rue des Sœurs, et sous elle : personne ne sait jusqu'où vont leurs caves."),
    ("Les casernes du Guet", [234,150], 3, [[222,158],[244,156],[246,174],[224,176],[222,158]], None),
    ("Le bureau du maître de port", [336,240], 2.5, [[326,248],[340,246],[341,256],[327,258],[326,248]],
     "Les rôles d'entrée : ce qui n'y est pas écrit n'est jamais entré."),
    ("Le hangar du chantier", None, 2.5, [[214,257],[230,255],[231,265],[215,267],[214,257]], None),
    (None, None, 2.5, [[218,268],[218,275],[224,275],[224,268],[230,268],[230,275]], None),
]
for nom, etiq, larg, pts, det in BATI:
    e = {"genre": "mur", "largeur": larg, "points": pts}
    if nom: e["nom"] = nom
    if etiq: e["etiq"] = etiq
    if det: e["detail"] = det
    sol.append(e)

A(genre="quai", nom="Les quais de la Néra", etiq=[330, 274], points=[[278,270],[314,266],[350,258]],
  detail="Sept coques de front à basse mer. Tout ce qui y touche doit passer la Gadoue pour entrer.")
A(genre="quai", points=[[226,270],[240,278]],
  detail="L'appontement du chantier : on y hale ce qu'on démonte.")

# ---- on écarte les étiquettes qui se marchent dessus ----------------------
pin = {s["nom"] for s in sol if s.get("nom") and s["genre"] not in ("village",)}
for _ in range(400):
    bouge = False
    for a in sol:
        if not a.get("etiq") or not a.get("nom"): continue
        for b in sol:
            if b is a or not b.get("etiq") or not b.get("nom"): continue
            dx, dy = a["etiq"][0]-b["etiq"][0], a["etiq"][1]-b["etiq"][1]
            d = math.hypot(dx, dy)
            if d >= 15 or d == 0: continue
            bouge = True
            k = (15-d)/2
            if a["nom"] not in pin:
                a["etiq"] = [round(a["etiq"][0]+dx/d*k, 1), round(a["etiq"][1]+dy/d*k, 1)]
            if b["nom"] not in pin:
                b["etiq"] = [round(b["etiq"][0]-dx/d*k, 1), round(b["etiq"][1]-dy/d*k, 1)]
    if not bouge: break

# ---- ce que le siège CROIT : corps et acteurs ------------------------------
vieux = json.load(io.open(CIBLE, encoding="utf-8"))
PLACE = {  # le bas de la ville a bougé : on replace ce qui s'y tient
    "coque-du-quinze": [238,262], "brise-coques": [222,260], "gosses-de-la-greve": [200,266],
    "guet-de-la-gadoue": [282,244], "queue-de-la-gadoue": [274,238], "manteaux-dor": [234,166],
    "foule-du-culpucier": [236,216], "marche-aux-poissons": [288,226], "cogues-a-quai": [316,264],
    "barques-de-peche": [168,278], "dragons-de-la-fosse": [276,98], "ost-de-la-couronne": [212,26],
}
for c in vieux["corps"]:
    if c["id"] in PLACE: c["centre"] = PLACE[c["id"]]
ACT = {
    "marlo-vasse": [228,259], "hann-bourbe": [236,261], "nel-bec": [204,265],
    "waltyr-poix": [281,247], "ollo-marran": [333,251], "sirel-quintaine": [238,212],
    "aegon-ii": [322,194], "otto": [316,186], "alicent": [330,202], "helaena": [332,190],
    "criston": [306,182], "aemond": [278,104], "larys": [312,208],
}
for a in vieux["acteurs"]:
    if a["id"] in ACT: a["ou"] = ACT[a["id"]]

d = {
    "_lisez_moi": vieux["_lisez_moi"],
    "_engendre": "Le tissu de cette ville n'est pas semé : il est ENGENDRÉ par la circulation "
        "(scripts hors dépôt, graine fixe). Nœuds obligatoires (portes, quais, Donjon, marchés, "
        "guildes, septuaire, cols) → artères entre ce qui draine des centaines de gens par jour "
        "→ rues qui tiennent les artères ensemble → ruelles là où un bloc est trop profond "
        "→ maisons à façade sur rue. Le tracé suit un coût « distance + pente + obstacle − reprise "
        "d'une voie existante » : c'est pourquoi aucune rue n'est droite et pourquoi elles se "
        "rejoignent. Chaque voie porte son `detail` : sa RAISON d'exister, lisible au survol.",
    "id": "port-real-129-3-23",
    "nom": "Port-Réal — les trois collines, les sept portes et la Néra",
    "quand": "129 AC — 3e lune, 23e jour",
    "echelle": "La ville entière : de la porte des Dieux à la rade, une lieue et demie de mur",
    "lieu_id": "port-real",
    "basculer": False,
    "repere": [0, 0, 440, 300],
    "par_cercle": 50,
    "sol": sol,
    "faits": [],
    "corps": vieux["corps"],
    "acteurs": vieux["acteurs"],
    "_acteurs_lisez_moi": vieux["_acteurs_lisez_moi"],
}

def rendre(o, ind=0):
    p = "  "*ind
    if isinstance(o, dict):
        L = []
        for k, v in o.items():
            if k == "points" and isinstance(v, list):
                fmt = lambda q: "[" + ",".join(("%g" % n) for n in q) + "]"
                if len(v) > 16:
                    paq, li = [], []
                    for q in v:
                        li.append(fmt(q))
                        if len(li) == 8: paq.append(",".join(li)); li = []
                    if li: paq.append(",".join(li))
                    s = "[\n" + p + "    " + (",\n"+p+"    ").join(paq) + "]"
                else:
                    s = "[" + ",".join(fmt(q) for q in v) + "]"
            elif k in ("etiq","centre","ou","repere") and isinstance(v, list):
                s = "[" + ", ".join("%g" % x for x in v) + "]"
            else:
                s = rendre(v, ind+1)
            L.append(p + "  " + json.dumps(k, ensure_ascii=False) + ": " + s)
        return "{\n" + ",\n".join(L) + "\n" + p + "}"
    if isinstance(o, list):
        if not o: return "[]"
        return "[\n" + ",\n".join(p + "  " + rendre(x, ind+1) for x in o) + "\n" + p + "]"
    return json.dumps(o, ensure_ascii=False)

io.open(CIBLE, "w", encoding="utf-8").write(rendre(d) + "\n")
nv = sum(1 for s in sol if s["genre"] == "route")
print("sol", len(sol), "| voies", nv, "| toits",
      sum(len(s["points"]) for s in sol if s["genre"] == "village"),
      "| quartiers", sum(1 for s in sol if s["genre"] == "village"))
for n, pts in sorted(QUARTIERS.items(), key=lambda kv: -len(kv[1])):
    print("   ", n, len(pts))
