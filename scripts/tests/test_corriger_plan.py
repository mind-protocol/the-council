# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plan"))
from plan.expose import corriger_plan as C  # noqa: E402


class CorrigerPlanTest(unittest.TestCase):
    def test_une_adresse_est_le_nombre_en_tete(self):
        self.assertEqual("26009", C.numero_de("**26009** — le verrou"))
        self.assertIsNone(C.numero_de("— LIGNE MORTE (doublon de 26009)"))

    def test_un_fragment_unique_est_remplace(self):
        livres = [{
            "id": "affaire-a",
            "tables": [{
                "titre": "Actions",
                "colonnes": ["N°", "Texte"],
                "lignes": [{"cellules": ["28023", "voir (verrou 26020)"]}],
            }],
        }]
        correction = {
            "livre": "affaire-a",
            "table": "Actions",
            "numero": "28023",
            "colonne": "Texte",
            "avant_dans": "26020",
            "apres_dans": "26009",
        }

        action, detail = C.preparer_correction(livres, correction)

        self.assertEqual("poser", action)
        self.assertEqual("voir (verrou 26009)", correction["_apres_calcule"])
        self.assertEqual("voir (verrou 26020)", detail[2])

    def test_un_fragment_ambigu_est_refuse(self):
        livres = [{
            "id": "affaire-a",
            "tables": [{
                "titre": "Actions",
                "colonnes": ["N°", "Texte"],
                "lignes": [{"cellules": ["28023", "26020 puis 26020"]}],
            }],
        }]
        correction = {
            "livre": "affaire-a",
            "table": "Actions",
            "numero": "28023",
            "colonne": "Texte",
            "avant_dans": "26020",
            "apres_dans": "26009",
        }

        action, _ = C.preparer_correction(livres, correction)

        self.assertEqual("refus", action)

    def test_un_remplacement_qui_contient_l_ancien_fragment_est_idempotent(self):
        livres = [{
            "id": "affaire-a",
            "tables": [{
                "titre": "Actions",
                "colonnes": ["N°", "Texte"],
                "lignes": [{"cellules": ["28023", "avant puis après"]}],
            }],
        }]
        correction = {
            "livre": "affaire-a",
            "table": "Actions",
            "numero": "28023",
            "colonne": "Texte",
            "avant_dans": "avant",
            "apres_dans": "avant puis après",
        }

        action, _ = C.preparer_correction(livres, correction)

        self.assertEqual("deja", action)


if __name__ == "__main__":
    unittest.main()
