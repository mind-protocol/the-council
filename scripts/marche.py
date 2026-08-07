# -*- coding: utf-8 -*-
"""MARCHE — combien de temps il faut pour aller là-bas, à pied, par les rues.

    python scripts/marche.py salle:cabane-du-peigne lieu:la-gaffe
    python scripts/marche.py "La porte de la Gadoue" "Le Donjon Rouge" --qui marlo-vasse
    python scripts/marche.py --cache          (re)construit le graphe des rues

POURQUOI. Le MJ posait `duree` à la main sur ses items de récit, en estimant.
Or le monde sait déjà marcher : `ecrans/modules/monde/journee.js` fait circuler
quarante mille personnes tous les jours, et il le fait mieux que moi —

  - l'allure est de 66 à 90 mètres la minute, TIRÉE DE L'IDENTITÉ de chacun :
    un vieux, un enfant et un portefaix chargé ne vont pas du même pas ;
  - le chemin coûte selon la rue : une artère vaut 1, une rue 1,15, une ruelle
    1,4, et un ESCALIER 2,2 — c'est ce qui fait que les flux prennent les
    grandes rues au lieu de couper ;
  - et l'on chemine sur la voirie, pas à vol d'oiseau.

Ce module applique exactement les mêmes règles au personnage du joueur. Sans
lui, le joueur traversait la ville à une vitesse que personne d'autre n'avait,
et le monde disait deux choses différentes sur la même distance.

LE CACHE. `monde/portreal.graph.json` fait trente-six mégaoctets : on ne le
relit pas pour dire trois minutes. Au premier appel on en extrait les rues de
surface dans `monde/portreal.rues.json` — quelques centaines de kilo-octets —
et l'on ne touche plus au gros fichier. Le cache se refait avec `--cache`.
"""
import io, json, math, os, sys, heapq, collections

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPHE = os.path.join(RACINE, "monde", "portreal.graph.json")
RUES = os.path.join(RACINE, "monde", "portreal.rues.json")
CORPS = os.path.join(RACINE, "etat", "corps.json")

# Les mêmes qu'à l'écran (journee.js). Une ruelle se marche moins vite qu'une
# artère, et un escalier deux fois moins : ce n'est pas de la couleur.
COUT = {"artere": 1.0, "rue": 1.15, "escalier": 2.2}
COUT_DEFAUT = 1.4

# L'allure, en mètres par minute. Bornes de journee.js : 66 + hasard * 24.
ALLURE_BASSE, ALLURE_ETENDUE = 66.0, 24.0


def sortir(msg):
    print(msg)
    sys.exit(1)


def melange(chaine):
    """Un hachage, pas un tirage : la même personne garde son allure d'un jour
    à l'autre, et deux hommes n'ont pas la même. Même esprit que `journee.js`."""
    h = 0
    for c in chaine or "x":
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFFFF) / 4294967296.0


def allure(qui):
    return ALLURE_BASSE + melange(qui) * ALLURE_ETENDUE


def bati_cache():
    if os.path.exists(RUES):
        return json.load(io.open(RUES, encoding="utf-8"))
    return refaire_cache()


def refaire_cache():
    if not os.path.exists(GRAPHE):
        sortir("  monde/portreal.graph.json manque.")
    G = json.load(io.open(GRAPHE, encoding="utf-8"))
    noeuds = {n["id"]: n["xyz"] for n in G["noeuds"] if n.get("niveau") == 0}
    reperes = {n["nom"]: n["id"] for n in G["noeuds"]
               if n.get("nom") and n.get("niveau") == 0}
    aretes = [{"de": a["de"], "vers": a["vers"], "m": a.get("longueur_m") or 1.0,
               "g": a.get("genre") or ""}
              for a in G["aretes"]
              if a.get("couche") == "L1-surface" and a.get("etat") != "ferme"]
    C = {"noeuds": noeuds, "reperes": reperes, "aretes": aretes}
    io.open(RUES, "w", encoding="utf-8").write(json.dumps(C, ensure_ascii=False))
    return C


def voisins(C):
    v = collections.defaultdict(list)
    for a in C["aretes"]:
        c = a["m"] * COUT.get(a["g"], COUT_DEFAUT)
        v[a["de"]].append((a["vers"], c, a["m"]))
        v[a["vers"]].append((a["de"], c, a["m"]))
    return v


