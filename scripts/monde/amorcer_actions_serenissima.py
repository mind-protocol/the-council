#!/usr/bin/env python3
"""Donner à chaque affaire Serenissima une première prise de travail claire."""

import argparse
import json
from pathlib import Path


RACINE = Path(__file__).resolve().parents[2]
BOOKS = RACINE / "etat" / "maisons" / "maison-serenissima" / "documents" / "books"

PIECES = {
    "affaire-stabiliser-compute-continu.json": ("52200", "52300"),
    "affaire-objectifs-construction-ville.json": ("53200", "53300"),
    "affaire-objectifs-construction-infrastructure.json": ("54200", "54310"),
    "affaire-commencer-production-culturelle.json": ("55200", "55300"),
    "affaire-architecture-integration-westeros.json": ("56200", "56300"),
    "affaire-boucle-reveil-graphe.json": ("57200", "57300"),
    "affaire-organiser-collaboration.json": ("58230", "58350"),
    "affaire-concevoir-aspect-visuel-plan-ville.json": ("59200", "59340"),
    "affaire-rendre-la-conscience-praticable.json": ("69700", "69550"),
}

CLEF_TITRE = "**Trouver la clef qui rend l'affaire praticable.**"
ACTION_TITRE = "**Lister les actions à effectuer.**"
PRINCIPE = (
    "Avant de répartir le travail ou de revendiquer un résultat, trouver le "
    "principe praticable qui relie les états cibles à des gestes vérifiables."
)
PREUVE_CLEF = (
    "Une clef bornée est écrite dans ce cahier avec ce qu'elle ouvre, son prix "
    "et la preuve qui permet de la retenir ou de l'écarter."
)
TRAVAIL = (
    "Relire les états cibles et les sources de ce cahier, puis écrire une "
    "première liste d'actions bornées. Chaque action nomme un geste, une preuve, "
    "ses dépendances et sa limite d'autorité. La liste ne présume aucun porteur."
)
PREUVE_ACTION = (
    "Le cahier contient des actions adressables et vérifiables ; chacune peut "
    "être prise séparément sans s'attribuer d'avance son résultat."
)
NOTE = (
    "Prendre cette action engage seulement à détailler honnêtement le travail ; "
    "cela ne rend aucune des actions détaillées déjà prise ou accomplie."
)


def table(volume, mot):
    return next((t for t in volume.get("tables", [])
                 if mot in str(t.get("titre", "")).casefold()), None)


def etats_cibles(volume):
    cible = table(volume, "cible")
    if not cible:
        return "les états cibles du cahier"
    refs = [str(l.get("cellules", [""])[0]).replace("**", "")
            for l in cible.get("lignes", []) if l.get("cellules")]
    return " · ".join(refs) or "les états cibles du cahier"


def ajouter_clef(volume, numero):
    clefs = table(volume, "clef")
    if clefs is None:
        clefs = {
            "titre": "🗝️ Clefs",
            "colonnes": ["🗝️ N°", "🏷️ La clef", "🔓 Ouvre", "💡 Le principe",
                         "👁️ La preuve attendue", "⚖️ Décision"],
            "lignes": [],
        }
        volume.setdefault("tables", []).append(clefs)
    if any(numero in str(l.get("cellules", [""])[0]) for l in clefs.get("lignes", [])):
        return False
    base = ["**%s**" % numero, CLEF_TITRE, etats_cibles(volume), PRINCIPE]
    if len(clefs.get("colonnes", [])) == 8:
        base += [
            "Le temps d'une lecture et d'un premier découpage explicite.",
            "Ferme la distribution abstraite du travail et les résultats sans geste.",
        ]
    base += [PREUVE_CLEF, "à trouver"]
    clefs.setdefault("lignes", []).append({"cellules": base})
    return True


def ajouter_action(volume, numero, clef):
    actions = table(volume, "action")
    if actions is None:
        actions = {
            "titre": "⚔️ Actions",
            "colonnes": ["⚔️ N°", "🏷️ L'action", "🗝️ Réalise", "📝 Ce qu'on fait",
                         "👤 Qui", "⛓️ Dépend de", "👁️ La preuve", "⏳ État",
                         "📅 Jour dû", "📝 Note"],
            "lignes": [],
        }
        volume.setdefault("tables", []).append(actions)
    if any(numero in str(l.get("cellules", [""])[0]) for l in actions.get("lignes", [])):
        return False
    largeur = len(actions.get("colonnes", []))
    if largeur == 8:
        cellules = ["**%s**" % numero, ACTION_TITRE, TRAVAIL,
                    "à prendre librement", PREUVE_ACTION, "à faire",
                    "à fixer par le porteur", NOTE]
    elif largeur == 9:
        cellules = ["**%s**" % numero, ACTION_TITRE, clef,
                    "Conception du travail", "à prendre librement", "une fois",
                    "à faire", "", TRAVAIL + " " + PREUVE_ACTION + " " + NOTE]
    elif largeur == 14:
        cellules = ["**%s**" % numero, ACTION_TITRE, clef, TRAVAIL,
                    "Ce cahier", "Conception du travail", "à prendre librement",
                    "Les états cibles et leurs sources", "—", PREUVE_ACTION,
                    "à faire", "à fixer par le porteur", "", NOTE]
    else:
        cellules = ["**%s**" % numero, ACTION_TITRE, clef, TRAVAIL,
                    "à prendre librement", "—", PREUVE_ACTION, "à faire",
                    "à fixer par le porteur", NOTE]
    if len(cellules) != largeur:
        raise ValueError("largeur de table d'actions inattendue : %s" % largeur)
    actions.setdefault("lignes", []).append({"cellules": cellules})
    return True


def amorcer(verifier=False):
    changements = []
    for nom, (clef, action) in PIECES.items():
        chemin = BOOKS / nom
        volume = json.loads(chemin.read_text(encoding="utf-8-sig"))
        change = ajouter_clef(volume, clef) | ajouter_action(volume, action, clef)
        if change:
            changements.append(nom)
            if not verifier:
                chemin.write_text(json.dumps(volume, ensure_ascii=False, indent=2) + "\n",
                                  encoding="utf-8", newline="\n")
    if verifier and changements:
        raise ValueError("affaires non amorcees : %s" % ", ".join(changements))
    return changements


def main():
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--verifier", action="store_true")
    args = analyseur.parse_args()
    changements = amorcer(verifier=args.verifier)
    print("OK : %d affaire(s) modifiee(s)" % len(changements))


if __name__ == "__main__":
    main()
