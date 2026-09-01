#!/usr/bin/env python3
"""Dresse la double lecture des salles de Braavos : adresse présente, nom hérité."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


RACINE = Path(__file__).resolve().parents[3]
SOURCE = RACINE / "monde" / "braavos.interieurs.json"
COUCHES = Path(__file__).with_name("couches_braavos.json")
MARQUES = (
    "dragon",
    "aegon",
    "roukerie",
    "table peinte",
    "tambour de pierre",
    "guivre des vents",
    "septuaire",
    "appartements",
)


def couche(nom: str) -> str:
    bas = nom.casefold()
    return "marque héritée forte" if any(marque in bas for marque in MARQUES) else "fonction commune"


def charger() -> list[dict]:
    donnees = json.loads(SOURCE.read_text(encoding="utf-8"))
    return donnees["salles"]


def charger_couches() -> list[dict]:
    donnees = json.loads(COUCHES.read_text(encoding="utf-8"))
    return donnees["renommages"]


def verifier(salles: list[dict], couches: list[dict]) -> list[str]:
    erreurs: list[str] = []
    ids = [salle.get("id") for salle in salles]
    if len(salles) != 34:
        erreurs.append(f"34 salles attendues, {len(salles)} trouvées")
    if len(ids) != len(set(ids)):
        erreurs.append("identifiants de salle dupliqués")
    if any(not identifiant.startswith("braavos-") for identifiant in ids if identifiant):
        erreurs.append("une adresse ne porte pas le préfixe braavos-")
    for salle in salles:
        for porte in salle.get("portes", []):
            if porte.get("vers") not in ids:
                erreurs.append(f"porte orpheline : {salle['id']} -> {porte.get('vers')}")
    par_id = {salle["id"]: salle for salle in salles}
    for changement in couches:
        salle = par_id.get(changement.get("salle_id"))
        if salle is None:
            erreurs.append(f"renommage sans salle : {changement.get('salle_id')}")
        elif salle["nom"] != changement.get("apres"):
            erreurs.append(
                f"nom courant divergent : {salle['id']} porte {salle['nom']!r}, "
                f"registre attend {changement.get('apres')!r}"
            )
    return erreurs


def rendre(salles: list[dict], couches: list[dict]) -> str:
    fortes = sum(couche(salle["nom"]) == "marque héritée forte" for salle in salles)
    lignes = [
        "# Palimpseste des murs de Braavos",
        "",
        "Source mesurée : `monde/braavos.interieurs.json`.",
        "",
        f"Braavos porte **{len(salles)} adresses intérieures** ; "
        f"**{fortes} noms courants** gardent une marque explicite de la couche de Peyredragon et "
        f"**{len(couches)} renommages** sont conservés avec leur provenance.",
        "La catégorie « fonction commune » ne prouve pas une origine différente : elle signifie seulement que le nom ne suffit pas à l'attribuer.",
        "",
        "| Adresse présente | Nom courant | Noms antérieurs conservés | Niveau | Portes | Lecture |",
        "|---|---|---|---:|---:|---|",
    ]
    for salle in sorted(salles, key=lambda item: item["id"]):
        lignes.append(
            "| `{id}` | {nom} | {anciens} | {niveau} | {portes} | {lecture} |".format(
                id=salle["id"],
                nom=salle["nom"].replace("|", "\\|"),
                anciens=", ".join(
                    changement["avant"] for changement in couches if changement["salle_id"] == salle["id"]
                ) or "—",
                niveau=salle.get("etage") or "principal",
                portes=len(salle.get("portes", [])),
                lecture=couche(salle["nom"]),
            )
        )
    lignes.extend(
        [
            "",
            "## Règle de prudence",
            "",
            "La marque héritée est attribuée seulement si le nom contient l'un des termes : "
            + ", ".join(f"`{mot}`" for mot in MARQUES)
            + ". Le témoignage de Nicolas sous la ref `vmti35qnkbyvy` établit l'héritage général ; "
            "le relevé mesure où cet héritage demeure lisible dans les noms, sans prétendre dater chaque mur.",
        ]
    )
    return "\n".join(lignes)


def fiche(salle: dict, couches: list[dict]) -> dict:
    histoire = [changement for changement in couches if changement["salle_id"] == salle["id"]]
    return {
        "adresse_presente": salle["id"],
        "nom_courant": salle["nom"],
        "renommages_conserves": histoire,
        "niveau": salle.get("etage") or "principal",
        "couvert": bool(salle.get("couvert")),
        "lecture": couche(salle["nom"]),
        "communique_avec": sorted(porte["vers"] for porte in salle.get("portes", [])),
        "prudence": "La lecture du nom ne date pas le mur et ne décide pas de son futur usage.",
    }


def inventaire(salles: list[dict], couches: list[dict]) -> dict:
    return {
        "schema": "palimpseste-braavos/v2",
        "source": str(SOURCE.relative_to(RACINE)).replace("\\", "/"),
        "ref_temoignage": "vmti35qnkbyvy",
        "mesure": {
            "salles": len(salles),
            "marques_heritees_fortes": sum(
                couche(salle["nom"]) == "marque héritée forte" for salle in salles
            ),
            "renommages_conserves": len(couches),
        },
        "salles": [fiche(salle, couches) for salle in sorted(salles, key=lambda item: item["id"])],
        "limite": "Le relevé décrit et conserve ; il ne rebaptise ni n'affecte les salles.",
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verifier", action="store_true")
    parser.add_argument("--salle", help="adresse exacte d'une salle à consulter")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()
    salles = charger()
    couches = charger_couches()
    erreurs = verifier(salles, couches)
    if args.verifier:
        print(json.dumps({"valide": not erreurs, "salles": len(salles), "erreurs": erreurs}, ensure_ascii=False))
        return 0 if not erreurs else 1
    if erreurs:
        raise SystemExit("; ".join(erreurs))
    if args.salle:
        trouvee = next((salle for salle in salles if salle["id"] == args.salle), None)
        if trouvee is None:
            print(json.dumps({"trouvee": False, "adresse": args.salle}, ensure_ascii=False))
            return 2
        print(json.dumps({"trouvee": True, **fiche(trouvee, couches)}, ensure_ascii=False, indent=2))
        return 0
    if args.format == "json":
        print(json.dumps(inventaire(salles, couches), ensure_ascii=False, indent=2))
        return 0
    print(rendre(salles, couches))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
