"""Reçus de réveil : validation et dépôt append-only dans le runtime local.

Le reçu décrit une cause servie et des suites matériellement observées. Il ne
contient ni score, ni verdict, ni intention attribuée à l'habitant.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


RACINE = Path(__file__).resolve().parents[2]
REGISTRE = RACINE / ".agents-runtime" / "reveils" / "recus.jsonl"
CHAMPS = {
    "schema", "cause", "rendu", "habitant", "session", "date_jeu",
    "ref", "suites", "inconnus",
}


class RecuInvalide(ValueError):
    pass


def _texte(objet, champ):
    valeur = objet.get(champ)
    if not isinstance(valeur, str) or not valeur.strip():
        raise RecuInvalide("%s doit être un texte non vide" % champ)


def valider(recu):
    if not isinstance(recu, dict):
        raise RecuInvalide("le reçu doit être un objet JSON")
    inconnus = set(recu) - CHAMPS
    if inconnus:
        raise RecuInvalide("champs inconnus : %s" % ", ".join(sorted(inconnus)))
    if recu.get("schema") != "recu-reveil/1":
        raise RecuInvalide("schema doit valoir recu-reveil/1")
    for champ in ("rendu", "habitant", "session", "date_jeu"):
        _texte(recu, champ)
    morceaux = recu["date_jeu"].split(".")
    if len(morceaux) != 3 or not all(p.isdigit() for p in morceaux):
        raise RecuInvalide("date_jeu doit suivre an.lune.jour")
    if "ref" in recu:
        _texte(recu, "ref")

    cause = recu.get("cause")
    if not isinstance(cause, dict) or set(cause) - {"type", "id", "adresse"}:
        raise RecuInvalide("cause doit contenir type, id et éventuellement adresse")
    if cause.get("type") not in {"amorce", "billet", "autre"}:
        raise RecuInvalide("type de cause inconnu")
    _texte(cause, "id")
    if "adresse" in cause:
        _texte(cause, "adresse")

    suites = recu.get("suites")
    if not isinstance(suites, dict) or set(suites) != {"observation", "elements"}:
        raise RecuInvalide("suites doit contenir exactement observation et elements")
    observation = suites["observation"]
    elements = suites["elements"]
    if not isinstance(elements, list):
        raise RecuInvalide("suites.elements doit être une liste")
    if observation == "aucune_sortie_visible":
        if elements:
            raise RecuInvalide("aucune sortie visible exclut tout élément")
    elif observation == "sorties_constatees":
        if not elements:
            raise RecuInvalide("une sortie constatée exige au moins un élément")
        for element in elements:
            if not isinstance(element, dict) or set(element) - {"type", "adresse", "constat"}:
                raise RecuInvalide("élément de suite invalide")
            if element.get("type") not in {"artefact", "parole"}:
                raise RecuInvalide("une suite est un artefact ou une parole")
            _texte(element, "adresse")
            if "constat" in element:
                _texte(element, "constat")
    else:
        raise RecuInvalide("observation de suites inconnue")

    if not isinstance(recu.get("inconnus"), list):
        raise RecuInvalide("inconnus doit être une liste")
    if any(not isinstance(x, str) or not x.strip() for x in recu["inconnus"]):
        raise RecuInvalide("chaque inconnu doit être un texte non vide")
    if len(recu["inconnus"]) != len(set(recu["inconnus"])):
        raise RecuInvalide("les inconnus doivent être uniques")
    return recu


def completer(recu):
    valider(recu)
    matiere = json.dumps(recu, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    complet = dict(recu)
    complet["id"] = "rr-" + hashlib.sha256(matiere).hexdigest()[:24]
    complet["enregistre_le"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return complet


def _lignes(chemin):
    if not chemin.exists():
        return []
    with chemin.open("r", encoding="utf-8") as flux:
        return [json.loads(ligne) for ligne in flux if ligne.strip()]


def deposer(recu, registre=REGISTRE):
    registre = Path(registre)
    complet = completer(recu)
    registre.parent.mkdir(parents=True, exist_ok=True)
    verrou = registre.with_suffix(registre.suffix + ".lock")
    for _ in range(100):
        try:
            fd = os.open(str(verrou), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            time.sleep(0.02)
    else:
        raise RuntimeError("registre occupé : %s" % registre)
    try:
        for ancien in _lignes(registre):
            if ancien.get("id") == complet["id"]:
                return ancien, False
        with registre.open("a", encoding="utf-8", newline="\n") as flux:
            flux.write(json.dumps(complet, ensure_ascii=False,
                                  sort_keys=True, separators=(",", ":")) + "\n")
            flux.flush()
            os.fsync(flux.fileno())
        return complet, True
    finally:
        try:
            verrou.unlink()
        except FileNotFoundError:
            pass

