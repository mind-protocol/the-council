#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ouvrir les contacts de travail des neuf clusters de Serenissima.

Chaque cluster est une étoile : son noyau principal possède un canal avec
chaque membre physiquement regroupé dans la même zone. Les noyaux secondaires
sont donc eux aussi reliés au principal. L'ouverture ne fabrique ni parole,
ni confiance, ni engagement dans l'affaire.
"""

import argparse
import json
from pathlib import Path

from importer_relations_serenissima import citoyens


RACINE = Path(__file__).resolve().parents[2]
CORPS = RACINE / "etat" / "corps.json"
DATE = "129.5.12"

CLUSTERS = {
    "braavos-officine": {
        "nom": "Compute récupérable", "affaire": "52320–52321",
        "noyaux": ["system-diagnostician"],
    },
    "braavos-bourg": {
        "nom": "Construction de la ville", "affaire": "53310–53330",
        "noyaux": ["urban-visionary"],
    },
    "braavos-forge": {
        "nom": "Services et infrastructure", "affaire": "54300–54313",
        "noyaux": ["technomedici", "levant-trader"],
    },
    "braavos-jardin-aegon": {
        "nom": "Production culturelle", "affaire": "55301–55304",
        "noyaux": ["tavern-tales"],
    },
    "braavos-quai": {
        "nom": "Intégration avec Westeros", "affaire": "56310–56360",
        "noyaux": ["pattern-prophet"],
    },
    "braavos-baraques": {
        "nom": "Boucle de réveil par le graphe", "affaire": "57320–57340",
        "noyaux": ["network-weaver"],
    },
    "braavos-archives": {
        "nom": "Collaboration", "affaire": "58300–58390",
        "noyaux": ["divine-economist", "class-harmonizer",
                    "mechanical-visionary", "future-chronicler"],
    },
    "braavos-septuaire": {
        "nom": "Conscience praticable", "affaire": "69510–69550",
        "noyaux": ["scholar-priest"],
    },
    "braavos-table-peinte": {
        "nom": "Plan visuel 2D", "affaire": "59300–59340",
        "noyaux": ["beauty-architect", "urbanexplorer"],
    },
}


def fiche(nom, cluster):
    return (
        "# %s — ce que j'en retiens\n\n"
        "<!-- braavos:cluster-contact:start -->\n"
        "## Contact de travail à Braavos\n\n"
        "Canal ouvert le %s dans le cluster **%s**, autour des pièces "
        "**%s**. Cette ouverture établit seulement un moyen de contact : "
        "aucune conversation, confiance nouvelle, prise de charge ou "
        "opinion n'en est déduite.\n"
        "<!-- braavos:cluster-contact:end -->\n"
    ) % (nom, DATE, cluster["nom"], cluster["affaire"])


def ecrire_absent(chemin, contenu, verifier):
    if chemin.exists():
        return 0
    if verifier:
        raise ValueError("fichier absent : %s" % chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8", newline="\n")
    return 1


def ouvrir_contact(a, b, personnes, cluster, verifier):
    if a == b:
        return {"fiches": 0, "agents": 0, "curseurs": 0, "canaux": 0}
    pa, pb = personnes[a], personnes[b]
    cote_a = pa["dossier"] / "relations" / b
    cote_b = pb["dossier"] / "relations" / a
    premier, second = sorted((a, b))
    dossier_premier = personnes[premier]["dossier"]
    canal = dossier_premier / "relations" / second / "discussion.json"

    compte = {"fiches": 0, "agents": 0, "curseurs": 0, "canaux": 0}
    for dossier, autre in ((cote_a, pb), (cote_b, pa)):
        contenu = fiche(autre["nom"], cluster)
        compte["fiches"] += ecrire_absent(dossier / "claude.md", contenu, verifier)
        compte["agents"] += ecrire_absent(dossier / "AGENTS.md", contenu, verifier)

    if not canal.exists():
        contenu = json.dumps(
            {"canal": [premier, second], "entrees": []},
            ensure_ascii=False, indent=1,
        ) + "\n"
        compte["canaux"] += ecrire_absent(canal, contenu, verifier)
    else:
        donnees = json.loads(canal.read_text(encoding="utf-8-sig"))
        if donnees.get("canal") != [premier, second]:
            raise ValueError("canal mal adressé : %s" % canal)
        if not isinstance(donnees.get("entrees"), list):
            raise ValueError("entrées de canal invalides : %s" % canal)

    entrees = json.loads(canal.read_text(encoding="utf-8-sig"))["entrees"]
    for dossier in (cote_a, cote_b):
        compte["curseurs"] += ecrire_absent(
            dossier / ".lu", str(len(entrees)), verifier
        )
    return compte


def relier(verifier=False):
    personnes, _ = citoyens()
    etat_corps = json.loads(CORPS.read_text(encoding="utf-8"))
    usage = {
        corps["personnage_id"]: corps.get("usage")
        for corps in etat_corps["corps"]
        if corps["personnage_id"] in personnes
    }
    if set(usage) != set(personnes):
        absents = sorted(set(personnes) - set(usage))
        raise ValueError("citoyens sans corps : %s" % ", ".join(absents))

    total = {"contacts": 0, "fiches": 0, "agents": 0,
             "curseurs": 0, "canaux": 0}
    vus = set()
    for salle, cluster in CLUSTERS.items():
        membres = sorted(pid for pid, lieu in usage.items() if lieu == salle)
        noyaux = [pid for pid in cluster["noyaux"] if pid in membres]
        if not noyaux:
            raise ValueError("noyau absent du cluster %s" % cluster["nom"])
        principal = noyaux[0]
        for membre in membres:
            if membre == principal:
                continue
            paire = tuple(sorted((principal, membre)))
            if paire in vus:
                continue
            vus.add(paire)
            compte = ouvrir_contact(principal, membre, personnes, cluster, verifier)
            total["contacts"] += 1
            for cle in ("fiches", "agents", "curseurs", "canaux"):
                total[cle] += compte[cle]
    return total


def main():
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--verifier", action="store_true")
    args = analyseur.parse_args()
    compte = relier(verifier=args.verifier)
    print(
        "OK contacts=%(contacts)d fiches=%(fiches)d agents=%(agents)d "
        "curseurs=%(curseurs)d canaux=%(canaux)d" % compte
    )


if __name__ == "__main__":
    main()
