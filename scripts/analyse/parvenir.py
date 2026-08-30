# -*- coding: utf-8 -*-
# PARVENIR — est-ce que ca va atteindre le joueur ? a quel point ? quand ?
#
# POURQUOI. Tout ce manuel repose sur une question posee a la main, avant
# d'ecrire quoi que ce soit : « par quelle bouche, ou par quel empechement, ca
# atteindra le joueur ? » On l'a posee pour les mains, pour les pieces d'en
# face, pour les routes de fuite. Elle n'avait aucune reponse calculable — on
# repondait de memoire, et l'on se trompait : six verrous de Hightower ont vecu
# des jours comme des murs invisibles sans que personne le voie.
#
# Ce script repond en trois chiffres, et pas un de plus :
#
#     PARVIENT   oui / non          y a-t-il une route, seulement
#     QUAND      une date de jeu    monde.date + le plus court chemin en jours
#     A QUEL POINT   0..100         ce qu'il en reste apres les bouches
#
# TROIS PRECISIONS QUI COMMANDENT LA LECTURE.
#
# 1. LA REPONSE EST PAR SIEGE. Le brouillard n'est pas partage : ce qui parvient
#    a la reine ne parvient pas a son agent en ville, et l'inverse. Un chiffre
#    unique pour « le joueur » serait faux le jour ou l'on joue a deux.
# 2. LE SCORE N'EST PAS UNE PROBABILITE. C'est ce qui SURVIT au trajet : le
#    produit des fiabilites ecrites, amorti par chaque bouche traversee. 100 =
#    la chose arrive telle qu'elle est ; 40 = il en arrive quelque chose, et ce
#    quelque chose est faux par endroits. Une nouvelle a 40 n'est pas une
#    nouvelle qui a 40% de chances d'arriver : elle arrive, abimee.
# 3. CE QUI N'A PAS DE ROUTE N'EN A PAS. Le script ne bouche aucun trou et
#    n'invente aucun canal. « aucune route » est une reponse, et c'est la plus
#    utile qu'il rende — elle dit qu'on a ecrit une piece que personne ne peut
#    apprendre.
#
# Usage :
#     python scripts/analyse/parvenir.py 71002                 une piece
#     python scripts/analyse/parvenir.py --en-face             tous les verrous d'en face
#     python scripts/analyse/parvenir.py --affaires            les journees d'hommes
#     python scripts/analyse/parvenir.py --muets               ce qui n'atteint personne
#     python scripts/analyse/parvenir.py 71002 --par-ou        le chemin, bouche par bouche
#     python scripts/analyse/parvenir.py --en-face --json
import argparse
import collections
import heapq
import io
import json
import os
import sys

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RACINE = os.path.dirname(SCRIPTS)
ETAT = os.path.join(RACINE, "etat")

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from agents.expose import boucle_activation as activation  # noqa: E402  (tissu, genres relais)
from etat.expose import tables  # LA PORTE de etat/ : une lecture, une ecriture, une semantique d'erreur

# CE QUI PORTE UNE NOUVELLE, ET CE QUI N'EN PORTE PAS.
#
# La faute que ce script a faite a sa premiere execution, et qu'on garde ecrite
# ici parce qu'elle est instructive : il faisait parvenir a la reine, en quatre
# jours, un fait de Villevieille situe a vingt-cinq jours de route — en passant
# par `depend_de`, `realise` et `bloque`. Ces aretes-la disent qu'une chose en
# COMMANDE une autre, jamais qu'une chose se RACONTE a quelqu'un. Les prendre
# pour des canaux revient a croire qu'un homme apprend le prix du grain parce
# que le prix du grain empeche son ost de marcher.
#
# Ne portent une nouvelle que : ce qui revele (une diffusion arrivee, un pli
# remis), ce qui achemine (un pli en route), et les routes ecrites a la main
# dans liens.json. C'est exactement l'ensemble que `tisser.py` marque deja
# `connaissance: true`, plus les routes.
CANAUX = {"revele", "achemine", "route"}


def porte_une_nouvelle(a):
    return bool(a.get("connaissance")) or a.get("nature") in CANAUX


