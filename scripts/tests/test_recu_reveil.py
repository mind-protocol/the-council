import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents.recu_reveil import RecuInvalide, deposer


def piece(observation, elements):
    return {
        "schema": "recu-reveil/1",
        "cause": {"type": "amorce", "id": "temps-libre-dans-un-lieu"},
        "rendu": "Un moment libre vous appartient aujourd’hui dans L’Archive.",
        "habitant": "living-stone-architect",
        "session": "session-essai",
        "date_jeu": "129.5.12",
        "suites": {"observation": observation, "elements": elements},
        "inconnus": ["L’intention de l’habitante reste inconnue."],
    }


class RecuReveilTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.registre = Path(self.tmp.name) / "recus.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def test_trois_formes_et_idempotence(self):
        artefact = piece("sorties_constatees", [
            {"type": "artefact", "adresse": "brouillons/prototype.json"}])
        parole = piece("sorties_constatees", [
            {"type": "parole", "adresse": "canal/a~b"}])
        silence = piece("aucune_sortie_visible", [])
        ids = []
        for valeur in (artefact, parole, silence):
            recu, ajoute = deposer(valeur, self.registre)
            self.assertTrue(ajoute)
            ids.append(recu["id"])
        _, ajoute = deposer(artefact, self.registre)
        self.assertFalse(ajoute)
        self.assertEqual(3, len(set(ids)))
        self.assertEqual(3, len(self.registre.read_text(encoding="utf-8").splitlines()))

    def test_le_silence_ne_peut_pas_cacher_une_sortie(self):
        faux = piece("aucune_sortie_visible", [
            {"type": "artefact", "adresse": "quelque-part"}])
        with self.assertRaises(RecuInvalide):
            deposer(faux, self.registre)

    def test_aucun_score_ni_verdict(self):
        faux = piece("aucune_sortie_visible", [])
        faux["score"] = 1
        with self.assertRaises(RecuInvalide):
            deposer(faux, self.registre)


if __name__ == "__main__":
    unittest.main()
