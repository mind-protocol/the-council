#!/usr/bin/env python3
"""Créer le monde provisoire de Braavos à partir de celui de Peyredragon.

Braavos a sa propre identité et ses propres fichiers servis, mais réemploie
temporairement toute la géométrie, le château, les pièces et la population de
Peyredragon. Relancer ce script après toute nouvelle cuisson de Peyredragon.

    python scripts/monde/braavos.py
    python scripts/monde/braavos.py --verifier
"""

import argparse
import json
import os
import shutil
import sys


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MONDE = os.path.join(RACINE, "monde")
SOURCE = "peyredragon"
DESTINATION = "braavos"

SUFFIXES_JSON = (
    "terrain",
    "bati",
    "graph",
    "rues",
    "plan2d",
    "carte",
    "maillage",
    "interieurs",
    "gens",
    "besoins",
)
SUFFIXES_BINAIRES = ("masque",)


def _adapter(valeur, cle=None):
    """Adapter l'identité sans falsifier les notices qui nomment la source."""
    if isinstance(valeur, dict):
        return {k: _adapter(v, k) for k, v in valeur.items()}
    if isinstance(valeur, list):
        return [_adapter(v, cle) for v in valeur]
    if not isinstance(valeur, str):
        return valeur
    if cle == "_lisez_moi":
        return ("COPIE PROVISOIRE POUR BRAAVOS — géométrie et contenu repris "
                "de Peyredragon. Source originale : " + valeur)
    # Les champs techniques commençant par _ documentent les générateurs de
    # Peyredragon. Les renommer prétendrait que des scripts inexistants les ont
    # produits.
    if isinstance(cle, str) and cle.startswith("_"):
        return valeur
    return valeur.replace("Peyredragon", "Braavos").replace(
        "peyredragon", "braavos")


def _chemin(prefixe, suffixe, extension):
    return os.path.join(MONDE, "%s.%s.%s" % (prefixe, suffixe, extension))


def _fichiers_attendus():
    fichiers = [_chemin(DESTINATION, s, "json") for s in SUFFIXES_JSON]
    fichiers += [_chemin(DESTINATION, s, "bin") for s in SUFFIXES_BINAIRES]
    return fichiers


def verifier():
    absents = [p for p in _fichiers_attendus() if not os.path.isfile(p)]
    dossier = os.path.join(MONDE, "gens", DESTINATION)
    if not os.path.isdir(dossier):
        absents.append(dossier)
    if absents:
        print("Le monde provisoire de Braavos est INCOMPLET :")
        for chemin in absents:
            print("  - " + os.path.relpath(chemin, RACINE))
        return 1

    with open(_chemin(DESTINATION, "plan2d", "json"), encoding="utf-8") as f:
        plan = json.load(f)
    with open(_chemin(DESTINATION, "carte", "json"), encoding="utf-8") as f:
        carte = json.load(f)
    with open(_chemin(DESTINATION, "interieurs", "json"), encoding="utf-8") as f:
        interieurs = json.load(f)
    with open(_chemin(DESTINATION, "gens", "json"), encoding="utf-8") as f:
        gens = json.load(f)

    erreurs = []
    if plan.get("lieu") != DESTINATION:
        erreurs.append("plan2d.lieu n'est pas braavos")
    if carte.get("lieu_id") != DESTINATION:
        erreurs.append("carte.lieu_id n'est pas braavos")
    if gens.get("dossier") != "monde/gens/braavos":
        erreurs.append("gens.dossier ne pointe pas vers monde/gens/braavos")
    if not interieurs.get("salles"):
        erreurs.append("aucune salle copiée")
    if erreurs:
        print("Le monde provisoire de Braavos est INVALIDE :")
        for erreur in erreurs:
            print("  - " + erreur)
        return 1

    print("Braavos est prêt : %d salles, %d fichiers de monde." % (
        len(interieurs["salles"]), len(_fichiers_attendus())))
    return 0


def engendrer():
    for suffixe in SUFFIXES_JSON:
        source = _chemin(SOURCE, suffixe, "json")
        destination = _chemin(DESTINATION, suffixe, "json")
        with open(source, encoding="utf-8") as f:
            donnees = json.load(f)
        with open(destination, "w", encoding="utf-8", newline="\n") as f:
            json.dump(_adapter(donnees), f, ensure_ascii=False,
                      separators=(",", ":"))

    for suffixe in SUFFIXES_BINAIRES:
        shutil.copyfile(_chemin(SOURCE, suffixe, "bin"),
                        _chemin(DESTINATION, suffixe, "bin"))

    source_gens = os.path.join(MONDE, "gens", SOURCE)
    destination_gens = os.path.join(MONDE, "gens", DESTINATION)
    os.makedirs(destination_gens, exist_ok=True)
    for nom in os.listdir(source_gens):
        source = os.path.join(source_gens, nom)
        if os.path.isfile(source):
            shutil.copyfile(source, os.path.join(destination_gens, nom))

    return verifier()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verifier", action="store_true",
                        help="vérifier les fichiers sans les réécrire")
    args = parser.parse_args()
    return verifier() if args.verifier else engendrer()


if __name__ == "__main__":
    sys.exit(main())