# CE QU'UNE BOUCHE COUTE. Chaque relais humain traverse abime ce qui passe : on
# ne repete pas un chiffre sans l'arrondir, ni un motif sans l'aplatir. 0.88 par
# personne est un reglage, pas une loi — il est ici, en clair, pour se corriger
# d'un seul endroit. Les objets (un pli, une piece, un registre) ne coutent
# rien : c'est le propre d'un ecrit que de traverser sans se deformer.
AMORTI_PAR_BOUCHE = 0.88
# Une arete sans fiabilite ecrite ne dit rien de sa qualite ; on ne la punit pas
# et on ne la croit pas non plus sur parole.
FIABILITE_MUETTE = 0.95
# En dessous, ce qui arrive n'est plus la chose : c'est une rumeur qui lui
# ressemble. Seuil de lecture, jamais de filtrage — on affiche tout.
SEUIL_DEFORME = 55
SEUIL_RUMEUR = 30


def lire_json(chemin, defaut):
    """Une seule porte, une seule semantique — voir `scripts/tables.py`.

    Il y avait quatre `lire_json` dans ce depot et quatre comportements devant
    un fichier corrompu : deux plantaient, deux repartaient en silence sur le
    defaut. C'est tranche une fois pour toutes — un JSON abime PLANTE, seule
    l'absence rend le defaut.
    """
    return tables.lire(chemin, defaut)


def sieges_occupes():
    """Un brouillard par siege. On repond pour chacun, jamais en moyenne."""
    j = lire_json(os.path.join(ETAT, "joueurs.json"), [])
    if isinstance(j, dict):
        j = j.get("joueurs") or j.get("sieges") or []
    # Un siege de REGIE (Corneille) n'a pas de brouillard : il n'incarne
    # personne, et l'on n'a rien a lui faire parvenir.
    return [s["personnage_id"] for s in j
            if s.get("occupe", True) and s.get("personnage_id")
            and not s.get("regie")]


def date_du_monde():
    m = lire_json(os.path.join(ETAT, "monde.json"), {})
    d = (m or {}).get("date") or {}
    return {"annee": d.get("annee", 129), "lune": d.get("lune", 1),
            "jour": d.get("jour", 1)}


def ajouter_jours(date, jours):
    j = int(round(jours))
    a, l, d = date["annee"], date["lune"], date["jour"] + j
    while d > 30:
        d -= 30
        l += 1
        if l > 12:
            l -= 12
            a += 1
    return {"annee": a, "lune": l, "jour": d}


def dire_date(d):
    return "{}.{}.{}".format(d["annee"], d["lune"], d["jour"])


def lieux_par_id():
    return {l.get("id"): l for l in lire_json(os.path.join(ETAT, "lieux.json"), [])
            if isinstance(l, dict) and l.get("id")}


def construire(noeuds, aretes, evaluation):
    """Le meme graphe que la diffusion, et les memes couts. On ne refait pas
    une deuxieme physique du monde a cote de la premiere : un delai calcule ici
    et la-bas donnerait deux verites, et c'est ainsi qu'un chiffre faux naît."""
    adj = collections.defaultdict(list)
    for a in aretes:
        de, vers = a.get("de"), a.get("vers")
        if a.get("flou") or a.get("virtuel") or de == vers:
            continue
        if de not in noeuds or vers not in noeuds:
            continue
        if not porte_une_nouvelle(a):
            continue
        adj[de].append((vers, a))
        adj[vers].append((de, a))
    presence = ((evaluation.get("presence") or {}).get("acteurs") or [])
    par_presence = {"pers:" + p.get("id"): p for p in presence if p.get("id")}
    return adj, par_presence


def distance_physique(nid, source_noeud, noeuds, par_presence, lieux):
    """Ce que coute d'aller jusqu'a quelqu'un quand aucune route ne le porte."""
    p = par_presence.get(nid) or {}
    d = p.get("distance_joueur_minutes")
    if isinstance(d, (int, float)):
        return float(d) / 1440.0
    a = (source_noeud or {}).get("lieu_id")
    b = (noeuds.get(nid) or {}).get("lieu_id")
    if not a or not b:
        return None
    if a == b:
        return 0.0
    la, lb = lieux.get(a) or {}, lieux.get(b) or {}
    da, db = la.get("jours_de_pr"), lb.get("jours_de_pr")
    if not isinstance(da, (int, float)) or not isinstance(db, (int, float)):
        return None
    return abs(da - db) if da == 0 or db == 0 else da + db


