import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).with_name("valider_fiche.py")
SPEC = importlib.util.spec_from_file_location("valider_fiche", MODULE)
valider_fiche = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = valider_fiche
SPEC.loader.exec_module(valider_fiche)


def piece(etat="NON ESSAYÉE", preuve=None):
    return {
        "type": "arpentage-heritage/1",
        "date_constat": "129.5.12",
        "lieu": "L’Archive, Braavos",
        "segment": "mur nord",
        "provenance_rapportee": {
            "origine": "forme héritée de Peyredragon",
            "source": "Nicolas Lester Reynolds",
            "ref": "vmti35qnkbyvy",
            "nature": "témoignage",
        },
        "mesure": {"largeur": None, "hauteur": None, "unite": "non mesurée"},
        "observation_materielle": "pierre visible",
        "usage_braavosi": "mur de l'Archive",
        "transformation_desiree": "mur-étalon",
        "transformation": {"etat": etat, "preuve": preuve},
        "reserve": "dimensions inconnues",
        "observateur": "precision-observer",
    }


class ValidationTest(unittest.TestCase):
    def test_non_essayee_recevable_avec_reserve(self):
        resultat = valider_fiche.valider(piece())
        self.assertEqual("RECEVABLE AVEC RÉSERVE", resultat["verdict"])
        self.assertIn("dimensions incomplètes", resultat["reserves"])

    def test_essayee_sans_preuve_refusee(self):
        resultat = valider_fiche.valider(piece("ESSAYÉE"))
        self.assertEqual("NON RECEVABLE", resultat["verdict"])
        self.assertIn("preuve obligatoire pour ESSAYÉE", resultat["erreurs"])

    def test_realisee_avec_mesure_et_preuve(self):
        donnee = piece("RÉALISÉE", "photo et relevé signés")
        donnee["mesure"] = {"largeur": 2.4, "hauteur": 3.1, "unite": "m"}
        resultat = valider_fiche.valider(donnee)
        self.assertEqual("RECEVABLE", resultat["verdict"])


if __name__ == "__main__":
    unittest.main()
