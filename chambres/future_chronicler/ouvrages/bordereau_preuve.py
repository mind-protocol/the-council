#!/usr/bin/env python3
"""Vérifie qu'un bordereau ne transforme pas une trace en résultat acquis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ETATS_GESTE = {"PROPOSE", "FAIT", "NON_FAIT"}
ETATS_RESULTAT = {"NON_ESSAYE", "CONFORME", "NON_CONFORME", "INCONNU"}
DECISIONS = {"NON_EXAMINE", "RECU", "NON_RECU", "RETENU"}


def verifier(bordereau: dict) -> list[str]:
    erreurs: list[str] = []
    obligatoires = {
        "date",
        "auteur",
        "ref",
        "source",
        "geste",
        "resultat",
        "decision",
        "preuve",
    }
    for champ in sorted(obligatoires - bordereau.keys()):
        erreurs.append(f"champ manquant : {champ}")

    geste = bordereau.get("geste", {})
    resultat = bordereau.get("resultat", {})
    decision = bordereau.get("decision", {})

    if geste.get("etat") not in ETATS_GESTE:
        erreurs.append("état du geste invalide")
    if resultat.get("etat") not in ETATS_RESULTAT:
        erreurs.append("état du résultat invalide")
    if decision.get("etat") not in DECISIONS:
        erreurs.append("décision de réception invalide")

    if decision.get("etat") == "RECU" and resultat.get("etat") != "CONFORME":
        erreurs.append("RECU exige un résultat CONFORME")
    if resultat.get("etat") in {"CONFORME", "NON_CONFORME"} and geste.get("etat") != "FAIT":
        erreurs.append("un résultat jugé exige un geste FAIT")
    if geste.get("etat") == "FAIT" and not bordereau.get("preuve"):
        erreurs.append("un geste FAIT exige une preuve adressable")

    return erreurs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bordereau", type=Path)
    args = parser.parse_args()

    try:
        donnees = json.loads(args.bordereau.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valide": False, "erreurs": [str(exc)]}, ensure_ascii=False))
        return 2

    erreurs = verifier(donnees)
    print(json.dumps({"valide": not erreurs, "erreurs": erreurs}, ensure_ascii=False))
    return 0 if not erreurs else 1


if __name__ == "__main__":
    raise SystemExit(main())
