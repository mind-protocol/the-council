#!/usr/bin/env python3
"""Valide une fiche d'arpentage sans prétendre mesurer ni transformer le mur."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ETATS = {"NON ESSAYÉE", "ESSAYÉE", "RÉALISÉE"}
CHAMPS_TEXTE = (
    "lieu",
    "segment",
    "observation_materielle",
    "usage_braavosi",
    "transformation_desiree",
    "reserve",
    "observateur",
)


def valider(piece: dict[str, Any]) -> dict[str, Any]:
    erreurs: list[str] = []
    reserves: list[str] = []

    if piece.get("type") != "arpentage-heritage/1":
        erreurs.append("type attendu : arpentage-heritage/1")

    for champ in CHAMPS_TEXTE:
        if not isinstance(piece.get(champ), str) or not piece[champ].strip():
            erreurs.append(f"champ requis absent ou vide : {champ}")

    provenance = piece.get("provenance_rapportee")
    if not isinstance(provenance, dict):
        erreurs.append("provenance_rapportee absente")
    else:
        for champ in ("origine", "source", "ref", "nature"):
            if not isinstance(provenance.get(champ), str) or not provenance[champ].strip():
                erreurs.append(f"provenance incomplète : {champ}")

    mesure = piece.get("mesure")
    if not isinstance(mesure, dict):
        erreurs.append("mesure absente")
    else:
        largeur = mesure.get("largeur")
        hauteur = mesure.get("hauteur")
        unite = mesure.get("unite")
        for nom, valeur in (("largeur", largeur), ("hauteur", hauteur)):
            if valeur is not None and (not isinstance(valeur, (int, float)) or valeur < 0):
                erreurs.append(f"mesure invalide : {nom}")
        if largeur is None or hauteur is None:
            reserves.append("dimensions incomplètes")
        if not isinstance(unite, str) or not unite.strip():
            erreurs.append("unité absente")
        elif (largeur is not None or hauteur is not None) and unite == "non mesurée":
            erreurs.append("une valeur chiffrée exige une unité mesurée")

    transformation = piece.get("transformation")
    if not isinstance(transformation, dict):
        erreurs.append("transformation absente")
        etat = None
        preuve = None
    else:
        etat = transformation.get("etat")
        preuve = transformation.get("preuve")
        if etat not in ETATS:
            erreurs.append("état de transformation inconnu")
        if etat in {"ESSAYÉE", "RÉALISÉE"} and (
            not isinstance(preuve, str) or not preuve.strip()
        ):
            erreurs.append(f"preuve obligatoire pour {etat}")
        if etat == "NON ESSAYÉE" and preuve:
            reserves.append("preuve fournie alors que la transformation est NON ESSAYÉE")

    if erreurs:
        verdict = "NON RECEVABLE"
    elif reserves:
        verdict = "RECEVABLE AVEC RÉSERVE"
    else:
        verdict = "RECEVABLE"

    return {
        "verdict": verdict,
        "erreurs": erreurs,
        "reserves": reserves,
        "portee": (
            "Validation documentaire seulement : aucun mur n'est mesuré ni "
            "transformé par ce programme."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fiche", type=Path)
    args = parser.parse_args()
    try:
        piece = json.loads(args.fiche.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"verdict": "ERREUR DE LECTURE", "detail": str(exc)}, ensure_ascii=False))
        return 2

    resultat = valider(piece)
    print(json.dumps(resultat, ensure_ascii=False, indent=2))
    return 0 if resultat["verdict"].startswith("RECEVABLE") else 1


if __name__ == "__main__":
    raise SystemExit(main())
