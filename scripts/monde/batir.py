# -*- coding: utf-8 -*-
"""Port-Réal, du graphe au volume — à lancer par Blender, sans interface.

    blender -b --python scripts/monde/batir.py

Lit monde/portreal.graph.json + monde/portreal.terrain.json, bâtit la scène en
MÈTRES (1 unité Blender = 1 m), écrit monde/portreal.blend et rend trois vues
dans monde/rendus/.

Rien n'est modélisé « à l'œil » : chaque volume sort d'une donnée du graphe.
"""
import bpy, bmesh, json, math, os, sys, random
from echelle import polygone_reel
import textures

ICI = os.path.dirname(os.path.abspath(bpy.data.filepath or __file__))
if "--" in sys.argv: ICI = os.path.dirname(os.path.abspath(sys.argv[sys.argv.index("--")+1]))
RACINE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MONDE = os.path.join(RACINE, "monde")
G = json.load(open(os.path.join(MONDE, "portreal.graph.json"), encoding="utf-8"))
T = json.load(open(os.path.join(MONDE, "portreal.terrain.json"), encoding="utf-8"))
# le bâti est sorti du graphe : à 30 000 volumes, un tableau de colonnes pèse
# le tiers d'une liste d'objets, et se lit aussi vite
BAT = json.load(open(os.path.join(MONDE, "portreal.bati.json"), encoding="utf-8"))
COL = {n: k for k, n in enumerate(BAT["_colonnes"])}
R = random.Random(4417)

# ---------------------------------------------------------------------------
def table_rase():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in (bpy.data.meshes, bpy.data.objects, bpy.data.materials):
        for x in list(c): c.remove(x)

def collection(nom, parent=None):
    c = bpy.data.collections.new(nom)
    (parent or bpy.context.scene.collection).children.link(c)
    return c

# --- l'habillage : une photo posée sans dépliage ---------------------------
# POURQUOI LA PROJECTION BOÎTE. Aucun volume d'ici n'a d'UV : `objet()` fait un
# `from_pydata` nu, et `boite`/`maison`/`ruban` sortent des faces brutes.
# Déplier trente mille maisons n'aurait pas de sens — la projection boîte pose
# l'image selon la normale de chaque face, sans une seule coordonnée à écrire.
#
# LE PIÈGE, et il est silencieux : il faut les coordonnées OBJET, pas
# « Generated ». Generated normalise sur la boîte englobante ; comme le bâti est
# fusionné en un maillage par famille, cette boîte fait toute la ville et la
# texture s'étire sur six kilomètres — l'image devient une teinte. Object donne
# des mètres, donc l'échelle réelle de `textures.TAILLE_M`.
#
# Une matière absente de `textures.CHOIX` traverse cette fonction sans rien :
# c'est ainsi que les couleurs de diagnostic (`secret`, `portail`, `egout`, les
# huit `MAT_CAT`) restent en aplat, sans qu'on ait à les lister ici.
def _image(chemin, donnees):
    im = bpy.data.images.load(chemin, check_existing=True)
    im.colorspace_settings.name = "sRGB" if not donnees else "Non-Color"
    return im

