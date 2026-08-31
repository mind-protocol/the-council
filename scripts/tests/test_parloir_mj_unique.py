# -*- coding: utf-8 -*-
import os
import sys
import unittest
from unittest import mock


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents import parloir
from agents import chambre_affaire


class MjUniqueTest(unittest.TestCase):
    def test_seul_mj_est_une_identite_de_maitre_du_jeu(self):
        self.assertTrue(parloir.est_un_mj("mj"))
        self.assertFalse(parloir.est_un_mj("mj-sombreval"))
        self.assertFalse(parloir.est_un_mj("mj-portreal"))
        self.assertFalse(parloir.est_un_mj("gerardys"))

    def test_seul_le_front_joueur_ou_dev_peut_appeler_le_mj(self):
        self.assertFalse(parloir.appel_mj_autorise("gerardys"))
        self.assertTrue(parloir.appel_mj_autorise("gerardys", joueur=True))
        self.assertTrue(parloir.appel_mj_autorise("dev"))

    def test_un_pnj_ne_peut_pas_demander_un_verdict(self):
        argv = ["parloir.py", "--demander", "--de", "gerardys",
                "--a", "mj", "que dit le registre ?"]
        with mock.patch.object(sys, "argv", argv):
            with self.assertRaisesRegex(SystemExit,
                                        "PNJ ne demande plus de verdict"):
                parloir.main()

    def test_un_pnj_ne_peut_pas_ecrire_au_mj(self):
        argv = ["parloir.py", "--dire", "--de", "gerardys",
                "--a", "mj", "que dois-je faire ?"]
        with mock.patch.object(sys, "argv", argv):
            with self.assertRaisesRegex(SystemExit,
                                        "PNJ ne s'adresse pas au MJ"):
                parloir.main()

    def test_le_gabarit_pnj_ne_prescrit_plus_d_appel_au_mj(self):
        volume = chambre_affaire.gabarit("gerardys")
        texte = str(volume)
        self.assertNotIn("--tenter", texte)
        self.assertNotIn("--faire", texte)
        self.assertNotIn("--demander", texte)
        self.assertIn("sans permission du MJ", texte)

    def test_le_manuel_pnj_ne_reintroduit_pas_les_anciens_verbes(self):
        manuel = os.path.join(SCRIPTS, "agents", "prompts", "metier.md")
        with open(manuel, encoding="utf-8") as f:
            texte = f.read()
        self.assertNotIn("parloir.py --tenter", texte)
        self.assertNotIn("parloir.py --faire", texte)
        self.assertNotIn("parloir.py --demander", texte)


if __name__ == "__main__":
    unittest.main()
