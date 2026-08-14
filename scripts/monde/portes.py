# -*- coding: utf-8 -*-
"""Les portes entrent dans le réseau — une maison n'est plus un point en l'air.

    python scripts/monde/portes.py     (après usages.py, avant marche.py --cache)

POURQUOI. Un trajet se calculait de carrefour à carrefour, et les deux bouts
étaient RACCROCHÉS EN LIGNE DROITE : du point cliqué au carrefour le plus
proche, à travers tout ce qui se trouvait entre les deux. Sur une artère dont
les carrefours sont à quarante-huit mètres l'un de l'autre, ce fil traversait
le pâté de maisons de part en part. C'est le seul endroit où un chemin de
Port-Réal franchissait une façade, et il le franchissait à chaque trajet.

CE QU'ON A DÉJÀ, ET QU'ON N'UTILISAIT PAS. `usages.py` écrit trois colonnes sur
chaque bâtiment : `porte_x`, `porte_y`, `voie`. La porte est posée SUR l'axe de
sa chaussée — un centimètre de médiane, mesuré sur les quarante-neuf mille —, et
`voie` nomme l'arête du graphe. Il n'y a donc rien à projeter ni à deviner : la
porte EST un point de la voirie, il ne lui manque que d'être un nœud.

CE QUE FAIT CE SCRIPT. Il coupe chaque arête de surface aux abscisses de ses
portes, exactement comme `coudre.py` coupe aux entrées et aux porches — « une
porte donne sur la rue devant elle, pas trente mètres plus loin ». Chaque
bâtiment gagne un nœud `porte:bat:<rang>`, et le rang est la monnaie du jeu
(`scripts/affecter.py`), donc un lieu de la fiction sait où il débouche sans
qu'on ait à chercher.

CE QU'IL NE FAIT PAS. Il ne déplace aucune maison et ne touche pas à
`bati.json` : les rangs sont l'ancrage des affectations, et les casser coûterait
plus cher que tout ce qu'on gagne ici.
"""
import json, io, math, os, sys
from collections import defaultdict

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
MONDE = os.path.join(RACINE, "monde")
PREFIXE = sys.argv[1] if len(sys.argv) > 1 else "portreal"

CHEMIN = os.path.join(MONDE, PREFIXE + ".graph.json")
G = json.load(io.open(CHEMIN, encoding="utf-8"))
B = json.load(io.open(os.path.join(MONDE, PREFIXE + ".bati.json"), encoding="utf-8"))

# Ce script coupe des arêtes et en réécrit le graphe : le relancer sur sa propre
# sortie recouperait des morceaux déjà coupés, aux mêmes abscisses, donc à
# longueur nulle. On le dit ici plutôt que de le laisser produire un réseau
# plein d'arêtes de zéro mètre.
if G.get("_portes"):
    sys.exit("Ce graphe porte déjà ses portes. Repars de « graphe.py » "
             "puis « densifier.py », « coudre.py », « usages.py ».")

C = {n: i for i, n in enumerate(B["_colonnes"])}
for besoin in ("porte_x", "porte_y", "voie"):
    if besoin not in C:
        sys.exit("  %s manque à bati.json : lance d'abord usages.py." % besoin)

ARETES = {a["id"]: a for a in G["aretes"] if "id" in a}
NOEUDS = {n["id"]: n for n in G["noeuds"]}


def abscisse(trace, px, py):
    """(distance curviligne du point projeté, écart au tracé, point projeté)"""
    s = 0.0
    best = None
    for u, v in zip(trace, trace[1:]):
        dx, dy = v[0] - u[0], v[1] - u[1]
        L = math.hypot(dx, dy)
        if L < 1e-9:
            continue
        t = max(0.0, min(1.0, ((px - u[0]) * dx + (py - u[1]) * dy) / (L * L)))
        qx, qy = u[0] + dx * t, u[1] + dy * t
        e = math.hypot(px - qx, py - qy)
        if best is None or e < best[1]:
            z = u[2] + (v[2] - u[2]) * t if len(u) > 2 and len(v) > 2 else 0.0
            best = (s + t * L, e, (qx, qy, z))
        s += L
    return best


def coupe(trace, s0, s1):
    """le morceau de polyligne entre deux abscisses, bouts compris"""
    out = []
    s = 0.0
    for u, v in zip(trace, trace[1:]):
        dx, dy = v[0] - u[0], v[1] - u[1]
        L = math.hypot(dx, dy)
        if L < 1e-9:
            continue
        a, b = s, s + L
        if b >= s0 and a <= s1:
            for cible in (max(a, s0), min(b, s1)):
                t = (cible - a) / L
                z = u[2] + (v[2] - u[2]) * t if len(u) > 2 and len(v) > 2 else 0.0
                p = [round(u[0] + dx * t, 2), round(u[1] + dy * t, 2), round(z, 2)]
                if not out or math.dist(p[:2], out[-1][:2]) > 1e-6:
                    out.append(p)
        s = b
    return out


