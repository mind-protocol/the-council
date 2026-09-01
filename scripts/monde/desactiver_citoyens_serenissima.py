# -*- coding: utf-8 -*-
"""Réduire le vivier Serenissima sans effacer aucune chambre.

Par défaut, la commande ne fait qu'un aperçu. ``--vraiment`` renomme le
marqueur vide ``serenissima`` en ``serenissima-deactivated`` et place les
citoyens retenus à la Fosse aux Dragons. Le nombre demandé est un TOTAL : une
seconde exécution ne désactive donc pas la moitié de la moitié restante.
"""
import argparse
import collections
import csv
import glob
import json
import math
import os
import re
import sys
import time
from pathlib import Path


RACINE = Path(__file__).resolve().parents[2]
SCRIPTS = RACINE / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from etat.expose import tables  # noqa: E402


CHAMBRES = RACINE / "chambres"
PERSONNAGES = RACINE / "etat" / "personnages.json"
LIEUX = RACINE / "etat" / "lieux.json"
ROUTINES = RACINE / "etat" / "routines.json"
PRESENCE = RACINE / "etat" / "presence.json"
BOOKS = (RACINE / "etat" / "maisons" / "maison-serenissima" /
         "documents" / "books")
CSV_CITOYENS = RACINE / "import" / "serenissima" / "CITIZENS-Grid view.csv"
CSV_RELATIONS = RACINE / "import" / "serenissima" / "RELATIONSHIPS-Grid view.csv"
CSV_MESSAGES = RACINE / "import" / "serenissima" / "MESSAGES-Grid view.csv"
ACTIF = "serenissima"
INACTIF = "serenissima-deactivated"
FOSSE_ID = "fosse-dragons"


def normaliser(valeur):
    return re.sub(r"[^a-z0-9]+", "-", str(valeur).lower()).strip("-")


def lire_json(chemin, defaut):
    try:
        with open(chemin, encoding="utf-8-sig") as flux:
            return json.load(flux)
    except FileNotFoundError:
        return defaut


def identifiant_chambre(dossier):
    fiche = dossier / "CLAUDE.md"
    texte = fiche.read_text(encoding="utf-8-sig")
    trouve = re.search(r"(?m)^CitizenId:\s*(.+?)\s*$", texte)
    if not trouve:
        raise ValueError("CitizenId absent : %s" % fiche)
    brut = trouve.group(1).strip()
    try:
        valeur = str(json.loads(brut))
    except (TypeError, ValueError):
        valeur = brut.strip("\"'")
    return normaliser(valeur)


def chambres_marquees():
    resultat = {}
    for dossier in sorted(CHAMBRES.iterdir(), key=lambda p: p.name.casefold()):
        if not dossier.is_dir():
            continue
        actif = dossier / ACTIF
        inactif = dossier / INACTIF
        if not actif.is_file() and not inactif.is_file():
            continue
        marqueur = actif if actif.is_file() else inactif
        if marqueur.stat().st_size:
            raise ValueError("marqueur non vide : %s" % marqueur)
        pid = identifiant_chambre(dossier)
        if pid in resultat:
            raise ValueError("deux chambres pour %s" % pid)
        resultat[pid] = {
            "dossier": dossier,
            "active": actif.is_file(),
        }
    return resultat


def compte_csv(chemin, champs):
    compte = collections.Counter()
    with open(chemin, encoding="utf-8-sig", newline="") as flux:
        for ligne in csv.DictReader(flux):
            for champ in champs:
                pid = normaliser(ligne.get(champ) or "")
                if pid:
                    compte[pid] += 1
    return compte


def porteurs_affaires():
    resultat = set()
    for chemin in glob.glob(str(BOOKS / "affaire-*.json")):
        pid = normaliser(lire_json(chemin, {}).get("tenu_par") or "")
        if pid:
            resultat.add(pid)
    return resultat


