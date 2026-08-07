# -*- coding: utf-8 -*-
"""ARPENTER — lever une carte comme un homme qui marche : au pas et à l'œil.

    python scripts/arpenter.py --de "La porte de Fer" --a "Le Donjon Rouge"
    python scripts/arpenter.py --de "La porte de la Gadoue" --a "Le Donjon Rouge" \
        --livre leve-de-la-gadoue --titre "Ce que j'ai compté de la Gadoue au Donjon"

POURQUOI. Marlo n'a pas de carte et ne peut pas en acheter : il n'en existe pas
à vendre. Ce qu'il a, c'est un métier — il compte les pas depuis toujours — et
deux yeux. Ce script ne DESSINE pas une ville vue d'en haut : il rend ce qu'un
homme rapporte d'une marche, et rien de plus.

CE QU'IL RELÈVE, par segment de rue :
  - la longueur, en PAS (0,75 m le pas d'un homme qui marche vite) ;
  - le nombre de MAISONS à vingt pas de part et d'autre — ce qu'on voit sans
    tourner la tête ;
  - la pente, en QUATRE DEGRÉS et pas en chiffres : un homme sent « plat »,
    « ça monte », « ça tire », « on souffle », et rien entre les deux ;
  - la largeur de la rue, parce qu'une charrette y passe ou n'y passe pas ;
  - ce qu'on longe de nommé.

CE QU'IL NE RELÈVE PAS, et c'est volontaire : rien qui ne se voie depuis la rue.
Pas de plan de bâtiment, pas de cour, pas de ce qu'il y a derrière un mur. Un
levé au pas est aveugle à tout ce qui n'est pas sur son chemin — c'est ce qui
en fait un document honnête, et une carte de la ville faite de dix levés serait
pleine de trous en forme de pâtés de maisons.

LE BROUILLARD s'applique : on ne lève que ce qu'on a marché. Le script refuse de
partir d'un point où le personnage n'est pas, sauf à le lui dire (`--sans-moi`).
"""
import io, json, math, os, sys, heapq, collections

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPHE = os.path.join(RACINE, "monde", "portreal.graph.json")
BATI = os.path.join(RACINE, "monde", "portreal.bati.json")
BOOKS = os.path.join(RACINE, "etat", "books.json")

PAS_M = 0.75              # le pas d'un homme qui marche vite
LARGEUR_VUE_M = 15.0      # vingt pas de part et d'autre : ce qu'on voit sans se tourner

# Les quatre degrés. Un homme ne lit pas une pente en centièmes : il la sent
# dans les jambes, et il n'a que quatre mots pour la dire.
DEGRES = [(0.02, "plat"), (0.05, "ça monte"), (0.09, "ça tire"), (9.9, "on souffle")]


def sortir(msg):
    print(msg)
    sys.exit(1)


def degre(pente):
    p = abs(pente or 0.0)
    for seuil, mot in DEGRES:
        if p < seuil:
            return mot
    return DEGRES[-1][1]


def sens(dz):
    if abs(dz) < 1.0:
        return ""
    return " en montant" if dz > 0 else " en descendant"


def charger():
    if not os.path.exists(GRAPHE):
        sortir("  monde/portreal.graph.json manque.")
    G = json.load(io.open(GRAPHE, encoding="utf-8"))
    return G


def par_nom(G, nom):
    """Un repère, par son nom exact ou par un morceau."""
    n = nom.lower()
    exact = [x for x in G["noeuds"] if (x.get("nom") or "").lower() == n]
    if exact:
        return exact[0]
    part = [x for x in G["noeuds"]
            if x.get("nom") and n in x["nom"].lower() and x.get("niveau") == 0]
    if not part:
        return None
    # Le plus court nom qui contient : « La porte de Fer » plutôt que
    # « Arcade de La porte de Fer ».
    return min(part, key=lambda x: len(x["nom"]))


