# -*- coding: utf-8 -*-
import json
import os
import sys
import tempfile
import unittest


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOYAU = os.path.join(SCRIPTS, "noyau")
for chemin in (SCRIPTS, NOYAU):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

from plan.tisser import (charger_affaires_personnelles,  # noqa: E402
                         noeuds_affaires_personnelles,
                         aretes_affaires_personnelles, indexer, tisser)
from diffusion import GENRES_RELAIS  # noqa: E402


def affaire_personnelle():
    return {
        "id": "affaire-madre", "type": "affaire", "titre": "Se tenir",
        "_personnage_id": "madre", "_cle_personnelle": "affaire-madre",
        "tables": [
            {"titre": "🎯 Ce que je veux",
             "colonnes": ["N°", "L'état visé"],
             "lignes": [{"cellules": ["C.1", "Une voix tenue"]}]},
            {"titre": "🔒 Verrous",
             "colonnes": ["N°", "Le verrou", "Ce qu'il bloque"],
             "lignes": [{"cellules": ["V.1", "Le silence", "C.1"]}]},
            {"titre": "🗝️ Clefs",
             "colonnes": ["N°", "La clef", "Ouvre"],
             "lignes": [{"cellules": ["K.1", "La question", "V.1"]}]},
            {"titre": "⚔️ Actions",
             "colonnes": ["N°", "L'action", "Réalise", "Dépend de", "État"],
             "lignes": [{"cellules": ["P.1", "Écrire", "C.1", "K.1",
                                          "à faire"]}]},
        ],
    }


class TisserAffairesPersonnellesTest(unittest.TestCase):
    def test_les_quatre_types_sont_des_relais_d_energie(self):
        self.assertTrue({"etat_cible_personnel", "verrou_personnel",
                         "clef_personnelle", "action_personnelle"}
                        .issubset(set(GENRES_RELAIS)))

    def test_charge_une_chambre_et_resout_underscore_vers_tiret(self):
        with tempfile.TemporaryDirectory(prefix="tissu-perso-") as racine:
            books = os.path.join(racine, "chambres", "madre_test", "books")
            os.makedirs(books)
            livre = affaire_personnelle()
            livre["id"] = "affaire-madre-test"
            with open(os.path.join(books, "affaire-madre-test.json"), "w",
                      encoding="utf-8") as fichier:
                json.dump(livre, fichier, ensure_ascii=False)
            charges = charger_affaires_personnelles(
                racine, [{"id": "madre-test"}])
        self.assertEqual(1, len(charges))
        self.assertEqual("madre-test", charges[0]["_personnage_id"])

    def test_pose_les_quatre_types_avec_namespace(self):
        noeuds = {n["id"]: n for n in
                  noeuds_affaires_personnelles([affaire_personnelle()])}
        prefixe = "perso:madre:affaire-madre:"
        self.assertEqual("etat_cible_personnel",
                         noeuds[prefixe + "etat:C.1"]["genre"])
        self.assertEqual("verrou_personnel",
                         noeuds[prefixe + "verrou:V.1"]["genre"])
        self.assertEqual("clef_personnelle",
                         noeuds[prefixe + "clef:K.1"]["genre"])
        self.assertEqual("action_personnelle",
                         noeuds[prefixe + "action:P.1"]["genre"])
        self.assertEqual([prefixe + "clef:K.1"],
                         noeuds[prefixe + "action:P.1"]["depend_de"])

    def test_tisse_portage_tenue_et_structure(self):
        aretes = aretes_affaires_personnelles([affaire_personnelle()])
        triplets = {(a["de"], a["vers"], a["nature"]) for a in aretes}
        racine = "perso:madre:affaire-madre"
        self.assertIn(("pers:madre", racine, "porte"), triplets)
        etat = racine + ":etat:C.1"
        verrou = racine + ":verrou:V.1"
        clef = racine + ":clef:K.1"
        action = racine + ":action:P.1"
        self.assertIn((racine, etat, "decoupe"), triplets)
        self.assertIn(("pers:madre", etat, "porte"), triplets)
        self.assertIn(("pers:madre", action, "tient"), triplets)
        self.assertIn((verrou, etat, "bloque"), triplets)
        self.assertIn((clef, verrou, "ouvre"), triplets)
        self.assertIn((action, etat, "realise"), triplets)
        self.assertIn((action, clef, "depend_de"), triplets)

    def test_integration_resout_toutes_les_aretes_personnelles(self):
        livre = affaire_personnelle()
        personnages = [{"id": "madre", "nom": "Madre", "etat": "actif"}]
        noeuds, _ = indexer([], [], [], [], [], personnages,
                            affaires_personnelles=[livre])
        aretes = tisser([], [], [], [], [], personnages=personnages,
                        affaires_personnelles=[livre])
        locales = [a for a in aretes
                   if a["source"].startswith("chambres/personnelles")]
        self.assertTrue(locales)
        self.assertTrue(all(a["de"] in noeuds and a["vers"] in noeuds
                            for a in locales))

    def test_tisse_plusieurs_porteurs_sur_un_verrou_de_maison(self):
        livre = {
            "id": "affaire-compute", "type": "plan", "titre": "Compute",
            "tables": [
                {"titre": "🎯 États cibles",
                 "colonnes": ["N°", "L'état cible"],
                 "lignes": [{"cellules": ["52100", "Un terme explicite"]}]},
                {"titre": "🔒 Verrous",
                 "colonnes": ["N°", "Le verrou", "Bloque", "Porteurs",
                              "État", "Dépend de"],
                 "lignes": [{"cellules": [
                     "52101", "Le terme est ambigu", "52100",
                     "madre · lucia", "ouvert", "52000"]}]},
                {"titre": "🎯 États cibles",
                 "colonnes": ["N°", "L'état cible"],
                 "lignes": [{"cellules": ["52000", "Le départ est établi"]}]},
            ],
        }
        personnages = [
            {"id": "madre", "nom": "Madre", "etat": "dormant"},
            {"id": "lucia", "nom": "Lucia", "etat": "dormant"},
        ]
        aretes = tisser([livre], [], [], [], [], personnages=personnages)
        triplets = {(a["de"], a["vers"], a["nature"]) for a in aretes}
        self.assertIn(("52101", "pers:madre", "tient"), triplets)
        self.assertIn(("52101", "pers:lucia", "tient"), triplets)
        self.assertIn(("52101", "52000", "depend_de"), triplets)


if __name__ == "__main__":
    unittest.main()
