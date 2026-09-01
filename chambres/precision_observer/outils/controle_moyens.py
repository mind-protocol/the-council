#!/usr/bin/env python3
"""Contrôle reproductible de cohérence entre les mains et le registre M110."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MAINS_PAR_DEFAUT = Path(
    "C:/Users/reyno/le-conseil2/etat/maisons/maison-serenissima/"
    "documents/mains.json"
)
REGISTRE_PAR_DEFAUT = Path(
    "C:/Users/reyno/le-conseil2/etat/maisons/maison-serenissima/"
    "documents/books/plan-moyens-serenissima.json"
)

LIBELLES = {
    "containers-declares": "containers déclarés",
    "modules-rattaches": "modules rattachés",
    "modules-orphelins": "modules orphelins",
    "liens-hors-porte": "liens hors porte",
    "dependances-remontantes": "dépendances remontantes",
    "commandes-bibliotheques": "commandes-bibliothèques",
}

MESURES_SONDE = ("modules-rattaches", "modules-orphelins", "modules-observes")


@dataclass(frozen=True)
class Comparaison:
    mesure: str
    mains: int | None
    registre: int | None
    statut: str

    def en_dict(self) -> dict[str, Any]:
        return {
            "mesure": self.mesure,
            "libelle": LIBELLES[self.mesure],
            "mains": self.mains,
            "registre": self.registre,
            "statut": self.statut,
        }


def charger(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"lecture impossible de {path}: {exc}") from exc


def mesures_des_mains(document: dict[str, Any]) -> tuple[dict[str, int], set[str]]:
    valeurs: dict[str, int] = {}
    dates: set[str] = set()
    for main in document.get("mains", []):
        if main.get("date_maj"):
            dates.add(str(main["date_maj"]))
        for mesure in main.get("mesure", []):
            identifiant = mesure.get("id")
            valeur = mesure.get("valeur")
            if identifiant in LIBELLES and isinstance(valeur, int):
                valeurs[identifiant] = valeur
    return valeurs, dates


def ligne_m110(document: dict[str, Any]) -> list[str]:
    for ligne in document.get("lignes", []):
        cellules = ligne.get("cellules", [])
        if cellules and re.search(r"\bM110\b", str(cellules[0])):
            return [str(cellule) for cellule in cellules]
    raise ValueError("ligne M110 absente du registre")


def extraire(registre: dict[str, Any]) -> tuple[dict[str, int], str | None]:
    cellules = ligne_m110(registre)
    texte = " ".join(cellules)
    motifs = {
        "modules-rattaches": r"(\d+)\s+fichiers rattachés",
        "modules-orphelins": r"(\d+)\s+orphelins",
        "liens-hors-porte": r"(\d+)\s+liens hors porte",
        "dependances-remontantes": r"(\d+)\s+remontées",
        "commandes-bibliotheques": r"(\d+)\s+commande-bibliothèque",
    }
    valeurs: dict[str, int] = {}
    for identifiant, motif in motifs.items():
        correspondance = re.search(motif, texte, flags=re.IGNORECASE)
        if correspondance:
            valeurs[identifiant] = int(correspondance.group(1))

    total = re.search(r"(\d+)\s+fichiers de code observés", texte)
    if total:
        valeurs["modules-observes"] = int(total.group(1))

    date = re.search(r"mesuré le\s+(\d+\.\d+\.\d+)", texte, re.IGNORECASE)
    return valeurs, date.group(1) if date else None


def compter_containers(registre: dict[str, Any]) -> int:
    compte = 0
    for ligne in registre.get("lignes", []):
        cellules = ligne.get("cellules", [])
        if len(cellules) > 1 and "container" in str(cellules[1]).lower():
            compte += 1
    return compte


def mesures_de_sonde(document: dict[str, Any]) -> tuple[dict[str, int], str | None, str]:
    if document.get("type") != "constat-sonde-architecture/1":
        raise ValueError("type de troisième pièce attendu : constat-sonde-architecture/1")
    provenance = str(document.get("provenance", "")).strip()
    if not provenance:
        raise ValueError("provenance absente de la troisième pièce")
    mesures = document.get("mesures")
    if not isinstance(mesures, dict):
        raise ValueError("mesures absentes de la troisième pièce")
    valeurs = {
        identifiant: valeur
        for identifiant in MESURES_SONDE
        if isinstance((valeur := mesures.get(identifiant)), int)
    }
    return valeurs, document.get("date_constat"), provenance


def avec_total_modules(valeurs: dict[str, int]) -> dict[str, int]:
    resultat = dict(valeurs)
    rattaches = resultat.get("modules-rattaches")
    orphelins = resultat.get("modules-orphelins")
    if rattaches is not None and orphelins is not None:
        resultat.setdefault("modules-observes", rattaches + orphelins)
    return resultat


def comparer_paire(
    gauche_nom: str,
    gauche: dict[str, int],
    droite_nom: str,
    droite: dict[str, int],
    mesures: tuple[str, ...],
) -> dict[str, Any]:
    comparaisons = []
    for mesure in mesures:
        valeur_gauche = gauche.get(mesure)
        valeur_droite = droite.get(mesure)
        if valeur_gauche is None or valeur_droite is None:
            statut = "INCONNU"
        elif valeur_gauche == valeur_droite:
            statut = "ACCORD"
        else:
            statut = "ECART"
        comparaisons.append({
            "mesure": mesure,
            gauche_nom: valeur_gauche,
            droite_nom: valeur_droite,
            "statut": statut,
        })
    statuts = [comparaison["statut"] for comparaison in comparaisons]
    if "ECART" in statuts:
        verdict = "A_CONTROLER"
    elif statuts and all(statut == "ACCORD" for statut in statuts):
        verdict = "COHERENT"
    else:
        verdict = "INCOMPLET"
    return {
        "sources": [gauche_nom, droite_nom],
        "verdict": verdict,
        "comparaisons": comparaisons,
    }


def controler(
    mains: dict[str, Any],
    registre: dict[str, Any],
    sonde: dict[str, Any] | None = None,
) -> dict[str, Any]:
    valeurs_mains, dates_mains = mesures_des_mains(mains)
    valeurs_registre, date_registre = extraire(registre)
    valeurs_registre["containers-declares"] = compter_containers(registre)

    comparaisons: list[Comparaison] = []
    for identifiant in LIBELLES:
        gauche = valeurs_mains.get(identifiant)
        droite = valeurs_registre.get(identifiant)
        if gauche is None or droite is None:
            statut = "INCONNU"
        elif gauche == droite:
            statut = "ACCORD"
        else:
            statut = "ECART"
        comparaisons.append(Comparaison(identifiant, gauche, droite, statut))

    attaches = valeurs_mains.get("modules-rattaches")
    orphelins = valeurs_mains.get("modules-orphelins")
    observes = valeurs_registre.get("modules-observes")
    somme_modules = attaches + orphelins if attaches is not None and orphelins is not None else None
    total_statut = (
        "ACCORD"
        if somme_modules is not None and observes is not None and somme_modules == observes
        else "ECART" if somme_modules is not None and observes is not None
        else "INCONNU"
    )
    dates_statut = (
        "ACCORD"
        if len(dates_mains) == 1 and date_registre in dates_mains
        else "ECART" if dates_mains and date_registre
        else "INCONNU"
    )

    valeurs_mains_etendues = avec_total_modules(valeurs_mains)
    valeurs_registre_etendues = avec_total_modules(valeurs_registre)
    paires = {
        "mains_registre": comparer_paire(
            "mains",
            valeurs_mains_etendues,
            "registre",
            valeurs_registre_etendues,
            tuple(LIBELLES) + ("modules-observes",),
        )
    }
    sonde_meta = None
    if sonde is not None:
        valeurs_sonde, date_sonde, provenance_sonde = mesures_de_sonde(sonde)
        paires["mains_sonde"] = comparer_paire(
            "mains", valeurs_mains_etendues, "sonde", valeurs_sonde, MESURES_SONDE
        )
        paires["registre_sonde"] = comparer_paire(
            "registre", valeurs_registre_etendues, "sonde", valeurs_sonde, MESURES_SONDE
        )
        sonde_meta = {
            "date_constat": date_sonde,
            "provenance": provenance_sonde,
            "mesures": valeurs_sonde,
        }

    verdicts_paires = [paire["verdict"] for paire in paires.values()]
    verdict = (
        "COHERENT"
        if all(verdict_paire == "COHERENT" for verdict_paire in verdicts_paires)
        and dates_statut == "ACCORD"
        else "A_CONTROLER"
    )
    resultat = {
        "verdict": verdict,
        "verdicts_paires": paires,
        "comparaisons": [c.en_dict() for c in comparaisons],
        "controle_total_modules": {
            "rattaches_plus_orphelins": somme_modules,
            "observes_registre": observes,
            "statut": total_statut,
        },
        "controle_dates": {
            "dates_mains": sorted(dates_mains),
            "date_registre": date_registre,
            "statut": dates_statut,
        },
        "portee": (
            "Cohérence documentaire seulement : ce contrôle ne prouve ni le "
            "fonctionnement du code ni la visibilité de ses sorties."
        ),
    }
    if sonde_meta is not None:
        resultat["troisieme_piece"] = sonde_meta
    return resultat


def rendre_markdown(resultat: dict[str, Any]) -> str:
    lignes = [
        "# Contrôle de cohérence des moyens",
        "",
        f"Verdict : **{resultat['verdict']}**",
        "",
        "| Mesure | Mains | Registre | Statut |",
        "|---|---:|---:|---|",
    ]
    for comparaison in resultat["comparaisons"]:
        lignes.append(
            f"| {comparaison['libelle']} | {comparaison['mains']} | "
            f"{comparaison['registre']} | {comparaison['statut']} |"
        )
    total = resultat["controle_total_modules"]
    dates = resultat["controle_dates"]
    lignes.extend(
        [
            "",
            f"Total modules : {total['rattaches_plus_orphelins']} calculés, "
            f"{total['observes_registre']} annoncés — **{total['statut']}**.",
            f"Dates : mains {dates['dates_mains']}, registre {dates['date_registre']} "
            f"— **{dates['statut']}**.",
            "",
            f"Limite : {resultat['portee']}",
            "",
        ]
    )
    if "troisieme_piece" in resultat:
        lignes.extend(["## Verdicts par paire", ""])
        for nom, paire in resultat["verdicts_paires"].items():
            lignes.append(f"- `{nom}` : **{paire['verdict']}**")
            for comparaison in paire["comparaisons"]:
                sources = paire["sources"]
                lignes.append(
                    f"  - `{comparaison['mesure']}` : "
                    f"{sources[0]}={comparaison[sources[0]]}, "
                    f"{sources[1]}={comparaison[sources[1]]} — {comparaison['statut']}"
                )
        lignes.extend(
            [
                "",
                f"Provenance de la troisième pièce : {resultat['troisieme_piece']['provenance']}",
                "",
            ]
        )
    return "\n".join(lignes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mains", type=Path, default=MAINS_PAR_DEFAUT)
    parser.add_argument("--registre", type=Path, default=REGISTRE_PAR_DEFAUT)
    parser.add_argument(
        "--sonde",
        type=Path,
        help="troisième pièce normalisée, avec provenance obligatoire",
    )
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--sortie", type=Path, help="écrit aussi le résultat à cette adresse")
    args = parser.parse_args()

    try:
        resultat = controler(
            charger(args.mains),
            charger(args.registre),
            charger(args.sonde) if args.sonde else None,
        )
    except ValueError as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 2

    contenu = (
        json.dumps(resultat, ensure_ascii=False, indent=2) + "\n"
        if args.format == "json"
        else rendre_markdown(resultat)
    )
    print(contenu, end="")
    if args.sortie:
        args.sortie.parent.mkdir(parents=True, exist_ok=True)
        args.sortie.write_text(contenu, encoding="utf-8")
    return 0 if resultat["verdict"] == "COHERENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
