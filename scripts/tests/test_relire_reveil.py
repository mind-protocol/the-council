import json
import os
import subprocess
import sys
import tempfile
import unittest


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(RACINE, "scripts", "analyse", "relire_reveil.py")


SCHEMA = {
    "required": [
        "schema", "id", "cause", "rendu", "habitant", "session",
        "date_jeu", "suites", "inconnus", "enregistre_le",
    ],
    "additionalProperties": False,
    "properties": {
        champ: {} for champ in (
            "schema", "id", "cause", "rendu", "habitant", "session",
            "date_jeu", "ref", "suites", "inconnus", "enregistre_le",
        )
    },
}


def recu(observation="sorties_constatees", type_suite="artefact"):
    elements = []
    if observation == "sorties_constatees":
        elements = [{
            "type": type_suite,
            "adresse": "chambres/essai/piece.txt",
            "constat": "Une pièce existe à cette adresse.",
        }]
    return {
        "schema": "recu-reveil/1",
        "id": "rr-a9a6c3e6edfc7b6fd4c53e47",
        "cause": {"type": "billet", "id": "ref-1", "adresse": "canal/essai"},
        "rendu": "Une phrase réellement servie.",
        "habitant": "habitant-essai",
        "session": "session-essai",
        "date_jeu": "129.5.12",
        "ref": "ref-1",
        "suites": {"observation": observation, "elements": elements},
        "inconnus": ["L'intention de l'habitant n'est pas établie."],
        "enregistre_le": "2026-09-01T03:25:12Z",
    }


class RelireReveilTest(unittest.TestCase):
    def passage(self, piece, en_json=False):
        with tempfile.TemporaryDirectory() as dossier:
            schema = os.path.join(dossier, "schema.json")
            registre = os.path.join(dossier, "recus.jsonl")
            with open(schema, "w", encoding="utf-8") as fichier:
                json.dump(SCHEMA, fichier)
            with open(registre, "w", encoding="utf-8") as fichier:
                fichier.write(json.dumps(piece, ensure_ascii=False) + "\n")
            commande = [sys.executable, SCRIPT, "--schema", schema,
                        "--registre", registre, "--id", piece["id"]]
            if en_json:
                commande.append("--json")
            return subprocess.run(
                commande, capture_output=True, text=True, encoding="utf-8"
            )

    def test_artefact_separe_cause_faits_et_inconnus(self):
        passage = self.passage(recu(), en_json=True)
        self.assertEqual(0, passage.returncode, passage.stderr)
        rapport = json.loads(passage.stdout)[0]
        self.assertEqual("ref-1", rapport["cause_servie"]["id"])
        self.assertEqual("artefact", rapport["faits_observes"]["elements"][0]["type"])
        self.assertEqual(
            ["L'intention de l'habitant n'est pas établie."], rapport["inconnus"]
        )

    def test_parole_conserve_son_statut_descriptif(self):
        passage = self.passage(recu(type_suite="parole"), en_json=True)
        self.assertEqual(0, passage.returncode, passage.stderr)
        rapport = json.loads(passage.stdout)[0]
        self.assertEqual("parole", rapport["faits_observes"]["elements"][0]["type"])

    def test_aucune_sortie_visible_est_un_fait_sans_verdict(self):
        passage = self.passage(recu(observation="aucune_sortie_visible"))
        self.assertEqual(0, passage.returncode, passage.stderr)
        self.assertIn("aucune sortie visible constatée", passage.stdout)
        minuscules = passage.stdout.lower()
        for jugement in ("a obéi", "a désobéi", "a voulu", "a préféré"):
            self.assertNotIn(jugement, minuscules)

    def test_refuse_une_sortie_inventee_dans_une_liste_vide(self):
        piece = recu(observation="aucune_sortie_visible")
        piece["suites"]["elements"] = [{"type": "artefact", "adresse": "x"}]
        passage = self.passage(piece)
        self.assertEqual(2, passage.returncode)
        self.assertIn("liste vide", passage.stderr)


if __name__ == "__main__":
    unittest.main()
