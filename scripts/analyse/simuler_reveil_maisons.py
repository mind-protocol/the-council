# -*- coding: utf-8 -*-
"""Combien de tours faut-il pour reveiller les tetes des grandes maisons ?

Le banc rejoue EXACTEMENT l'election de ``boucle_activation.cycle`` — meme
diffusion d'importance, meme integration d'energie, meme polarites d'horloge,
meme rotation, meme choix de tache — mais n'appelle aucun modele et n'ecrit
rien : ni ``etat/``, ni ``boucle.json``, ni rapport depose.

Ce qu'il remplace, faute de modele, ce sont les deux seules sorties que
l'activation reelle rend au moteur :

  * ``depense``      — l'energie reellement consommee. Par defaut le budget
                       entier, c'est-a-dire le cas ou l'homme use sa fenetre.
  * ``duree_monde``  — les secondes de monde produites, soit ``budget * 30``.

L'horloge avance alors de la duree de l'activation la plus longue du tour,
puisque dans la boucle reelle une seconde de mur vaut une seconde de monde.

Usage :
    python scripts/analyse/simuler_reveil_maisons.py
    python scripts/analyse/simuler_reveil_maisons.py --tours 100 --parallele 1
    python scripts/analyse/simuler_reveil_maisons.py --fraction-depense 0.6
    python scripts/analyse/simuler_reveil_maisons.py --json rapport.json
"""

import argparse
import collections
import copy
import io
import json
import math
import os
import sys

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RACINE = os.path.dirname(SCRIPTS)
ETAT = os.path.join(RACINE, "etat")
sys.path.insert(0, SCRIPTS)

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import boucle_activation as activation  # noqa: E402


# Les sept tetes. Une grande maison est ici une maison du royaume qui pese sur
# la Danse sans etre la notre, et sa tete est celui qui decide pour elle.
TETES_PAR_DEFAUT = [
    ("maison-targaryen-vert", "aegon-ii"),
    ("maison-hightower", "ormund-hightower"),
    ("maison-velaryon", "corlys"),
    ("maison-baratheon", "borros-baratheon"),
    ("maison-lannister", "jason-lannister"),
    ("maison-stark", "cregan-stark"),
    ("maison-arryn", "jeyne-arryn"),
]


def lire(chemin, defaut):
    try:
        with io.open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return defaut


def liste(valeur, *cles):
    if isinstance(valeur, dict):
        for cle in cles:
            if isinstance(valeur.get(cle), list):
                return valeur[cle]
        return []
    return valeur if isinstance(valeur, list) else []


def camp_des_notres():
    """Notre camp : les sieges, leurs PNJ rattaches, et la maison noire.

    C'est la definition operante du jeu, pas une geographie : ``pnj`` dit qui
    une regie tient. Corlys y figure alors qu'il est Velaryon — et c'est juste,
    puisqu'il est joue depuis notre table.
    """
    sieges = liste(lire(os.path.join(ETAT, "joueurs.json"), []),
                   "joueurs", "sieges")
    notres = set()
    for siege in sieges:
        if not siege.get("occupe", True):
            continue
        if siege.get("personnage_id"):
            notres.add(siege["personnage_id"])
        notres.update(x for x in (siege.get("pnj") or []) if x)
    personnages = liste(lire(os.path.join(ETAT, "personnages.json"), []),
                        "personnages")
    for p in personnages:
        if p.get("maison_id") == "maison-targaryen-noir" and p.get("id"):
            notres.add(p["id"])
    return notres, {p.get("id"): p for p in personnages if p.get("id")}


class ArgsSimulation(object):
    """Le sous-ensemble d'arguments que l'election consulte reellement."""

    def __init__(self, parallele):
        self.parallele = parallele
        self.capacite_cycle = parallele
        self.acteur = None
        self.sec = True


def horloge_simulee(etat, base_horloge, ecoule):
    horloge = dict(base_horloge)
    horloge["present_secondes"] = float(base_horloge["base_secondes"]) + ecoule
    return horloge