# --- 1. chaque porte trouve son abscisse sur sa voie ------------------------
print("… les portes sur leur voie")
par_voie = defaultdict(list)
sans_voie = hors = 0
for k, r in enumerate(B["bati"]):
    v = r[C["voie"]]
    a = ARETES.get(v) if v else None
    if a is None or a.get("couche") != "L1-surface":
        sans_voie += 1
        continue
    t = a.get("trace") or []
    if len(t) < 2:
        sans_voie += 1
        continue
    got = abscisse(t, r[C["porte_x"]], r[C["porte_y"]])
    if got is None or got[1] > 4.0:      # la porte n'est pas sur cette voie
        hors += 1
        continue
    par_voie[v].append((got[0], k, got[2]))
print("   %d portes placées, %d sans voie, %d écartées (> 4 m de leur axe)"
      % (sum(len(x) for x in par_voie.values()), sans_voie, hors))

# --- 2. on coupe les arêtes à ces abscisses ---------------------------------
# DEUX PORTES TROP PROCHES PARTAGENT LEUR NŒUD. Des mitoyennes donnent sur la
# rue à quelques centimètres l'une de l'autre ; les couper séparément
# fabriquerait des arêtes de dix centimètres par milliers, qui ne servent qu'à
# ralentir le Dijkstra. Au-delà d'un demi-mètre elles ont chacune la leur.
GRAIN = 0.5
print("… on coupe les voies aux portes")
neuves, retirees, noeuds_neufs = [], set(), []
attache = {}
for v, portes in par_voie.items():
    a = ARETES[v]
    t = a["trace"]
    total = sum(math.dist(p[:2], q[:2]) for p, q in zip(t, t[1:]))
    portes.sort()
    groupes = []
    for s, k, p in portes:
        s = max(GRAIN * 0.5, min(total - GRAIN * 0.5, s))
        if groupes and s - groupes[-1][0] < GRAIN:
            groupes[-1][2].append(k)
        else:
            groupes.append([s, p, [k]])
    if not groupes:
        continue
    coupures = []
    for s, p, ks in groupes:
        nid = "porte:bat:%d" % min(ks)
        noeuds_neufs.append({
            "id": nid, "genre": "porte-maison", "niveau": 0,
            "xyz": [round(p[0], 1), round(p[1], 1), round(p[2], 1)],
            "bat": sorted(ks),
            "raison": "La porte de %d maison(s) : elle donne sur la rue devant "
                      "elle, et le chemin y commence." % len(ks),
        })
        for k in ks:
            attache[k] = nid
        coupures.append((s, nid))
    # les morceaux : du départ à la première porte, entre les portes, puis la fin
    bornes = [(0.0, a["de"])] + coupures + [(total, a["vers"])]
    for i, ((s0, n0), (s1, n1)) in enumerate(zip(bornes, bornes[1:])):
        seg = coupe(t, s0, s1)
        if len(seg) < 2:
            continue
        lg = sum(math.dist(p[:2], q[:2]) for p, q in zip(seg, seg[1:]))
        if lg < 1e-3:
            continue
        b = dict(a)
        b["id"] = "%s.p%d" % (a["id"], i)
        b["de"], b["vers"] = n0, n1
        b["trace"] = seg
        b["longueur_m"] = round(lg, 2)
        dz = abs(seg[-1][2] - seg[0][2]) if len(seg[0]) > 2 else 0.0
        b["pente"] = round(dz / lg, 3) if lg else 0.0
        neuves.append(b)
    retirees.add(a["id"])

G["noeuds"].extend(noeuds_neufs)
G["aretes"] = [e for e in G["aretes"] if e.get("id") not in retirees] + neuves
G["_portes"] = True
G["portes_bat"] = attache          # rang du bâtiment → nœud de sa porte

io.open(CHEMIN, "w", encoding="utf-8").write(json.dumps(G, ensure_ascii=False))

# ON REPORTE LA COLONNE `voie` SUR LE MORCEAU. Couper une arête tue son
# identifiant : `v3.0` devient `v3.0.p0`, `v3.0.p1`… et la colonne écrite par
# `usages.py` ne résolvait plus RIEN une fois ce script passé. Le défaut est
# silencieux — personne ne plante, on lit simplement zéro bâtiment rattaché à
# sa rue — et c'est le pire genre. Chaque bâtiment reçoit donc le morceau qui
# aboutit à sa porte.
par_noeud = {}
for b in neuves:
    par_noeud.setdefault(b["vers"], b["id"])
    par_noeud.setdefault(b["de"], b["id"])
iv = C["voie"]
recolles = 0
for k, nid in attache.items():
    e = par_noeud.get(nid)
    if e:
        B["bati"][k][iv] = e
        recolles += 1
io.open(os.path.join(MONDE, PREFIXE + ".bati.json"), "w", encoding="utf-8").write(
    json.dumps(B, ensure_ascii=False, separators=(",", ":")))

L1 = [e for e in G["aretes"] if e.get("couche") == "L1-surface"]
print()
print("  %s" % os.path.relpath(CHEMIN, RACINE))
print("  %d noeuds de porte, %d batiments rattaches, %d colonnes voie recollees"
      % (len(noeuds_neufs), len(attache), recolles))
print("  aretes de surface : %d decoupees en %d morceaux (%d au total)"
      % (len(retirees), len(neuves), len(L1)))
print("  voirie de surface : %.1f km" % (sum(e["longueur_m"] for e in L1) / 1000))
print()
print("  puis : python scripts/marche.py --cache")
