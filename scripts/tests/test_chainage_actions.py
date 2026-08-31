# -*- coding: utf-8 -*-
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOYAU = os.path.join(SCRIPTS, "noyau")
for p in (SCRIPTS, NOYAU):
    if p not in sys.path:
        sys.path.insert(0, p)

import chainage_actions  # noqa: E402
from etat import entree  # noqa: E402


def ecrire(fichier, valeur):
    os.makedirs(os.path.dirname(fichier), exist_ok=True)
    with io.open(fichier, "w", encoding="utf-8") as f:
        json.dump(valeur, f, ensure_ascii=False)


class ChainageActionsTest(unittest.TestCase):
    def test_reference_partielle_est_refusee(self):
        with self.assertRaises(ValueError):
            chainage_actions.valider_reference({"action_id": "26051"})
        with self.assertRaises(ValueError):
            chainage_actions.valider_reference({
                "action_id": "26051", "affaire_id": "affaire-x",
                "relation_action": "peut-etre"})

    def test_contexte_action_complete_le_lien_sans_bloquer_la_fermeture(self):
        etat = tempfile.mkdtemp(prefix="chainage-actions-")
        try:
            ecrire(os.path.join(etat, "maisons.json"), [{"id": "maison-test"}])
            ecrire(os.path.join(etat, "books", "_ordre.json"), [])
            base = os.path.join(etat, "maisons", "maison-test", "documents", "books")
            ecrire(os.path.join(base, "_ordre.json"), ["affaire-test"])
            ecrire(os.path.join(base, "affaire-test.json"), {
                "id": "affaire-test", "maison_id": "maison-test",
                "tables": [{"titre": "⚔️ Actions",
                            "colonnes": ["N°", "Action", "⏳ État"],
                            "lignes": [{"cellules": ["120", "Faire", "faite"]}]}]})
            ecrire(os.path.join(etat, "actes.json"), [])
            acte = chainage_actions.completer_depuis_contexte(
                {"id": "acte-test"}, etat, contexte_id="120")
            self.assertEqual(acte["action_id"], "120")
            self.assertEqual(acte["affaire_id"], "affaire-test")
            self.assertEqual(acte["relation_action"], "preuve")
            ecrire(os.path.join(etat, "actes.json"), [acte])
            self.assertEqual(chainage_actions.auditer(etat), [])

            # Une fermeture est déjà conservée dans affaires.jsonl. Son
            # absence dans actes.json n'est pas une faute : l'état du registre
            # n'est pas, à lui seul, un fait du monde à inventer.
            ecrire(os.path.join(etat, "actes.json"), [])
            self.assertEqual(chainage_actions.auditer(etat), [])
        finally:
            shutil.rmtree(etat)

    def test_la_vraie_porte_ajouter_deduit_le_lien_depuis_environnement(self):
        racine = tempfile.mkdtemp(prefix="porte-chainage-")
        ancien = entree.racine
        try:
            etat = os.path.join(racine, "etat")
            ecrire(os.path.join(etat, "maisons.json"), [{"id": "maison-test"}])
            ecrire(os.path.join(etat, "books", "_ordre.json"), [])
            base = os.path.join(etat, "maisons", "maison-test",
                                "documents", "books")
            ecrire(os.path.join(base, "_ordre.json"), ["affaire-test"])
            ecrire(os.path.join(base, "affaire-test.json"), {
                "id": "affaire-test", "maison_id": "maison-test",
                "tables": [{"titre": "⚔️ Actions", "colonnes": ["N°", "Action"],
                            "lignes": [{"cellules": ["120", "Faire"]}]}]})
            ecrire(os.path.join(etat, "actes.json"), [])
            entree.racine = racine
            with mock.patch.dict(os.environ,
                                 {"LE_CONSEIL_CONTEXTE": "120"}, clear=False):
                entree.ajouter("actes", [{"id": "acte-par-la-porte"}])
            with io.open(os.path.join(etat, "actes.json"), encoding="utf-8") as f:
                acte = json.load(f)[0]
            self.assertEqual(acte["action_id"], "120")
            self.assertEqual(acte["affaire_id"], "affaire-test")
            self.assertEqual(acte["relation_action"], "preuve")
        finally:
            entree.racine = ancien
            shutil.rmtree(racine)

    def test_une_action_d_affaire_locale_de_chambre_est_indexee(self):
        racine = tempfile.mkdtemp(prefix="chainage-chambre-")
        try:
            etat = os.path.join(racine, "etat")
            ecrire(os.path.join(etat, "maisons.json"), [])
            ecrire(os.path.join(etat, "books", "_ordre.json"), [])
            ecrire(os.path.join(etat, "actes.json"), [{
                "id": "acte-local", "action_id": "91001",
                "affaire_id": "affaire-locale", "relation_action": "preuve"}])
            ecrire(os.path.join(racine, "chambres", "alarra", "books",
                                "affaire-locale.json"), {
                "id": "affaire-locale",
                "tables": [{"titre": "⚔️ Actions", "colonnes": ["N°"],
                            "lignes": [{"cellules": ["91001"]}]}]})
            self.assertEqual(chainage_actions.auditer(etat), [])
        finally:
            shutil.rmtree(racine)


if __name__ == "__main__":
    unittest.main()
