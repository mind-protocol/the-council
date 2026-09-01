# -*- coding: utf-8 -*-
import os
import sys
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from plan.expose import registre_decisions as R  # noqa: E402


class RegistreDecisionsTest(unittest.TestCase):
    def test_refuse_validation_si_resultat_non_verifie(self):
        proposition = {
            "geste_contributif": "FAIT — envoi réussi",
            "resultat_sous_jacent": "NON VÉRIFIÉ",
            "decision_reception": "VALIDÉ",
            "ligne": [""] * 9,
        }
        self.assertIn("explicitement VÉRIFIÉ", R.valider(proposition))

    def test_accepte_validation_apres_verification_explicite(self):
        proposition = {
            "geste_contributif": "FAIT",
            "resultat_sous_jacent": "CONFORME — VÉRIFIÉ",
            "decision_reception": "VALIDÉ",
            "ligne": [""] * 9,
        }
        self.assertIsNone(R.valider(proposition))

    def test_non_valide_ne_declenche_pas_la_garde_de_conformite(self):
        proposition = {
            "geste_contributif": "FAIT",
            "resultat_sous_jacent": "NON VÉRIFIÉ",
            "decision_reception": "NON REÇU",
            "ligne": [""] * 9,
        }
        self.assertIsNone(R.valider(proposition))


if __name__ == "__main__":
    unittest.main()
