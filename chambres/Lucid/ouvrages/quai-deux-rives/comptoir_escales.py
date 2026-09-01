#!/usr/bin/env python3
"""Comptoir minimal des escales du Quai des Deux Rives."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


REGISTRE = Path(__file__).with_name("escales.json")
STATUTS = ("ANNONCEE", "A_QUAI", "REPARTIE")


def charger(chemin: Path) -> dict:
    try:
        registre = json.loads(chemin.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"registre illisible : {exc}") from exc
    if registre.get("lieu_id") != "braavos-quai":
        raise ValueError("ce registre ne concerne pas braavos-quai")
    if not isinstance(registre.get("escales"), list):
        raise ValueError("la liste des escales est absente")
    return registre


def sauver(chemin: Path, registre: dict) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    fd, temporaire = tempfile.mkstemp(
        prefix=chemin.name + ".", suffix=".tmp", dir=str(chemin.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as flux:
            json.dump(registre, flux, ensure_ascii=False, indent=2)
            flux.write("\n")
        os.replace(temporaire, chemin)
    except Exception:
        try:
            os.unlink(temporaire)
        except OSError:
            pass
        raise


def prochain_id(registre: dict) -> str:
    nombres = []
    for escale in registre["escales"]:
        identifiant = str(escale.get("id", ""))
        if identifiant.startswith("escale-") and identifiant[7:].isdigit():
            nombres.append(int(identifiant[7:]))
    return f"escale-{max(nombres, default=0) + 1:04d}"


def annoncer(registre: dict, args: argparse.Namespace) -> dict:
    escale = {
        "id": prochain_id(registre),
        "date": args.date,
        "navire": args.navire,
        "capitaine": args.capitaine,
        "provenance": args.provenance,
        "cargaison": args.cargaison,
        "statut": "ANNONCEE",
        "preuve": args.preuve,
    }
    registre["escales"].append(escale)
    return escale


def changer_statut(registre: dict, identifiant: str, statut: str, preuve: str) -> dict:
    for escale in registre["escales"]:
        if escale.get("id") != identifiant:
            continue
        attendu = {
            "A_QUAI": "ANNONCEE",
            "REPARTIE": "A_QUAI",
        }[statut]
        if escale.get("statut") != attendu:
            raise ValueError(
                f"{identifiant} est {escale.get('statut')}, transition attendue depuis {attendu}"
            )
        escale["statut"] = statut
        escale["preuve"] = preuve
        return escale
    raise ValueError(f"escale inconnue : {identifiant}")


def rendre(registre: dict, en_json: bool) -> str:
    if en_json:
        return json.dumps(registre, ensure_ascii=False, indent=2) + "\n"
    lignes = [f"{registre['nom']} — {len(registre['escales'])} escale(s)"]
    for e in registre["escales"]:
        lignes.append(
            f"{e['id']} | {e['statut']} | {e['navire']} | {e['capitaine']} | "
            f"{e['provenance']} | {e['cargaison']}"
        )
    return "\n".join(lignes) + "\n"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registre", type=Path, default=REGISTRE)
    sous = p.add_subparsers(dest="commande", required=True)

    consulter = sous.add_parser("consulter")
    consulter.add_argument("--json", action="store_true")

    annonce = sous.add_parser("annoncer")
    for nom in ("date", "navire", "capitaine", "provenance", "cargaison"):
        annonce.add_argument(f"--{nom}", required=True)
    annonce.add_argument(
        "--preuve",
        required=True,
        help="source de l'annonce ; une annonce sans source n'entre pas au registre",
    )

    accoster = sous.add_parser("accoster")
    accoster.add_argument("--id", required=True)
    accoster.add_argument("--preuve", required=True)

    repartir = sous.add_parser("repartir")
    repartir.add_argument("--id", required=True)
    repartir.add_argument("--preuve", required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        registre = charger(args.registre)
        if args.commande == "consulter":
            print(rendre(registre, args.json), end="")
            return 0
        if args.commande == "annoncer":
            resultat = annoncer(registre, args)
        elif args.commande == "accoster":
            resultat = changer_statut(registre, args.id, "A_QUAI", args.preuve)
        else:
            resultat = changer_statut(registre, args.id, "REPARTIE", args.preuve)
        sauver(args.registre, registre)
        print(json.dumps(resultat, ensure_ascii=False, indent=2))
        return 0
    except ValueError as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