def habiller(mt, nom, bsdf):
    choix = textures.CHOIX.get(nom)
    if not choix: return False
    asset = choix[0]
    cartes = textures.cartes(asset)
    if len(cartes) < len(textures.CARTES):
        MANQUE.add(asset)
        return False
    # (horizontale, verticale) : X et Y prennent l'horizontale, Z la verticale.
    # Sur une face verticale, la projection boîte échantillonne un axe du sol et
    # l'axe Z — donc largeur et hauteur tombent chacune sur la bonne mesure ; sur
    # un toit ou le terrain, elle prend X et Y, tous deux horizontaux. Une seule
    # échelle uniforme étirerait du double les tuiles non carrées.
    th, tv = textures.TAILLE_M.get(asset, (2.0, 2.0, False))[:2]
    nt = mt.node_tree
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapp = nt.nodes.new("ShaderNodeMapping")
    mapp.inputs["Scale"].default_value = (1.0/th, 1.0/th, 1.0/tv)
    nt.links.new(coord.outputs["Object"], mapp.inputs["Vector"])

    def pose(carte, donnees):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = _image(cartes[carte], donnees)
        t.projection = "BOX"
        t.projection_blend = 0.30      # adoucit l'arête entre deux faces
        t.extension = "REPEAT"
        nt.links.new(mapp.outputs["Vector"], t.inputs["Vector"])
        return t

    nt.links.new(pose("Color", False).outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(pose("Roughness", True).outputs["Color"], bsdf.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(pose("NormalGL", True).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    HABILLES.add(nom)
    return True

HABILLES, MANQUE = set(), set()

def matiere(nom, rgb, rugosite=0.85, metal=0.0, alpha=1.0, emission=None):
    if nom in bpy.data.materials: return bpy.data.materials[nom]
    mt = bpy.data.materials.new(nom)
    mt.use_nodes = True
    b = mt.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rugosite
    if "Metallic" in b.inputs: b.inputs["Metallic"].default_value = metal
    if emission:
        b.inputs["Emission Color"].default_value = (*emission, 1.0)
        b.inputs["Emission Strength"].default_value = 2.0
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        mt.blend_method = "BLEND" if hasattr(mt, "blend_method") else mt.blend_method
    # La couleur reste posée AVANT l'habillage, et ce n'est pas une precaution
    # inutile : si les images manquent, le monde se bâtit quand même, en aplat,
    # comme avant. Une texture absente ne doit pas casser un rendu.
    habiller(mt, nom, b)
    return mt

def objet(nom, verts, faces, mat, coll):
    me = bpy.data.meshes.new(nom)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.shade_flat() if hasattr(me, "shade_flat") else None
    if mat: me.materials.append(mat)
    ob = bpy.data.objects.new(nom, me)
    coll.objects.link(ob)
    return ob

# --- le relief : on l'interroge partout ------------------------------------
RES, NX, NY = T["res_m"], T["nx"], T["ny"]
Z, EAUM = T["z"], T["eau"]
def zsol(x, y):
    i, j = min(NX-2, max(0, int(x/RES))), min(NY-2, max(0, int(y/RES)))
    tx, ty = (x - i*RES)/RES, (y - j*RES)/RES
    a = Z[j][i]*(1-tx) + Z[j][i+1]*tx
    b = Z[j+1][i]*(1-tx) + Z[j+1][i+1]*tx
    return a*(1-ty) + b*ty

# ---------------------------------------------------------------------------
table_rase()
sc = bpy.context.scene
C_TERRAIN = collection("00 terrain")
C_MUR     = collection("01 enceinte")
C_L1      = collection("L1 circulation")
C_L2      = collection("L2 bati")
C_L4      = collection("L4 passages secrets")
C_L5      = collection("L5 sous-sol")
C_REPERE  = collection("99 reperes")

M_TERRE = matiere("terre",    (0.42, 0.38, 0.28))
M_EAU   = matiere("nera",     (0.06, 0.13, 0.19), 0.12)
M_MUR   = matiere("muraille", (0.52, 0.48, 0.42))
M_PORTE = matiere("porte",    (0.62, 0.55, 0.40))
M_ART   = matiere("artere",   (0.72, 0.66, 0.52))
M_RUE   = matiere("rue",      (0.60, 0.55, 0.44))
M_RUELLE= matiere("ruelle",   (0.47, 0.43, 0.36))
M_ESC   = matiere("escalier", (0.66, 0.52, 0.36))
M_QUAI  = matiere("quai",     (0.55, 0.52, 0.48))
M_TOIT  = matiere("toit",     (0.36, 0.20, 0.15))
M_HAUT  = matiere("toit haut",(0.30, 0.24, 0.26))
M_TAUDIS= matiere("taudis",   (0.28, 0.24, 0.18))
M_HANGAR= matiere("hangar",   (0.34, 0.30, 0.24))
M_EGOUT = matiere("egout",    (0.20, 0.32, 0.42), emission=(0.05, 0.14, 0.22))
M_TUNNEL= matiere("tunnel",   (0.45, 0.30, 0.16), emission=(0.20, 0.10, 0.02))
M_SECRET= matiere("secret",   (0.75, 0.14, 0.14), emission=(0.45, 0.03, 0.03))
M_PORTAIL=matiere("portail",  (0.95, 0.78, 0.20), emission=(0.60, 0.42, 0.05))

# ---------------------------------------------------------------------------
# LE TERRAIN
# ---------------------------------------------------------------------------
print("[monde] terrain %d x %d" % (NX, NY))
verts, faces = [], []
for j in range(NY):
    for i in range(NX):
        verts.append((i*RES, j*RES, Z[j][i]))
for j in range(NY-1):
    for i in range(NX-1):
        a = j*NX+i
        faces.append((a, a+1, a+NX+1, a+NX))
ter = objet("terrain", verts, faces, M_TERRE, C_TERRAIN)
ter.data.polygons.foreach_set("use_smooth", [True]*len(ter.data.polygons))

# la nappe d'eau : un plan à l'étale, sur toute l'emprise
L, H = (NX-1)*RES, (NY-1)*RES
objet("nera", [(0,0,0.0), (L,0,0.0), (L,H,0.0), (0,H,0.0)], [(0,1,2,3)], M_EAU, C_TERRAIN)

# ---------------------------------------------------------------------------
# outils de volume
# ---------------------------------------------------------------------------
def boite(cx, cy, z0, larg, prof, haut, cap_deg, verts, faces):
    a = math.radians(cap_deg)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    n = len(verts)
    for dz in (0.0, haut):
        for sx, sy in ((-.5,-.5), (.5,-.5), (.5,.5), (-.5,.5)):
            verts.append((cx + ux*larg*sx + vx*prof*sy,
                          cy + uy*larg*sx + vy*prof*sy, z0 + dz))
    faces += [(n,n+1,n+2,n+3), (n+4,n+7,n+6,n+5),
              (n,n+4,n+5,n+1), (n+1,n+5,n+6,n+2),
              (n+2,n+6,n+7,n+3), (n+3,n+7,n+4,n)]

def maison(cx, cy, z0, larg, prof, haut, cap_deg, toit, verts, faces):
    """Des murs, puis un TOIT — c'est le toit qui fait qu'une ville se lit.

    `pignon` : le faîte perpendiculaire à la rue, donc un pignon sur rue. C'est
    la parcelle étroite et profonde, la plus commune d'une ville médiévale.
    `long`   : le faîte parallèle à la rue — hangars, granges, écuries, manses.
    `plat`   : une terrasse, pour ce qui reçoit du feu (forge, four, étuve).
    `tour`   : une pyramide, pour ce qui doit se voir de loin.
    """
    a = math.radians(cap_deg)
    ux, uy = math.cos(a), math.sin(a)          # le long de la façade
    vx, vy = -uy, ux                           # vers le fond de la parcelle
    def pt(su, sv, z):
        return (cx + ux*larg*su + vx*prof*sv, cy + uy*larg*su + vy*prof*sv, z)
    n = len(verts)
    coins = ((-.5,-.5), (.5,-.5), (.5,.5), (-.5,.5))
    for z in (z0, z0+haut):
        for su, sv in coins: verts.append(pt(su, sv, z))
    faces += [(n,n+1,n+2,n+3),
              (n,n+4,n+5,n+1), (n+1,n+5,n+6,n+2),
              (n+2,n+6,n+7,n+3), (n+3,n+7,n+4,n)]
    zt = z0 + haut
    if toit == "plat":
        faces.append((n+4,n+7,n+6,n+5)); return
    if toit == "tour":
        h = min(larg, prof)*0.75
        verts.append(pt(0, 0, zt+h))
        s_ = n+8
        faces += [(n+4,n+5,s_), (n+5,n+6,s_), (n+6,n+7,s_), (n+7,n+4,s_)]
        return
    h = min(larg, prof)*0.45
    if toit == "long":                          # faîte le long de la façade
        verts.append(pt(-.5, 0, zt+h)); verts.append(pt(.5, 0, zt+h))
        g, d = n+8, n+9
        faces += [(n+4, n+5, d, g), (n+7, g, d, n+6),
                  (n+4, g, n+7), (n+5, n+6, d)]
    else:                                       # pignon sur rue
        verts.append(pt(0, -.5, zt+h)); verts.append(pt(0, .5, zt+h))
        av, ar = n+8, n+9
        faces += [(n+4, av, ar, n+7), (n+5, n+6, ar, av),
                  (n+4, n+5, av), (n+7, ar, n+6)]

def ruban(trace, larg, verts, faces, dz=0.25, ferme_bouts=False):
    """une bande posée sur le terrain, le long d'une polyligne 3D"""
    n0 = len(verts)
    for k, p in enumerate(trace):
        a = trace[min(k+1, len(trace)-1)]
        b = trace[max(k-1, 0)]
        dx, dy = a[0]-b[0], a[1]-b[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy/d*larg/2, dx/d*larg/2
        z = zsol(p[0], p[1]) + dz
        verts.append((p[0]+nx, p[1]+ny, z))
        verts.append((p[0]-nx, p[1]-ny, z))
    for k in range(len(trace)-1):
        a = n0 + k*2
        faces.append((a, a+1, a+3, a+2))

def tube(trace, larg, z_fixe, verts, faces, haut=None):
    """une galerie : une bande à profondeur donnée, avec un plafond"""
    haut = haut or larg*1.3
    n0 = len(verts)
    for k, p in enumerate(trace):
        a = trace[min(k+1, len(trace)-1)]
        b = trace[max(k-1, 0)]
        dx, dy = a[0]-b[0], a[1]-b[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy/d*larg/2, dx/d*larg/2
        z = p[2] if z_fixe is None else z_fixe
        for dz in (0.0, haut):
            verts.append((p[0]+nx, p[1]+ny, z+dz))
            verts.append((p[0]-nx, p[1]-ny, z+dz))
    for k in range(len(trace)-1):
        a = n0 + k*4
        faces += [(a, a+1, a+5, a+4), (a+1, a+3, a+7, a+5),
                  (a+3, a+2, a+6, a+7), (a+2, a, a+4, a+6)]

# ---------------------------------------------------------------------------
# L'ENCEINTE — reprise de la carte, en vraie épaisseur
# ---------------------------------------------------------------------------
MU = G["echelle"]["metre_par_unite_carte"]
carte = json.load(open(os.path.join(RACINE, "etat", "villes", "port-real.json"), encoding="utf-8"))
MUR_H, MUR_E = 18.0, 6.0
vm, fm = [], []
for s in carte["sol"]:
    if s["genre"] != "mur" or "largeur" in s: continue
    pts = [(p[0]*MU, (300-p[1])*MU) for p in s["points"]]
    for a, b in zip(pts, pts[1:]):
        cx, cy = (a[0]+b[0])/2, (a[1]+b[1])/2
        lg = math.hypot(b[0]-a[0], b[1]-a[1])
        cap = math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))
        z = min(zsol(a[0], a[1]), zsol(b[0], b[1])) - 2
        boite(cx, cy, z, lg, MUR_E, MUR_H + 2, cap, vm, fm)
objet("courtine", vm, fm, M_MUR, C_MUR)

vp, fp = [], []
for s in carte["sol"]:
    if s["genre"] != "mur" or s.get("largeur") != 6: continue
    a, b = s["points"][0], s["points"][-1]
    cx, cy = (a[0]+b[0])/2*MU, (300-(a[1]+b[1])/2)*MU
    cap = math.degrees(math.atan2(-(b[1]-a[1]), b[0]-a[0]))
    boite(cx, cy, zsol(cx, cy)-2, 16.0, 12.0, 24.0, cap, vp, fp)
objet("corps de garde", vp, fp, M_PORTE, C_MUR)

# les grands édifices, ramenés à leur taille réelle (voir TAILLE_REELLE)
M_EDIF = matiere("edifice", (0.46, 0.30, 0.26))
ve, fe = [], []
for s in carte["sol"]:
    if s["genre"] != "mur" or not (0 < s.get("largeur", 0) <= 4): continue
    pts = polygone_reel(s.get("nom", ""), s["points"])
    W = [(p[0]*MU, (300-p[1])*MU) for p in pts]
    haut = 46.0 if s.get("nom") == "Le Donjon Rouge" else (
           38.0 if s.get("nom") == "La Fosse aux Dragons" else (
           58.0 if s.get("nom") == "La tour de la Main" else 22.0))
    for a, b in zip(W, W[1:] + W[:1]):
        lg = math.hypot(b[0]-a[0], b[1]-a[1])
        if lg < 1: continue
        cx, cy = (a[0]+b[0])/2, (a[1]+b[1])/2
        cap = math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))
        boite(cx, cy, zsol(cx, cy)-2, lg, 7.0, haut, cap, ve, fe)
objet("edifices", ve, fe, M_EDIF, C_MUR)

# ---------------------------------------------------------------------------
# L1 — LA CIRCULATION, à sa vraie largeur
# ---------------------------------------------------------------------------
BANDES = {"artere": ([], [], M_ART), "rue": ([], [], M_RUE), "ruelle": ([], [], M_RUELLE),
          "escalier": ([], [], M_ESC), "quai": ([], [], M_QUAI)}
for e in G["aretes"]:
    if e["couche"] != "L1-surface": continue
    g = e["genre"] if e["genre"] in BANDES else "rue"
    v, f, _ = BANDES[g]
    ruban(e["trace"], e["largeur_m"], v, f, dz=0.3)
for g, (v, f, mt) in BANDES.items():
    if v: objet("L1 " + g, v, f, mt, C_L1)

# ---------------------------------------------------------------------------
# L2 — LE BÂTI : 4 500 volumes, un seul maillage par famille
# ---------------------------------------------------------------------------
# Une couleur par CATÉGORIE de métier, pas par quartier : c'est ce qui fait
# apparaître le port, les tanneries et la rue d'Acier sans qu'on les dessine.
MAT_CAT = {
    "habitat":   matiere("bati habitat",   (0.40, 0.22, 0.17)),
    "commerce":  matiere("bati commerce",  (0.62, 0.46, 0.20)),
    "artisanat": matiere("bati artisanat", (0.34, 0.34, 0.38)),
    "nuisance":  matiere("bati nuisance",  (0.24, 0.21, 0.15)),
    "plaisir":   matiere("bati plaisir",   (0.55, 0.16, 0.22)),
    "service":   matiere("bati service",   (0.50, 0.38, 0.24)),
    "culte":     matiere("bati culte",     (0.78, 0.74, 0.64)),
    "civique":   matiere("bati civique",   (0.56, 0.56, 0.52)),
}
M_TAUDIS2 = matiere("bati taudis", (0.26, 0.19, 0.14))
cx_, cy_, cf_, cp_, ch_, cc_, cu_ = (COL["x"], COL["y"], COL["facade_m"],
    COL["profondeur_m"], COL["hauteur_m"], COL["cap"], COL["usage"])
ccat_, ctoit_ = COL.get("cat"), COL.get("toit")
paquets = {}
for b in BAT["bati"]:
    cat = b[ccat_] if ccat_ is not None else "habitat"
    toit = b[ctoit_] if ctoit_ is not None else "pignon"
    mt = M_TAUDIS2 if b[cu_] == "taudis" else MAT_CAT.get(cat, MAT_CAT["habitat"])
    v, f, _ = paquets.setdefault(mt.name, ([], [], mt))
    x, y = b[cx_], b[cy_]
    # 0.98 : le retrait n'est là que pour éviter deux murs coplanaires. L'écart
    # entre maisons vient du quartier (echelle.GRAIN), pas du rendu.
    maison(x, y, zsol(x, y) - 1.0, b[cf_]*0.98, b[cp_]*0.98,
           b[ch_] + 1.0, b[cc_], toit, v, f)
for nom, (v, f, mt) in paquets.items():
    if v: objet("L2 " + nom, v, f, mt, C_L2)
print("[monde] bati :", len(BAT["bati"]), "volumes,", len(paquets), "familles")

# L3 — le dedans : cours, halls, arcades, passages entre cours, caves
C_L3 = collection("L3 interieurs")
M_COUR = matiere("cour",    (0.68, 0.64, 0.52))
M_HALL = matiere("hall",    (0.30, 0.46, 0.52), emission=(0.04, 0.16, 0.20))
M_ARC  = matiere("arcade",  (0.58, 0.50, 0.32))
M_PASS = matiere("passage inter-cour", (0.72, 0.52, 0.26), emission=(0.30, 0.16, 0.02))
M_CAVE = matiere("cave",    (0.32, 0.26, 0.34), emission=(0.10, 0.06, 0.14))

vc, fc = [], []
vh, fh = [], []
vv, fv = [], []
for n in G["noeuds"]:
    x, y = n["xyz"][0], n["xyz"][1]
    if n["genre"] == "cour":
        r = math.sqrt(max(20.0, n.get("aire_m2", 60))/math.pi)
        boite(x, y, zsol(x, y) + 0.4, r*1.7, r*1.7, 0.5, 0, vc, fc)
    elif n["genre"] == "hall":
        r = math.sqrt(max(40.0, n.get("aire_m2", 90)))
        boite(x, y, zsol(x, y) + 0.6, r*0.8, r*0.8, 1.2, 0, vh, fh)
    elif n["genre"] == "cave" and n.get("niveau") == -1:
        boite(x, y, n["xyz"][2], 5.0, 5.0, 2.6, 0, vv, fv)
if vc: objet("L3 cours", vc, fc, M_COUR, C_L3)
if vh: objet("L3 halls", vh, fh, M_HALL, C_L3)
if vv: objet("L3 caves", vv, fv, M_CAVE, C_L3)

PAQ = {"porche": ([], [], M_COUR), "arcade": ([], [], M_ARC),
       "passage": ([], [], M_PASS), "entree": ([], [], M_HALL),
       "escalier": ([], [], M_CAVE)}
for e in G["aretes"]:
    if e["couche"] != "L3-interieurs": continue
    v, f, _ = PAQ.get(e["genre"], PAQ["porche"])
    if e["genre"] == "escalier":
        a, b = e["trace"][0], e["trace"][-1]
        if math.hypot(b[0]-a[0], b[1]-a[1]) < 1.5:
            zb, zh = min(a[2], b[2]), max(a[2], b[2])
            boite(a[0], a[1], zb, 1.6, 1.6, max(1.0, zh-zb), 0, v, f)
        else:
            tube([(p[0], p[1], p[2]) for p in e["trace"]], 1.4, None, v, f, haut=2.0)
    else:
        ruban(e["trace"], max(1.2, e["largeur_m"]), v, f, dz=0.7)
for nom, (v, f, mt) in PAQ.items():
    if v: objet("L3 " + nom, v, f, mt, C_L3)
print("[monde] L3 :", sum(1 for n in G["noeuds"] if n["genre"] in ("cour","hall","cave")),
      "lieux,", sum(1 for e in G["aretes"] if e["couche"] == "L3-interieurs"), "liaisons")

# ---------------------------------------------------------------------------
# L5 / L4 — CE QUI EST DESSOUS ET CE QUI EST CACHÉ
# ---------------------------------------------------------------------------
NIV = {int(k): v["z_m"] for k, v in G["niveaux"].items()}
for couche, coll, defaut in (("L5-sous-sol", C_L5, M_EGOUT), ("L4-cache", C_L4, M_SECRET)):
    paquets = {}
    for e in G["aretes"]:
        if e["couche"] != couche: continue
        mt = M_SECRET if e["genre"] == "passage" else (M_TUNNEL if e["genre"] == "tunnel" else M_EGOUT)
        v, f = paquets.setdefault(mt.name, ([], [], mt))[:2]
        dz = NIV.get(e.get("niveau", -2), -10.0)
        tr = [(p[0], p[1], zsol(p[0], p[1]) + dz) for p in e["trace"]]
        tube(tr, max(1.4, e["largeur_m"]), None, v, f, haut=max(2.2, e["largeur_m"]*1.2))
    for nom, (v, f, mt) in paquets.items():
        if v: objet(couche + " " + nom, v, f, mt, coll)

# Les portails : un PUITS entre les deux niveaux qu'ils cousent — pas un mât.
# Un portail est un escalier, une trappe, un puits : il descend, il ne dépasse
# pas. Le jalon de 26 m d'avant se lisait bien quand il y en avait vingt ; à
# cinq mille il traversait la ville de part en part.
NOEUDS = {x["id"]: x for x in G["noeuds"]}
vpo, fpo = [], []
for p in G["portails"]:
    h, b = NOEUDS.get(p["haut"]), NOEUDS.get(p["bas"])
    if not h or not b: continue
    x, y = h["xyz"][0], h["xyz"][1]
    zs = zsol(x, y)
    z_haut = min(h["xyz"][2], zs) + 0.4          # affleure, sans percer le sol
    z_bas = min(b["xyz"][2], z_haut - 1.2)
    boite(x, y, z_bas, 1.8, 1.8, z_haut - z_bas, 0, vpo, fpo)
objet("portails", vpo, fpo, M_PORTAIL, C_REPERE)

# la barre d'échelle : 100 m, et un cube de 1 m à l'origine
vs, fs = [], []
boite(200, 60, 0, 100, 6, 3, 0, vs, fs)
boite(60, 60, 0, 1, 1, 1, 0, vs, fs)
objet("echelle 100m + cube 1m", vs, fs, matiere("repere", (0.95, 0.9, 0.2)), C_REPERE)

# ---------------------------------------------------------------------------
# LUMIÈRE, CAMÉRAS, RENDU
# ---------------------------------------------------------------------------
sol_l = bpy.data.lights.new("soleil", "SUN")
sol_l.energy = 4.0; sol_l.angle = math.radians(2)
so = bpy.data.objects.new("soleil", sol_l)
so.rotation_euler = (math.radians(52), 0, math.radians(212))
sc.collection.objects.link(so)
sc.world = bpy.data.worlds.new("monde")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.42, 0.55, 1)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.7

