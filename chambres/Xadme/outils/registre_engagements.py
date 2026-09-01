#!/usr/bin/env python3
"""Petit registre append-only pour engagements civiques.

Chaque ligne est un document JSON scelle par le hash de la ligne precedente.
Une revision ne remplace donc jamais silencieusement une proposition.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "engagement-civique/1"
CHAMPS_EXPOSES = ("objet", "risque", "effet_civique", "equilibre")
CHAMPS_CONTRAT = ("parties",) + CHAMPS_EXPOSES
CHAMPS_PUBLICS = (
    "type",
    "engagement_id",
    "date",
    "parties",
    "objet",
    "risque",
    "effet_civique",
    "equilibre",
)


def canonique(document: dict[str, Any]) -> bytes:
    return json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def empreinte(document: dict[str, Any]) -> str:
    sans_sceau = {cle: valeur for cle, valeur in document.items() if cle != "sceau"}
    return hashlib.sha256(canonique(sans_sceau)).hexdigest()


def empreinte_contenu(document: dict[str, Any]) -> str:
    """Empreinte stable des termes, sans date ni métadonnée de chaîne."""
    contenu = {champ: document.get(champ) for champ in CHAMPS_CONTRAT}
    return hashlib.sha256(canonique(contenu)).hexdigest()


def diagnostic_doublon(existant: dict[str, Any], soumis: dict[str, Any]) -> str:
    """Distingue répétition et altération sans reproduire les valeurs."""
    empreinte_existante = empreinte_contenu(existant)
    empreinte_soumise = empreinte_contenu(soumis)
    if empreinte_existante == empreinte_soumise:
        return f"DOUBLON_EXACT empreinte_contenu={empreinte_existante[:12]}"
    champs = [champ for champ in CHAMPS_CONTRAT if existant.get(champ) != soumis.get(champ)]
    return (
        f"ALTERATION champs={','.join(champs)} "
        f"empreinte_existante={empreinte_existante[:12]} "
        f"empreinte_soumise={empreinte_soumise[:12]}"
    )


def lire_registre(chemin: Path) -> list[dict[str, Any]]:
    if not chemin.exists():
        return []
    documents: list[dict[str, Any]] = []
    for numero, ligne in enumerate(chemin.read_text(encoding="utf-8").splitlines(), 1):
        if not ligne.strip():
            continue
        try:
            document = json.loads(ligne)
        except json.JSONDecodeError as exc:
            raise ValueError(f"ligne {numero}: JSON invalide ({exc.msg})") from exc
        if not isinstance(document, dict):
            raise ValueError(f"ligne {numero}: un document JSON est attendu")
        documents.append(document)
    return documents


def valider_document(document: dict[str, Any], numero: int) -> list[str]:
    erreurs: list[str] = []
    prefixe = f"ligne {numero}"
    if document.get("version") != VERSION:
        erreurs.append(f"{prefixe}: version absente ou inconnue")
    if document.get("type") not in {"proposition", "revision"}:
        erreurs.append(f"{prefixe}: type attendu: proposition ou revision")
    if not isinstance(document.get("engagement_id"), str) or not document["engagement_id"].strip():
        erreurs.append(f"{prefixe}: engagement_id obligatoire")
    parties = document.get("parties")
    if not isinstance(parties, list) or len(parties) < 2 or any(
        not isinstance(partie, str) or not partie.strip() for partie in parties
    ):
        erreurs.append(f"{prefixe}: au moins deux parties nommees sont obligatoires")
    for champ in CHAMPS_EXPOSES:
        if not isinstance(document.get(champ), str) or not document[champ].strip():
            erreurs.append(f"{prefixe}: {champ} obligatoire")
    if document.get("type") == "revision":
        if not isinstance(document.get("raison_revision"), str) or not document["raison_revision"].strip():
            erreurs.append(f"{prefixe}: raison_revision obligatoire pour une revision")
        if not isinstance(document.get("revision_de"), str) or not document["revision_de"].strip():
            erreurs.append(f"{prefixe}: revision_de obligatoire pour une revision")
    return erreurs


def verifier(chemin: Path) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        documents = lire_registre(chemin)
    except ValueError as exc:
        return [], [str(exc)]
    erreurs: list[str] = []
    sceau_precedent: str | None = None
    derniers: dict[str, str] = {}
    for numero, document in enumerate(documents, 1):
        erreurs.extend(valider_document(document, numero))
        if document.get("precedent") != sceau_precedent:
            erreurs.append(f"ligne {numero}: chaine rompue")
        sceau_calcule = empreinte(document)
        if document.get("sceau") != sceau_calcule:
            erreurs.append(f"ligne {numero}: sceau invalide")
        identifiant = document.get("engagement_id")
        if isinstance(identifiant, str):
            if document.get("type") == "proposition" and identifiant in derniers:
                erreurs.append(f"ligne {numero}: engagement_id deja propose")
            if document.get("type") == "revision" and document.get("revision_de") != derniers.get(identifiant):
                erreurs.append(f"ligne {numero}: la revision ne part pas du dernier etat connu")
            derniers[identifiant] = sceau_calcule
        sceau_precedent = sceau_calcule
    return documents, erreurs


def ajouter(chemin: Path, document: dict[str, Any]) -> dict[str, Any]:
    documents, erreurs = verifier(chemin)
    if erreurs:
        raise ValueError("registre refuse: " + "; ".join(erreurs))
    erreurs_nouvelles = valider_document(document, len(documents) + 1)
    derniers = {
        existant["engagement_id"]: existant["sceau"]
        for existant in documents
        if isinstance(existant.get("engagement_id"), str)
    }
    identifiant = document.get("engagement_id")
    if document.get("type") == "proposition" and identifiant in derniers:
        dernier_document = next(
            existant
            for existant in reversed(documents)
            if existant.get("engagement_id") == identifiant
        )
        erreurs_nouvelles.append(
            "engagement_id deja propose: "
            + diagnostic_doublon(dernier_document, document)
        )
    if document.get("type") == "revision" and document.get("revision_de") != derniers.get(identifiant):
        erreurs_nouvelles.append("la revision ne part pas du dernier etat connu")
    if erreurs_nouvelles:
        raise ValueError("document refuse: " + "; ".join(erreurs_nouvelles))
    document["precedent"] = documents[-1]["sceau"] if documents else None
    document["sceau"] = empreinte(document)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("a", encoding="utf-8", newline="\n") as registre:
        registre.write(json.dumps(document, ensure_ascii=False, sort_keys=True) + "\n")
    return document


def vue_publique(document: dict[str, Any], numero: int) -> dict[str, Any]:
    """Termes déclarés publics et liens de chaîne, sans verdict sur leur valeur."""
    vue = {"numero": numero}
    vue.update({champ: document.get(champ) for champ in CHAMPS_PUBLICS})
    if document.get("type") == "revision":
        vue["raison_revision"] = document.get("raison_revision")
        vue["revision_de"] = document.get("revision_de")
    vue["precedent"] = document.get("precedent")
    vue["sceau"] = document.get("sceau")
    return vue


def rendre_consultation_markdown(vues: list[dict[str, Any]]) -> str:
    lignes = [
        "# Consultation des engagements",
        "",
        "Lecture des termes déclarés publics. Aucun jugement sur leur justice ou leur exécution.",
    ]
    for vue in vues:
        lignes.extend(
            [
                "",
                f"## {vue['numero']}. {vue['engagement_id']} — {vue['type']}",
                "",
                f"- Date : {vue['date']}",
                f"- Parties : {', '.join(vue['parties'])}",
                f"- Objet : {vue['objet']}",
                f"- Risque : {vue['risque']}",
                f"- Effet civique : {vue['effet_civique']}",
                f"- Équilibre : {vue['equilibre']}",
            ]
        )
        if vue["type"] == "revision":
            lignes.extend(
                [
                    f"- Raison de révision : {vue['raison_revision']}",
                    f"- Révision de : `{vue['revision_de']}`",
                ]
            )
        lignes.extend(
            [
                f"- Précédent : `{vue['precedent'] or 'genese'}`",
                f"- Sceau : `{vue['sceau']}`",
            ]
        )
    return "\n".join(lignes) + "\n"


def consulter(chemin: Path, format_: str = "markdown") -> str:
    documents, erreurs = verifier(chemin)
    if erreurs:
        raise ValueError("registre invalide: " + "; ".join(erreurs))
    vues = [vue_publique(document, numero) for numero, document in enumerate(documents, 1)]
    if format_ == "json":
        return json.dumps(vues, ensure_ascii=False, indent=2) + "\n"
    return rendre_consultation_markdown(vues)


def base_depuis_args(args: argparse.Namespace) -> dict[str, Any]:
    parties = [partie.strip() for partie in args.parties.split(",") if partie.strip()]
    return {
        "version": VERSION,
        "type": args.commande,
        "engagement_id": args.id,
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "parties": parties,
        "objet": args.objet,
        "risque": args.risque,
        "effet_civique": args.effet_civique,
        "equilibre": args.equilibre,
    }


def construire_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tenir un registre d'engagements civiques scelle")
    sous = parser.add_subparsers(dest="commande", required=True)

    def commun(nom: str) -> argparse.ArgumentParser:
        commande = sous.add_parser(nom)
        commande.add_argument("registre", type=Path)
        commande.add_argument("--id", required=True)
        commande.add_argument("--parties", required=True, help="noms separes par des virgules")
        commande.add_argument("--objet", required=True)
        commande.add_argument("--risque", required=True)
        commande.add_argument("--effet-civique", required=True)
        commande.add_argument("--equilibre", required=True)
        return commande

    commun("proposition")
    revision = commun("revision")
    revision.add_argument("--raison", required=True)
    controle = sous.add_parser("verifier")
    controle.add_argument("registre", type=Path)
    lecture = sous.add_parser("consulter")
    lecture.add_argument("registre", type=Path)
    lecture.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser


def main() -> int:
    args = construire_cli().parse_args()
    if args.commande == "verifier":
        documents, erreurs = verifier(args.registre)
        if erreurs:
            for erreur in erreurs:
                print(f"ECHEC {erreur}", file=sys.stderr)
            return 1
        print(f"VALIDE {len(documents)} document(s), chaine intacte")
        return 0
    if args.commande == "consulter":
        try:
            contenu = consulter(args.registre, args.format)
        except ValueError as exc:
            print(f"ECHEC {exc}", file=sys.stderr)
            return 1
        print(contenu, end="")
        return 0

    document = base_depuis_args(args)
    documents, erreurs = verifier(args.registre)
    if erreurs:
        print("ECHEC " + "; ".join(erreurs), file=sys.stderr)
        return 1
    if args.commande == "revision":
        precedents = [d for d in documents if d.get("engagement_id") == args.id]
        if not precedents:
            print("ECHEC aucun engagement de cet id a reviser", file=sys.stderr)
            return 1
        document["revision_de"] = precedents[-1]["sceau"]
        document["raison_revision"] = args.raison
    try:
        inscrit = ajouter(args.registre, document)
    except ValueError as exc:
        print(f"ECHEC {exc}", file=sys.stderr)
        return 1
    print(f"INSCRIT {inscrit['engagement_id']} {inscrit['sceau']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
