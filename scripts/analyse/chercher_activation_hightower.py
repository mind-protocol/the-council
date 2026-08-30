# -*- coding: utf-8 -*-
"""Cherche les parametres d'une vague locale d'activation Hightower.

Le chercheur est entierement en lecture seule. Il projette des liens entre les
personnages de la maison lorsqu'ils partagent un objet du graphe deja recu
(``route.etat`` vaut ``arrive`` ou ``remis``), simule une activation par tour,
puis evalue chaque configuration avec ``scorer_activation_hightower.py``.

L'energie d'un acteur n'est jamais consommee. Deux cooldowns distincts evitent
les boucles immediates : un cooldown d'acteur et un cooldown de lien. Un lien
encore chaud transmet avec ``multiplicateur_lien_recent``.

Usage :
    python scripts/analyse/chercher_activation_hightower.py
    python scripts/analyse/chercher_activation_hightower.py --top 20
    python scripts/analyse/chercher_activation_hightower.py --auto-test
"""

import argparse
import collections
import itertools
import json
import math
import os
import sys


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS)

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from agents.expose import boucle_activation as activation  # noqa: E402
import scorer_activation_hightower as scoreur  # noqa: E402


ETATS_ROUTE_PRETS = {"arrive", "arrivee", "remis", "recu"}


def relation_prete(arete):
    route = arete.get("route") if isinstance(arete.get("route"), dict) else {}
    etat = str(route.get("etat") or "").strip().lower()
    return etat in ETATS_ROUTE_PRETS


def projection_maison(noeuds, aretes, personnages):
    """Projette personne--objet--personne sans traverser une autre personne."""
    ids = {"pers:" + p["id"] for p in personnages}
    par_objet = collections.defaultdict(set)
    for arete in aretes:
        if arete.get("flou") or arete.get("virtuel") or not relation_prete(arete):
            continue
        de, vers = arete.get("de"), arete.get("vers")
        if de in ids and vers in noeuds and noeuds[vers].get("genre") != "personne":
            par_objet[vers].add(de)
        if vers in ids and de in noeuds and noeuds[de].get("genre") != "personne":
            par_objet[de].add(vers)

    brut = collections.defaultdict(float)
    preuves = collections.defaultdict(list)
    for objet, acteurs in par_objet.items():
        if len(acteurs) < 2:
            continue
        # Un objet diffuse a dix personnes est un lien beaucoup plus faible
        # qu'un objet partage par deux : cela borne naturellement les hubs.
        contribution = 1.0 / float(len(acteurs) - 1)
        for gauche, droite in itertools.combinations(sorted(acteurs), 2):
            paire = (gauche, droite)
            brut[paire] += contribution
            preuves[paire].append(objet)

    graphe = {nid: {} for nid in ids}
    details = []
    for (gauche, droite), valeur in brut.items():
        affinite = 1.0 - math.exp(-valeur)
        graphe[gauche][droite] = affinite
        graphe[droite][gauche] = affinite
        objets = preuves[(gauche, droite)]
        details.append({
            "de": gauche.removeprefix("pers:"),
            "vers": droite.removeprefix("pers:"),
            "affinite": round(affinite, 6),
            "objets_partages": objets,
        })
    return graphe, sorted(details, key=lambda x: (-x["affinite"], x["de"], x["vers"]))


def simuler(graphe, importances, configuration, cible_initiale,
            tours_maximum, tour_secondes):
    """Simule une activation par tour ; l'energie reste dans les acteurs."""
    energies = {nid: 0.0 for nid in graphe}
    cible_initiale = "pers:" + cible_initiale.removeprefix("pers:")
    if cible_initiale not in energies:
        raise ValueError("la cible initiale n'appartient pas a la maison")
    energies[cible_initiale] = 1.0
    dernier_acteur = {}
    dernier_lien = {}
    premieres = {}
    sequence = []

    for tour in range(tours_maximum):
        eligibles = []
        for nid, energie in energies.items():
            if energie <= 1e-12:
                continue
            dernier = dernier_acteur.get(nid)
            if dernier is not None and tour - dernier <= configuration["cooldown_acteur"]:
                continue
            importance = importances.get(nid, 0.0)
            priorite = energie * (1.0 + configuration["biais_importance"] * importance)
            eligibles.append((priorite, importance, energie, nid))

        if not eligibles:
            sequence.append({"tour": tour, "acteur": None})
            continue
        _priorite, importance, energie, elu = max(
            eligibles, key=lambda x: (x[0], x[1], x[2], x[3])
        )
        pid = elu.removeprefix("pers:")
        premieres.setdefault(pid, tour)
        sequence.append({
            "tour": tour,
            "acteur": pid,
            "energie": round(energie, 6),
            "importance": round(importance, 6),
        })
        dernier_acteur[elu] = tour

        for voisin, affinite in graphe.get(elu, {}).items():
            lien = tuple(sorted((elu, voisin)))
            dernier = dernier_lien.get(lien)
            recent = dernier is not None and tour - dernier <= configuration["cooldown_lien"]
            multiplicateur = (
                configuration["multiplicateur_lien_recent"] if recent else 1.0
            )
            transfert = (
                energie
                * configuration["impulsion"]
                * configuration["decay"]
                * affinite
                * multiplicateur
            )
            energies[voisin] = min(1.0, energies[voisin] + transfert)
            dernier_lien[lien] = tour

    entrees = []
    for nid in sorted(graphe):
        pid = nid.removeprefix("pers:")
        premier_tour = premieres.get(pid)
        entrees.append({
            "id": pid,
            "importance": importances.get(nid, 0.0),
            "disponible_s": (
                premier_tour * tour_secondes if premier_tour is not None else None
            ),
        })
    score = scoreur.scorer_calendrier(entrees, tour_secondes)
    return {"score": score, "sequence": sequence, "premieres": premieres}


