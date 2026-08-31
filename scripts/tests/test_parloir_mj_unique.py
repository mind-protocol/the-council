# -*- coding: utf-8 -*-
import os
import sys
import unittest


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents import parloir


class MjUniqueTest(unittest.TestCase):
    def test_seul_mj_est_une_identite_de_maitre_du_jeu(self):
        self.assertTrue(parloir.est_un_mj("mj"))
        self.assertFalse(parloir.est_un_mj("mj-sombreval"))
        self.assertFalse(parloir.est_un_mj("mj-portreal"))
        self.assertFalse(parloir.est_un_mj("gerardys"))


if __name__ == "__main__":
    unittest.main()