for moteur in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
    try:
        sc.render.engine = moteur; break
    except Exception: pass
if sc.render.engine == "CYCLES": sc.cycles.samples = 24
print("[monde] moteur", sc.render.engine)
sc.render.resolution_x, sc.render.resolution_y = 1800, 1200
sc.render.film_transparent = False

cam_d = bpy.data.cameras.new("cam")
# une caméra Blender ne voit rien au-delà de 100 m au repos : à l'échelle d'une
# ville, c'est le premier piège, et il rend des images vides sans rien dire.
cam_d.clip_start, cam_d.clip_end = 0.5, 14000.0
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
os.makedirs(os.path.join(MONDE, "rendus"), exist_ok=True)

def vue(nom, loc, cible, ortho=None, cacher=(), focale=42):
    for c in bpy.data.collections:
        c.hide_render = c.name in cacher
    cam.location = loc
    d = (cible[0]-loc[0], cible[1]-loc[1], cible[2]-loc[2])
    n = math.hypot(*d) or 1
    dx, dy, dz = d[0]/n, d[1]/n, d[2]/n
    # une caméra Blender regarde vers -Z au repos : l'inclinaison se prend depuis
    # le bas, et le lacet depuis +Y. Se tromper de signe, c'est filmer le ciel.
    cam.rotation_euler = (math.acos(max(-1, min(1, -dz))), 0, math.atan2(-dx, dy))
    if ortho:
        cam_d.type = "ORTHO"; cam_d.ortho_scale = ortho
    else:
        cam_d.type = "PERSP"; cam_d.lens = focale
    sc.render.filepath = os.path.join(MONDE, "rendus", nom + ".png")
    bpy.ops.render.render(write_still=True)
    print("[monde] rendu", nom)

