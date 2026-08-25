# -*- coding: utf-8 -*-
"""Appliquer la géographie régionale sans régénérer le bâti de Port-Réal.

Cette migration est volontairement étroite : elle remplace l'autorité 2D de la
côte, des routes d'approche et du port, puis corrige dans le graphe actif les
deux seules extrémités de route qui finissaient sous l'eau. Les rangs de
``bati.json`` — donc les adresses de la partie — ne sont jamais ouverts.
"""
import io
import json
import math
import os

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
REGION_CHEM = os.path.join(RACINE, "scripts", "ville", "port-real-region.json")
CARTE_CHEM = os.path.join(RACINE, "etat", "villes", "port-real.json")
GRAPHE_CHEM = os.path.join(RACINE, "monde", "portreal.graph.json")
TERRAIN_CHEM = os.path.join(RACINE, "monde", "portreal.terrain.json")
MU = 12.0


def lire(p):
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def ecrire(p, d):
    # Le serveur de jeu peut lire la carte au même instant. Une écriture directe
    # sous Windows a alors parfois rendu EINVAL ; un voisin complet puis un
    # remplacement atomique ne laisse jamais un JSON tronqué au lecteur.
    tmp = p + ".region.tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, p)


def monde(p):
    return [round(p[0] * MU, 1), round((300 - p[1]) * MU, 1)]


def altitude(terrain, x, y):
    res, nx, ny = terrain["res_m"], terrain["nx"], terrain["ny"]
    fx, fy = x / res, y / res
    i = min(nx - 2, max(0, int(fx)))
    j = min(ny - 2, max(0, int(fy)))
    tx, ty = fx - i, fy - j
    z = terrain["z"]
    a = z[j][i] * (1 - tx) + z[j][i + 1] * tx
    b = z[j + 1][i] * (1 - tx) + z[j + 1][i + 1] * tx
    return round(a * (1 - ty) + b * ty, 1)


def longueur(trace):
    return round(sum(math.dist(a[:2], b[:2]) for a, b in zip(trace, trace[1:])), 1)


def remplacer_carte(carte, region):
    noms_routes = {r["nom"] for r in region["routes"]}
    sol = [s for s in carte["sol"] if s.get("genre") != "eau" and
           not (s.get("genre") == "route" and s.get("nom") in noms_routes) and
           s.get("genre") != "quai"]
    for e in region["eau"]:
        sol.append({"genre":"eau", "nom":e["nom"], "points":e["points"]})
    for r in region["routes"]:
        sol.append({"genre":"route", "largeur":6, "nom":r["nom"],
                    "points":r["points"], "destination":r.get("destination"),
                    "detail":"Route régionale : une porte, une destination et aucun pas dans l'eau."})
    for q in region["port"]["quais"]:
        sol.append({"genre":"quai", "nom":q["nom"], "points":q["points"],
                    "detail":"Quai spécialisé, continu avec la chaussée du port."})
    for q in region["port"]["appontements"]:
        sol.append({"genre":"quai", "nom":q["nom"], "points":q["points"],
                    "ouvrage":"appontement",
                    "detail":"Ouvrage porté sur l'eau; ce n'est pas une route."})
    carte["sol"] = sol
    carte["region"] = {"source":"scripts/ville/port-real-region.json",
                        "version":region.get("version", 1),
                        "repere":region["repere"], "lieux":region.get("lieux", [])}