def grille():
    valeurs = {
        "decay": (0.45, 0.60, 0.75, 0.90),
        "impulsion": (0.35, 0.55, 0.75, 1.00),
        # Le but demande explicitement un biais d'importance : zero n'est pas
        # une configuration admissible, meme si les affinites donnent par
        # hasard le bon ordre sur l'instant observe.
        "biais_importance": (0.25, 0.5, 1.0, 2.0),
        "cooldown_acteur": (1, 2, 3, 4),
        "cooldown_lien": (1, 2, 3, 4),
        "multiplicateur_lien_recent": (0.0, 0.15, 0.35, 0.60),
    }
    cles = tuple(valeurs)
    for combinaison in itertools.product(*(valeurs[cle] for cle in cles)):
        yield dict(zip(cles, combinaison))


def cle_classement(candidat):
    cfg = candidat["configuration"]
    # A score egal, on prefere la moindre impulsion, le moindre cooldown et le
    # multiplicateur recent le moins punitif : c'est la solution la plus douce.
    return (
        -candidat["score"],
        cfg["impulsion"],
        cfg["cooldown_acteur"],
        cfg["cooldown_lien"],
        -cfg["multiplicateur_lien_recent"],
        -cfg["decay"],
        cfg["biais_importance"],
    )


def chercher(maison_id="maison-hightower", cible_initiale="otto",
             tours_maximum=8, tour_secondes=300.0, top=10):
    noeuds, aretes, evaluation = activation.charger_tissu()
    personnages = scoreur.personnages_cibles(maison_id)
    if not personnages:
        raise RuntimeError("aucun personnage eligible pour %s" % maison_id)
    graphe, liens = projection_maison(noeuds, aretes, personnages)
    source_id = scoreur.source_principale()
    importances, _ = activation.importance(noeuds, aretes, evaluation, source_id)

    candidats = []
    total = 0
    for configuration in grille():
        total += 1
        simulation = simuler(
            graphe, importances, configuration, cible_initiale,
            tours_maximum, tour_secondes,
        )
        candidats.append({
            "score": simulation["score"]["score"],
            "verdict": simulation["score"]["verdict"],
            "composantes": simulation["score"]["composantes"],
            "configuration": configuration,
            "premieres_activations": simulation["premieres"],
            "sequence": simulation["sequence"],
        })
    candidats.sort(key=cle_classement)
    meilleur = candidats[0] if candidats else None
    reussis = sum(1 for candidat in candidats if candidat["score"] >= 85.0)
    return {
        "maison_id": maison_id,
        "cible_initiale": cible_initiale,
        "tour_secondes": tour_secondes,
        "energie_consommee": False,
        "configurations_testees": total,
        "configurations_reussies": reussis,
        "liens_projetes": liens,
        "meilleur": meilleur,
        "top": candidats[:top],
    }


def auto_test():
    graphe = {
        "pers:otto": {"pers:alicent": 1.0, "pers:ormund": 0.4},
        "pers:alicent": {"pers:otto": 1.0, "pers:ormund": 0.7},
        "pers:ormund": {"pers:otto": 0.4, "pers:alicent": 0.7},
    }
    importances = {"pers:otto": 0.9, "pers:alicent": 0.6, "pers:ormund": 0.2}
    configuration = {
        "decay": 0.75,
        "impulsion": 0.55,
        "biais_importance": 1.0,
        "cooldown_acteur": 2,
        "cooldown_lien": 2,
        "multiplicateur_lien_recent": 0.15,
    }
    simulation = simuler(graphe, importances, configuration, "otto", 5, 300)
    assert simulation["premieres"] == {"otto": 0, "alicent": 1, "ormund": 2}
    assert simulation["score"]["score"] == 100.0
    return {"ok": True, "score": 100.0, "sequence": simulation["sequence"]}


def analyser_arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maison-id", default="maison-hightower")
    parser.add_argument("--cible-initiale", default="otto")
    parser.add_argument("--tours", type=int, default=8)
    parser.add_argument("--tour-secondes", type=float, default=300.0)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--auto-test", action="store_true")
    return parser.parse_args()


def main():
    args = analyser_arguments()
    if args.tours <= 0 or args.tour_secondes <= 0 or args.top <= 0:
        raise SystemExit("tours, tour-secondes et top doivent etre positifs")
    resultat = (
        auto_test() if args.auto_test
        else chercher(
            maison_id=args.maison_id,
            cible_initiale=args.cible_initiale,
            tours_maximum=args.tours,
            tour_secondes=args.tour_secondes,
            top=args.top,
        )
    )
    print(json.dumps(resultat, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
