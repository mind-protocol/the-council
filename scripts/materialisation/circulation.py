# -*- coding: utf-8 -*-
"""La circulation du château — sur l'anneau, où l'adjacence est DONNÉE.

    python scripts/materialisation/circulation.py

La version d'avant lisait les salles du plan du jeu et devinait leurs voisines
à la distance. C'était du rattrapage : le plan les fait flotter, alors on
mesurait des écarts et on élargissait des seuils jusqu'à ce que ça passe.

L'anneau supprime le problème. Deux corps qui se suivent dans le programme
PARTAGENT leur refend : la porte entre eux n'est plus une hypothèse, c'est une
conséquence. Il ne reste qu'à décider lesquelles percer — et un château n'ouvre
pas tout sur tout : une cuisine communique avec l'office, pas avec l'armurerie.

Trois règles, et l'invariant :
  · la COUR est le carrefour : tout corps de rez y ouvre par sa façade ;
  · le REFEND se perce entre voisins de même genre, ou quand la séquence
    l'exige (la chaîne cuisines → office → écrans → grande salle) ;
  · un ÉTAGE ne se gagne que par un escalier, qui a une emprise réelle ;
  · et rien n'est inatteignable depuis la porte — sinon on perce, et on le dit.
"""
import math
import sys

import programme as Prog
import peyredragon as P

SOUS_PLAFOND = Prog.SOUS_PLAFOND
VIS_RAYON = 1.35              # une vis tient dans 2,7 m hors œuvre
COURSE = 9.2                  # ce qu'une volée droite prend au sol par niveau

# Ce qui communique de plain-pied sans passer par la cour. Le reste s'ouvre sur
# la cour et pas ailleurs : dans un château, on ressort pour changer de corps.
CHAINE = [
    ("cuisines", "office"), ("office", "ecrans"), ("ecrans", "grande-salle"),
    ("grande-salle", "retrait"), ("retrait", "chambre-haute"),
    ("chambre-haute", "galerie"), ("galerie", "chambre-enfants"),
    ("chambre-enfants", "garde-robe"),
    ("corps-de-garde", "garnison"), ("garnison", "armurerie"),
    ("ecuries", "selleries"), ("selleries", "forge"),
    ("boulangerie", "brasserie"), ("brasserie", "buanderie"),
]


def _cle(corps, etage):
    return "%s@%d" % (corps, etage)


def noeuds(p):
    """Un nœud par corps et par étage, plus la cour et les caves."""
    N = {"cour@0": {"id": "cour@0", "nom": "La cour", "corps": "cour",
                    "etage": 0, "ou": _milieu_cour(p), "genre": "cour"}}
    for c in p["corps"]:
        for e in range(c["etages"]):
            k = _cle(c["id"], e)
            N[k] = {"id": k, "nom": c["nom"] + ("" if e == 0 else " (étage %d)" % e),
                    "corps": c["id"], "etage": e, "ou": c["milieu"],
                    "genre": c["genre"], "aire": c["aire"]}
    for v in p["caves"]:
        k = _cle(v["id"], -1)
        N[k] = {"id": k, "nom": v["nom"], "corps": v["id"], "etage": -1,
                "ou": v["milieu"], "genre": "cave", "sous": v["sous"]}
    return N


def _milieu_cour(p):
    f = p["facade"]
    return (sum(q[0] for q in f) / len(f), sum(q[1] for q in f) / len(f))


def liaisons(p, N):
    """Les portes : sur la cour, et dans les refends que la séquence exige."""
    L = []
    for c in p["corps"]:
        L.append({"de": "cour@0", "vers": _cle(c["id"], 0), "genre": "porte",
                  "cout": 3.0, "ou": c["milieu"],
                  "raison": "%s ouvre sur la cour" % c["nom"]})

    voisins = {}
    ordonnes = sorted(p["corps"], key=lambda c: c["s"][0])
    for a, b in zip(ordonnes, ordonnes[1:] + ordonnes[:1]):
        voisins[(a["id"], b["id"])] = (a, b)

    paires = {tuple(sorted(x)) for x in CHAINE}
    for (ida, idb), (a, b) in voisins.items():
        mitoyen = tuple(sorted((ida, idb))) in paires
        # deux appentis de la même travée se traversent : c'est une remise, pas
        # une enfilade de pièces closes
        if a["genre"] == b["genre"] == "appentis":
            mitoyen = True
        if not mitoyen:
            continue
        L.append({"de": _cle(ida, 0), "vers": _cle(idb, 0), "genre": "refend",
                  "cout": 1.0, "ou": _entre(a, b),
                  "raison": "Refend percé : la séquence va %s à %s"
                            % (de_(a["nom"]), b["nom"].lower())})
    return L


def _entre(a, b):
    return ((a["milieu"][0] + b["milieu"][0]) / 2,
            (a["milieu"][1] + b["milieu"][1]) / 2)