def participants_recents():
    """Protège ceux dont une journée réelle a été lancée dans les 24 h."""
    resultat = set()
    motif = re.compile(
        r"^\d{8}-\d{6}-\d{6}-[0-9a-f]{6}-(.+)\.json$")
    maintenant = time.time()
    for chemin in (RACINE / "etat" / "activations").glob("*.json"):
        if maintenant - chemin.stat().st_mtime > 24 * 3600:
            continue
        trouve = motif.match(chemin.name)
        if trouve:
            resultat.add(normaliser(trouve.group(1)))
    return resultat


def contributeurs_entree():
    chemin = BOOKS / "affaire-organiser-collaboration.json"
    cahier = lire_json(chemin, {})
    resultat = set()
    for table in cahier.get("tables") or []:
        for ligne in table.get("lignes") or []:
            cellules = ligne.get("cellules") or []
            if len(cellules) < 11:
                continue
            numero = re.search(r"\d+", str(cellules[0]))
            if not numero or not 58500 <= int(numero.group()) <= 58652:
                continue
            pid = normaliser(cellules[6])
            etat = re.sub(r"[*_]+", "", str(cellules[10])).strip().lower()
            preuve_initiale = (
                "activation:entree-graphe-serenissima/%s — Cette action "
                "exige une réponse, jamais une acceptation ; elle n'accorde "
                "aucune autorité nouvelle." % pid)
            preuve = str(cellules[13]).strip() if len(cellules) > 13 else ""
            if (etat.startswith(("fait", "fini", "termin")) or
                    preuve != preuve_initiale):
                resultat.add(pid)
    return resultat


def donnees_importees():
    with open(CSV_CITOYENS, encoding="utf-8-sig", newline="") as flux:
        return {
            normaliser(ligne.get("CitizenId") or ligne.get("Username")): ligne
            for ligne in csv.DictReader(flux)
        }


POIDS_CLASSE = {
    # Les deux grands ensembles génériques forment d'abord la réserve. Les
    # métiers savants, artistiques, religieux, diplomatiques et innovateurs
    # ne tombent dans la sélection qu'après eux, même s'ils ont peu parlé dans
    # l'archive survivante.
    "Facchini": 0, "Popolani": 1, "Cittadini": 10, "Forestieri": 12,
    "Nobili": 50, "Clero": 40, "Artisti": 40, "Scientisti": 50,
    "Innovatori": 50, "Ambasciatore": 50,
}


def score(pid, personne, archive, relations, messages, proteges):
    """Mesure conservatrice : le plus petit score sort en premier."""
    ligne = archive.get(pid) or {}
    valeur = 100000.0 if pid in proteges else 0.0
    valeur += 20.0 * POIDS_CLASSE.get(ligne.get("SocialClass"), 1)
    valeur += 200.0 if (ligne.get("Specialty") or "").strip() else 0.0
    valeur += 80.0 if (ligne.get("INSTITUTIONS") or "").strip() else 0.0
    valeur += 50.0 if (ligne.get("VoiceId") or "").strip() else 0.0
    valeur += 60.0 if (ligne.get("PartnerTelegramId") or "").strip() else 0.0
    valeur += 30.0 if personne.get("titre") != "Habitant de Braavos" else 0.0
    valeur += 12.0 * math.log1p(relations.get(pid, 0))
    valeur += 8.0 * math.log1p(messages.get(pid, 0))
    valeur += min(30.0, len((ligne.get("Description") or "")) / 500.0)
    valeur += min(30.0, len((ligne.get("Personality") or "")) / 500.0)
    return valeur


