# -*- coding: utf-8 -*-
import os
import sys
import unittest
from unittest import mock


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents import expose
from agents.activation.appels import _mission


date_civile_acteur = expose.boucle_activation.date_civile_acteur
commettre_lot_horloge = expose.boucle_activation.commettre_lot_horloge
horloge_directe = expose.boucle_activation.horloge_directe


class HorlogeLocaleActivationTests(unittest.TestCase):
    def test_le_temps_mural_ne_fait_plus_avancer_la_fiction(self):
        horloges = {
            "rhaenyra": {"annee": 129, "lune": 4, "jour": 4,
                          "minute": 540},
        }
        joueurs = [{"personnage_id": "rhaenyra", "role": "principal"}]
        ancien = {"horloge": {
            "source_cle": "rhaenyra:%s" % (
                ((129 * 12 + 3) * 30 + 3) * 1440 + 540),
            "front_cle": "rhaenyra:%s" % (
                ((129 * 12 + 3) * 30 + 3) * 1440 + 540),
            "commis_secondes": 900.0,
        }}

        def lire(chemin, _defaut):
            return joueurs if chemin.endswith("joueurs.json") else horloges

        mesures = [{"personnage_id": "rhaenyra", "occupe": True,
                    "a_tete": True}]
        with mock.patch("agents.activation.horloges.lire_json",
                        side_effect=lire), mock.patch(
                            "agents.activation.horloges.occupation.mesures",
                            return_value=mesures):
            matin, _ = horloge_directe(ancien, maintenant=1000.0)
            soir, _ = horloge_directe(ancien, maintenant=5000.0)
        self.assertEqual(matin["present_secondes"], 900.0)
        self.assertEqual(soir["present_secondes"], 900.0)

    def test_un_front_force_prend_sa_propre_source_et_sa_propre_horloge(self):
        horloges = {
            "rhaenyra": {"annee": 129, "lune": 5, "jour": 12,
                           "minute": 641},
            "nicolas-lester-reynolds": {
                "annee": 129, "lune": 5, "jour": 12, "minute": 467},
        }
        joueurs = [
            {"personnage_id": "rhaenyra", "role": "principal"},
            {"personnage_id": "nicolas-lester-reynolds", "role": "second"},
        ]

        def lire(chemin, _defaut):
            return joueurs if chemin.endswith("joueurs.json") else horloges

        mesures = [
            {"personnage_id": "rhaenyra", "occupe": True,
             "a_tete": True},
            {"personnage_id": "nicolas-lester-reynolds", "occupe": False,
             "a_tete": True},
        ]
        with mock.patch("agents.activation.horloges.lire_json",
                        side_effect=lire), mock.patch(
                            "agents.activation.horloges.occupation.mesures",
                            return_value=mesures):
            vague, _ = horloge_directe(
                {}, source_force="nicolas-lester-reynolds",
                front_force="nicolas-lester-reynolds")

        self.assertEqual(vague["source_id"], "nicolas-lester-reynolds")
        self.assertEqual(vague["front_id"], "nicolas-lester-reynolds")
        self.assertEqual(vague["base_secondes"], 0.0)

    def test_un_lot_parallele_avance_du_maximum_pas_de_la_somme(self):
        horloge = {"base_secondes": 600.0, "commis_secondes": 120.0,
                   "present_secondes": 720.0}
        avance = commettre_lot_horloge(horloge, [300, 900, 600])
        self.assertEqual(avance, 900.0)
        self.assertEqual(horloge["commis_secondes"], 1020.0)
        self.assertEqual(horloge["present_secondes"], 1620.0)

    def test_un_lot_sans_reussite_n_avance_pas(self):
        horloge = {"base_secondes": 600.0, "commis_secondes": 120.0,
                   "present_secondes": 720.0}
        self.assertEqual(commettre_lot_horloge(horloge, []), 0.0)
        self.assertEqual(horloge["present_secondes"], 720.0)

    def test_emploie_l_ancre_de_l_acteur_sans_doubler_l_ecart_du_front(self):
        horloges = {
            "rhaenyra": {"annee": 129, "lune": 4, "jour": 4, "minute": 540},
            "marlo-vasse": {"annee": 129, "lune": 4, "jour": 4, "minute": 720},
        }
        vague = {
            "source_id": "rhaenyra",
            "front_id": "marlo-vasse",
            "horloge_pj": "marlo-vasse",
            "base_secondes": 10800.0,
            "present_secondes": 10890.0,
        }

        self.assertEqual(
            date_civile_acteur("aegon-ii", vague, horloges),
            {"annee": 129, "lune": 4, "jour": 4, "minute": 721},
        )

    def test_un_siege_activable_garde_sa_propre_horloge(self):
        horloges = {
            "rhaenyra": {"annee": 129, "lune": 4, "jour": 4, "minute": 540},
            "marlo-vasse": {"annee": 129, "lune": 4, "jour": 5, "minute": 15},
        }
        vague = {
            "source_id": "rhaenyra",
            "front_id": "rhaenyra",
            "horloge_pj": "rhaenyra",
            "base_secondes": 0.0,
            "present_secondes": 0.0,
        }

        self.assertEqual(
            date_civile_acteur("marlo-vasse", vague, horloges),
            {"annee": 129, "lune": 4, "jour": 5, "minute": 15},
        )

    def test_la_mission_directe_porte_la_tache_et_l_acces_depot(self):
        mission = _mission({"id": "t", "quoi": "Tenir le registre"}, 10)
        self.assertIn("TÂCHE : `t`", mission)
        self.assertIn("Tenir le registre", mission)
        self.assertIn("accès au dépôt", mission)
        self.assertIn("Ne demande rien au MJ", mission)

    def test_la_mission_verrou_laisse_les_actions_contestables(self):
        mission = _mission({"id": "52101", "genre": "verrou",
                            "quoi": "Le terme est ambigu"}, 10)
        self.assertIn("VERROU : `52101`", mission)
        self.assertIn("pas sur une action prescrite", mission)
        self.assertIn("confirmer, les critiquer, les modifier", mission)
        self.assertIn("communique", mission)


if __name__ == "__main__":
    unittest.main()
