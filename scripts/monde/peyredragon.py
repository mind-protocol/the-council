# -*- coding: utf-8 -*-
"""Peyredragon pour le monde 3D — mêmes formats que portreal.*.json.

    python scripts/monde/peyredragon.py            # engendre
    python scripts/monde/peyredragon.py --verifier # dit si c'est périmé, sort 1

Écrit `monde/peyredragon.terrain.json`, `.bati.json` et `.graph.json`, lisibles
tels quels par `ecrans/modules/monde/`. Rien n'est modélisé ici : tout vient de
`scripts/materialisation/peyredragon.py`, qui reste la seule autorité sur le
relief, le site du château et le bourg. Ce fichier ne fait que TRADUIRE.

Deux différences de repère avec la matérialisation, et elles sont ici, nulle
part ailleurs :
  · le monde 3D compte depuis le coin sud-ouest, en mètres positifs — on décale.
  · il veut un cap en DEGRÉS, comptés comme les instances three.js — on convertit.
"""
import io
import json
import math
import os
import sys

MATER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "materialisation")
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SORTIE = os.path.join(RACINE, "monde")

# ---------------------------------------------------------------------------
# Péremption : les cinq sorties sont-elles postérieures au modèle ?
# Ce bloc vit AVANT l'import de numpy et de la matérialisation, et c'est
# délibéré : `--verifier` doit pouvoir se brancher partout (un hook, un
# démarrage, une boucle de guet) sans payer trois secondes d'import ni tomber
# si le modèle est en cours d'édition et ne s'importe pas.
SORTIES = ("terrain", "bati", "maillage", "carte", "graph")


def _sources():
    """Les .py dont les sorties dépendent : le modèle, et ce fichier-ci."""
    fichiers = [os.path.abspath(__file__)]
    if os.path.isdir(MATER):
        # Pas de récursion : `__pycache__` n'est pas une source et rebouge à
        # chaque import — il ferait sonner l'alarme sans arrêt.
        fichiers += [os.path.join(MATER, n) for n in sorted(os.listdir(MATER))
                     if n.endswith(".py")]
    return fichiers


def _verifier():
    """Sort 1 si une sortie manque ou date d'avant une source. N'écrit rien."""
    horloge = [(f, os.path.getmtime(f)) for f in _sources() if os.path.exists(f)]
    dernier = max([m for _, m in horloge] or [0.0])
    manque, vieilles, vues = [], [], []
    for nom in SORTIES:
        chemin = os.path.join(SORTIE, "peyredragon." + nom + ".json")
        if not os.path.exists(chemin):
            manque.append(nom)
            continue
        m = os.path.getmtime(chemin)
        vues.append(m)
        if m < dernier:
            vieilles.append((nom, m))
    if not manque and not vieilles:
        print("Le monde 3D de Peyredragon est À JOUR (%d sources, %d sorties)."
              % (len(horloge), len(SORTIES)))
        return 0
    print("Le monde 3D de Peyredragon est PÉRIMÉ.")
    if manque:
        print("  absentes : " + ", ".join(manque))
    for nom, m in vieilles:
        print("  peyredragon.%s.json date de %s, le modèle de %s"
              % (nom, _quand(m), _quand(dernier)))
    # Ce qui a bougé depuis la plus ANCIENNE sortie encore là : c'est cette
    # liste-là qui dit quoi relire, pas la seule source la plus récente.
    seuil = min(vues) if vues else 0.0
    for f, m in sorted([x for x in horloge if x[1] > seuil],
                       key=lambda x: -x[1])[:6]:
        print("    plus récent : %s (%s)"
              % (os.path.relpath(f, RACINE).replace(os.sep, "/"), _quand(m)))
    print("  relancez : python scripts/monde/peyredragon.py")
    return 1


def _quand(m):
    import time
    return time.strftime("%H:%M:%S", time.localtime(m))


if __name__ == "__main__" and "--verifier" in sys.argv:
    sys.exit(_verifier())

import numpy as np           # noqa: E402

sys.path.insert(0, MATER)

import lieux as Li            # noqa: E402
import peyredragon as P       # noqa: E402

RES = 10.0                    # mètres par point de relief, comme Port-Réal
DEMI = 2600.0                 # l'emprise : 5,2 km de côté, l'île tient dedans
X0 = P.ILE[0] - DEMI
Y0 = P.ILE[1] - DEMI
NX = NY = int(2 * DEMI / RES) + 1


def _local(x, y):
    """Du repère de la matérialisation à celui du monde 3D."""
    return (x - X0, y - Y0)


