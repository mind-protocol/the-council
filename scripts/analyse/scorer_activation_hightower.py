# -*- coding: utf-8 -*-
"""Score la cadence d'activation d'une maison sans modifier l'etat.

Le score mesure la condition suivante : les personnages eligibles d'une maison
doivent etre actives approximativement un par tour, et les plus importants
doivent tendre a passer avant les autres.

Par defaut un tour vaut cinq minutes, duree de test de la boucle d'activation.
Le script reutilise strictement le graphe projete et les formules de diffusion
de ``boucle_activation.py``.

Usage :
    python scripts/analyse/scorer_activation_hightower.py
    python scripts/analyse/scorer_activation_hightower.py --tour-secondes 300
    python scripts/analyse/scorer_activation_hightower.py --minimum 85
    python scripts/analyse/scorer_activation_hightower.py --auto-test
"""

import argparse
import collections
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

from agents.expose import boucle_activation as activation  # noqa: E402
import tables  # LA PORTE de etat/ : une lecture, une ecriture, une semantique d'erreur


def lire_json(chemin, defaut):
    """Une seule porte, une seule semantique — voir `scripts/tables.py`.

    Il y avait quatre `lire_json` dans ce depot et quatre comportements devant
    un fichier corrompu : deux plantaient, deux repartaient en silence sur le
    defaut. C'est tranche une fois pour toutes — un JSON abime PLANTE, seule
    l'absence rend le defaut.
    """
    return tables.lire(chemin, defaut)


def personnage_eligible(personnage, inclure_dormants=False):
    """Le statut existant suffit : aucun champ de scoring n'est invente."""
    if inclure_dormants:
        return True
    etat = str(personnage.get("etat") or "actif").strip().lower()
    condition = str(personnage.get("condition") or "libre").strip().lower()
    return etat == "actif" and condition not in {
        "mort", "morte", "disparu", "disparue", "prisonnier", "prisonniere"
    }


def personnages_cibles(maison_id, inclure_dormants=False):
    personnages = lire_json(os.path.join(ETAT, "personnages.json"), [])
    return [
        personnage for personnage in personnages
        if personnage.get("maison_id") == maison_id
        and personnage_eligible(personnage, inclure_dormants)
    ]


def source_principale():
    sieges = lire_json(os.path.join(ETAT, "joueurs.json"), [])
    if isinstance(sieges, dict):
        sieges = sieges.get("joueurs") or sieges.get("sieges") or []
    occupes = [s for s in sieges if s.get("occupe", True) and s.get("personnage_id")]
    principal = next(
        (s for s in occupes if s.get("role") == "principal"),
        occupes[0] if occupes else None,
    )
    if not principal:
        raise RuntimeError("aucun siege joueur occupe ne donne l'origine de la diffusion")
    return principal["personnage_id"]


def arrondir_tour(secondes, origine, tour_secondes):
    """Le tour le plus proche rend 'a peu pres tour par tour' explicite."""
    return int(math.floor(((secondes - origine) / tour_secondes) + 0.5))


def scorer_calendrier(entrees, tour_secondes):
    """Calcule couverture, cadence et concordance avec l'importance.

    ``entrees`` contient une ligne par cible avec ``importance`` et, lorsque le
    graphe la rend atteignable, ``disponible_s``.
    """
    if tour_secondes <= 0:
        raise ValueError("--tour-secondes doit etre strictement positif")

    datables = [e for e in entrees if isinstance(e.get("disponible_s"), (int, float))]
    couverture = len(datables) / float(len(entrees)) if entrees else 0.0

    if datables:
        origine = min(e["disponible_s"] for e in datables)
        for entree in entrees:
            disponible = entree.get("disponible_s")
            entree["tour"] = (
                arrondir_tour(disponible, origine, tour_secondes)
                if isinstance(disponible, (int, float)) else None
            )
    else:
        origine = None
        for entree in entrees:
            entree["tour"] = None

    par_tour = collections.Counter(e["tour"] for e in datables)
    collisions = sum(max(0, nombre - 1) for nombre in par_tour.values())
    tours_uniques = sorted(par_tour)
    trous = sum(
        max(0, apres - avant - 1)
        for avant, apres in zip(tours_uniques, tours_uniques[1:])
    )
    penalites = collisions + trous
    cadence = (
        math.exp(-penalites / float(max(1, len(datables) - 1)))
        if datables else 0.0
    )

    poids_total = 0.0
    concordance = 0.0
    inversions = []
    for index, gauche in enumerate(datables):
        for droite in datables[index + 1:]:
            ecart = abs(float(gauche["importance"]) - float(droite["importance"]))
            if ecart <= 1e-12:
                continue
            haute, basse = (
                (gauche, droite)
                if gauche["importance"] > droite["importance"]
                else (droite, gauche)
            )
            poids_total += ecart
            if haute["tour"] < basse["tour"]:
                concordance += ecart
            elif haute["tour"] == basse["tour"]:
                concordance += 0.5 * ecart
            else:
                inversions.append({
                    "plus_importante": haute["id"],
                    "moins_importante": basse["id"],
                })
    biais_importance = concordance / poids_total if poids_total else 1.0

    # La cadence est la condition principale. Le biais d'importance departage
    # ensuite les calendriers de cadence comparable. La couverture multiplie le
    # tout afin qu'un beau calendrier partiel ne puisse pas obtenir un bon score.
    score = 100.0 * couverture * (0.70 * cadence + 0.30 * biais_importance)
    score = round(score, 2)
    verdict = "atteint" if score >= 85 else "approche" if score >= 65 else "insuffisant"

    diagnostic = []
    absents = [e["id"] for e in entrees if e.get("tour") is None]
    if absents:
        diagnostic.append({"type": "inatteignables", "personnages": absents})
    if collisions:
        diagnostic.append({
            "type": "collisions",
            "nombre": collisions,
            "tours": {
                str(tour): [e["id"] for e in datables if e["tour"] == tour]
                for tour, nombre in sorted(par_tour.items()) if nombre > 1
            },
        })
    if trous:
        diagnostic.append({"type": "tours_vides", "nombre": trous})
    if inversions:
        diagnostic.append({"type": "inversions_importance", "paires": inversions})

    return {
        "score": score,
        "verdict": verdict,
        "composantes": {
            "couverture": round(couverture, 4),
            "cadence": round(cadence, 4),
            "biais_importance": round(biais_importance, 4),
        },
        "mesures": {
            "cibles": len(entrees),
            "datables": len(datables),
            "collisions": collisions,
            "tours_vides": trous,
            "origine_secondes": origine,
        },
        "diagnostic": diagnostic,
    }


