# -*- coding: utf-8 -*-
import copy
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
if NOYAU not in sys.path:
    sys.path.insert(0, NOYAU)

import histoire  # noqa: E402
SCRIPTS_DIR = os.path.dirname(NOYAU)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
from agents import reconcilier  # noqa: E402


def volume():
    return {
        "id": "affaire-test",
        "maison_id": "maison-test",
        "tables": [
            {"titre": "⚔️ Actions",
             "colonnes": ["N°", "Action", "🧰 Moyens", "⏳ État", "Jour fait"],
             "lignes": [{"cellules": ["120", "Faire", "M01", "à faire", ""]}]},
            {"titre": "🗝️ Clefs",
             "colonnes": ["N°", "Clef", "⚖️ Décision"],
             "lignes": [{"cellules": ["110", "Ouvrir", "en suspens"]}]},
            {"titre": "🔒 Verrous", "colonnes": ["N°", "Verrou"],
             "lignes": [{"cellules": ["101", "Ancien"]}]},
            {"titre": "🎯 États cibles", "colonnes": ["N°", "État"],
             "lignes": [{"cellules": ["100", "Tenir"]}]},
        ],
    }


class HistoireAffairesTest(unittest.TestCase):
    def setUp(self):
        self.etat = tempfile.mkdtemp(prefix="histoire-affaires-")
        with io.open(os.path.join(self.etat, "horloges.json"), "w", encoding="utf-8") as f:
            json.dump({"rhaenyra": {"annee": 129, "lune": 4, "jour": 4}}, f)
        with io.open(os.path.join(self.etat, "joueurs.json"), "w", encoding="utf-8") as f:
            json.dump([{"personnage_id": "rhaenyra", "role": "principal"}], f)

    def tearDown(self):
        shutil.rmtree(self.etat)

    def test_toutes_les_mutations_de_ligne_sont_structurees(self):
        avant = volume()
        apres = copy.deepcopy(avant)
        action = apres["tables"][0]["lignes"][0]["cellules"]
        action[2], action[3], action[4] = "M02", "faite", "129.4.4"
        clef = apres["tables"][1]["lignes"][0]["cellules"]
        clef[1], clef[2] = "Ouvrir vite", "oui"
        apres["tables"][2]["lignes"][0]["cellules"][1] = "Nouveau"

        ev = histoire.evenements_du_volume(avant, apres)
        par_type = {}
        for e in ev:
            par_type.setdefault(e["quoi"], []).append(e)
        self.assertEqual(par_type["action.fermee"][0]["avant"], "à faire")
        self.assertEqual(par_type["action.fermee"][0]["apres"], "faite")
        self.assertEqual(par_type["action.datee"][0]["apres"], "129.4.4")
        self.assertEqual(par_type["action.modifiee"][0]["changements"][0]["colonne"],
                         "🧰 Moyens")
        self.assertEqual(par_type["clef.decidee"][0]["apres"], "oui")
        self.assertEqual(par_type["clef.modifiee"][0]["changements"][0]["colonne"],
                         "Clef")
        self.assertEqual(par_type["verrou.modifiee"][0]["changements"][0]["avant"],
                         "Ancien")

    def test_registres_plats_des_moyens_et_offices(self):
        moyen_a = {"id": "plan-moyens", "maison_id": "maison-test",
                    "titre": "Les moyens",
                    "colonnes": ["🧰 N°", "Le moyen", "🔎 État"],
                    "lignes": [{"cellules": ["M01", "Or", "sûr"]}]}
        moyen_b = copy.deepcopy(moyen_a)
        moyen_b["lignes"][0]["cellules"][1:] = ["Or compté", "épuisé"]
        ev = histoire.evenements_du_volume(moyen_a, moyen_b)
        self.assertEqual([e["quoi"] for e in ev],
                         ["moyen.etat", "moyen.modifie"])
        self.assertEqual(ev[0]["avant"], "sûr")
        self.assertEqual(ev[0]["apres"], "épuisé")
        self.assertEqual(ev[1]["changements"][0]["colonne"], "Le moyen")

        office_a = {"id": "plan-offices", "maison_id": "maison-test",
                    "titre": "Les offices",
                    "colonnes": ["🪶 N°", "Office", "Titulaire"],
                    "lignes": [{"cellules": ["O01", "Deniers", "Aldon"]}]}
        office_b = copy.deepcopy(office_a)
        office_b["lignes"][0]["cellules"][2] = "Vacant"
        ev = histoire.evenements_du_volume(office_a, office_b)
        self.assertEqual(ev[0]["quoi"], "office.modifiee")
        self.assertEqual(ev[0]["changements"][0]["apres"], "Vacant")

    def test_mains_mesures_et_seuils_laissent_une_transition(self):
        avant = {"id": "@mains", "_type_document": "mains",
                 "maison_id": "maison-test", "mains": [{
                     "id": "vivres", "mandat": None,
                     "mesure": [{"id": "jours", "valeur": 73, "reliquat": 0}],
                     "seuils": [{"id": "alerte", "valeur": 20, "quand": "sous"}]}]}
        apres = copy.deepcopy(avant)
        apres["mains"][0]["mandat"] = "Sara tranche"
        apres["mains"][0]["mesure"][0]["valeur"] = 72
        apres["mains"][0]["seuils"][0]["valeur"] = 18
        ev = histoire.evenements_du_volume(avant, apres)
        self.assertEqual([e["quoi"] for e in ev],
                         ["main.modifiee", "mesure.changee", "seuil.modifie"])
        self.assertEqual(ev[1]["avant"], 73)
        self.assertEqual(ev[1]["apres"], 72)
        self.assertEqual(ev[1]["changements"][0]["champ"], "valeur")

    def test_journal_et_empreinte_avancent_ensemble(self):
        avant = volume()
        apres = copy.deepcopy(avant)
        apres["tables"][0]["lignes"][0]["cellules"][3] = "en cours"
        n = histoire.journaliser_et_actualiser(
            {avant["id"]: avant}, {apres["id"]: apres}, self.etat,
            par="aldon-hask", outil="test")
        self.assertEqual(n, 1)
        with io.open(os.path.join(self.etat, histoire.FICHIER), encoding="utf-8") as f:
            ligne = json.loads(f.readline())
        self.assertEqual(ligne["quoi"], "action.engagee")
        self.assertEqual(ligne["par"], "aldon-hask")
        self.assertEqual(ligne["document"],
                         "etat/maisons/maison-test/documents/books/affaire-test.json")
        self.assertTrue(ligne["transition_id"])
        with io.open(os.path.join(self.etat, histoire.EMPREINTES), encoding="utf-8") as f:
            empreinte = json.load(f)
        self.assertEqual(empreinte["maison:maison-test"]["affaire-test"], apres)

    def test_la_porte_conserve_la_provenance_du_call_contextualise(self):
        avant = volume()
        apres = copy.deepcopy(avant)
        apres["tables"][0]["lignes"][0]["cellules"][3] = "en cours"
        env = {
            "LE_CONSEIL_QUI": "gerardys",
            "LE_CONSEIL_CONTEXTE": "23030",
            "LE_CONSEIL_SESSION": "session-gerardys-23030",
            "LE_CONSEIL_REF": "r-1",
            "LE_CONSEIL_MODE": "journee",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            histoire.journaliser(
                {avant["id"]: avant}, {apres["id"]: apres}, self.etat,
                outil="test")
        with io.open(os.path.join(self.etat, histoire.FICHIER),
                     encoding="utf-8") as f:
            ligne = json.loads(f.readline())
        self.assertEqual(ligne["par"], "gerardys")
        self.assertEqual(ligne["contexte_id"], "23030")
        self.assertEqual(ligne["session_id"], "session-gerardys-23030")
        self.assertEqual(ligne["ref"], "r-1")
        self.assertEqual(ligne["mode_appel"], "journee")

    def test_une_reconciliation_ne_sattribue_pas_le_contexte_declencheur(self):
        avant = volume()
        apres = copy.deepcopy(avant)
        apres["tables"][0]["lignes"][0]["cellules"][3] = "en cours"
        env = {"LE_CONSEIL_QUI": "gerardys",
               "LE_CONSEIL_CONTEXTE": "23030",
               "LE_CONSEIL_SESSION": "session-gerardys-23030"}
        with mock.patch.dict(os.environ, env, clear=False):
            histoire.journaliser(
                {avant["id"]: avant}, {apres["id"]: apres}, self.etat,
                certitude="constate", outil="runtime:codex")
        with io.open(os.path.join(self.etat, histoire.FICHIER),
                     encoding="utf-8") as f:
            ligne = json.loads(f.readline())
        self.assertEqual(ligne["certitude"], "constate")
        self.assertNotIn("contexte_id", ligne)
        self.assertNotIn("session_id", ligne)

    def test_ecriture_directe_est_reconciliee_une_seule_fois(self):
        racine = tempfile.mkdtemp(prefix="reconcilier-direct-")
        ancien_etat, anciennes_chambres = reconcilier.ETAT, reconcilier.CHAMBRES
        try:
            etat = os.path.join(racine, "etat")
            chambres = os.path.join(racine, "chambres")
            base = os.path.join(etat, "maisons", "maison-test", "documents", "books")
            os.makedirs(base)
            os.makedirs(chambres)
            with io.open(os.path.join(etat, "maisons.json"), "w", encoding="utf-8") as f:
                json.dump([{"id": "maison-test"}], f)
            with io.open(os.path.join(base, "_ordre.json"), "w", encoding="utf-8") as f:
                json.dump(["affaire-test"], f)
            fichier = os.path.join(base, "affaire-test.json")
            with io.open(fichier, "w", encoding="utf-8") as f:
                json.dump(volume(), f)
            reconcilier.ETAT, reconcilier.CHAMBRES = etat, chambres
            reconcilier.passer(True, amorcer=True)

            change = volume()
            change["tables"][0]["lignes"][0]["cellules"][3] = "en cours"
            with io.open(fichier, "w", encoding="utf-8") as f:
                json.dump(change, f)
            _, total, _, _, _ = reconcilier.passer(
                True, outil="runtime:codex")
            self.assertEqual(total, 1)
            _, second, _, _, _ = reconcilier.passer(
                True, outil="runtime:codex")
            self.assertEqual(second, 0)
            with io.open(os.path.join(etat, histoire.FICHIER), encoding="utf-8") as f:
                lignes = [json.loads(x) for x in f if x.strip()]
            self.assertEqual(len(lignes), 1)
            self.assertEqual(lignes[0]["outil"], "runtime:codex")
            self.assertEqual(lignes[0]["certitude"], "constate")
        finally:
            reconcilier.ETAT, reconcilier.CHAMBRES = ancien_etat, anciennes_chambres
            shutil.rmtree(racine)


if __name__ == "__main__":
    unittest.main()