def escaliers(p, N):
    """Une vis par corps à étages, une volée droite par cave. Rien de gratuit."""
    E = []
    for c in p["corps"]:
        if c["etages"] < 2:
            continue
        # au bout du corps, contre le refend : c'est là qu'une vis se loge sans
        # manger la pièce, et c'est là qu'on les trouve
        f = c["facade"]
        x, y = f[-1]
        dx, dy = c["arriere"][-1][0] - x, c["arriere"][-1][1] - y
        n = math.hypot(dx, dy) or 1.0
        E.append({"id": "vis-" + c["id"], "genre": "vis",
                  "ou": (x + dx / n * 2.4, y + dy / n * 2.4), "rayon": VIS_RAYON,
                  "corps": c["id"], "du": 0, "au": c["etages"] - 1,
                  "raison": "La vis %s : %d étages à monter"
                            % (de_(c["nom"]), c["etages"] - 1)})
    for v in p["caves"]:
        hote = next((c for c in p["corps"] if c["id"] == v["sous"]), None)
        if not hote:
            continue
        E.append({"id": "descente-" + v["id"], "genre": "droit",
                  "ou": v["milieu"], "course": COURSE,
                  "corps": v["id"], "du": -1, "au": 0,
                  "raison": "La descente %s, sous %s"
                            % (de_(v["nom"]), hote["nom"].lower())})
    return E


def dessertes(E):
    """Ce qu'un escalier relie : son corps, d'un niveau au suivant."""
    liens = []
    for e in E:
        for n in range(e["du"], e["au"]):
            liens.append({"de": _cle(e["corps"], n), "vers": _cle(e["corps"], n + 1),
                          "genre": e["genre"], "cout": 5.0, "ou": e["ou"],
                          "raison": e["raison"]})
        if e["genre"] == "droit":
            liens.append({"de": _cle(e["corps"], -1), "vers": "cour@0",
                          "genre": "droit", "cout": 6.0, "ou": e["ou"],
                          "raison": e["raison"]})
    return liens


DEPART = "cour@0"


def de_(nom):
    """« de » + un nom qui porte déjà son article : du, de la, de l'."""
    n = nom.lower()
    if n.startswith("le "):
        return "du " + nom[3:].lower()
    if n.startswith("la "):
        return "de la " + nom[3:].lower()
    if n.startswith("les "):
        return "des " + nom[4:].lower()
    if n.startswith("l'"):
        return "de l'" + nom[2:].lower()
    return "de " + n


def resoudre(N, tous):
    """L'arbre couvrant, MAIS les refends sont acquis d'avance.

    Un arbre couvrant ne garde que ce qui rend un nœud nouveau : comme tout
    corps ouvre déjà sur la cour, chaque refend refermait un circuit et se
    faisait jeter — on obtenait un château où l'on ressort dans la cour pour
    passer de la cuisine à l'office. Or ces refends sont des décisions du
    programme, pas des redondances à élaguer : on les pose d'abord.
    """
    vus, gardees = {DEPART}, []
    reste = [a for a in tous if a["genre"] != "refend"]
    for a in tous:
        if a["genre"] == "refend":
            gardees.append(a)
            vus.add(a["de"])
            vus.add(a["vers"])
    bouge = True
    while bouge:
        bouge = False
        for a in sorted(reste, key=lambda x: x["cout"]):
            d, v = a["de"] in vus, a["vers"] in vus
            if d == v:
                continue
            vus.add(a["vers"] if d else a["de"])
            gardees.append(a)
            reste.remove(a)
            bouge = True
    hors = [k for k in N if k not in vus]
    return gardees, vus, hors


def engendrer_sur(p):
    """Le graphe sur un plan DÉJÀ calculé — pour ne pas le redérouler."""
    N = noeuds(p)
    E = escaliers(p, N)
    tous = liaisons(p, N) + dessertes(E)
    gardees, vus, hors = resoudre(N, tous)
    return {"plan": p, "noeuds": N, "escaliers": E, "possibles": tous,
            "liaisons": gardees, "atteints": vus, "hors": hors}


def refends_perces(g):
    """Les couples de corps dont le refend est ouvert — ce que la pierre doit percer."""
    out = set()
    for a in g["liaisons"]:
        if a["genre"] != "refend":
            continue
        out.add(tuple(sorted((a["de"].split("@")[0], a["vers"].split("@")[0]))))
    return out


def engendrer():
    p = Prog.plan()
    N = noeuds(p)
    E = escaliers(p, N)
    tous = liaisons(p, N) + dessertes(E)
    gardees, vus, hors = resoudre(N, tous)
    return {"plan": p, "noeuds": N, "escaliers": E, "possibles": tous,
            "liaisons": gardees, "atteints": vus, "hors": hors}


if __name__ == "__main__":
    g = engendrer()
    N = g["noeuds"]
    portes = [a for a in g["liaisons"] if a["genre"] == "porte"]
    refends = [a for a in g["liaisons"] if a["genre"] == "refend"]
    montees = [a for a in g["liaisons"] if a["genre"] in ("vis", "droit")]
    print("LA CIRCULATION")
    print("  %d lieux (corps x etage, caves, cour)" % len(N))
    print("  %d liaisons possibles, %d retenues" % (len(g["possibles"]), len(g["liaisons"])))
    print("    %3d portes sur la cour" % len(portes))
    print("    %3d refends perces entre voisins" % len(refends))
    print("    %3d montees d'escalier" % len(montees))
    print("\nLES ESCALIERS  (%d)" % len(g["escaliers"]))
    for e in g["escaliers"][:8]:
        print("  %-26s %-6s %s" % (e["id"], e["genre"], e["raison"]))
    if len(g["escaliers"]) > 8:
        print("  … et %d autres" % (len(g["escaliers"]) - 8))
    print("\n  %d lieux atteints depuis la cour" % len(g["atteints"]))
    if g["hors"]:
        print("  ! INATTEIGNABLES : " + ", ".join(N[k]["nom"] for k in g["hors"]))
    else:
        print("  tout est atteignable.")
