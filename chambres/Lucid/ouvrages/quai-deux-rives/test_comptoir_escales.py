import importlib.util
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


MODULE = Path(__file__).with_name("comptoir_escales.py")
SPEC = importlib.util.spec_from_file_location("comptoir_escales", MODULE)
comptoir = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = comptoir
SPEC.loader.exec_module(comptoir)


class ComptoirEscalesTest(unittest.TestCase):
    def registre(self):
        return {
            "version": 1,
            "lieu_id": "braavos-quai",
            "nom": "Le Quai des Deux Rives",
            "escales": [],
        }

    def test_annonce_accostage_et_depart_restent_distincts(self):
        registre = self.registre()
        args = Namespace(
            date="129.5.12",
            navire="La Patiente",
            capitaine="Capitaine d'essai",
            provenance="Deuxième rive",
            cargaison="Cordages",
            preuve="billet d'essai",
        )
        escale = comptoir.annoncer(registre, args)
        self.assertEqual("ANNONCEE", escale["statut"])

        comptoir.changer_statut(registre, escale["id"], "A_QUAI", "vue du quai")
        self.assertEqual("A_QUAI", escale["statut"])

        comptoir.changer_statut(registre, escale["id"], "REPARTIE", "vue du départ")
        self.assertEqual("REPARTIE", escale["statut"])

    def test_accostage_sans_annonce_est_refuse(self):
        registre = self.registre()
        with self.assertRaisesRegex(ValueError, "escale inconnue"):
            comptoir.changer_statut(registre, "escale-0001", "A_QUAI", "rien")

    def test_sauvegarde_atomique_recharge_le_registre(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "escales.json"
            comptoir.sauver(chemin, self.registre())
            self.assertEqual("braavos-quai", comptoir.charger(chemin)["lieu_id"])
            json.loads(chemin.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