def trajet(depart, siege, noeuds, adj, par_presence, lieux):
    """Le plus court chemin en JOURS de `depart` jusqu'au siege, et ce qui
    survit du message le long de ce chemin.

    On classe sur les jours seuls. Le score ne departage pas deux routes : une
    nouvelle qui arrive vite et fausse EST ce qui arrive, et la remplacer par
    une route plus lente parce qu'elle serait plus propre mentirait sur le
    monde. Le score qualifie l'arrivee, il ne la choisit pas.
    """
    cible = "pers:" + siege
    source_noeud = noeuds.get(cible) or {}
    depart_noeud = noeuds.get(depart)
    if depart_noeud is None:
        return None

    # UN HOMME DANS LA SALLE N'A PAS DE ROUTE : IL A UNE BOUCHE. Le graphe ne
    # sait pas qu'on est assis a la meme table — la presence n'est pas une
    # arete de connaissance — et sans ce court-circuit le script cherchait a
    # Gerardys, debout devant la reine, un chemin de rumeurs a score 16. Ce
    # qu'un homme present veut dire, il le dit ; ce qu'il tait est une autre
    # question, et ce n'est pas celle-ci.
    if depart.startswith("pers:") and depart != cible:
        p = par_presence.get(depart) or {}
        q = par_presence.get(cible) or {}
        meme_salle = p.get("salle") and p.get("salle") == q.get("salle")
        a_portee = p.get("distance_joueur_minutes") == 0
        if meme_salle or a_portee:
            return {"jours": 0.0, "sauts": 0, "bouches": 0, "score": 100,
                    "chemin": [], "deformations": [],
                    "de_vive_voix": True}
    meilleur = {depart: (0.0, 0)}
    venu = {depart: None}
    file = [(0.0, 0, depart)]
    while file:
        jours, sauts, ici = heapq.heappop(file)
        if meilleur.get(ici) != (jours, sauts):
            continue
        if ici == cible:
            break
        n = noeuds.get(ici) or {}
        if ici != depart and n.get("genre") not in activation.GENRES_RELAIS:
            continue
        for suivant, a in adj.get(ici) or []:
            route = a.get("route") if isinstance(a.get("route"), dict) else {}
            ajout = 0.0
            if isinstance(route.get("delai_jours"), (int, float)) \
                    and route["delai_jours"] > 0:
                ajout = float(route["delai_jours"])
            elif (noeuds.get(suivant) or {}).get("genre") == "personne" \
                    and suivant != depart:
                phys = distance_physique(suivant, source_noeud, noeuds,
                                         par_presence, lieux)
                if phys is None:
                    continue
                ajout = phys
            candidat = (jours + ajout, sauts + 1)
            if meilleur.get(suivant) is None or candidat < meilleur[suivant]:
                meilleur[suivant] = candidat
                venu[suivant] = (ici, a)
                heapq.heappush(file, (candidat[0], candidat[1], suivant))

    if cible not in meilleur:
        return None

    chemin, ici = [], cible
    while venu.get(ici):
        precedent, a = venu[ici]
        chemin.append((precedent, a, ici))
        ici = precedent
    chemin.reverse()

    survie, bouches, deformations = 1.0, 0, []
    for precedent, a, suivant in chemin:
        route = a.get("route") if isinstance(a.get("route"), dict) else {}
        f = route.get("fiabilite")
        survie *= (float(f) / 100.0 if isinstance(f, (int, float))
                   else FIABILITE_MUETTE)
        if (noeuds.get(suivant) or {}).get("genre") == "personne" \
                and suivant != cible:
            bouches += 1
            survie *= AMORTI_PAR_BOUCHE
        if route.get("deforme_comment"):
            deformations.append(route["deforme_comment"])
    return {
        "jours": meilleur[cible][0],
        "sauts": meilleur[cible][1],
        "bouches": bouches,
        "score": int(round(100 * survie)),
        "chemin": chemin,
        "deformations": deformations,
    }


def verdict(t):
    if t is None:
        return "AUCUNE ROUTE"
    if t["score"] >= SEUIL_DEFORME:
        return "parvient"
    if t["score"] >= SEUIL_RUMEUR:
        return "parvient deforme"
    return "n'en arrive qu'une rumeur"


def etiquette(noeuds, nid):
    n = noeuds.get(nid) or {}
    return (n.get("quoi") or nid)[:52]


