# -*- coding: utf-8 -*-
"""RUES — projeter la surface d'un graphe en réseau piéton.

    python scripts/monde/rues.py                        (port-real, par défaut)
    python scripts/monde/rues.py --lieu peyredragon
    python scripts/monde/rues.py --lieu port-real --sortie monde/portreal.rues.json

LE TROU QU'IL BOUCHE. `monde/<x>.rues.json` était lu partout — par
`serveur/serveur.js` pour le Dijkstra de la balade, par `plan_ville.py` pour
dessiner les voies, par `scripts/marche.py` — et ÉCRIT PAR RIEN. Le pipeline
le déclare en `veut` de l'étape « plan » sans qu'aucune étape ne le `donne` :
celui de Port-Réal datait du 7 août avec 18 314 arêtes quand son graphe en
portait 45 155. On routait donc les piétons sur une ville qui n'existait plus.

CE QUE C'EST, ET POURQUOI CE N'EST PAS LE GRAPHE. `<x>.graph.json` fait 37 Mo :
il porte les intérieurs, les caves, le réseau caché, les portails qui cousent
les couches, et la `raison` écrite de chaque arête. Marcher dans la rue n'a
besoin de rien de tout ça — d'où cette projection, qui ne garde que la couche
`L1-surface` et, de chaque arête, les quatre choses dont un pas a besoin : d'où,
vers où, combien de mètres, et de quel genre (c'est le genre qui donne la
vitesse, côté serveur : on ne monte pas un escalier à l'allure d'une artère).

LES COORDONNÉES SONT DANS LE `trace`. Les nœuds de voirie (`pv0`, `pv1`, `c433.339_0`)
n'ont pas de fiche à eux : chaque arête porte sa polyligne en mètres, et ses
deux bouts SONT les positions de `de` et `vers`. On les recueille en passant.

LES REPÈRES SE TRIENT, et c'est le seul jugement du script. Port-Réal a 10 732
nœuds nommés dont 4 062 « seuil », 2 527 « cour » et 2 009 « hall » : c'est la
structure du semis, et « à 190 pas de Arcade de Le marché aux poissons » ne
situe personne. Un repère est ce qu'on nomme en LEVANT LA TÊTE. On écarte donc
les genres de structure et l'on garde le reste ; le serveur tient en plus sa
propre liste blanche (`REPERES_VRAIS`), et les deux filtres valent mieux qu'un.
"""
import argparse
import io
import json
import math
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MONDE = os.path.join(RACINE, "monde")

PREFIXES = {"port-real": "portreal", "peyredragon": "peyredragon"}

# La couche qu'on marche. Les autres — intérieurs, sous-sol, réseau caché — ne
# sont pas des rues, et les mêler ferait passer un piéton par une cave.
COUCHE = "L1-surface"

# Ce qui n'est PAS un repère : la structure que le semis a nommée pour son
# propre usage. Tout le reste passe.
STRUCTURE = {"seuil", "cour", "cave", "hall", "arcade", "acces", "regard",
             "bouche", "salle", "palier", "couloir"}


def lire(p):
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def projeter(graphe):
    """Le graphe complet → {noeuds, reperes, aretes}."""
    noeuds = {}
    aretes = []
    sans_trace = 0

    for a in graphe.get("aretes", []):
        if a.get("couche") != COUCHE:
            continue
        tr = a.get("trace")
        if not tr or len(tr) < 2:
            sans_trace += 1
            continue
        de, vers = a.get("de"), a.get("vers")
        if not de or not vers:
            sans_trace += 1
            continue
        # Les deux bouts de la polyligne SONT les deux nœuds. On arrondit au
        # décimètre : c'est la précision du monde, et ça divise le fichier par
        # deux sans qu'un pas s'en aperçoive.
        for cle, p in ((de, tr[0]), (vers, tr[-1])):
            if cle not in noeuds:
                noeuds[cle] = [round(float(p[0]), 1), round(float(p[1]), 1),
                               round(float(p[2]), 1) if len(p) > 2 else 0.0]
        # La longueur ÉCRITE fait foi quand elle est là : une arête peut être
        # courbe, et sa polyligne compte alors plus de mètres que ses deux bouts.
        m = a.get("longueur_m")
        if not m:
            m = sum(math.dist(tr[i][:2], tr[i + 1][:2]) for i in range(len(tr) - 1))
        ar = {"de": de, "vers": vers,
              "m": round(float(m), 1), "g": a.get("genre") or "rue"}
        # Le nom n'influe pas sur le chemin le plus court ; il est pourtant ce
        # qui permet à un passant de dire par où il est passé.
        if a.get("nom"):
            ar["n"] = a["nom"]
        aretes.append(ar)

    # Les repères : leur position entre dans `noeuds` sous leur propre id, et
    # `reperes` fait l'annuaire nom → id. Ils n'ont besoin d'AUCUNE arête —
    # personne ne route à travers eux, on ne mesure qu'une distance à vol d'œil.
    reperes = {}
    for n in graphe.get("noeuds", []):
        nom = n.get("nom")
        genre = str(n.get("genre") or "")
        if not nom or genre in STRUCTURE or genre.startswith("regard"):
            continue
        xyz = n.get("xyz")
        if not xyz:
            continue
        cle = n.get("id") or nom
        noeuds[cle] = [round(float(xyz[0]), 1), round(float(xyz[1]), 1),
                       round(float(xyz[2]), 1) if len(xyz) > 2 else 0.0]
        reperes[nom] = cle

    return {"noeuds": noeuds, "reperes": reperes, "aretes": aretes}, sans_trace