def construire_evaluation(maison_id, tour_secondes, inclure_dormants=False):
    noeuds, aretes, evaluation = activation.charger_tissu()
    source_id = source_principale()
    importances, _ = activation.importance(noeuds, aretes, evaluation, source_id)
    disponibilites = activation.calendrier(noeuds, aretes, evaluation, source_id)

    entrees = []
    for personnage in personnages_cibles(maison_id, inclure_dormants):
        noeud_id = "pers:" + personnage["id"]
        entrees.append({
            "id": personnage["id"],
            "nom": personnage.get("nom") or personnage["id"],
            "etat": personnage.get("etat"),
            "condition": personnage.get("condition"),
            "importance": round(float(importances.get(noeud_id, 0.0)), 6),
            "disponible_s": (
                round(float(disponibilites[noeud_id]), 3)
                if noeud_id in disponibilites else None
            ),
        })

    resultat = scorer_calendrier(entrees, tour_secondes)
    resultat.update({
        "condition": "personnages de la maison actives approximativement un par tour, avec biais d'importance",
        "maison_id": maison_id,
        "source_id": source_id,
        "tour_secondes": tour_secondes,
        "ponderation": {"cadence": 0.70, "biais_importance": 0.30},
        "personnages": sorted(
            entrees,
            key=lambda e: (e["tour"] is None, e["tour"] if e["tour"] is not None else 0, -e["importance"]),
        ),
    })
    return resultat


def auto_test():
    def ligne(identifiant, tour, importance, duree=300):
        return {
            "id": identifiant,
            "importance": importance,
            "disponible_s": tour * duree,
        }

    ideal = scorer_calendrier([
        ligne("fort", 0, 0.9), ligne("moyen", 1, 0.6), ligne("faible", 2, 0.2)
    ], 300)
    simultane = scorer_calendrier([
        ligne("fort", 0, 0.9), ligne("moyen", 0, 0.6), ligne("faible", 0, 0.2)
    ], 300)
    inverse = scorer_calendrier([
        ligne("fort", 2, 0.9), ligne("moyen", 1, 0.6), ligne("faible", 0, 0.2)
    ], 300)
    partiel = scorer_calendrier([
        ligne("fort", 0, 0.9), ligne("moyen", 1, 0.6),
        {"id": "absent", "importance": 0.2, "disponible_s": None},
    ], 300)

    assert ideal["score"] == 100.0
    assert simultane["score"] < inverse["score"] < ideal["score"]
    assert partiel["composantes"]["couverture"] < 1.0
    assert partiel["score"] < ideal["score"]
    return {
        "ok": True,
        "cas": {
            "ideal": ideal["score"],
            "simultane": simultane["score"],
            "ordre_inverse": inverse["score"],
            "couverture_partielle": partiel["score"],
        },
    }


def analyser_arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maison-id", default="maison-hightower")
    parser.add_argument("--tour-secondes", type=float, default=300.0)
    parser.add_argument("--inclure-dormants", action="store_true")
    parser.add_argument(
        "--minimum", type=float,
        help="sort avec le code 1 lorsque le score est inferieur a ce seuil",
    )
    parser.add_argument("--auto-test", action="store_true")
    return parser.parse_args()


def main():
    args = analyser_arguments()
    resultat = (
        auto_test() if args.auto_test
        else construire_evaluation(args.maison_id, args.tour_secondes, args.inclure_dormants)
    )
    print(json.dumps(resultat, ensure_ascii=False, indent=2))
    if args.minimum is not None and not args.auto_test:
        return 0 if resultat["score"] >= args.minimum else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
