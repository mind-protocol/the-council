# -*- coding: utf-8 -*-
import unittest

import mesures


class AdressesDeMesureTest(unittest.TestCase):
    def test_une_main_connue_est_lue_partout(self):
        self.assertEqual(
            mesures.adresses_dans(
                "preuve `vivres-peyredragon.jours-de-vivres`",
                {"vivres-peyredragon"}, autoriser_inconnues=False),
            [("vivres-peyredragon.jours-de-vivres",
              "vivres-peyredragon.jours-de-vivres")])

    def test_les_references_de_code_inconnues_sont_ignorees(self):
        texte = "`bataille2d.js` · `h.l1` · `process.argv` · `.cv-foule`"
        self.assertEqual(
            mesures.adresses_dans(texte, {"vivres-peyredragon"},
                                   autoriser_inconnues=False),
            [])

    def test_une_adresse_inconnue_reste_diagnosticable_dans_sa_colonne(self):
        self.assertEqual(
            mesures.adresses_dans("`vivres-peyredargon.jours`", set(),
                                   autoriser_inconnues=True),
            [("vivres-peyredargon.jours", "vivres-peyredargon.jours")])

    def test_la_forme_abregee_herite_seulement_dune_adresse_retenue(self):
        self.assertEqual(
            mesures.adresses_dans(
                "`vivres-peyredragon.jours` · `.muids`",
                {"vivres-peyredragon"}, autoriser_inconnues=False),
            [("vivres-peyredragon.jours", "vivres-peyredragon.jours"),
             ("vivres-peyredragon.muids", ".muids")])
        self.assertEqual(
            mesures.adresses_dans("`h.l1` · `.reflexe`", set(),
                                   autoriser_inconnues=False),
            [])


if __name__ == "__main__":
    unittest.main()