def composantes(rues):
    """La plus grande composante, et le nombre de miettes. C'est le seul chiffre
    qui dit si le réseau est marchable : le serveur raccroche toujours à la
    grande, et un but posé sur un îlot rend « pas de chemin »."""
    adj = {}
    for a in rues["aretes"]:
        adj.setdefault(a["de"], []).append(a["vers"])
        adj.setdefault(a["vers"], []).append(a["de"])
    vus, tailles = set(), []
    for d in adj:
        if d in vus:
            continue
        pile, t = [d], 0
        vus.add(d)
        while pile:
            x = pile.pop()
            t += 1
            for y in adj.get(x, ()):
                if y not in vus:
                    vus.add(y)
                    pile.append(y)
        tailles.append(t)
    tailles.sort(reverse=True)
    return (tailles[0] if tailles else 0), len(tailles)


def main():
    ap = argparse.ArgumentParser(description="Projeter la surface d'un graphe en rues")
    ap.add_argument("--lieu", default="port-real")
    ap.add_argument("--sortie", default=None)
    a = ap.parse_args()

    prefixe = PREFIXES.get(a.lieu, a.lieu)
    src = os.path.join(MONDE, prefixe + ".graph.json")
    if not os.path.exists(src):
        print("  pas de graphe pour « %s » : %s est introuvable." % (a.lieu, src))
        return 1
    dst = a.sortie or os.path.join(MONDE, prefixe + ".rues.json")

    print("  lecture de %s…" % os.path.basename(src))
    g = lire(src)
    rues, sans_trace = projeter(g)
    # La géométrie vient du graphe ; les noms d'usage viennent d'un catalogue
    # humain séparé. Les joindre ici donne au serveur de marche le même monde
    # nommé que celui que le plan montre.
    from toponymie import enrichir_rues
    rues = enrichir_rues(rues, prefixe, strict=True)
    if not rues["aretes"]:
        print("  aucune arête de surface : rien à écrire.")
        return 1

    grande, miettes = composantes(rues)
    with io.open(dst, "w", encoding="utf-8") as f:
        json.dump(rues, f, ensure_ascii=False, separators=(",", ":"))

    import collections
    genres = collections.Counter(x["g"] for x in rues["aretes"])
    metres = sum(x["m"] for x in rues["aretes"])
    print("  %s — %d nœuds, %d arêtes, %s km de voirie"
          % (os.path.basename(dst), len(rues["noeuds"]), len(rues["aretes"]),
             round(metres / 1000.0, 1)))
    print("     genres : " + ", ".join("%s %d" % (k, v) for k, v in genres.most_common()))
    print("     %d repères : %s" % (len(rues["reperes"]),
                                    ", ".join(sorted(rues["reperes"])[:6]) +
                                    ("…" if len(rues["reperes"]) > 6 else "")))
    # LA CONNEXITÉ EST LE CHIFFRE QUI COMPTE. Un réseau en miettes se route mal,
    # et l'on ne s'en aperçoit qu'en essayant d'aller quelque part.
    print("     composantes : la grande en tient %d sur %d nœuds d'arête (%d en tout)"
          % (grande, len({x for a in rues["aretes"] for x in (a["de"], a["vers"])}), miettes))
    if sans_trace:
        print("     %d arêtes de surface écartées, faute de tracé" % sans_trace)
    return 0


if __name__ == "__main__":
    sys.exit(main())
