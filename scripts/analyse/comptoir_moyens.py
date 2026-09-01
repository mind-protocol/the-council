#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Comparer les moyens inscrits d'une maison a l'observation courante.

    python scripts/analyse/comptoir_moyens.py
    python scripts/analyse/comptoir_moyens.py --json

La commande est en lecture seule. Elle rejoue M110, accepte son code de sortie
1 (des ecarts d'architecture existent), puis compare ses six mesures au
registre ``mains.json``. Son propre code de sortie vaut 0 si les comptes sont
identiques, 1 s'ils ont derive et 2 si le contrat d'entree est incomplet.

``--observation`` permet de fournir une sortie JSON deja produite par M110.
Cette porte rend le comptoir essayable sans toucher au depot courant.

Chaque comparaison porte ses deux sources. En sortie lisible, les lignes qui
divergent impriment explicitement les deux valeurs et leur provenance : le
registre inscrit d'un cote, la sonde ou l'observation fournie de l'autre.
"""

import argparse
import json
import os
import subprocess
import sys


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAINS_PAR_DEFAUT = os.path.join(
    RACINE,
    "etat",
    "maisons",
    "maison-serenissima",
    "documents",
    "mains.json",
)
SONDE = os.path.join(RACINE, "scripts", "analyse", "graphe_archi.py")

MESURES = (
    "containers-declares",
    "modules-rattaches",
    "modules-orphelins",
    "liens-hors-porte",
    "dependances-remontantes",
    "commandes-bibliotheques",
)

CHAMPS_OBSERVES = {
    "containers-declares": "declaration",
    "modules-rattaches": "fichiers moins orphelins",
    "modules-orphelins": "orphelins",
    "liens-hors-porte": "hors_porte",
    "dependances-remontantes": "remontees",
    "commandes-bibliotheques": "commandes_bibliotheques",
}


class ContratIncomplet(Exception):
    pass


def charger_json(chemin):
    try:
        with open(chemin, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise ContratIncomplet("impossible de lire %s : %s" % (chemin, exc)) from exc


def rejouer_sonde():
    passage = subprocess.run(
        [sys.executable, SONDE, "--json"],
        cwd=RACINE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if passage.returncode not in (0, 1):
        raise ContratIncomplet(
            "la sonde M110 a echoue (code %d) : %s"
            % (passage.returncode, passage.stderr.strip())
        )
    try:
        return json.loads(passage.stdout)
    except json.JSONDecodeError as exc:
        raise ContratIncomplet("la sonde M110 n'a pas rendu de JSON lisible") from exc


def mesures_inscrites(mains):
    inscrites = {}
    libelles = {}
    for main in mains.get("mains", []):
        for mesure in main.get("mesure", []):
            identifiant = mesure.get("id")
            if identifiant in MESURES:
                if identifiant in inscrites:
                    raise ContratIncomplet("mesure inscrite deux fois : %s" % identifiant)
                inscrites[identifiant] = mesure.get("valeur")
                libelles[identifiant] = mesure.get("quoi", identifiant)
    manquantes = [identifiant for identifiant in MESURES if identifiant not in inscrites]
    if manquantes:
        raise ContratIncomplet("mesures absentes de mains.json : %s" % ", ".join(manquantes))
    return inscrites, libelles


def mesures_observees(observation):
    requis = ("declaration", "fichiers", "orphelins", "hors_porte", "remontees",
              "commandes_bibliotheques")
    manquants = [cle for cle in requis if cle not in observation]
    if manquants:
        raise ContratIncomplet("champs absents de l'observation : %s" % ", ".join(manquants))
    return {
        "containers-declares": len(observation["declaration"]),
        "modules-rattaches": observation["fichiers"] - len(observation["orphelins"]),
        "modules-orphelins": len(observation["orphelins"]),
        "liens-hors-porte": len(observation["hors_porte"]),
        "dependances-remontantes": len(observation["remontees"]),
        "commandes-bibliotheques": len(observation["commandes_bibliotheques"]),
    }


def comparer(mains, observation, source_mains, source_observation):
    inscrites, libelles = mesures_inscrites(mains)
    observees = mesures_observees(observation)
    lignes = []
    for identifiant in MESURES:
        inscrit = inscrites[identifiant]
        observe = observees[identifiant]
        lignes.append({
            "id": identifiant,
            "quoi": libelles[identifiant],
            "inscrit": inscrit,
            "observe": observe,
            "ecart": observe - inscrit,
            "conforme": observe == inscrit,
            "source_inscrite": "%s#mesure/%s" % (source_mains, identifiant),
            "source_observee": "%s#%s" %
                                (source_observation, CHAMPS_OBSERVES[identifiant]),
        })
    return {
        "maison_id": mains.get("maison_id"),
        "conforme": all(ligne["conforme"] for ligne in lignes),
        "comparaisons": lignes,
    }


def imprimer(resultat):
    print()
    print("COMPTOIR DES MOYENS — %s" % (resultat.get("maison_id") or "maison inconnue"))
    print()
    print("  %-29s %9s %9s %8s  %s" %
          ("mesure", "inscrit", "observe", "ecart", "etat"))
    for ligne in resultat["comparaisons"]:
        etat = "conforme" if ligne["conforme"] else "a instruire"
        print("  %-29s %9s %9s %+8d  %s" %
              (ligne["id"], ligne["inscrit"], ligne["observe"], ligne["ecart"], etat))
    print()
    print("  VERDICT : %s" % ("CONFORME" if resultat["conforme"] else "A INSTRUIRE"))
    divergentes = [ligne for ligne in resultat["comparaisons"] if not ligne["conforme"]]
    if divergentes:
        print()
        print("  VALEURS DIVERGENTES ET LEURS SOURCES")
        for ligne in divergentes:
            print("    %s" % ligne["id"])
            print("      inscrit : %s — %s" %
                  (ligne["inscrit"], ligne["source_inscrite"]))
            print("      observe : %s — %s" %
                  (ligne["observe"], ligne["source_observee"]))
    print()


def arguments(argv=None):
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--mains", default=MAINS_PAR_DEFAUT,
                         help="registre mains.json a comparer")
    parseur.add_argument("--observation",
                         help="sortie JSON de M110 ; sinon la sonde est rejouee")
    parseur.add_argument("--json", action="store_true", dest="en_json",
                         help="rendre le contrat en JSON")
    return parseur.parse_args(argv)


def main(argv=None):
    opts = arguments(argv)
    try:
        mains = charger_json(opts.mains)
        observation = charger_json(opts.observation) if opts.observation else rejouer_sonde()
        source_mains = os.path.relpath(opts.mains, RACINE).replace("\\", "/")
        if opts.observation:
            source_observation = os.path.relpath(opts.observation, RACINE).replace("\\", "/")
        else:
            source_observation = "python scripts/analyse/graphe_archi.py --json"
        resultat = comparer(mains, observation, source_mains, source_observation)
    except ContratIncomplet as exc:
        print("contrat incomplet : %s" % exc, file=sys.stderr)
        return 2
    if opts.en_json:
        print(json.dumps(resultat, ensure_ascii=False, indent=2))
    else:
        imprimer(resultat)
    return 0 if resultat["conforme"] else 1


if __name__ == "__main__":
    sys.exit(main())