# ---------------------------------------------------------------------------
def terrain():
    xs = X0 + np.arange(NX, dtype=np.float32) * RES
    ys = Y0 + np.arange(NY, dtype=np.float32) * RES
    X, Y = np.meshgrid(xs, ys)                 # [ny][nx], comme le format
    Z = P.altitude(X, Y).astype(np.float32)
    return {
        "_lisez_moi":
            "Relief de Peyredragon, décalque de scripts/materialisation/"
            "peyredragon.py — cône du Dragonmont, caldeira ouverte au levant, "
            "frange de falaises sauf du côté de la rade, éperon du château et "
            "assise arasée à %.0f m. C'est L'AUTORITÉ d'altitude : le bâti et "
            "la voirie s'y posent, ils ne la corrigent jamais." % P.ASSISE,
        "res_m": RES, "nx": NX, "ny": NY,
        "z": np.round(Z, 2).tolist(),
        "eau": (Z <= 0.0).astype(np.int8).tolist(),
    }


# ---------------------------------------------------------------------------
COLONNES = ["x", "y", "z", "cap", "facade_m", "profondeur_m", "etages",
            "hauteur_m", "quartier", "usage", "cave"]


def _ligne(x, y, z, cap, facade, profondeur, hauteur, quartier, usage, cave=0):
    return [round(x, 1), round(y, 1), round(z, 1),
            round(math.degrees(cap) % 360, 1), round(facade, 1),
            round(profondeur, 1), max(1, int(hauteur // 3.2)), round(hauteur, 1),
            quartier, usage, cave]


def bati():
    """Le bourg, les logis du plan, la courtine et les tours — en boîtes.

    La courtine entre ici et pas dans l'enceinte tirée de la carte 2D : le
    module `enceinte.js` métrise le dessin de Port-Réal avec SON échelle
    (12 m par unité). Peyredragon n'a pas cette échelle-là ; plutôt que de
    tordre une constante partagée, on livre ses murs déjà en mètres.
    """
    lignes = []

    for f in P.feux():
        x, y = _local(f["x"], f["y"])
        lignes.append(_ligne(x, y, f["z"], f["cap"], f["larg"], f["long"],
                             f["haut"], f["quartier"], f["usage"]))

    # Les logis du château ne sont plus ici : ils sont dans le maillage, avec
    # leurs murs épais et leurs portes. Le bâti ne garde que le bourg, dont les
    # soixante-sept feux n'ont rien à gagner à être maillés un par un.
    for L in []:
        # Trois exclusions, chacune pour une raison différente :
        #  · `dessous` est taillé dans la roche — pas un volume posé ;
        #  · `sommet` est un ÉTAGE d'une masse existante. Le sortir ici le pose
        #    à 158 m sur un terrain qui en fait 124 : la salle flotte ;
        #  · une aire (un jardin, des lices) n'est pas un bâtiment, et le bâti
        #    coiffe tout ce qu'il reçoit d'un toit à deux pentes.
        if L["etage"] in ("dessous", "sommet") or L["id"] in Li.AIRES:
            continue
        x, y = _local(L["ou"][0], L["ou"][1])
        dx, dy = L["demi"]
        h = Li.HAUTEUR.get(L["id"], 13.0 if L["genre"] == "rond" else 10.0)
        usage = ("caserne" if L["id"] in ("communs", "baraques") else
                 "culte" if L["id"] == "septuaire" else
                 "forge" if L["id"] == "forge" else
                 "office" if L["id"] in ("roukerie", "officine", "archives") else
                 "logis")
        lignes.append(_ligne(x, y, L["ou"][2], P.RADE, dx * 2, dy * 2, h,
                             "Le château", usage))

    # La courtine et les tours ne sont PAS ici : `bati.js` coiffe chaque ligne
    # d'un toit à deux pentes, ce qui donne un mur de soixante mètres sous une
    # toiture et une tour carrée. Elles passent par la carte (voir `carte()`).
    return {"_colonnes": COLONNES, "bati": lignes,
            "_lisez_moi": "Une ligne par volume posé au sol, en mètres, dans le "
                          "repère du monde. Ni murs ni tours : ils sont dans "
                          "peyredragon.carte.json, que l'enceinte sait bâtir."}


# ---------------------------------------------------------------------------
def carte():
    """La muraille, la porte et les tours — EN MÈTRES, comme tout le reste.

    `metres: true` dit à `enceinte.js` de ne rien remettre à l'échelle : ni les
    unités de dessin, ni la correction de taille des monuments. Le modèle
    travaille en mètres de bout en bout ; lui faire écrire des unités de carte
    pour qu'on les remultiplie de l'autre côté serait une échelle de plus à
    tenir juste, et c'est précisément ce qu'on ne veut plus.
    """
    sol = []
    pts = [_local(*P._monde(p)) for p in P.ENCEINTE]
    sol.append({"genre": "mur", "nom": "L'enceinte de Peyredragon",
                "haut": 26.0, "epaisseur": 7.0,
                "points": [[round(x, 1), round(y, 1)] for x, y in pts + pts[:1]]})
    # la porte de mer : deux points et une largeur de 6 — c'est ce qui en fait
    # un corps de garde plutôt qu'un pan de courtine
    g = _local(*P._monde((P.PORTE[0], P.PORTE[1] - 9)))
    d = _local(*P._monde((P.PORTE[0], P.PORTE[1] + 9)))
    sol.append({"genre": "mur", "nom": "La porte de mer", "largeur": 6,
                "larg": 18.0, "epaisseur": 12.0, "haut": 34.0,
                "points": [[round(g[0], 1), round(g[1], 1)],
                           [round(d[0], 1), round(d[1], 1)]]})
    # les tours et le donjon : leurs vrais rayons et leurs vraies hauteurs
    for (x, y, r, h, fl) in P.TOURS:
        c = [_local(*P._monde((x + math.cos(a) * r, y + math.sin(a) * r)))
             for a in np.linspace(0, 2 * math.pi, 13)[:-1]]
        sol.append({"genre": "mur", "largeur": 3, "haut": h + 3.0,
                    "epaisseur": 5.0, "assise": P.ASSISE,
                    "points": [[round(u, 1), round(v, 1)] for u, v in c]})
    c = [_local(*P._monde((-8 + math.cos(a) * 31, -4 + math.sin(a) * 31)))
         for a in np.linspace(0, 2 * math.pi, 17)[:-1]]
    sol.append({"genre": "mur", "nom": "Le Tambour de Pierre", "largeur": 3,
                "haut": 44.0, "epaisseur": 8.0, "assise": P.ASSISE,
                "points": [[round(u, 1), round(v, 1)] for u, v in c]})
    return {"_lisez_moi": "La muraille de Peyredragon, en MÈTRES dans le repère "
                          "du monde (`metres: true`). Ce n'est pas la carte du "
                          "jeu : c'est le relevé du modèle, engendré par "
                          "scripts/monde/peyredragon.py.",
            "id": "peyredragon-monde3d", "lieu_id": "peyredragon",
            "metres": True, "sol": sol, "corps": [], "acteurs": [], "faits": []}


# ---------------------------------------------------------------------------
def maillage():
    """Le château en VRAI maillage : parois épaisses, portes, archères.

    Le bâti d'une ville se rend en boîtes instanciées — c'est ce qui permet à
    Port-Réal de tenir ses quarante-huit mille volumes en deux appels de dessin.
    Un château de deux cents mètres n'a pas ce problème : vingt mille triangles
    passent sans effort, et c'est le seul moyen de voir qu'une porte est percée.

    Les sommets sont dédoublonnés et les faces groupées par matière, pour que le
    navigateur en fasse une géométrie indexée et un matériau par groupe.
    """
    import formes as F
    import programme as Prog
    import circulation as Circ
    # Le château ne vient plus du plan du jeu mais du PROGRAMME architectural,
    # et les refends percés viennent du graphe de circulation. Servir encore
    # `lieux.bati()` ici, c'était livrer au monde 3D un château qui n'existe
    # plus dans les images.
    tris, mat = F.joindre(P.chateau(),
                          Prog.batir(Circ.refends_perces(Circ.engendrer())),
                          P.montee(), P.quai())
    plats = tris.reshape(-1, 3).astype(np.float64)
    plats[:, 0] -= X0
    plats[:, 1] -= Y0
    _, premier, inverse = np.unique(np.round(plats, 3), axis=0,
                                    return_index=True, return_inverse=True)
    sommets = plats[premier]
    faces = inverse.reshape(-1, 3)

    ordre = np.argsort(mat.astype(str), kind="stable")
    faces, mat = faces[ordre], mat[ordre]
    groupes, debut = [], 0
    for i in range(1, len(mat) + 1):
        if i == len(mat) or mat[i] != mat[debut]:
            groupes.append({"matiere": str(mat[debut]), "debut": debut * 3,
                            "compte": (i - debut) * 3})
            debut = i
    return {
        "_lisez_moi": "Le château de Peyredragon en maillage indexé, en mètres "
                      "dans le repère du monde. Une géométrie, un groupe par "
                      "matière. Engendré par scripts/monde/peyredragon.py.",
        "sommets": [round(float(v), 2) for v in sommets.reshape(-1)],
        "index": [int(v) for v in faces.reshape(-1)],
        "groupes": groupes,
    }


# ---------------------------------------------------------------------------
def graphe():
    """La voirie : la montée en lacets, les chemins du bourg, le quai."""
    aretes = []

    def ajouter(trace, genre, largeur, nom=None):
        aretes.append({"couche": "L1-surface", "genre": genre,
                       "largeur_m": largeur,
                       "trace": [[round(x, 1), round(y, 1)]
                                 for x, y in (_local(p[0], p[1]) for p in trace)],
                       "nom": nom})

    ajouter(P._lacets(), "escalier", 7.0, "Le grand escalier")

    ux, uy = -P._SA, P._CA
    def q(u, v):
        return (P.QUAI[0] + ux * u - P._D[0] * v, P.QUAI[1] + uy * u - P._D[1] * v)
    for trace, nom in (
            ([q(-40, 30), q(-150, 46), q(-260, 78), q(-350, 128)], None),
            ([q(40, 30), q(150, 44), q(250, 74), q(330, 120)], None),
            ([q(-70, 55), q(0, 62), q(80, 58)], "La rue du bourg"),
            ([q(-190, 96), q(-120, 128), q(-40, 150)], None)):
        ajouter(trace, "rue", 5.0, nom)
    ajouter([q(-78, 0), q(78, 0)], "quai", 26.0, "Le quai")

    noeuds = []
    import programme as Prog
    pl = Prog.plan()
    # Un repère est ce qu'on nomme en REGARDANT le château de loin : la grande
    # salle, le septuaire, les écuries. Pas l'armurerie ni la buanderie, et
    # surtout pas les appentis de comblement.
    NOMMES = {"grande-salle", "septuaire", "cuisines", "ecuries", "roukerie",
              "corps-de-garde", "garnison", "hotes", "retrait", "forge"}
    for c in pl["corps"]:
        if c["id"] not in NOMMES:
            continue
        x, y = _local(*c["milieu"])
        genre = ("monument" if c["id"] == "grande-salle" else
                 "septuaire" if c["id"] == "septuaire" else
                 "porte" if c["id"] == "corps-de-garde" else
                 "caserne" if c["id"] in ("garnison", "ecuries") else "office")
        noeuds.append({"id": c["id"], "nom": c["nom"], "genre": genre,
                       "niveau": 0, "xyz": [round(x, 1), round(y, 1),
                                            round(P.ASSISE, 1)]})
    tx, ty = _local(*P._monde((-8, -4)))
    noeuds.append({"id": "tambour", "nom": "Le Tambour de Pierre",
                   "genre": "forteresse", "niveau": 0,
                   "xyz": [round(tx, 1), round(ty, 1), round(P.ASSISE + 44, 1)]})
    qx, qy = _local(*P.QUAI)
    noeuds.append({"id": "quai", "nom": "Le quai", "genre": "quai", "niveau": 0,
                   "xyz": [round(qx, 1), round(qy, 1), 3.4]})
    sx, sy = _local(*P.SOMMET)
    noeuds.append({"id": "dragonmont", "nom": "Le Dragonmont", "genre": "sommet",
                   "niveau": 0, "xyz": [round(sx, 1), round(sy, 1), P.CIME]})
    return {"aretes": aretes, "noeuds": noeuds}


# ---------------------------------------------------------------------------
def ecrire(nom, obj):
    os.makedirs(SORTIE, exist_ok=True)
    chemin = os.path.join(SORTIE, "peyredragon." + nom + ".json")
    with io.open(chemin, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    print("  %-34s %8.1f Mo" % (chemin, os.path.getsize(chemin) / 1e6))


if __name__ == "__main__":
    print("Peyredragon pour le monde 3D — repère décalé de (%.0f, %.0f)" % (X0, Y0))
    t = terrain()
    print("  relief %d × %d à %.0f m, de %.0f à %.0f m"
          % (t["nx"], t["ny"], t["res_m"],
             min(map(min, t["z"])), max(map(max, t["z"]))))
    ecrire("terrain", t)
    b = bati()
    print("  %d volumes" % len(b["bati"]))
    ecrire("bati", b)
    m = maillage()
    print("  maillage : %d sommets, %d faces, %d matières"
          % (len(m["sommets"]) // 3, len(m["index"]) // 3, len(m["groupes"])))
    ecrire("maillage", m)
    c = carte()
    print("  %d pièces de muraille" % len(c["sol"]))
    ecrire("carte", c)
    g = graphe()
    print("  %d tronçons, %d repères" % (len(g["aretes"]), len(g["noeuds"])))
    ecrire("graph", g)
