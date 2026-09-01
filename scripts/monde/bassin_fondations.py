#!/usr/bin/env python3
"""Mesurer un essai simple de fondation sans inventer sa réception.

Le premier banc du Bassin des Fondations reçoit une série de paliers de charge
croissante. Il contrôle la forme de la pièce, calcule pression et enfoncement,
puis produit un bordereau JSON. Il n'écrit dans aucun état canonique.

    python scripts/monde/bassin_fondations.py mesurer essai.json
    python scripts/monde/bassin_fondations.py mesurer essai.json --sortie bordereau.json
"""

import argparse
import json
import math
import os
import sys


TYPE_ENTREE = "essai-bassin-fondations/1"
TYPE_SORTIE = "bordereau-bassin-fondations/1"
LIEU_ID = "braavos-fosses"
LIEU_NOM = "Le Bassin des Fondations"


def _nombre(valeur, champ):
    if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
        raise ValueError("%s doit être un nombre" % champ)
    if not math.isfinite(valeur):
        raise ValueError("%s doit être fini" % champ)
    return float(valeur)


def mesurer(entree):
    if entree.get("type") != TYPE_ENTREE:
        raise ValueError("type attendu : %s" % TYPE_ENTREE)

    identifiant = str(entree.get("id") or "").strip()
    objet = str(entree.get("objet") or "").strip()
    if not identifiant or not objet:
        raise ValueError("id et objet sont obligatoires")

    section = _nombre(entree.get("section_m2"), "section_m2")
    if section <= 0:
        raise ValueError("section_m2 doit être strictement positive")

    paliers = entree.get("paliers")
    if not isinstance(paliers, list) or len(paliers) < 2:
        raise ValueError("paliers doit contenir au moins deux mesures")

    mesures = []
    charge_precedente = -1.0
    for rang, palier in enumerate(paliers, 1):
        if not isinstance(palier, dict):
            raise ValueError("palier %d invalide" % rang)
        charge = _nombre(palier.get("charge_kn"), "paliers[%d].charge_kn" % rang)
        enfoncement = _nombre(
            palier.get("enfoncement_mm"), "paliers[%d].enfoncement_mm" % rang)
        if charge < 0 or enfoncement < 0:
            raise ValueError("charge et enfoncement ne peuvent pas être négatifs")
        if charge <= charge_precedente:
            raise ValueError("les charges doivent être strictement croissantes")
        charge_precedente = charge
        mesures.append({"charge_kn": charge, "enfoncement_mm": enfoncement})

    maximum = mesures[-1]
    pression_kpa = maximum["charge_kn"] / section
    raideur_kn_mm = (maximum["charge_kn"] / maximum["enfoncement_mm"]
                     if maximum["enfoncement_mm"] > 0 else None)

    seuils = entree.get("seuils") or {}
    if not isinstance(seuils, dict):
        raise ValueError("seuils doit être un objet")
    seuil_enfoncement = seuils.get("enfoncement_max_mm")
    if seuil_enfoncement is None:
        etat_resultat = "MESURÉ, NON QUALIFIÉ"
        conformite = None
    else:
        seuil_enfoncement = _nombre(seuil_enfoncement, "seuils.enfoncement_max_mm")
        if seuil_enfoncement < 0:
            raise ValueError("le seuil d'enfoncement ne peut pas être négatif")
        conformite = maximum["enfoncement_mm"] <= seuil_enfoncement
        etat_resultat = "CONFORME" if conformite else "NON CONFORME"

    simulation = entree.get("simulation") is True
    return {
        "type": TYPE_SORTIE,
        "lieu": {"id": LIEU_ID, "nom": LIEU_NOM},
        "essai": {"id": identifiant, "objet": objet, "simulation": simulation},
        "preuve_geste": {
            "etat": "SIMULÉ" if simulation else "FAIT",
            "paliers_valides": len(mesures),
            "serie_charge_strictement_croissante": True,
        },
        "resultat_sous_jacent": {
            "etat": "SIMULATION — " + etat_resultat if simulation else etat_resultat,
            "charge_max_kn": maximum["charge_kn"],
            "pression_max_kpa": round(pression_kpa, 3),
            "enfoncement_a_charge_max_mm": maximum["enfoncement_mm"],
            "raideur_secante_kn_par_mm": (
                round(raideur_kn_mm, 3) if raideur_kn_mm is not None else None),
            "seuil_enfoncement_max_mm": seuil_enfoncement,
            "conforme_au_seuil": conformite,
        },
        "decision": "À EXAMINER — aucune réception automatique",
        "limite": ("Les données sont une simulation de fonctionnement ; elles ne prouvent "
                   "aucun comportement matériel." if simulation else
                   "Le calcul traite les observations fournies ; il ne prouve ni leur "
                   "provenance, ni l'étalonnage des instruments."),
    }


def lire_json(chemin):
    with open(chemin, encoding="utf-8") as fichier:
        return json.load(fichier)


def ecrire_json(piece, chemin=None):
    texte = json.dumps(piece, ensure_ascii=False, indent=2) + "\n"
    if chemin:
        dossier = os.path.dirname(os.path.abspath(chemin))
        os.makedirs(dossier, exist_ok=True)
        with open(chemin, "w", encoding="utf-8", newline="\n") as fichier:
            fichier.write(texte)
    else:
        sys.stdout.write(texte)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sous = parser.add_subparsers(dest="commande", required=True)
    commande = sous.add_parser("mesurer", help="former le bordereau d'un essai")
    commande.add_argument("entree", help="fichier JSON de l'essai")
    commande.add_argument("--sortie", help="écrire le bordereau à cette adresse")
    args = parser.parse_args(argv)
    try:
        piece = mesurer(lire_json(args.entree))
        ecrire_json(piece, args.sortie)
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as erreur:
        print("ESSAI INVALIDE : %s" % erreur, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
