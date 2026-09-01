#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Relire les reçus de réveil sans attribuer d'intention à l'habitant.

La commande est en lecture seule. Elle sépare strictement la cause servie, les
faits que le reçu porte et les inconnus que le reçu déclare. L'ordre temporel
des pièces n'est jamais présenté comme une causalité.
"""

import argparse
import datetime
import json
import os
import re
import sys


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMA_PAR_DEFAUT = os.path.join(
    RACINE,
    "etat",
    "maisons",
    "maison-serenissima",
    "documents",
    "recus-reveils.schema.json",
)
REGISTRE_PAR_DEFAUT = os.path.join(
    RACINE, ".agents-runtime", "reveils", "recus.jsonl"
)


class ContratInvalide(Exception):
    pass


def charger_json(chemin):
    try:
        with open(chemin, encoding="utf-8") as fichier:
            return json.load(fichier)
    except (OSError, json.JSONDecodeError) as exc:
        raise ContratInvalide("impossible de lire %s : %s" % (chemin, exc)) from exc


def lire_registre(chemin):
    recus = []
    try:
        with open(chemin, encoding="utf-8") as fichier:
            for numero, ligne in enumerate(fichier, 1):
                if not ligne.strip():
                    continue
                try:
                    recus.append(json.loads(ligne))
                except json.JSONDecodeError as exc:
                    raise ContratInvalide(
                        "%s:%d n'est pas un reçu JSON lisible" % (chemin, numero)
                    ) from exc
    except OSError as exc:
        raise ContratInvalide("impossible de lire %s : %s" % (chemin, exc)) from exc
    return recus


def _exiger(condition, message):
    if not condition:
        raise ContratInvalide(message)


def _champs_permis(objet, permis, nom):
    surplus = sorted(set(objet) - set(permis))
    _exiger(not surplus, "%s porte des champs hors schéma : %s" %
             (nom, ", ".join(surplus)))


def valider_recu(recu, schema):
    """Appliquer les clauses structurelles utiles du schéma recu-reveil/1."""
    _exiger(isinstance(recu, dict), "le reçu n'est pas un objet")
    requis = schema.get("required", [])
    manquants = [champ for champ in requis if champ not in recu]
    _exiger(not manquants, "champs absents : %s" % ", ".join(manquants))

    if schema.get("additionalProperties") is False:
        permis = set(schema.get("properties", {}))
        inconnus = sorted(set(recu) - permis)
        _exiger(not inconnus, "champs hors schéma : %s" % ", ".join(inconnus))

    _exiger(recu.get("schema") == "recu-reveil/1", "version de reçu inconnue")
    _exiger(isinstance(recu.get("id"), str) and
             re.fullmatch(r"rr-[0-9a-f]{24}", recu["id"]),
             "identifiant de reçu invalide")

    cause = recu.get("cause")
    _exiger(isinstance(cause, dict), "cause absente ou invalide")
    _champs_permis(cause, {"type", "id", "adresse"}, "cause")
    _exiger(cause.get("type") in {"amorce", "billet", "autre"},
             "type de cause inconnu")
    _exiger(isinstance(cause.get("id"), str) and bool(cause["id"]),
             "identifiant de cause absent")
    _exiger(isinstance(recu.get("rendu"), str) and recu["rendu"],
             "rendu absent ou invalide")

    for champ in ("habitant", "session", "date_jeu", "enregistre_le"):
        _exiger(isinstance(recu.get(champ), str) and bool(recu[champ]),
                 "%s absent ou invalide" % champ)
    _exiger(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", recu["date_jeu"]),
             "date_jeu hors schéma")
    try:
        datetime.datetime.fromisoformat(recu["enregistre_le"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContratInvalide("enregistre_le n'est pas une date-heure") from exc
    if "ref" in recu:
        _exiger(isinstance(recu["ref"], str) and recu["ref"],
                 "ref vide ou invalide")

    suites = recu.get("suites")
    _exiger(isinstance(suites, dict), "suites absentes ou invalides")
    _champs_permis(suites, {"observation", "elements"}, "suites")
    _exiger(set(suites) == {"observation", "elements"},
             "suites doit porter observation et elements")
    observation = suites.get("observation")
    elements = suites.get("elements")
    _exiger(observation in {"sorties_constatees", "aucune_sortie_visible"},
             "observation de suites inconnue")
    _exiger(isinstance(elements, list), "liste des suites absente")
    if observation == "aucune_sortie_visible":
        _exiger(not elements, "aucune_sortie_visible exige une liste vide")
    else:
        _exiger(bool(elements), "sorties_constatees exige au moins une pièce")
        for position, element in enumerate(elements, 1):
            _exiger(isinstance(element, dict), "suite %d invalide" % position)
            _champs_permis(element, {"type", "adresse", "constat"},
                            "suite %d" % position)
            _exiger(element.get("type") in {"artefact", "parole"},
                     "type de suite %d inconnu" % position)
            _exiger(isinstance(element.get("adresse"), str) and element["adresse"],
                     "adresse de suite %d absente" % position)
            if "constat" in element:
                _exiger(isinstance(element["constat"], str) and element["constat"],
                         "constat de suite %d vide" % position)

    _exiger(isinstance(recu.get("inconnus"), list), "inconnus doit être une liste")
    _exiger(all(isinstance(item, str) and item for item in recu["inconnus"]),
             "chaque inconnu doit être un texte non vide")
    _exiger(len(recu["inconnus"]) == len(set(recu["inconnus"])),
             "les inconnus doivent être uniques")


def relire(recu, source):
    cause = {
        "type": recu["cause"]["type"],
        "id": recu["cause"]["id"],
        "rendu": recu["rendu"],
    }
    if "adresse" in recu["cause"]:
        cause["adresse"] = recu["cause"]["adresse"]

    faits = {
        "habitant": recu["habitant"],
        "session": recu["session"],
        "date_jeu": recu["date_jeu"],
        "enregistre_le": recu["enregistre_le"],
        "observation": recu["suites"]["observation"],
        "elements": recu["suites"]["elements"],
    }
    if "ref" in recu:
        faits["ref"] = recu["ref"]

    return {
        "schema": "relecture-reveil/1",
        "recu_id": recu["id"],
        "source": source,
        "cause_servie": cause,
        "faits_observes": faits,
        "inconnus": list(recu["inconnus"]),
        "limite": (
            "Le rapport restitue les pièces du reçu ; il ne déduit ni intention "
            "ni relation causale entre la cause et les suites."
        ),
    }


def rendre_markdown(rapports):
    blocs = ["# Relecture factuelle des réveils", ""]
    for rapport in rapports:
        cause = rapport["cause_servie"]
        faits = rapport["faits_observes"]
        blocs.extend([
            "## Reçu `%s`" % rapport["recu_id"],
            "",
            "Source : `%s`" % rapport["source"],
            "",
            "### Cause servie",
            "",
            "- Type : `%s`" % cause["type"],
            "- Identifiant : `%s`" % cause["id"],
        ])
        if cause.get("adresse"):
            blocs.append("- Adresse : `%s`" % cause["adresse"])
        blocs.extend(["- Rendu : %s" % cause["rendu"], "", "### Faits observés", ""])
        blocs.extend([
            "- Habitant : `%s`" % faits["habitant"],
            "- Session : `%s`" % faits["session"],
            "- Date de jeu : `%s`" % faits["date_jeu"],
            "- Enregistré le : `%s`" % faits["enregistre_le"],
        ])
        if faits.get("ref"):
            blocs.append("- Ref : `%s`" % faits["ref"])
        if faits["observation"] == "aucune_sortie_visible":
            blocs.append("- Suites : aucune sortie visible constatée.")
        else:
            blocs.append("- Suites matériellement constatées :")
            for element in faits["elements"]:
                texte = "  - `%s` — `%s`" % (element["type"], element["adresse"])
                if element.get("constat"):
                    texte += " — %s" % element["constat"]
                blocs.append(texte)
        blocs.extend(["", "### Inconnus", ""])
        if rapport["inconnus"]:
            blocs.extend("- %s" % item for item in rapport["inconnus"])
        else:
            blocs.append("- Aucun inconnu n'est déclaré dans ce reçu.")
        blocs.extend(["", "> %s" % rapport["limite"], ""])
    return "\n".join(blocs).rstrip() + "\n"


def arguments(argv=None):
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--registre", default=REGISTRE_PAR_DEFAUT)
    parseur.add_argument("--schema", default=SCHEMA_PAR_DEFAUT)
    parseur.add_argument("--id", action="append", dest="identifiants",
                         help="reçu à relire ; répétable, tous si absent")
    parseur.add_argument("--json", action="store_true", dest="en_json")
    parseur.add_argument("--sortie", help="écrire aussi le rapport à cette adresse")
    return parseur.parse_args(argv)


def main(argv=None):
    opts = arguments(argv)
    try:
        schema = charger_json(opts.schema)
        recus = lire_registre(opts.registre)
        if opts.identifiants:
            demandes = set(opts.identifiants)
            recus = [recu for recu in recus if recu.get("id") in demandes]
            trouves = {recu.get("id") for recu in recus}
            absents = sorted(demandes - trouves)
            _exiger(not absents, "reçus introuvables : %s" % ", ".join(absents))
        source = os.path.relpath(opts.registre, RACINE).replace("\\", "/")
        rapports = []
        for recu in recus:
            valider_recu(recu, schema)
            rapports.append(relire(recu, source))
        _exiger(bool(rapports), "aucun reçu à relire")
        rendu = (json.dumps(rapports, ensure_ascii=False, indent=2) + "\n"
                 if opts.en_json else rendre_markdown(rapports))
        if opts.sortie:
            with open(opts.sortie, "w", encoding="utf-8", newline="\n") as fichier:
                fichier.write(rendu)
        sys.stdout.write(rendu)
        return 0
    except ContratInvalide as exc:
        print("contrat invalide : %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("écriture impossible : %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
