# -*- coding: utf-8 -*-
import os
import sys
import json
import tempfile
import unittest
from unittest import mock


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents import expose
from agents.activation import cli as activation_cli


borner_eligibles_lieu = expose.boucle_activation.borner_eligibles_lieu
mettre_a_jour_energies = expose.boucle_activation.mettre_a_jour_energies
mettre_a_jour_energie_graphe = \
    expose.boucle_activation.mettre_a_jour_energie_graphe
choisir_tache = expose.boucle_activation.choisir_tache
energie_de_tache = expose.boucle_activation.energie_de_tache
amorcer_sources_energie = expose.boucle_activation.amorcer_sources_energie
sources_energie_braavos = expose.boucle_activation.sources_energie_braavos


class ActivationLieuTests(unittest.TestCase):
    def test_retissage_utilise_la_facade_et_refuse_un_echec(self):
        succes = mock.Mock(returncode=0, stdout="ok", stderr="")
        with mock.patch("agents.activation.cli.subprocess.run",
                        return_value=succes) as lancer:
            activation_cli.retisser_tissu()
        commande = lancer.call_args.args[0]
        self.assertEqual(commande[-1], "--ecrire")
        self.assertEqual(os.path.basename(commande[-2]), "tisser.py")
        self.assertEqual(lancer.call_args.kwargs["cwd"], activation_cli.socle.RACINE)

        echec = mock.Mock(returncode=1, stdout="", stderr="cassé")
        with mock.patch("agents.activation.cli.subprocess.run",
                        return_value=echec):
            with self.assertRaisesRegex(RuntimeError, "cassé"):
                activation_cli.retisser_tissu()

    def test_un_lot_actif_force_un_retissage_avant_le_cycle_suivant(self):
        cycles = [({}, 1, 1), KeyboardInterrupt()]

        def cycle_puis_arret(*_args, **_kwargs):
            resultat = cycles.pop(0)
            if isinstance(resultat, BaseException):
                raise resultat
            return resultat

        argv = ["boucle_activation.py", "--intervalle", "0.01"]
        sortie = mock.MagicMock()
        with mock.patch.object(activation_cli.sys, "argv", argv), \
                mock.patch.object(activation_cli.sys, "stdout", sortie), \
                mock.patch.object(activation_cli.io, "TextIOWrapper",
                                  return_value=sortie), \
                mock.patch.object(activation_cli, "journaliser"), \
                mock.patch.object(activation_cli, "VerrouBoucle") as verrou, \
                mock.patch.object(activation_cli, "retisser_tissu") as retisser, \
                mock.patch.object(activation_cli, "cycle",
                                  side_effect=cycle_puis_arret):
            verrou.return_value.__enter__.return_value = None
            self.assertEqual(activation_cli.main(), 130)

        self.assertEqual(retisser.call_count, 2)

    def test_braavos_ne_garde_que_les_acteurs_du_lieu(self):
        eligibles = [
            (20.0, 0.5, "venitien", {}),
            (19.0, 0.4, "dragon", {}),
        ]
        noeuds = {
            "pers:venitien": {"lieu_id": "braavos"},
            "pers:dragon": {"lieu_id": "peyredragon"},
        }
        self.assertEqual(
            borner_eligibles_lieu(eligibles, noeuds, "braavos"),
            [eligibles[0]],
        )

    def test_sans_lieu_ne_change_pas_le_classement(self):
        eligibles = [(20.0, 0.5, "venitien", {})]
        self.assertIs(borner_eligibles_lieu(eligibles, {}, None), eligibles)

    def test_braavos_n_amorce_pas_un_habitant_ordinaire(self):
        etat = {}
        classes = mettre_a_jour_energies(
            etat,
            {"present_secondes": 0.0, "horloge_pj": None,
             "source_cle": "test"},
            {"pers:venitien": 0.0},
            {"pers:venitien": 0.0},
            {"pers:venitien": 0.0},
            {"pers:venitien": {
                "genre": "personne", "etat": "dormant",
                "condition": "libre", "lieu_id": "braavos",
            }},
            set(),
            maintenant_mur=1000.0,
            lieu_force="braavos",
            sources_energie={"nicolas"},
        )
        self.assertEqual(classes, [])

    def test_braavos_inclut_un_porteur_dormant_sans_creer_son_energie(self):
        etat = {}
        classes = mettre_a_jour_energies(
            etat,
            {"present_secondes": 0.0, "horloge_pj": None,
             "source_cle": "test"},
            {"pers:venitien": 0.0},
            {"pers:venitien": 7.0},
            {"pers:venitien": 0.0},
            {"pers:venitien": {
                "genre": "personne", "etat": "dormant",
                "condition": "libre", "lieu_id": "braavos",
            }},
            set(), maintenant_mur=1000.0, lieu_force="braavos",
            sources_energie={"venitien"},
        )
        self.assertEqual([ligne[2] for ligne in classes], ["venitien"])
        self.assertEqual(classes[0][0], 7.0)
        self.assertEqual(classes[0][3]["source_energie"], "braavos")

    def test_braavos_inclut_un_dormant_relie_avec_energie_positive(self):
        etat = {}
        classes = mettre_a_jour_energies(
            etat,
            {"present_secondes": 0.0, "horloge_pj": None,
             "source_cle": "test"},
            {"pers:venitien": 0.2},
            {"pers:venitien": 0.2},
            {"pers:venitien": 0.0},
            {"pers:venitien": {
                "genre": "personne", "etat": "dormant",
                "condition": "libre", "lieu_id": "braavos",
            }},
            set(), maintenant_mur=1000.0, lieu_force="braavos",
            sources_energie={"nicolas"},
        )
        self.assertEqual([ligne[2] for ligne in classes], ["venitien"])
        self.assertNotIn("source_energie", classes[0][3])

    def test_sources_braavos_viennent_de_nicolas_et_des_tenu_par(self):
        noeuds = {
            "pers:nicolas-lester-reynolds": {"lieu_id": "braavos"},
            "pers:madre": {"lieu_id": "braavos"},
            "pers:ailleurs": {"lieu_id": "peyredragon"},
        }
        with tempfile.TemporaryDirectory() as dossier:
            for nom, porteur in (("affaire-a.json", "madre"),
                                 ("affaire-b.json", "ailleurs")):
                with open(os.path.join(dossier, nom), "w", encoding="utf-8") as f:
                    json.dump({"tenu_par": porteur}, f)
            self.assertEqual(
                sources_energie_braavos(noeuds, dossier),
                ["madre", "nicolas-lester-reynolds"],
            )

    def test_une_source_n_est_amorcee_qu_une_fois(self):
        etat = {}
        energies = {"pers:madre": 0.0}
        self.assertEqual(
            amorcer_sources_energie(etat, energies, {"madre"}, "braavos", 2),
            ["madre"],
        )
        self.assertEqual(energies["pers:madre"], 1.0)
        energies["pers:madre"] = 1.0
        etat["graphe"]["fronts"]["braavos"]["noeuds"]["pers:madre"] = 1.0
        self.assertEqual(
            amorcer_sources_energie(etat, energies, {"madre"}, "braavos", 3),
            [],
        )
        self.assertEqual(energies["pers:madre"], 1.0)

    def test_energie_braavos_a_son_overlay_independant(self):
        etat = {"graphe": {
            "mis_a_jour_a": 600.0,
            "noeuds": {"pers:venitien": 0.0},
        }}
        energies = mettre_a_jour_energie_graphe(
            etat,
            {"present_secondes": 0.0},
            {"pers:venitien": 0.5},
            {"pers:venitien": {"genre": "personne"}},
            {"pers:venitien": []}, {}, front="braavos",
        )
        self.assertEqual(energies["pers:venitien"], 50.0)
        self.assertEqual(etat["graphe"]["noeuds"]["pers:venitien"], 0.0)
        self.assertEqual(
            etat["graphe"]["fronts"]["braavos"]["mis_a_jour_a"], 0.0)

    def test_source_fatiguee_reste_classable_sous_un_point(self):
        etat = {}
        classes = mettre_a_jour_energies(
            etat,
            {"present_secondes": 0.0, "horloge_pj": None,
             "source_cle": "test"},
            {"pers:madre": 1.0}, {"pers:madre": 0.4},
            {"pers:madre": 0.0},
            {"pers:madre": {
                "genre": "personne", "etat": "dormant",
                "condition": "libre", "lieu_id": "braavos",
            }},
            set(), maintenant_mur=1000.0, lieu_force="braavos",
            sources_energie={"madre"},
        )
        self.assertEqual([x[2] for x in classes], ["madre"])
        self.assertGreater(classes[0][0], 0.0)
        self.assertLess(classes[0][0], 1.0)

    def test_amorcage_braavos_propose_une_premiere_tache(self):
        noeuds = {
            "pers:venitien": {
                "genre": "personne", "lieu_id": "braavos",
                "objectifs": [],
            },
        }
        tache = choisir_tache(
            "pers:venitien", noeuds, [], {"pers:venitien": []},
            {"pers:venitien": 10.0}, amorcage_lieu="braavos",
        )
        self.assertTrue(tache["creee"])
        self.assertIn("explorer sa situation à Braavos", tache["quoi"])

    def test_amorcage_braavos_prend_l_action_explicitement_tenue(self):
        noeuds = {
            "pers:madre": {
                "genre": "personne", "lieu_id": "braavos",
                "objectifs": [{"but": "Pratiquer"}],
            },
            "58300": {
                "genre": "action", "quoi": "Cartographier",
                "etat": "en cours", "depend_de": [],
            },
            "58310": {
                "genre": "action", "quoi": "Écrire le contrat",
                "etat": "à faire", "depend_de": ["58300"],
            },
        }
        aretes = [
            {"de": "58300", "vers": "pers:madre", "nature": "tient",
             "flou": False},
            {"de": "58310", "vers": "pers:madre", "nature": "tient",
             "flou": False},
        ]
        adj = {"pers:madre": ["58300", "58310"],
               "58300": ["pers:madre"], "58310": ["pers:madre"]}
        tache = choisir_tache(
            "pers:madre", noeuds, aretes, adj,
            {"pers:madre": 10.0, "58300": 0.0, "58310": 0.0},
            amorcage_lieu="braavos",
        )
        self.assertEqual("58300", tache["id"])
        self.assertTrue(tache["affectation_directe"])
        self.assertEqual(10.0, energie_de_tache(
            tache, {"58300": 0.0}, 10.0))

    def test_braavos_reveille_sur_le_verrou_et_ignore_l_action(self):
        noeuds = {
            "pers:madre": {"genre": "personne", "lieu_id": "braavos"},
            "52101": {"genre": "verrou", "quoi": "Le terme est ambigu",
                      "etat": "ouvert"},
            "52310": {"genre": "action", "quoi": "Cartographier",
                      "etat": "à faire", "depend_de": []},
        }
        aretes = [
            {"de": "52101", "vers": "pers:madre", "nature": "tient",
             "flou": False},
            {"de": "52310", "vers": "pers:madre", "nature": "tient",
             "flou": False},
        ]
        adj = {"pers:madre": ["52101", "52310"],
               "52101": ["pers:madre"], "52310": ["pers:madre"]}
        tache = choisir_tache(
            "pers:madre", noeuds, aretes, adj,
            {"pers:madre": 10.0, "52101": 0.0, "52310": 100.0},
            amorcage_lieu="braavos", sur_verrous=True)
        self.assertEqual("52101", tache["id"])
        self.assertEqual("verrou", tache["genre"])

    def test_braavos_ne_reveille_pas_sur_un_verrou_sans_porteur(self):
        noeuds = {
            "pers:madre": {"genre": "personne", "lieu_id": "braavos"},
            "52101": {"genre": "verrou", "quoi": "Le terme est ambigu",
                      "etat": "ouvert"},
        }
        adj = {"pers:madre": ["52101"], "52101": ["pers:madre"]}
        tache = choisir_tache(
            "pers:madre", noeuds, [], adj,
            {"pers:madre": 10.0, "52101": 100.0},
            amorcage_lieu="braavos", sur_verrous=True)
        self.assertIsNone(tache)


if __name__ == "__main__":
    unittest.main()