def selectionner(nombre_total=None):
    chambres = chambres_marquees()
    personnes = lire_json(PERSONNAGES, [])
    par_id = {p.get("id"): p for p in personnes}
    archive = donnees_importees()
    relations = compte_csv(CSV_RELATIONS, ("Citizen1", "Citizen2"))
    messages = compte_csv(CSV_MESSAGES, ("Sender", "Receiver"))
    proteges = (porteurs_affaires() | contributeurs_entree() |
                participants_recents())
    proteges |= {
        pid for pid, p in par_id.items()
        if pid in chambres and (p.get("objectifs") or [])
    }
    deja = sorted(pid for pid, c in chambres.items() if not c["active"])
    cible = nombre_total if nombre_total is not None else len(chambres) // 2
    cible = max(0, min(int(cible), len(chambres)))
    manque = max(0, cible - len(deja))
    candidats = []
    for pid, chambre in chambres.items():
        if not chambre["active"]:
            continue
        personne = par_id.get(pid)
        if not personne or personne.get("maison_id") != "maison-serenissima":
            continue
        candidats.append((
            score(pid, personne, archive, relations, messages, proteges),
            pid, chambre, personne,
        ))
    candidats.sort(key=lambda x: (x[0], x[1]))
    retenus = candidats[:manque]
    return chambres, personnes, proteges, deja, cible, retenus


def appliquer(nombre_total=None, vraiment=False):
    chambres, personnes, proteges, deja, cible, retenus = selectionner(nombre_total)
    print("Serenissima : %d chambres · cible désactivée %d · déjà %d · à déplacer %d"
          % (len(chambres), cible, len(deja), len(retenus)))
    for rang, (valeur, pid, chambre, personne) in enumerate(retenus, 1):
        print("%3d  %-28s %7.2f  %s" %
              (rang, pid, valeur, personne.get("nom") or chambre["dossier"].name))
    if not vraiment:
        print("APERÇU SEULEMENT — ajouter --vraiment pour écrire.")
        return retenus

    ids = {pid for _score, pid, _chambre, _personne in retenus}
    ids |= set(deja)
    for personne in personnes:
        if personne.get("id") in ids:
            personne["lieu_id"] = FOSSE_ID
            personne["etat"] = "dormant"

    lieux = lire_json(LIEUX, [])
    if not any(l.get("id") == FOSSE_ID for l in lieux):
        lieux.append({
            "id": FOSSE_ID,
            "nom": "La Fosse aux Dragons",
            "region": "Port-Réal — colline de Rhaenys",
            "type": "chateau",
            "controle_id": "maison-targaryen-vert",
            "jours_de_pr": 0,
        })

    # La vue « Le château » ne lit pas personnages.lieu_id : elle calcule les
    # positions depuis routines.json, puis superpose les exceptions et le
    # dernier instantané de presence.json. Un citoyen dormant qui garderait sa
    # routine continuerait donc à se promener visiblement dans Braavos. La
    # désactivation retire aussi ces deux projections ; la chambre et la fiche
    # restent intactes et permettront une réactivation explicite plus tard.
    routines = lire_json(ROUTINES, {})
    gens_routines = routines.setdefault("gens", {})
    for pid in ids:
        gens_routines.pop(pid, None)

    presence = lire_json(PRESENCE, {})
    gens_presence = presence.setdefault("presence", {})
    gens_resolus = presence.setdefault("resolu", {}).setdefault("gens", {})
    for pid in ids:
        gens_presence.pop(pid, None)
        gens_resolus.pop(pid, None)

    for _valeur, _pid, chambre, _personne in retenus:
        (chambre["dossier"] / ACTIF).rename(chambre["dossier"] / INACTIF)
    tables.ecrire(str(PERSONNAGES), personnes, indent=1)
    tables.ecrire(str(LIEUX), lieux, indent=1)
    tables.ecrire(str(ROUTINES), routines, indent=1)
    tables.ecrire(str(PRESENCE), presence, indent=1)
    print("ÉCRIT — %d chambres désactivées au total, toutes à %s."
          % (len(ids), FOSSE_ID))
    return retenus


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nombre", type=int,
                    help="nombre TOTAL de chambres désactivées")
    ap.add_argument("--vraiment", action="store_true")
    args = ap.parse_args()
    appliquer(args.nombre, args.vraiment)


if __name__ == "__main__":
    main()