def elire(etat, horloge, noeuds, aretes, evaluation, occupes, capacite):
    """Copie fidele de la phase d'election de ``cycle`` (avant les appels)."""
    activation.amorcer_continuite_historique(etat, noeuds)
    scores, adj = activation.importance(
        noeuds, aretes, evaluation, horloge["source_id"], occupes)
    polarites, _ = activation.polarites_horloge_acteurs(noeuds, adj)
    energies_graphe = activation.mettre_a_jour_energie_graphe(
        etat, horloge, scores, noeuds, adj, polarites)
    disponibilites = activation.calendrier(
        noeuds, aretes, evaluation, horloge["source_id"])
    for nid, score in scores.items():
        noeuds[nid]["importance_activation"] = score
    eligibles = activation.mettre_a_jour_energies(
        etat, horloge, scores, energies_graphe, disponibilites, noeuds, occupes)

    rotation = etat.setdefault("rotation_activation", {"tour": 1, "vus": []})
    vus = set(rotation.get("vus") or [])

    def selectionner(exclus):
        choix = []
        taches = set()
        for energie, score, pid, jauge in eligibles:
            if energie < activation.ENERGIE_ACTIVATION_MIN:
                break
            if pid in exclus:
                continue
            if activation.acteur_en_repos(etat, pid, horloge["present_secondes"]):
                continue
            tache = activation.choisir_tache(
                "pers:" + pid, noeuds, aretes, adj, energies_graphe,
                etat=etat, present=horloge["present_secondes"])
            if tache is None:
                continue
            energie_tache = activation.energie_de_tache(
                tache, energies_graphe, energie)
            if energie_tache < activation.ENERGIE_MIN:
                continue
            if tache["id"] in taches:
                continue
            choix.append((energie, score, pid, jauge, tache))
            taches.add(tache["id"])
            if len(choix) >= capacite:
                break
        return choix

    selections = selectionner(vus)
    tour_neuf = False
    if not selections and vus:
        rotation["tour"] = int(rotation.get("tour") or 1) + 1
        rotation["vus"] = []
        vus = set()
        tour_neuf = True
        selections = selectionner(vus)
    if selections:
        rotation["vus"] = sorted(vus | {s[2] for s in selections})
    return selections, energies_graphe, tour_neuf, len(eligibles)


def simuler(tours_max=100, parallele=1, fraction_depense=1.0, tetes=None,
            verbeux=True):
    tetes = tetes or TETES_PAR_DEFAUT
    attendues = {pid: maison for maison, pid in tetes}
    notres, fiches = camp_des_notres()

    etat = copy.deepcopy(activation.lire_json(
        activation.ETAT_BOUCLE, {"version": 1, "historique": []}))
    base_horloge, occupes = activation.horloge_directe(etat)
    noeuds, aretes, evaluation = activation.charger_tissu()

    args = ArgsSimulation(parallele)
    ecoule = 0.0
    reveillees = {}
    activations = []
    par_camp = collections.Counter()
    par_maison = collections.Counter()
    tours_vides = 0

    if verbeux:
        print("Sept tetes attendues : %s" %
              ", ".join(pid for _m, pid in tetes))
        print("Notre camp : %d personnes (sieges + PNJ rattaches + maison noire)"
              % len(notres))
        print("Depense simulee : %.0f%% du budget · parallele %d · max %d tours"
              % (fraction_depense * 100, parallele, tours_max))
        print("-" * 78)

    for tour in range(1, tours_max + 1):
        horloge = horloge_simulee(etat, base_horloge, ecoule)
        selections, energies, tour_neuf, nb_eligibles = elire(
            etat, horloge, noeuds, aretes, evaluation, occupes,
            args.capacite_cycle)

        if not selections:
            tours_vides += 1
            if verbeux:
                print("t%-3d  %-22s eligibles=%d  monde=%s  — personne"
                      % (tour, "(vide)", nb_eligibles, duree_lisible(ecoule)))
            # Sans elu, rien ne consomme et rien ne bouge : on avance quand meme
            # d'une demi-vie pour laisser l'energie se recharger, sinon la
            # simulation pietine sur un etat strictement identique.
            ecoule += activation.DEMI_VIE_ENERGIE
            continue

        duree_tour = 0
        for energie, score, pid, jauge, tache in selections:
            budget = min(100, int(math.floor(energie)))
            budget_s = activation.secondes_monde_pour_energie(budget)
            depense = min(float(budget), float(budget) * fraction_depense)
            duree_monde = int(round(budget_s * fraction_depense))
            duree_tour = max(duree_tour, duree_monde)

            reserves = etat.setdefault("graphe", {}).setdefault("noeuds", {})
            reserves["pers:" + pid] = max(0.0, float(energie) - depense)
            jauge["energie"] = reserves["pers:" + pid]
            jauge["disponible_a"] = round(
                float(horloge["present_secondes"]) + duree_monde, 3)
            jauge["activations"] = int(jauge.get("activations") or 0) + 1

            fiche = fiches.get(pid) or {}
            maison = fiche.get("maison_id") or "(sans maison)"
            camp = "nous" if pid in notres else "eux"
            par_camp[camp] += 1
            par_maison[maison] += 1
            activations.append({"tour": tour, "qui": pid, "camp": camp,
                                "maison": maison, "budget": budget,
                                "importance": round(score, 4)})

            marque = ""
            if pid in attendues and pid not in reveillees:
                reveillees[pid] = tour
                marque = "  <<< TETE %s (%d/7)" % (
                    attendues[pid], len(reveillees))

            if verbeux:
                print("t%-3d  %-22s %-5s %-24s e=%5.1f imp=%.3f bud=%3d "
                      "(%2d min)  monde=%s%s"
                      % (tour, pid, camp, maison.replace("maison-", ""),
                         energie, score, budget, round(budget_s / 60),
                         duree_lisible(ecoule), marque))

        ecoule += max(duree_tour, 1)

        if len(reveillees) == len(attendues):
            if verbeux:
                print("-" * 78)
                print("Les sept tetes sont reveillees au tour %d." % tour)
            return rapport(tour, True, reveillees, attendues, activations,
                           par_camp, par_maison, ecoule, tours_vides, notres)

    return rapport(tours_max, False, reveillees, attendues, activations,
                   par_camp, par_maison, ecoule, tours_vides, notres)


