#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Relier chaque citoyen de Braavos à l'affaire commune de collaboration.

La ligne créée ne prétend pas que le citoyen accepte un chantier. Elle lui
attribue seulement une réponse vérifiable à l'invitation : proposer, prendre
ou refuser. Ce geste suffit à créer un vrai chemin dans le tissu sans inventer
une contribution substantielle.
"""
import argparse
import json
import os
import re
import sys


ICI = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(ICI)
RACINE = os.path.dirname(SCRIPTS)
NOYAU = os.path.join(SCRIPTS, "noyau")
for chemin in (SCRIPTS, NOYAU):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

from etat.expose import tables  # noqa: E402


AFFAIRE = os.path.join(
    RACINE, "etat", "maisons", "maison-serenissima", "documents", "books",
    "affaire-organiser-collaboration.json")
PERSONNAGES = os.path.join(RACINE, "etat", "personnages.json")
DEBUT = 58500
FIN = 58999
MARQUEUR = "activation:entree-graphe-serenissima/"


def _numero(cellule):
    trouve = re.search(r"\d{5}", str(cellule or ""))
    return int(trouve.group()) if trouve else None


def _table_actions(volume):
    return next(t for t in volume.get("tables") or []
                if "action" in str(t.get("titre") or "").casefold())


def _citoyens(personnages):
    return sorted(
        (p for p in personnages
         if isinstance(p, dict) and p.get("id")
         and p.get("lieu_id") == "braavos"),
        key=lambda p: p["id"],
    )


def preparer(volume, personnages):
    actions = _table_actions(volume)
    colonnes = actions.get("colonnes") or []
    if len(colonnes) != 14:
        raise ValueError("la table Actions de collaboration n'a pas 14 colonnes")
    lignes = actions.setdefault("lignes", [])
    utilises = {_numero(l.get("cellules", [""])[0]) for l in lignes}
    utilises.discard(None)
    par_citoyen = {}
    for ligne in lignes:
        cellules = ligne.get("cellules") or []
        note = str(cellules[13] if len(cellules) > 13 else "")
        if MARQUEUR in note:
            par_citoyen[note.split(MARQUEUR, 1)[1].split()[0]] = ligne

    libres = iter(n for n in range(DEBUT, FIN + 1) if n not in utilises)
    ajoutees = []
    for personne in _citoyens(personnages):
        pid = personne["id"]
        if pid in par_citoyen:
            continue
        try:
            numero = next(libres)
        except StopIteration as exc:
            raise ValueError("plage 58500-58999 épuisée") from exc
        nom = personne.get("nom") or pid
        cellules = [
            "**%d**" % numero,
            "**Répondre à l'invitation de la maison — %s.**" % nom,
            "58110",
            ("Ouvrir son affaire personnelle et les affaires de la maison, "
             "puis publier une réponse de sa propre main : PROPOSER une "
             "contribution bornée, PRENDRE une charge précise, ou REFUSER "
             "en nommant ce qui manque. Aucune de ces trois réponses ne vaut "
             "acceptation d'une autre charge."),
            "Sa chambre et l'affaire Organiser la collaboration",
            "Prise de contact et réponse autonome",
            pid,
            "Son affaire personnelle ; le contrat minimal de contribution",
            "—",
            ("Une parole datée et adressable de la personne porte PROPOSER, "
             "PRENDRE ou REFUSER, avec l'affaire visée et sa limite."),
            "à faire",
            "au prochain réveil",
            "",
            (MARQUEUR + pid + " — Cette action exige une réponse, jamais une "
             "acceptation ; elle n'accorde aucune autorité nouvelle."),
        ]
        lignes.append({"cellules": cellules})
        ajoutees.append((numero, pid, nom))
    return ajoutees


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vraiment", action="store_true")
    args = ap.parse_args()
    volume = tables.lire(AFFAIRE, {})
    personnages = tables.lire(PERSONNAGES, [])
    ajoutees = preparer(volume, personnages)
    print("%d action(s) d'entrée à ajouter" % len(ajoutees))
    for numero, pid, nom in ajoutees[:20]:
        print("  %d  %-32s %s" % (numero, pid, nom))
    if len(ajoutees) > 20:
        print("  … %d autres" % (len(ajoutees) - 20))
    if args.vraiment and ajoutees:
        tables.ecrire(AFFAIRE, volume, indent=2)
        print("Écrit : %s" % AFFAIRE)
    elif ajoutees:
        print("À blanc — relancer avec --vraiment")


if __name__ == "__main__":
    main()
