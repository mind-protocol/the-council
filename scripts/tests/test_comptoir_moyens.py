import json
import os
import subprocess
import sys
import tempfile
import unittest


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(RACINE, "scripts", "analyse", "comptoir_moyens.py")


def registre(liens_hors_porte=116):
    valeurs = {
        "containers-declares": 9,
        "modules-rattaches": 431,
        "modules-orphelins": 20,
        "liens-hors-porte": liens_hors_porte,
        "dependances-remontantes": 13,
        "commandes-bibliotheques": 0,
    }
    return {
        "maison_id": "maison-essai",
        "mains": [{
            "mesure": [
                {"id": identifiant, "quoi": identifiant, "valeur": valeur}
                for identifiant, valeur in valeurs.items()
            ]
        }],
    }


def observation(liens_hors_porte=116):
    return {
        "declaration": {str(n): {} for n in range(9)},
        "fichiers": 451,
        "orphelins": [str(n) for n in range(20)],
        "hors_porte": [str(n) for n in range(liens_hors_porte)],
        "remontees": [str(n) for n in range(13)],
        "commandes_bibliotheques": [],
    }


class ComptoirMoyensTest(unittest.TestCase):
    def passage(self, mains, obs, en_json=True):
        with tempfile.TemporaryDirectory() as dossier:
            chemin_mains = os.path.join(dossier, "mains.json")
            chemin_obs = os.path.join(dossier, "observation.json")
            with open(chemin_mains, "w", encoding="utf-8") as fh:
                json.dump(mains, fh)
            with open(chemin_obs, "w", encoding="utf-8") as fh:
                json.dump(obs, fh)
            commande = [sys.executable, SCRIPT, "--mains", chemin_mains,
                        "--observation", chemin_obs]
            if en_json:
                commande.append("--json")
            return subprocess.run(
                commande,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

    def test_comptes_identiques(self):
        passage = self.passage(registre(), observation())
        self.assertEqual(0, passage.returncode, passage.stderr)
        resultat = json.loads(passage.stdout)
        self.assertTrue(resultat["conforme"])
        self.assertTrue(all(ligne["ecart"] == 0 for ligne in resultat["comparaisons"]))

    def test_derive_d_un_lien(self):
        passage = self.passage(registre(116), observation(115))
        self.assertEqual(1, passage.returncode, passage.stderr)
        resultat = json.loads(passage.stdout)
        ligne = next(ligne for ligne in resultat["comparaisons"]
                      if ligne["id"] == "liens-hors-porte")
        self.assertEqual(-1, ligne["ecart"])
        self.assertFalse(ligne["conforme"])
        self.assertTrue(ligne["source_inscrite"].endswith(
            "mains.json#mesure/liens-hors-porte"))
        self.assertTrue(ligne["source_observee"].endswith(
            "observation.json#hors_porte"))

    def test_sortie_lisible_imprime_les_deux_valeurs_et_sources(self):
        passage = self.passage(registre(116), observation(115), en_json=False)
        self.assertEqual(1, passage.returncode, passage.stderr)
        self.assertIn("VALEURS DIVERGENTES ET LEURS SOURCES", passage.stdout)
        self.assertIn("inscrit : 116", passage.stdout)
        self.assertIn("mains.json#mesure/liens-hors-porte", passage.stdout)
        self.assertIn("observe : 115", passage.stdout)
        self.assertIn("observation.json#hors_porte", passage.stdout)

    def test_registre_incomplet(self):
        mains = registre()
        mains["mains"][0]["mesure"].pop()
        passage = self.passage(mains, observation())
        self.assertEqual(2, passage.returncode)
        self.assertIn("mesures absentes", passage.stderr)


if __name__ == "__main__":
    unittest.main()
