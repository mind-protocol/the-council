# -*- coding: utf-8 -*-
import math
import os
import sys
import unittest


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents import expose


ajouter_activation = expose.boucle_activation.ajouter_activation
charge_compute_decroissante = expose.boucle_activation.charge_compute_decroissante
mesurer_fatigue = expose.boucle_activation.mesurer_fatigue
mettre_a_jour_energies = expose.boucle_activation.mettre_a_jour_energies
mettre_a_jour_porte = expose.boucle_activation.mettre_a_jour_porte


class FatigueActivationTests(unittest.TestCase):
    def test_trente_minutes_de_compute_divisent_energie_par_deux(self):
        fiche = {"compute_minutes": 30.0, "compute_maj_mur_s": 1000.0}
        mesure = mesurer_fatigue(fiche, maintenant=1000.0)
        self.assertAlmostEqual(mesure["facteur_compute"], 0.5)
        self.assertAlmostEqual(mesure["facteur_total"], 0.5)

    def test_charge_compute_se_divise_par_deux_en_douze_heures(self):
        fiche = {"compute_minutes": 30.0, "compute_maj_mur_s": 1000.0}
        charge = charge_compute_decroissante(
            fiche, maintenant=1000.0 + 12 * 3600)
        self.assertAlmostEqual(charge, 15.0)
        self.assertAlmostEqual(
            mesurer_fatigue(fiche, maintenant=1000.0 + 12 * 3600)
            ["facteur_compute"], math.sqrt(0.5))

    def test_vingt_quatre_heures_de_retard_sont_gratuites(self):
        fiche = {"fin_fiction_s": 10 * 3600.0}
        mesure = mesurer_fatigue(
            fiche, instant_fiction_s=34 * 3600.0, maintenant=1000.0)
        self.assertAlmostEqual(mesure["ecart_heures"], 24.0)
        self.assertAlmostEqual(mesure["facteur_heures"], 1.0)

    def test_un_jour_apres_la_grace_divise_energie_par_deux(self):
        fiche = {"fin_fiction_s": 10 * 3600.0}
        mesure = mesurer_fatigue(
            fiche, instant_fiction_s=58 * 3600.0, maintenant=1000.0)
        self.assertAlmostEqual(mesure["ecart_heures"], 48.0)
        self.assertAlmostEqual(mesure["facteur_heures"], 0.5)

    def test_activation_empile_compute_et_temps_fictionnel(self):
        fiche = {}
        mesure = ajouter_activation(
            fiche, compute_minutes=30.0, instant_fiction_s=8 * 3600.0,
            duree_monde_s=2 * 3600.0, maintenant=1000.0)
        self.assertAlmostEqual(fiche["compute_minutes"], 30.0)
        self.assertAlmostEqual(fiche["fin_fiction_s"], 10 * 3600.0)
        self.assertAlmostEqual(mesure["facteur_compute"], 0.5)
        self.assertAlmostEqual(mesure["facteur_heures"], 1.0)
        self.assertAlmostEqual(mesure["facteur_total"], 0.5)

    def test_classe_sur_effective_sans_detruire_la_reserve_brute(self):
        etat = {
            "fatigue_acteurs": {
                "a": {"compute_minutes": 30.0,
                      "compute_maj_mur_s": 1000.0},
                "b": {"compute_minutes": 0.0,
                      "compute_maj_mur_s": 1000.0},
            },
        }
        horloge = {"present_secondes": 0.0, "source_cle": "test",
                   "source_id": "personne-sans-horloge",
                   "front_id": "personne-sans-horloge"}
        noeuds = {
            "pers:a": {"etat": "actif", "genre": "personne"},
            "pers:b": {"etat": "actif", "genre": "personne"},
        }
        classes = mettre_a_jour_energies(
            etat, horloge, {"pers:a": 1.0, "pers:b": 1.0},
            {"pers:a": 80.0, "pers:b": 50.0},
            {"pers:a": 0.0, "pers:b": 0.0}, noeuds, set(),
            maintenant_mur=1000.0)
        self.assertEqual([x[2] for x in classes], ["b", "a"])
        self.assertAlmostEqual(etat["acteurs"]["a"]["energie"], 40.0)
        self.assertAlmostEqual(etat["acteurs"]["a"]["energie_brute"], 80.0)

    def test_porte_a_hysteresis_trente_cinquante(self):
        etat = {}
        self.assertTrue(mettre_a_jour_porte(etat, "acteurs", "a", 0.40))
        self.assertFalse(mettre_a_jour_porte(etat, "acteurs", "a", 0.29))
        self.assertFalse(mettre_a_jour_porte(etat, "acteurs", "a", 0.40))
        self.assertTrue(mettre_a_jour_porte(etat, "acteurs", "a", 0.50))


if __name__ == "__main__":
    unittest.main()

