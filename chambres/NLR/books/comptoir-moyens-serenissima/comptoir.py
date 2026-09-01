"""Porte de consultation des moyens techniques de la maison Serenissima."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


CONSEIL = Path(__file__).resolve().parents[4]
DOCUMENTS = CONSEIL / "etat" / "maisons" / "maison-serenissima" / "documents"
PLAN = DOCUMENTS / "books" / "plan-moyens-serenissima.json"
MAINS = DOCUMENTS / "mains.json"


def lire_json(chemin: Path) -> dict:
    with chemin.open("r", encoding="utf-8-sig") as source:
        return json.load(source)


def texte(cellule: str) -> str:
    return cellule.replace("**", "").replace("`", "")


def consulter() -> int:
    plan = lire_json(PLAN)
    print(f"{plan['titre']} — {plan['sous_titre']}")
    for ligne in plan["lignes"]:
        cellules = ligne["cellules"]
        print(f"{texte(cellules[0])} | {texte(cellules[1])}")
        print(f"  porte : {texte(cellules[5])}")
        print(f"  état  : {texte(cellules[8])}")
    print("Limite : recensement lisible, fonctionnement des services non prouvé.")
    return 0


def verifier() -> int:
    plan = lire_json(PLAN)
    mains = lire_json(MAINS)
    mesures = {
        mesure["id"]: mesure["valeur"]
        for main in mains["mains"]
        for mesure in main["mesure"]
    }
    ligne_m110 = next(
        ligne["cellules"] for ligne in plan["lignes"] if "M110" in ligne["cellules"][0]
    )
    etat_m110 = texte(ligne_m110[8])
    controles = {
        "containers-declares": (mesures.get("containers-declares"), "9" in etat_m110),
        "modules-rattaches": (
            mesures.get("modules-rattaches"),
            str(mesures.get("modules-rattaches")) in etat_m110,
        ),
        "modules-orphelins": (
            mesures.get("modules-orphelins"),
            str(mesures.get("modules-orphelins")) in etat_m110,
        ),
        "liens-hors-porte": (
            mesures.get("liens-hors-porte"),
            str(mesures.get("liens-hors-porte")) in etat_m110,
        ),
        "dependances-remontantes": (
            mesures.get("dependances-remontantes"),
            str(mesures.get("dependances-remontantes")) in etat_m110,
        ),
        "commandes-bibliotheques": (
            mesures.get("commandes-bibliotheques"),
            "0 commande-bibliothèque" in etat_m110,
        ),
    }
    divergences = []
    for nom, (valeur, concorde) in controles.items():
        verdict = "CONCORDE" if concorde else "DIVERGE"
        print(f"{nom}: mains={valeur} — {verdict}")
        if not concorde:
            divergences.append(nom)
    print(f"Verdict : {len(divergences)} divergence(s) publiée(s), aucune correction appliquée.")
    return 1 if divergences else 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("geste", choices=("consulter", "verifier"))
    arguments = analyseur.parse_args()
    return consulter() if arguments.geste == "consulter" else verifier()


if __name__ == "__main__":
    raise SystemExit(main())