def duree_lisible(secondes):
    secondes = int(secondes)
    jours, reste = divmod(secondes, 86400)
    heures, reste = divmod(reste, 3600)
    minutes = reste // 60
    if jours:
        return "%dj%02dh%02d" % (jours, heures, minutes)
    return "%02dh%02d" % (heures, minutes)


def rapport(tours, complet, reveillees, attendues, activations, par_camp,
            par_maison, ecoule, tours_vides, notres):
    total = sum(par_camp.values())
    return {
        "tours_joues": tours,
        "toutes_reveillees": complet,
        "tetes_reveillees": len(reveillees),
        "tetes_attendues": len(attendues),
        "tour_par_tete": reveillees,
        "tetes_muettes": sorted(set(attendues) - set(reveillees)),
        "activations_total": total,
        "activations_chez_nous": par_camp.get("nous", 0),
        "activations_chez_les_autres": par_camp.get("eux", 0),
        "part_chez_nous": round(100.0 * par_camp.get("nous", 0) / total, 1)
        if total else 0.0,
        "acteurs_distincts": len({a["qui"] for a in activations}),
        "acteurs_distincts_chez_nous": len(
            {a["qui"] for a in activations if a["camp"] == "nous"}),
        "acteurs_distincts_chez_les_autres": len(
            {a["qui"] for a in activations if a["camp"] == "eux"}),
        "par_maison": dict(par_maison.most_common()),
        "tours_sans_acteur": tours_vides,
        "monde_ecoule_s": int(ecoule),
        "monde_ecoule": duree_lisible(ecoule),
        "taille_camp_nous": len(notres),
        "activations": activations,
    }


def analyser_arguments():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tours", type=int, default=100)
    p.add_argument("--parallele", type=int, default=1)
    p.add_argument("--fraction-depense", type=float, default=1.0,
                   help="part du budget reellement consommee par activation")
    p.add_argument("--json", help="ecrit le rapport complet dans ce fichier")
    p.add_argument("--muet", action="store_true")
    return p.parse_args()


def main():
    args = analyser_arguments()
    if args.tours <= 0 or args.parallele <= 0:
        raise SystemExit("tours et parallele doivent etre positifs")
    if not 0 < args.fraction_depense <= 1:
        raise SystemExit("fraction-depense doit tenir dans ]0, 1]")
    activation.AFFICHER_LOGS = False
    activation.PERSISTER_LOGS = False
    resultat = simuler(tours_max=args.tours, parallele=args.parallele,
                       fraction_depense=args.fraction_depense,
                       verbeux=not args.muet)
    print()
    print("=" * 78)
    print("RESULTAT")
    print("  tours joues ................ %d" % resultat["tours_joues"])
    print("  tetes reveillees ........... %d/%d"
          % (resultat["tetes_reveillees"], resultat["tetes_attendues"]))
    for pid, tour in sorted(resultat["tour_par_tete"].items(),
                            key=lambda x: x[1]):
        print("      t%-4d %s" % (tour, pid))
    if resultat["tetes_muettes"]:
        print("  jamais reveillees .......... %s"
              % ", ".join(resultat["tetes_muettes"]))
    print("  monde ecoule ............... %s" % resultat["monde_ecoule"])
    print("  activations ................ %d" % resultat["activations_total"])
    print("      chez nous .............. %d (%.1f%%) sur %d personnes"
          % (resultat["activations_chez_nous"], resultat["part_chez_nous"],
             resultat["acteurs_distincts_chez_nous"]))
    print("      chez les autres ........ %d (%.1f%%) sur %d personnes"
          % (resultat["activations_chez_les_autres"],
             100.0 - resultat["part_chez_nous"],
             resultat["acteurs_distincts_chez_les_autres"]))
    print("  par maison :")
    for maison, n in resultat["par_maison"].items():
        print("      %-28s %d" % (maison, n))
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(resultat, f, ensure_ascii=False, indent=2)
        print("  rapport .................... %s" % args.json)
    return 0 if resultat["toutes_reveillees"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