def chemin(G, depart, arrivee, couche="L1-surface"):
    """Le plus court chemin par les RUES. On ne passe pas par les caves : un
    homme qui lève une carte marche dehors, à la vue de tous — c'est le prix."""
    voisins = collections.defaultdict(list)
    for a in G["aretes"]:
        if a.get("couche") != couche or a.get("etat") == "ferme":
            continue
        L = a.get("longueur_m") or 1.0
        voisins[a["de"]].append((a["vers"], L, a))
        voisins[a["vers"]].append((a["de"], L, a))
    if depart not in voisins:
        sortir("  « %s » n'est sur aucune rue de la surface." % depart)
    dist = {depart: 0.0}
    vient = {}
    tas = [(0.0, depart)]
    vus = set()
    while tas:
        d, ici = heapq.heappop(tas)
        if ici in vus:
            continue
        vus.add(ici)
        if ici == arrivee:
            break
        for suiv, L, a in voisins[ici]:
            nd = d + L
            if nd < dist.get(suiv, 1e18):
                dist[suiv] = nd
                vient[suiv] = (ici, a)
                heapq.heappush(tas, (nd, suiv))
    if arrivee not in vient and arrivee != depart:
        sortir("  aucun chemin par les rues entre ces deux points.")
    route = []
    ici = arrivee
    while ici != depart:
        avant, a = vient[ici]
        route.append((a, avant, ici))
        ici = avant
    route.reverse()
    return route, dist.get(arrivee, 0.0)