def grand_reseau(C):
    """Les rues qui communiquent VRAIMENT entre elles.

    La voirie de surface compte cent trente-quatre morceaux : un grand — treize
    mille sept cents carrefours, la ville — et cent trente-trois miettes, seuils
    et arcades qui ne mènent nulle part. Chercher « le carrefour le plus proche »
    sans regarder ça, c'est accrocher un trajet à une impasse et conclure qu'on
    ne peut pas aller de sa cabane à la taverne d'à côté. C'est arrivé, et c'est
    ce que ce filtre corrige.
    """
    if "_grand" in C:
        return C["_grand"]
    v = collections.defaultdict(list)
    for a in C["aretes"]:
        v[a["de"]].append(a["vers"])
        v[a["vers"]].append(a["de"])
    vus, meilleur = set(), set()
    for n in v:
        if n in vus:
            continue
        pile, bloc = [n], set()
        vus.add(n)
        while pile:
            x = pile.pop()
            bloc.add(x)
            for y in v[x]:
                if y not in vus:
                    vus.add(y)
                    pile.append(y)
        if len(bloc) > len(meilleur):
            meilleur = bloc
    C["_grand"] = meilleur
    return meilleur


def plus_proche(C, x, y):
    """Le carrefour le plus proche — parmi ceux d'où l'on peut aller ailleurs."""
    grand = grand_reseau(C)
    best, bd = None, 1e18
    for nid, p in C["noeuds"].items():
        if nid not in grand:
            continue
        d = (p[0] - x) ** 2 + (p[1] - y) ** 2
        if d < bd:
            bd, best = d, nid
    return best, math.sqrt(bd)


def ou_est(C, clef):
    """Un repère du monde, ou une chose affectée (`lieu:`, `salle:`…)."""
    if ":" in clef:
        try:
            A = json.load(io.open(CORPS, encoding="utf-8")).get("affectations") or {}
        except (OSError, ValueError):
            A = {}
        e = A.get(clef)
        if not e or not e.get("xyz"):
            sortir("  %s n'a pas d'adresse physique (scripts/affecter.py)." % clef)
        return e["xyz"][0], e["xyz"][1], (e.get("nom") or clef)
    nid = C["reperes"].get(clef)
    if not nid:
        proches = [n for n in C["reperes"] if clef.lower() in n.lower()]
        if not proches:
            sortir("  repère inconnu : %s" % clef)
        nid = C["reperes"][min(proches, key=len)]
        clef = min(proches, key=len)
    p = C["noeuds"][nid]
    return p[0], p[1], clef


def chemin(C, a, b):
    """Le trajet le moins COÛTEUX — pas le plus court. Un homme prend la grande
    rue plutôt que la ruelle qui coupe, et il évite les escaliers."""
    v = voisins(C)
    dist = {a: 0.0}
    metres = {a: 0.0}
    tas = [(0.0, a)]
    vus = set()
    while tas:
        d, ici = heapq.heappop(tas)
        if ici in vus:
            continue
        vus.add(ici)
        if ici == b:
            break
        for suiv, c, m in v[ici]:
            nd = d + c
            if nd < dist.get(suiv, 1e18):
                dist[suiv] = nd
                metres[suiv] = metres[ici] + m
                heapq.heappush(tas, (nd, suiv))
    if b not in dist:
        return None, None
    return dist[b], metres[b]


def duree(clef_a, clef_b, qui="marlo-vasse"):
    """Minutes de marche, et ce qu'il a fallu pour le dire."""
    C = bati_cache()
    ax, ay, na = ou_est(C, clef_a)
    bx, by, nb = ou_est(C, clef_b)
    na_id, da = plus_proche(C, ax, ay)
    nb_id, db = plus_proche(C, bx, by)
    cout, m = chemin(C, na_id, nb_id)
    if cout is None:
        return None
    # Les deux bouts : de la porte de la maison au carrefour, on marche aussi.
    m += da + db
    cout += da + db
    al = allure(qui)
    return {"de": na, "a": nb, "metres": m, "cout": cout,
            "pas": round(m / 0.75), "allure": al,
            "minutes": max(1, int(round(cout / al)))}


def main():
    a = sys.argv[1:]
    if "--cache" in a:
        C = refaire_cache()
        print("  %d carrefours, %d rues de surface — cache écrit."
              % (len(C["noeuds"]), len(C["aretes"])))
        return
    qui = "marlo-vasse"
    if "--qui" in a:
        i = a.index("--qui")
        qui = a[i + 1]
        a = a[:i] + a[i + 2:]
    if len(a) < 2:
        print(__doc__)
        return
    r = duree(a[0], a[1], qui)
    if not r:
        sortir("  aucun chemin par les rues.")
    print()
    print("  DE %s À %s" % (r["de"].upper(), r["a"].upper()))
    print("  %d m par les rues — %d pas" % (round(r["metres"]), r["pas"]))
    print("  %d minutes à son pas (%.0f m/min)" % (r["minutes"], r["allure"]))
    if r["cout"] > r["metres"] * 1.05:
        print("  (le chemin coûte %.0f%% de plus que sa longueur : ruelles, "
              "escaliers)" % ((r["cout"] / r["metres"] - 1) * 100))
    print()


if __name__ == "__main__":
    main()
