import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).with_name("controle_moyens.py")
SPEC = importlib.util.spec_from_file_location("controle_moyens", MODULE)
controle_moyens = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = controle_moyens
SPEC.loader.exec_module(controle_moyens)


class ControleMoyensTest(unittest.TestCase):
    def test_accord_complet(self):
        mesures = [
            ("containers-declares", 1),
            ("modules-rattaches", 4),
            ("modules-orphelins", 1),
            ("liens-hors-porte", 2),
            ("dependances-remontantes", 3),
            ("commandes-bibliotheques", 0),
        ]
        mains = {
            "mains": [{
                "date_maj": "129.5.12",
                "mesure": [{"id": identifiant, "valeur": valeur} for identifiant, valeur in mesures],
            }]
        }
        registre = {
            "lignes": [{
                "cellules": [
                    "**M110**", "Container test", "5 fichiers de code observés",
                    "", "", "", "", "",
                    "mesuré le 129.5.12 : 4 fichiers rattachés, 1 orphelins, "
                    "2 liens hors porte, 3 remontées, 0 commande-bibliothèque",
                ]
            }]
        }
        resultat = controle_moyens.controler(mains, registre)
        self.assertEqual("COHERENT", resultat["verdict"])

    def test_ecart_detecte(self):
        mains = {
            "mains": [{
                "date_maj": "129.5.12",
                "mesure": [
                    {"id": "containers-declares", "valeur": 1},
                    {"id": "modules-rattaches", "valeur": 4},
                    {"id": "modules-orphelins", "valeur": 1},
                    {"id": "liens-hors-porte", "valeur": 9},
                    {"id": "dependances-remontantes", "valeur": 3},
                    {"id": "commandes-bibliotheques", "valeur": 0},
                ],
            }]
        }
        registre = {
            "lignes": [{
                "cellules": [
                    "M110", "Container test", "5 fichiers de code observés", "", "", "", "", "",
                    "mesuré le 129.5.12 : 4 fichiers rattachés, 1 orphelins, "
                    "2 liens hors porte, 3 remontées, 0 commande-bibliothèque",
                ]
            }]
        }
        resultat = controle_moyens.controler(mains, registre)
        self.assertEqual("A_CONTROLER", resultat["verdict"])
        ecarts = [c for c in resultat["comparaisons"] if c["statut"] == "ECART"]
        self.assertEqual(["liens-hors-porte"], [c["mesure"] for c in ecarts])

    def test_trois_pieces_gardent_trois_verdicts(self):
        mesures = [
            ("containers-declares", 1),
            ("modules-rattaches", 6),
            ("modules-orphelins", 2),
            ("liens-hors-porte", 0),
            ("dependances-remontantes", 0),
            ("commandes-bibliotheques", 0),
        ]
        mains = {
            "mains": [{
                "date_maj": "129.5.12",
                "mesure": [{"id": identifiant, "valeur": valeur} for identifiant, valeur in mesures],
            }]
        }
        registre = {
            "lignes": [{
                "cellules": [
                    "M110", "Container test", "7 fichiers de code observés", "", "", "", "", "",
                    "mesuré le 129.5.12 : 5 fichiers rattachés, 2 orphelins, "
                    "0 liens hors porte, 0 remontées, 0 commande-bibliothèque",
                ]
            }]
        }
        sonde = {
            "type": "constat-sonde-architecture/1",
            "date_constat": "129.5.12",
            "provenance": "fixture de test",
            "mesures": {
                "modules-rattaches": 6,
                "modules-orphelins": 3,
                "modules-observes": 9,
            },
        }
        resultat = controle_moyens.controler(mains, registre, sonde)
        self.assertEqual("A_CONTROLER", resultat["verdict"])
        self.assertEqual(
            {"mains_registre", "mains_sonde", "registre_sonde"},
            set(resultat["verdicts_paires"]),
        )
        self.assertTrue(all(
            paire["verdict"] == "A_CONTROLER"
            for paire in resultat["verdicts_paires"].values()
        ))


if __name__ == "__main__":
    unittest.main()