def cibles_en_face():
    brut = lire_json(os.path.join(ETAT, "plans.json"), {})
    plans = brut.get("plans", []) if isinstance(brut, dict) else brut
    out = []
    for p in plans:
        for fam in ("verrous", "etats_cibles", "actions"):
            for x in p.get(fam) or []:
                if x.get("id"):
                    out.append((x["id"], "{} · {}".format(p.get("id"), x.get("quoi") or "")))
    return out


def cibles_affaires():
    """Une affaire n'est pas un noeud du tissu : elle voyage par son porteur.
    On repond donc pour l'homme, en disant que c'est par lui qu'elle passe."""
    brut = lire_json(os.path.join(ETAT, "pensees.json"), {})
    liste = brut.get("pensees", brut) if isinstance(brut, dict) else brut
    vues = {}
    for x in liste:
        if isinstance(x, dict) and x.get("qui"):
            vues.setdefault((x["qui"], x.get("affaire") or ""), 0)
            vues[(x["qui"], x.get("affaire") or "")] += 1
    return [("pers:" + qui, "{} · {} ({} pensees)".format(qui, aff, n))
            for (qui, aff), n in sorted(vues.items(), key=lambda kv: -kv[1])]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pieces", nargs="*", help="un ou plusieurs id de noeud")
    ap.add_argument("--en-face", action="store_true")
    ap.add_argument("--affaires", action="store_true")
    ap.add_argument("--muets", action="store_true",
                    help="ne montrer que ce qui n'atteint aucun siege")
    ap.add_argument("--par-ou", action="store_true", help="le chemin, bouche par bouche")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    noeuds, aretes, evaluation = activation.charger_tissu()
    adj, par_presence = construire(noeuds, aretes, evaluation)
    lieux = lieux_par_id()
    sieges = sieges_occupes()
    aujourdhui = date_du_monde()

    cibles = [(p, etiquette(noeuds, p)) for p in args.pieces]
    if args.en_face:
        cibles += cibles_en_face()
    if args.affaires:
        cibles += cibles_affaires()
    if not cibles:
        ap.error("donne un id, ou --en-face, ou --affaires")

    lignes = []
    for nid, libelle in cibles:
        par_siege = {}
        for s in sieges:
            t = trajet(nid, s, noeuds, adj, par_presence, lieux)
            par_siege[s] = {
                "verdict": verdict(t),
                "quand": dire_date(ajouter_jours(aujourdhui, t["jours"])) if t else None,
                "jours": round(t["jours"], 1) if t else None,
                "score": t["score"] if t else 0,
                "bouches": t["bouches"] if t else None,
                "chemin": ([etiquette(noeuds, c[0]) for c in t["chemin"]]
                           + [s] if t else []),
                "deformations": t["deformations"] if t else [],
            }
        if args.muets and any(v["verdict"] != "AUCUNE ROUTE"
                              for v in par_siege.values()):
            continue
        lignes.append({"piece": nid, "quoi": libelle, "sieges": par_siege})

    if args.json:
        print(json.dumps({"date": aujourdhui, "sieges": sieges,
                          "pieces": lignes}, ensure_ascii=False, indent=1))
        return 0

    print("PARVENIR — au {} · sieges : {}".format(
        dire_date(aujourdhui), ", ".join(sieges)))
    print("  score = ce qui SURVIT au trajet, pas une probabilite d'arriver.")
    print("  {} bouche(s) traversee(s) coutent {}x chacune.".format(
        "chaque", AMORTI_PAR_BOUCHE))
    print()
    muets = 0
    for l in lignes:
        print("{:<10} {}".format(l["piece"], l["quoi"][:64]))
        for s, v in l["sieges"].items():
            if v["verdict"] == "AUCUNE ROUTE":
                print("    {:<18} AUCUNE ROUTE — personne ne peut l'apprendre".format(s))
                muets += 1
                continue
            print("    {:<18} {:<26} {}  ({:+d} j · {} bouche{})  score {}".format(
                s, v["verdict"], v["quand"], int(v["jours"]), v["bouches"],
                "s" if v["bouches"] > 1 else "", v["score"]))
            if args.par_ou:
                print("        par : " + " -> ".join(v["chemin"]))
                for d in v["deformations"]:
                    print("        deforme : " + str(d)[:150])
        print()
    if muets:
        print("{} couple(s) piece/siege sans aucune route.".format(muets))
        print("Une piece qu'aucun siege ne peut apprendre est une piece ecrite")
        print("pour le MJ seul : ou bien on lui donne une bouche, ou bien on")
        print("l'efface. C'est la borne des mains, rendue calculable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
