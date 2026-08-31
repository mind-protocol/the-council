# -*- coding: utf-8 -*-
"""Pose le premier chaînage action -> acte, depuis le recoupement d'Aldon."""
import os
import sys

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOYAU = os.path.join(SCRIPTS, "noyau")
for p in (SCRIPTS, NOYAU):
    if p not in sys.path:
        sys.path.insert(0, p)

import ajouter  # noqa: E402 — façade append-only d'etat/


ACTE = {
    "id": "acte-26051-sortie-non-remise-3e",
    "date": {"annee": 129, "lune": 4, "jour": 3, "minute": 460},
    "acteur_id": "aldon-hask",
    "cible_id": "steffon-darklyn",
    "lieu_id": "peyredragon",
    "type": "remise",
    "quoi": ("À sept heures quarante, treize dragons sont sortis du coffre "
              "et ont été remis à ser Steffon Darklyn comme porteur. Ils "
              "n'ont pas quitté l'île, le créancier ne les a pas reçus et "
              "aucune quittance n'est revenue : la remise demeure inachevée."),
    "temoins": [],
    "connu_de": ["aldon-hask", "steffon-darklyn"],
    "action_id": "26051",
    "affaire_id": "affaire-logistique-transport",
    "relation_action": "preuve",
}


if __name__ == "__main__":
    poses = ajouter.ajouter("actes", [ACTE])
    print("actes : %s" % (", ".join(poses) if poses else "déjà lié"))
