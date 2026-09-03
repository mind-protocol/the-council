# -*- coding: utf-8 -*-
"""Les chemins d'une ville composée — la topologie qui fait marcher les gens.

    python bataille/outils/osm/06_chemins.py --id gallipoli [--pas-m-s 1.3]

Lit etat/villes/<id>.json et en tire DEUX choses, du même graphe :

- `etat/chemins.json` — ce que la présence lit (scripts/temps/presence.py) :
  les PLACES NOMMÉES (villages, lieux-dits, îlots) en nœuds, et en arêtes le
  chemin le plus court par les routes entre deux places sans autre place
  entre elles, en MINUTES au pas d'un homme. C'est le remplaçant du château
  salle par salle : « il est à bolayir » et « Güneyli est à 71 minutes »
  deviennent des faits calculés.
- `bataille/donnees/ville/<id>.routes.json` — le même graphe en MÈTRES avec
  sa géométrie (les sommets des routes, les arêtes et leur longueur, la place
  → son sommet), pour qui doit poser des corps le long d'une route
  (serveur/domaine/ost.js). Repère du plan cuit : mètres, y vers le sud.

Une place à plus de `--rattache` mètres de toute route est quand même
rattachée au sommet le plus proche, et on le dit : un lieu-dit n'est pas
toujours au bord du chemin.
"""
import argparse, heapq, io, json, math, os
from collections import defaultdict

MOTEUR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # bataille/
RACINE = os.path.dirname(MOTEUR)


def graphe_routes(sol, u):
    """Sommets = tous les points des pièces `route` (fondus à 0,5 m), arêtes = segments."""
    index, noeuds, aretes = {}, [], defaultdict(dict)

    def sommet(p):
        k = (round(p[0] * u * 2) / 2, round(p[1] * u * 2) / 2)
        if k not in index:
            index[k] = len(noeuds)
            noeuds.append([k[0], k[1]])
        return index[k]

    for s in sol:
        if s.get("genre") != "route" or len(s.get("points") or []) < 2:
            continue
        ids = [sommet(p) for p in s["points"]]
        for a, b in zip(ids, ids[1:]):
            if a == b:
                continue
            (ax, ay), (bx, by) = noeuds[a], noeuds[b]
            d = math.hypot(bx - ax, by - ay)
            aretes[a][b] = min(d, aretes[a].get(b, d))
            aretes[b][a] = aretes[a][b]
    return noeuds, aretes


def recoller(noeuds, aretes, portee):
    """Un bout de route qui finit à quelques mètres d'une autre route sans la
    toucher (une rue tissée coupée à l'enceinte, un tronçon OSM mal noué) : on
    le raccorde au sommet le plus proche d'un AUTRE îlot, s'il est à moins de
    `portee` mètres. Rend les raccords faits, pour le dire."""
    comp, c = {}, 0
    for s in range(len(noeuds)):
        if s in comp:
            continue
        pile = [s]; comp[s] = c
        while pile:
            x = pile.pop()
            for y in aretes[x]:
                if y not in comp:
                    comp[y] = c; pile.append(y)
        c += 1
    faits = []
    for s in range(len(noeuds)):
        if len(aretes[s]) != 1:
            continue  # seuls les bouts (degré 1) se raccordent
        sx, sy = noeuds[s]
        meilleur, dm = None, portee
        for t in range(len(noeuds)):
            if comp[t] == comp[s]:
                continue
            d = math.hypot(noeuds[t][0] - sx, noeuds[t][1] - sy)
            if d < dm:
                meilleur, dm = t, d
        if meilleur is not None:
            aretes[s][meilleur] = dm; aretes[meilleur][s] = dm
            faits.append((s, meilleur, round(dm)))
            comp = {k: (comp[s] if v == comp[meilleur] else v) for k, v in comp.items()}
    return faits


def plus_proche(noeuds, p):
    px, py = p
    return min(range(len(noeuds)), key=lambda i: (noeuds[i][0] - px) ** 2 + (noeuds[i][1] - py) ** 2)


