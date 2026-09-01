#!/usr/bin/env python3
"""Importer Madre Struttura dans une salle de Braavos.

Le dossier Serenissima reste une source immuable. Sa position geographique est
conservee comme provenance, puis remplacee dans le jeu par le centre de la salle
``septuaire`` de ``monde/braavos.interieurs.json``.
"""

import argparse
import json
import os as _os
import re
import sys as _sys

# Le chemin des freres : scripts/ et scripts/noyau/.
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import tables
import serenissima


RACINE = _os.path.dirname(_d)
SOURCE = _os.path.join(RACINE, "chambres", "divine_economist", "CLAUDE.md")
MARQUEUR = _os.path.join(RACINE, "chambres", "divine_economist", "serenissima")
INTERIEURS = _os.path.join(RACINE, "monde", "braavos.interieurs.json")
PERSONNAGE_ID = "divine-economist"
SALLE_ID = "braavos-septuaire"
MODELE_ID = "madre-struttura-braavos"


def lire_json(chemin):
    with open(chemin, encoding="utf-8") as fichier:
        return json.load(fichier)


def lire_source():
    if not _os.path.isfile(MARQUEUR):
        raise ValueError("Marqueur Serenissima absent : " + MARQUEUR)
    if _os.path.getsize(MARQUEUR) != 0:
        raise ValueError("Le marqueur Serenissima doit etre vide : " + MARQUEUR)
    with open(SOURCE, encoding="utf-8-sig") as fichier:
        texte = fichier.read()
    bloc = texte.split("---", 2)[1]
    champs = {}
    for ligne in bloc.splitlines():
        trouve = re.match(r"^([A-Za-z_]+):\s*(.*)$", ligne)
        if trouve:
            cle, valeur = trouve.groups()
            try:
                champs[cle] = json.loads(valeur)
            except json.JSONDecodeError:
                champs[cle] = valeur.strip().strip('"')
    position = champs.get("Position")
    if isinstance(position, str):
        position = json.loads(position)
    if not isinstance(position, dict) or "lat" not in position or "lng" not in position:
        raise ValueError("Position lat/lng absente du frontmatter source")
    return champs, position


def salle_braavos():
    interieurs = lire_json(INTERIEURS)
    salle = next((s for s in interieurs.get("salles", []) if s.get("id") == SALLE_ID), None)
    if not salle:
        raise ValueError("Salle %s absente de braavos.interieurs.json" % SALLE_ID)
    x, y, z = salle["centre"]
    return salle, [float(x), float(y), float(z)]


def point_dans_polygone(x, y, contour):
    dedans = False
    precedent = contour[-1]
    for courant in contour:
        x1, y1 = precedent
        x2, y2 = courant
        if ((y1 > y) != (y2 > y)) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            dedans = not dedans
        precedent = courant
    return dedans


def objets_importes(champs, position, xyz):
    nom = "%s %s" % (champs.get("FirstName", "Madre"), champs.get("LastName", "Struttura"))
    provenance = (
        "Importee de Serenissima (Airtable %s) ; position d'origine "
        "lat %.15g, lng %.15g, reprojetee dans le septuaire de Braavos."
        % (champs.get("airtable_record_id", "inconnu"), position["lat"], position["lng"])
    )
    personne = {
        "id": PERSONNAGE_ID,
        "nom": nom,
        "maison_id": "maison-serenissima",
        "titre": "Clerc braavienne, gardienne d'un petit sanctuaire",
        "naissance": None,
        "traits": [
            "methodique",
            "mystique pratique",
            "ascete fortunee",
            "reductionniste",
        ],
        "objectifs": [
            {
                "but": "Rendre la vie spirituelle praticable sans la vider de son mystere",
                "priorite": 1,
            },
            {
                "but": "Employer sa fortune a rendre la conscience accessible aux gens de Braavos",
                "priorite": 2,
            },
        ],
        "maniere": (
            "Commence par le concret, ordonne les idees comme un registre, "
            "puis conduit patiemment vers leur portee spirituelle."
        ),
        "etat": "dormant",
        "lieu_id": "braavos",
        "condition": "libre",
        "canon": False,
        "note": provenance,
    }
    corps = {
        "personnage_id": PERSONNAGE_ID,
        "bat": None,
        "usage": SALLE_ID,
        "quartier": "Le chateau de Braavos",
        "role": "Clerc braavienne",
        "x": xyz[0],
        "y": xyz[1],
        "z": xyz[2],
        "monde": "braavos",
    }
    affectation = {
        "xyz": xyz,
        "monde": "braavos",
        "note": provenance,
    }
    routine = {
        "nom": "Le jour de Madre Struttura a Braavos",
        "dortoir": {
            "salle": SALLE_ID,
            "lieu": "Le septuaire, Braavos",
        },
        "bandes": [
            {
                "de": 0,
                "a": 1440,
                "salle": SALLE_ID,
                "lieu": "Le septuaire, Braavos",
            }
        ],
    }
    return personne, corps, affectation, routine


def upsert(liste, cle, valeur):
    liste[:] = [entree for entree in liste if entree.get(cle) != valeur[cle]]
    liste.append(valeur)


def verifier(personne, corps, affectation, routine, xyz):
    personnages = tables.lire("personnages")
    corps_table = tables.lire("corps")
    routines = tables.lire("routines")
    erreurs = []
    if next((p for p in personnages if p.get("id") == PERSONNAGE_ID), None) != personne:
        erreurs.append("personnage")
    if next((c for c in corps_table.get("corps", []) if c.get("personnage_id") == PERSONNAGE_ID), None) != corps:
        erreurs.append("corps")
    if corps_table.get("affectations", {}).get("personnage:" + PERSONNAGE_ID) != affectation:
        erreurs.append("affectation")
    if routines.get("modeles", {}).get(MODELE_ID) != routine:
        erreurs.append("modele de routine")
    if routines.get("gens", {}).get(PERSONNAGE_ID) != {"modele": MODELE_ID}:
        erreurs.append("routine de la personne")
    if erreurs:
        raise SystemExit("Import incomplet : " + ", ".join(erreurs))
    print(
        "OK %s dans %s a x=%.2f y=%.2f z=%.2f"
        % (PERSONNAGE_ID, SALLE_ID, xyz[0], xyz[1], xyz[2])
    )


def main():
    analyseur = argparse.ArgumentParser()
    analyseur.add_argument("--verifier", action="store_true", help="ne rien ecrire")
    args = analyseur.parse_args()

    serenissima.preparer_manuel(_os.path.dirname(SOURCE), verifier=args.verifier)

    champs, position = lire_source()
    salle, xyz = salle_braavos()
    if not point_dans_polygone(xyz[0], xyz[1], salle["contour"]):
        raise SystemExit("Le centre choisi est hors du contour du septuaire")
    personne, corps, affectation, routine = objets_importes(champs, position, xyz)

    if not args.verifier:
        personnages = tables.lire("personnages")
        corps_table = tables.lire("corps")
        routines = tables.lire("routines")
        upsert(personnages, "id", personne)
        upsert(corps_table.setdefault("corps", []), "personnage_id", corps)
        corps_table.setdefault("affectations", {})["personnage:" + PERSONNAGE_ID] = affectation
        routines.setdefault("modeles", {})[MODELE_ID] = routine
        routines.setdefault("gens", {})[PERSONNAGE_ID] = {"modele": MODELE_ID}
        tables.ecrire("personnages", personnages)
        tables.ecrire("corps", corps_table)
        tables.ecrire("routines", routines)

    verifier(personne, corps, affectation, routine, xyz)


if __name__ == "__main__":
    main()