def corriger_extremite(graphe, terrain, nom, point_source):
    lot = [e for e in graphe["aretes"] if e.get("couche") == "L1-surface" and
           e.get("nom") == nom]
    if not lot:
        raise RuntimeError("route absente du graphe : " + nom)
    # L'extrémité extérieure est l'arête dont le dernier point est le plus près
    # d'un bord du cœur. On garde toutes ses coutures avec les façades et l'on
    # ne déplace que le nœud terminal, qui n'a pas d'autre raison d'exister.
    cible_xy = monde(point_source)
    depart = lot[0]["trace"][0]
    vx, vy = cible_xy[0] - depart[0], cible_xy[1] - depart[1]
    fin = max(lot, key=lambda e: (e["trace"][-1][0] - depart[0]) * vx +
                                   (e["trace"][-1][1] - depart[1]) * vy)
    z = altitude(terrain, cible_xy[0], cible_xy[1])
    fin["trace"] = [fin["trace"][0], [cible_xy[0], cible_xy[1], z]]
    fin["longueur_m"] = longueur(fin["trace"])
    fin["pente"] = round(abs(fin["trace"][-1][2] - fin["trace"][0][2]) /
                         max(1.0, fin["longueur_m"]), 3)
    for n in graphe.get("noeuds", []):
        if n.get("id") == fin.get("vers"):
            n["xyz"] = fin["trace"][-1]
            break
    return fin["id"], fin["trace"][-1]


def ajouter_port(graphe, terrain, region):
    # Les deux quais centraux existent déjà et portent les portes de dizaines
    # d'entrepôts. On ne les double pas : on ajoute les prolongements spécialisés
    # et les jetées, raccordés au nœud de surface le plus proche.
    a_ajouter = region["port"]["quais"][2:] + region["port"]["appontements"]
    graphe["aretes"] = [e for e in graphe["aretes"]
                         if not str(e.get("id", "")).startswith("region:port:")]
    existants = []
    for e in graphe["aretes"]:
        if e.get("couche") == "L1-surface" and e.get("trace"):
            existants.extend([(e["de"], e["trace"][0]), (e["vers"], e["trace"][-1])])
    faits = []
    for q in a_ajouter:
        pts = [monde(p) for p in q["points"]]
        nid, proche = min(existants, key=lambda x: math.dist(x[1][:2], pts[0]))
        trace = [[proche[0], proche[1], proche[2]]] + [
            [x, y, max(2.8, altitude(terrain, x, y))] for x, y in pts[1:]]
        vers = "region:port:noeud:" + q["id"]
        graphe["noeuds"] = [n for n in graphe.get("noeuds", []) if n.get("id") != vers]
        graphe["noeuds"].append({"id":vers, "nom":q["nom"], "genre":"quai",
                                  "niveau":0, "xyz":trace[-1]})
        graphe["aretes"].append({
            "id":"region:port:" + q["id"], "de":nid, "vers":vers,
            "genre":"quai", "couche":"L1-surface", "largeur_m":8.0,
            "longueur_m":longueur(trace), "pente":0.0,
            "raison":"Ouvrage portuaire régional; son type autorise seul l'avancée sur l'eau.",
            "trace":trace, "nom":q["nom"], "visibilite":"publique",
            "acces":"public", "etat":"ouvert", "ouvrage":q.get("ouvrage", "quai")})
        faits.append(q["id"])
    return faits


def main():
    region, carte, graphe, terrain = map(lire,
        (REGION_CHEM, CARTE_CHEM, GRAPHE_CHEM, TERRAIN_CHEM))
    remplacer_carte(carte, region)
    # Les deux points sont les derniers points assurément terrestres avant que
    # la route régionale ne poursuive hors du cœur détaillé.
    corrections = [
        corriger_extremite(graphe, terrain, "La route de Rosby", [390, 58]),
        corriger_extremite(graphe, terrain, "La route du gué", [74, 258]),
    ]
    port = ajouter_port(graphe, terrain, region)
    graphe["_region"] = {"source":"scripts/ville/port-real-region.json",
                          "version":region.get("version", 1),
                          "routes_corrigees":[x[0] for x in corrections],
                          "ouvrages_portuaires":port}
    ecrire(CARTE_CHEM, carte)
    ecrire(GRAPHE_CHEM, graphe)
    print("carte : côte, %d routes, %d quais/appontements" %
          (len(region["routes"]), len(region["port"]["quais"]) +
           len(region["port"]["appontements"])))
    for aid, p in corrections:
        print("route : %s finit sur la terre en %s" % (aid, p))
    print("port :", ", ".join(port))


if __name__ == "__main__":
    main()