def dijkstra(aretes, depart, arrets=()):
    """Distances depuis `depart` ; l'expansion s'arrête aux sommets d'`arrets` (les autres places)."""
    dist, prec = {depart: 0.0}, {}
    file = [(0.0, depart)]
    while file:
        d, n = heapq.heappop(file)
        if d > dist.get(n, math.inf):
            continue
        if n != depart and n in arrets:
            continue
        for m, l in aretes[n].items():
            nd = d + l
            if nd < dist.get(m, math.inf):
                dist[m] = nd
                prec[m] = n
                heapq.heappush(file, (nd, m))
    return dist, prec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--pas-m-s", type=float, default=1.3, help="vitesse d'un homme au pas, m/s")
    ap.add_argument("--rattache", type=float, default=400.0, help="au-delà, on signale la place loin des routes (m)")
    ap.add_argument("--recoller", type=float, default=30.0, help="un bout de route à moins de tant d'un autre îlot s'y raccorde (m)")
    a = ap.parse_args()
    ville = json.load(io.open(os.path.join(RACINE, "etat", "villes", f"{a.id}.json"), encoding="utf-8"))
    u = ville.get("metres_par_unite") or 5.0
    if not ville.get("metres_par_unite"):
        u = 5.0  # la convention des villes de l'état (cuire_ville.py --metres-par-unite)
    sol = ville.get("sol", [])
    noeuds, aretes = graphe_routes(sol, u)
    if not noeuds:
        raise SystemExit("aucune route dans le sol : pas de chemins")
    recolles = recoller(noeuds, aretes, a.recoller)

    # les places : villages (leur `etiq`, le centre), lieux-dits et îlots (leur point)
    places, loin = {}, []
    for s in sol:
        if not s.get("id"):
            continue
        if s["genre"] == "village":
            p = s.get("etiq") or s["points"][0]
        elif s["genre"] in ("lieu-dit", "ilot"):
            p = s["points"][0]
        else:
            continue
        pm = (p[0] * u, p[1] * u)
        n = plus_proche(noeuds, pm)
        d = math.hypot(noeuds[n][0] - pm[0], noeuds[n][1] - pm[1])
        places[s["id"]] = {"noeud": n, "nom": s.get("nom", ""), "genre": s["genre"], "ou_m": [round(pm[0]), round(pm[1])],
                           "ecart_m": round(d)}
        if d > a.rattache:
            loin.append((s["id"], round(d)))

    # les arêtes entre places : le plus court chemin sans autre place entre
    noeud_place = {v["noeud"]: k for k, v in places.items()}
    arcs, vus = [], set()
    for pid, pl in places.items():
        dist, _ = dijkstra(aretes, pl["noeud"], arrets=set(noeud_place) - {pl["noeud"]})
        for n, d in dist.items():
            q = noeud_place.get(n)
            if q and q != pid and (q, pid) not in vus and (pid, q) not in vus:
                vus.add((pid, q))
                minutes = max(1, int(math.ceil(d / a.pas_m_s / 60)))
                arcs.append([pid, q, minutes, round(d)])

    chemins = {"_lisez_moi": f"Dérivé de etat/villes/{a.id}.json par bataille/outils/osm/06_chemins.py : les places nommées en nœuds, les routes en arêtes, minutes au pas de {a.pas_m_s} m/s. Relancer, ne pas éditer.",
               "alias": {}, "aretes": [[p, q, m] for p, q, m, _ in arcs]}
    dst = os.path.join(RACINE, "etat", "chemins.json")
    io.open(dst, "w", encoding="utf-8").write(json.dumps(chemins, ensure_ascii=False, indent=1))

    routes = {"_lisez_moi": "Le graphe des routes en mètres du plan cuit (y vers le sud), pour poser des corps le long d'un chemin. Même source que etat/chemins.json.",
              "id": a.id, "metres_par_unite": u, "noeuds": [[round(x, 1), round(y, 1)] for x, y in noeuds],
              "aretes": [[i, j, round(l, 1)] for i in range(len(noeuds)) for j, l in aretes[i].items() if i < j],
              "places": places,
              "places_aretes": [{"de": p, "a": q, "minutes": m, "metres": d} for p, q, m, d in arcs]}
    dst2 = os.path.join(MOTEUR, "donnees", "ville", f"{a.id}.routes.json")
    io.open(dst2, "w", encoding="utf-8").write(json.dumps(routes, ensure_ascii=False))

    print(f"{len(noeuds)} sommets, {sum(len(v) for v in aretes.values()) // 2} segments de route ; {len(places)} places, {len(arcs)} arêtes entre places ; {len(recolles)} bouts recollés à moins de {a.recoller:.0f} m")
    print(f"  -> {os.path.relpath(dst, RACINE)} et {os.path.relpath(dst2, RACINE)}")
    villages = [p for p, v in places.items() if v["genre"] == "village"]
    for p, q, m, d in arcs:
        if p in villages and q in villages:
            print(f"  {p} — {q} : {d} m, {m} min")
    for pid, d in loin:
        print(f"  ⚠ {pid} est à {d} m de la route la plus proche — rattaché quand même")


if __name__ == "__main__":
    main()
