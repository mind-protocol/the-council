"""Prépare un signalement complet avant de le porter au comptoir de Lucid."""

from __future__ import annotations

import argparse
from datetime import date


CHAMPS = ("date", "navire", "capitaine", "provenance", "cargaison", "source")


def valeur_non_vide(valeur: str) -> str:
    propre = valeur.strip()
    if not propre:
        raise argparse.ArgumentTypeError("le champ ne peut pas être vide")
    return propre


def date_iso(valeur: str) -> str:
    propre = valeur_non_vide(valeur)
    try:
        date.fromisoformat(propre)
    except ValueError as erreur:
        raise argparse.ArgumentTypeError("date attendue au format AAAA-MM-JJ") from erreur
    return propre


def construire_analyseur() -> argparse.ArgumentParser:
    analyseur = argparse.ArgumentParser(
        description="Refuse un avis d'escale tant que ses six amarres ne sont pas tenues."
    )
    analyseur.add_argument("--date", required=True, type=date_iso)
    analyseur.add_argument("--navire", required=True, type=valeur_non_vide)
    analyseur.add_argument("--capitaine", required=True, type=valeur_non_vide)
    analyseur.add_argument("--provenance", required=True, type=valeur_non_vide)
    analyseur.add_argument("--cargaison", required=True, type=valeur_non_vide)
    analyseur.add_argument("--source", required=True, type=valeur_non_vide)
    return analyseur


def main() -> None:
    avis = vars(construire_analyseur().parse_args())
    print("ETAT: PRET_A_PORTER")
    for champ in CHAMPS:
        print(f"{champ.upper()}: {avis[champ]}")
    print("LIMITE: cet avis ne prouve ni l'arrivée ni l'accostage du navire")


if __name__ == "__main__":
    main()