def grille_bati():
    """Les bâtiments rangés en cases de 100 m : on n'en parcourt jamais 48 000."""
    B = json.load(io.open(BATI, encoding="utf-8"))
    C = {k: i for i, k in enumerate(B["_colonnes"])}
    cases = collections.defaultdict(list)
    for b in B["bati"]:
        x, y = b[C["x"]], b[C["y"]]
        cases[(int(x // 100), int(y // 100))].append((x, y, b[C["usage"]]))
    return cases, C


def distance_segment(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


# CE QUI PORTE DES ARMES, ET CE QUI PREND DE L'ARGENT. Un homme qui lève une
# carte pour savoir par où passent des lances ne compte pas les maisons pour
# elles-mêmes : il note les corps de garde, les casernes, les geôles — et les
# endroits où l'on paie pour entrer, qui sont les mêmes endroits où l'on est
# regardé. Les portes de Port-Réal sont les deux à la fois : « tout ce qui entre
# y est vu, compté, ou payé ».
GARNISON = {"caserne": "caserne", "corps-de-garde": "corps de garde",
            "geole": "geôle", "donjon-rouge": "la forteresse"}
PEAGE = {"porte": "on y paie", "octroi": "octroi", "quai": "droit de quai",
         "bureau-port": "les rôles"}


def postes(cases, trace, largeur=45.0):
    """Ce qui porte des armes le long de la trace, sans compter deux fois."""
    vus = {}
    for i in range(len(trace) - 1):
        ax, ay = trace[i][0], trace[i][1]
        bx, by = trace[i + 1][0], trace[i + 1][1]
        for cx in range(int(min(ax, bx) // 100) - 1, int(max(ax, bx) // 100) + 2):
            for cy in range(int(min(ay, by) // 100) - 1, int(max(ay, by) // 100) + 2):
                for (x, y, u) in cases.get((cx, cy), ()):
                    if u not in GARNISON:
                        continue
                    if distance_segment(x, y, ax, ay, bx, by) <= largeur:
                        vus[(round(x, 1), round(y, 1))] = GARNISON[u]
    return sorted(set(vus.values()))


def peages(G, trace, rayon=70.0):
    """Où l'on paie, où l'on est compté : les portes, les quais, les bureaux."""
    out = []
    for n in G["noeuds"]:
        if n.get("niveau") != 0 or n.get("genre") not in PEAGE:
            continue
        for p in trace:
            if math.hypot(n["xyz"][0] - p[0], n["xyz"][1] - p[1]) <= rayon:
                out.append((n.get("nom") or PEAGE[n["genre"]], PEAGE[n["genre"]]))
                break
    return out


# Ce qu'un homme appelle « une maison » en comptant depuis la rue : un toit sous
# lequel on habite ou l'on tient boutique. Un entrepôt n'est pas une maison, un
# puits non plus.
MAISONS = {"maison", "taudis", "cabane", "echoppe", "maison-officier", "manse",
           "taverne", "auberge", "forge", "boulangerie", "bordel", "poterie",
           "etuve", "brasserie", "tannerie", "teinturerie", "abattoir"}


def compter(cases, trace, largeur=LARGEUR_VUE_M):
    """Les maisons à portée de vue le long d'une trace. Chacune une fois."""
    vues = set()
    for i in range(len(trace) - 1):
        ax, ay = trace[i][0], trace[i][1]
        bx, by = trace[i + 1][0], trace[i + 1][1]
        for cx in range(int(min(ax, bx) // 100) - 1, int(max(ax, bx) // 100) + 2):
            for cy in range(int(min(ay, by) // 100) - 1, int(max(ay, by) // 100) + 2):
                for (x, y, u) in cases.get((cx, cy), ()):
                    if u not in MAISONS:
                        continue
                    if distance_segment(x, y, ax, ay, bx, by) <= largeur:
                        vues.add((round(x, 1), round(y, 1)))
    return len(vues)


def segmenter(G, route):
    """On regroupe par NOM DE RUE : c'est ainsi qu'un homme découpe sa marche —
    « la rue du Fleuve jusqu'au coude, puis la montée »."""
    segs = []
    noeuds = {x["id"]: x for x in G["noeuds"]}
    for a, de, vers in route:
        nom = a.get("nom") or "sans nom"
        z0 = (noeuds.get(de) or {}).get("xyz", [0, 0, 0])[2]
        z1 = (noeuds.get(vers) or {}).get("xyz", [0, 0, 0])[2]
        trace = a.get("trace") or [noeuds[de]["xyz"], noeuds[vers]["xyz"]]
        # On coupe quand la RUE change, quand la PENTE change de degré, ou au
        # bout de deux cents pas. C'est ainsi qu'un homme note : il ne tient pas
        # une ligne par pavé, il marque ce qui change et il marque quand ça
        # dure. Sans la coupe de longueur, toute une rue rentre dans un seul
        # nombre et le levé ne dit plus rien de l'endroit où ça se redresse.
        meme = (segs and segs[-1]["nom"] == nom
                and degre(sum(segs[-1]["pentes"]) / len(segs[-1]["pentes"]))
                    == degre(abs(a.get("pente") or 0.0))
                and segs[-1]["m"] < 150.0)
        if meme:
            s = segs[-1]
            s["m"] += a.get("longueur_m") or 0.0
            s["pentes"].append(abs(a.get("pente") or 0.0))
            s["dz"] += z1 - z0
            s["trace"] += trace
            s["fin"] = vers
        else:
            segs.append({"nom": nom, "m": a.get("longueur_m") or 0.0,
                         "pentes": [abs(a.get("pente") or 0.0)],
                         "dz": z1 - z0, "trace": list(trace),
                         "largeur": a.get("largeur_m") or 0.0,
                         "genre": a.get("genre") or "", "debut": de, "fin": vers})
    return segs


def G_noeud(G, nid):
    for n in G["noeuds"]:
        if n["id"] == nid:
            return n
    return None


# Ce qui sert de BORNE à un homme qui n'a pas de plaques de rue : une chose
# qu'on ne peut pas confondre et qui ne bouge pas. Un puits, une forge, un four.
# On les nomme comme il les nommerait — « le puits », pas « bâtiment 22144 ».
BORNES_USAGE = [
    ("puits", "le puits"), ("forge", "la forge"), ("boulangerie", "le four"),
    ("septuaire-quartier", "le septuaire"), ("moulin", "le moulin"),
    ("abattoir", "l'abattoir"), ("tannerie", "les tanneries"),
    ("etuve", "l'étuve"), ("bordel", "la maison"), ("ecurie", "l'écurie"),
    ("brasserie", "la brasserie"), ("marche-quartier", "le petit marché"),
    ("geole", "la geôle"), ("corps-de-garde", "le corps de garde"),
]


def borne_usage(cases, x, y, rayon=45.0):
    """À défaut de monument, ce qu'on a sous les yeux au coin de la rue."""
    rang = {u: i for i, (u, _) in enumerate(BORNES_USAGE)}
    mots = dict(BORNES_USAGE)
    best = None
    for cx in range(int((x - rayon) // 100), int((x + rayon) // 100) + 1):
        for cy in range(int((y - rayon) // 100), int((y + rayon) // 100) + 1):
            for (bx, by, u) in cases.get((cx, cy), ()):
                if u not in rang:
                    continue
                d = math.hypot(bx - x, by - y)
                if d > rayon:
                    continue
                cle = (rang[u], d)
                if best is None or cle < best[0]:
                    best = (cle, mots[u], (round(bx, 1), round(by, 1)))
    if not best:
        return ("", "")
    # La REF est ce qui fait la correspondance. « le puits » de deux marches
    # differentes n'est pas le meme puits : sans identite, on souderait deux
    # lignes en un point ou Marlo n'est jamais passe deux fois.
    return (best[1], "bat:%.0f,%.0f" % best[2])


def repere_pres(G, x, y, rayon=60.0):
    """Ce qu'on longe de nommé — les monuments, pas les maisons."""
    GENRES = {"porte", "forteresse", "monument", "septuaire", "guilde",
              "caserne", "marche", "quai", "office", "chantier", "sommet"}
    proches = []
    for n in G["noeuds"]:
        if n.get("niveau") != 0 or n.get("genre") not in GENRES or not n.get("nom"):
            continue
        d = math.hypot(n["xyz"][0] - x, n["xyz"][1] - y)
        if d <= rayon:
            proches.append((d, n["nom"]))
    proches.sort()
    return proches[0][1] if proches else ""


def main():
    a = sys.argv[1:]
    def opt(nom, defaut=None):
        return a[a.index(nom) + 1] if nom in a and len(a) > a.index(nom) + 1 else defaut

    de_nom = opt("--de")
    a_nom = opt("--a")
    if not (de_nom and a_nom):
        print(__doc__)
        return

    G = charger()
    d0 = par_nom(G, de_nom)
    d1 = par_nom(G, a_nom)
    if not d0: sortir("  point de départ inconnu : %s" % de_nom)
    if not d1: sortir("  point d'arrivée inconnu : %s" % a_nom)

    route, total = chemin(G, d0["id"], d1["id"])
    segs = segmenter(G, route)
    cases, _ = grille_bati()

    print()
    print("  DE %s À %s" % (d0["nom"].upper(), d1["nom"].upper()))
    print("  %d pas — %.0f m — environ %d minutes de marche, sans s'arrêter"
          % (round(total / PAS_M), total, max(1, round(total / 83.0))))
    print()
    print("  %-30s %7s %8s %10s  %s" % ("rue", "pas", "maisons", "pente", "on longe"))
    print("  " + "-" * 78)
    total_maisons = 0
    lignes = []
    for s in segs:
        pas = round(s["m"] / PAS_M)
        if pas < 8:                      # un bout de rue de six pas n'est pas un segment
            continue
        n = compter(cases, s["trace"])
        total_maisons += n
        pente = degre(sum(s["pentes"]) / len(s["pentes"])) + sens(s["dz"])
        x, y = s["trace"][len(s["trace"]) // 2][0], s["trace"][len(s["trace"]) // 2][1]
        rep = repere_pres(G, x, y)
        print("  %-30s %7d %8d %10s  %s" % (s["nom"][:30], pas, n, pente, rep))
        lignes.append({"cellules": [s["nom"], str(pas), str(n), pente, rep or ""],
                       "note": ""})
    print("  " + "-" * 78)
    print("  %-30s %7d %8d" % ("EN TOUT", round(total / PAS_M), total_maisons))
    print()

    # --- la LIGNE, pour le plan ---------------------------------------------
    # Un levé au pas ne donne pas une forme, il donne une suite : des bornes,
    # et entre elles des pas, des maisons, une pente. C'est un plan de métro
    # avant la lettre — et c'est la seule figure honnête, parce qu'elle ne
    # prétend à aucune géographie que Marlo n'a pas mesurée.
    leve = opt("--leve")
    if leve:
        bornes = [{"nom": d0["nom"], "ref": "rep:" + d0["nom"],
                   "genre": d0.get("genre", "")}]
        troncons = []
        for s in segs:
            pas = round(s["m"] / PAS_M)
            if pas < 8:
                continue
            mi = s["trace"][len(s["trace"]) // 2]
            rep = repere_pres(G, mi[0], mi[1], 120.0)
            # LE CAP. Un homme ne sait pas un azimut, mais il sait les huit
            # aires de vent : la mer est au nord, la riviere au levant, le soleil
            # fait le reste. C'est ce qui rend un leve lisible — sans direction,
            # des longueurs seules ne font qu'un noeud de ficelle.
            t0, t1 = s["trace"][0], s["trace"][-1]
            cap = math.degrees(math.atan2(t1[1] - t0[1], t1[0] - t0[0]))
            cap8 = round(cap / 45.0) * 45 % 360
            VENTS = {0: "au levant", 45: "au nord-est", 90: "au nord",
                     135: "au nord-ouest", 180: "au couchant",
                     225: "au sud-ouest", 270: "au midi", 315: "au sud-est"}
            troncons.append({
                "garnison": postes(cases, s["trace"]),
                "peage": [p[0] for p in peages(G, s["trace"])],
                "cap": cap8, "vent": VENTS[cap8],
                "rue": s["nom"], "pas": pas,
                "maisons": compter(cases, s["trace"]),
                "pente": degre(sum(s["pentes"]) / len(s["pentes"])),
                "sens": ("monte" if s["dz"] > 1 else
                         "descend" if s["dz"] < -1 else "plat"),
                "largeur_m": round(s["largeur"], 1),
            })
            fin = G_noeud(G, s["fin"])
            # Une borne ne se répète pas : si l'on longe encore le même repère
            # qu'au tronçon d'avant, c'est qu'on n'a pas changé d'endroit, et
            # une station sans nom vaut mieux qu'un nom deux fois.
            ref = ("rep:" + rep) if rep else ""
            if not rep:
                fin_n = G_noeud(G, s["fin"]) or {}
                fx, fy = (fin_n.get("xyz") or [mi[0], mi[1], 0])[:2]
                rep, ref = borne_usage(cases, fx, fy)
            if ref and bornes and bornes[-1].get("ref") == ref:
                rep, ref = "", ""      # on n'est pas reparti : meme borne
            bornes.append({"nom": rep or "", "ref": ref,
                           "genre": (fin or {}).get("genre", "")})
        bornes[-1] = {"nom": d1["nom"], "ref": "rep:" + d1["nom"],
                      "genre": d1.get("genre", "")}
        p = os.path.join(RACINE, "etat", "leves.json")
        try:
            T = json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError):
            T = {"leves": []}
        T.setdefault("leves", [])
        T["leves"] = [x for x in T["leves"] if x.get("id") != leve]
        T["leves"].append({
            "id": leve, "leve_par": opt("--porteur", "marlo-vasse"),
            "de": d0["nom"], "a": d1["nom"],
            "pas": round(total / PAS_M), "maisons": total_maisons,
            "minutes": max(1, round(total / 83.0)),
            "bornes": bornes, "troncons": troncons,
        })
        io.open(p, "w", encoding="utf-8").write(
            json.dumps(T, ensure_ascii=False, indent=2))
        print("  écrit dans etat/leves.json : %s" % leve)

    livre = opt("--livre")
    if not livre:
        if not leve:
            print("  (rien écrit — --leve <id> pour la ligne, --livre <id> pour la page)")
        return

    titre = opt("--titre") or ("Le levé de %s à %s" % (d0["nom"], d1["nom"]))
    porteur = opt("--porteur", "marlo-vasse")
    B = json.load(io.open(BOOKS, encoding="utf-8"))
    L = B if isinstance(B, list) else B["livres"]
    neuf = {
        "id": livre, "lieu_id": "port-real", "acteur_id": porteur, "prive": True,
        "titre": titre,
        "sous_titre": ("Levé au pas, de %s à %s : %d pas, %d maisons comptées. "
                       "Ce qui n'est pas sur le chemin n'y est pas."
                       % (d0["nom"], d1["nom"], round(total / PAS_M), total_maisons)),
        "type": "registre",
        "colonnes": ["Rue", "Pas", "Maisons", "Pente", "On longe"],
        "lignes": lignes,
        "pages": ["Un levé au pas ne voit que sa rue. Ce qu'il y a derrière les "
                  "façades n'y est pas, et l'oublier serait la seule façon de "
                  "s'en servir de travers."],
    }
    L = [b for b in L if b.get("id") != livre] + [neuf]
    if isinstance(B, list): B = L
    else: B["livres"] = L
    io.open(BOOKS, "w", encoding="utf-8").write(
        json.dumps(B, ensure_ascii=False, indent=2))
    print("  écrit dans etat/books.json : %s" % livre)


if __name__ == "__main__":
    main()
