import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "monde" / "braavos.py"
SPEC = importlib.util.spec_from_file_location("monde_braavos", MODULE)
braavos = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = braavos
SPEC.loader.exec_module(braavos)


class AdapterBraavosTest(unittest.TestCase):
    def test_quai_recoit_un_nom_braavien_sans_perdre_ses_adresses(self):
        source = {
            "salles": [{
                "id": "quai",
                "nom": "Le quai",
                "portes": [{"vers": "bourg"}],
            }]
        }

        resultat = braavos._adapter(source, salles={"quai", "bourg"})
        quai = resultat["salles"][0]

        self.assertEqual("braavos-quai", quai["id"])
        self.assertEqual("Le Quai des Deux Rives", quai["nom"])
        self.assertEqual("braavos-bourg", quai["portes"][0]["vers"])

    def test_les_autres_salles_gardent_leur_nom(self):
        source = {"id": "bourg", "nom": "Le bourg"}
        resultat = braavos._adapter(source, salles={"bourg"})

        self.assertEqual("braavos-bourg", resultat["id"])
        self.assertEqual("Le bourg", resultat["nom"])


if __name__ == "__main__":
    unittest.main()