CX, CY = 2640, 1800
vue("01-plan", (CX, CY, 3400), (CX, CY, 0), ortho=3900)
vue("02-ville", (4300, 3450, 1150), (2750, 1900, 40), focale=40)
# le Donjon Rouge : carte (286,198) → monde (3432, 1224). On le prend du fleuve.
vue("03-donjon-et-port", (4180, 480, 330), (3432, 1224, 80), focale=52)
# une vue rapprochée : c'est la seule façon de juger si la rue existe encore
vue("05-culpucier", (2980, 2020, 165), (2760, 2280, 20), focale=48)
# le relief seul : la seule façon de juger une sous-couche est de la voir nue
vue("07-relief", (CX, CY, 3400), (CX, CY, 0), ortho=5400,
    cacher=("L2 bati", "01 enceinte", "L1 circulation", "L3 interieurs",
            "L4 passages secrets", "L5 sous-sol", "99 reperes"))
vue("08-relief-rasant", (400, 300, 260), (2900, 2000, 30), focale=45,
    cacher=("L2 bati", "01 enceinte", "L1 circulation", "L3 interieurs",
            "L4 passages secrets", "L5 sous-sol", "99 reperes"))
vue("06-le-dedans", (CX, CY, 3400), (CX, CY, 0), ortho=3900,
    cacher=("L2 bati", "01 enceinte"))
vue("04-souterrains", (CX, CY, 3400), (CX, CY, 0), ortho=3900,
    cacher=("L2 bati", "01 enceinte", "00 terrain"))

for c in bpy.data.collections: c.hide_render = False   # on rend le .blend intact
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(MONDE, "portreal.blend"))
print("[monde] blend écrit —", len(BAT["bati"]), "bâtiments,",
      len(G["aretes"]), "arêtes,", len(G["portails"]), "portails")
# Le compte des habillées se DIT : une texture qui n'a pas pris ne se voit pas
# sur un rendu — l'aplat a l'air d'un parti pris, pas d'une panne.
print("[monde] textures — %d matières habillées : %s"
      % (len(HABILLES), ", ".join(sorted(HABILLES)) or "aucune"))
if MANQUE:
    print("[monde] textures MANQUANTES pour %s — lance "
          "« python scripts/monde/textures.py --tirer »" % ", ".join(sorted(MANQUE)))
