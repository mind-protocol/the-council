# -*- coding: utf-8 -*-
import json
import importlib
import os
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents.expose import chambre, trace, depeche as brief
from agents import runtime
from agents.depeche import cli
from agents.depeche import contexte_affaire

mission_module = importlib.import_module("agents.depeche.mission")


class DepecheContextesTests(unittest.TestCase):
    def test_archive_prompt_conserve_contexte_et_ref(self):
        with tempfile.TemporaryDirectory() as dossier, \
                mock.patch.object(mission_module, "DEPECHES", dossier), \
                mock.patch.object(mission_module, "date_du_monde",
                                  return_value=(129, 4, 4)):
            chemin = mission_module.archiver_le_prompt(
                "gerardys", "session-item", "manuel", "mission",
                contexte_id="23030", ref="r-parole", mode="discussion")
            with open(chemin, encoding="utf-8") as f:
                archive = json.load(f)
        self.assertEqual("23030", archive["contexte_id"])
        self.assertEqual("r-parole", archive["ref"])
        self.assertEqual("discussion", archive["mode"])

    def test_un_item_a_sa_session_stable_et_distincte(self):
        jour_1 = (129, 4, 4)
        jour_2 = (129, 4, 5)
        port = brief.identifiant_de_session(
            "gerardys", jour_1, contexte_id="23030")
        meme_port_demain = brief.identifiant_de_session(
            "gerardys", jour_2, contexte_id="23030")
        autre_item = brief.identifiant_de_session(
            "gerardys", jour_1, contexte_id="23031")

        self.assertEqual(port, meme_port_demain)
        self.assertNotEqual(port, autre_item)
        self.assertNotEqual(
            brief.identifiant_de_session("gerardys", jour_1),
            brief.identifiant_de_session("gerardys", jour_2))

    def test_chaque_item_a_un_fil_de_chambre_sans_traversee(self):
        with tempfile.TemporaryDirectory() as dossier, \
                mock.patch.object(chambre, "CHAMBRES", dossier):
            un = chambre.fil("gerardys", "23030")
            deux = chambre.fil("gerardys", "23031")

        self.assertNotEqual(un, deux)
        self.assertEqual(os.path.join(dossier, "gerardys", "fil",
                                      "contextes", "23030"), un)
        with self.assertRaises(ValueError):
            chambre.fil("gerardys", "../23030")

    def test_chaque_item_a_un_depot_de_rapport_distinct(self):
        ancien = mission_module.cible_rapport("gerardys", brut=True)
        un = mission_module.cible_rapport(
            "gerardys", "#23030", brut=True)
        deux = mission_module.cible_rapport(
            "gerardys", "n° 92100", brut=True)

        self.assertTrue(ancien.endswith("gerardys.brut.txt"))
        self.assertTrue(un.endswith("gerardys--contexte-23030.brut.txt"))
        self.assertTrue(deux.endswith("gerardys--contexte-92100.brut.txt"))
        self.assertEqual(3, len({ancien, un, deux}))

    def test_le_vecu_est_depose_dans_le_fil_du_contexte(self):
        with tempfile.TemporaryDirectory() as dossier, \
                mock.patch.object(chambre, "CHAMBRES", dossier):
            transcript = os.path.join(dossier, "transcript.jsonl")
            with open(transcript, "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": "Fait."},
                }) + "\n")
            chemin = trace.deposer(
                "gerardys", "12345678-session", etiquette="129.4.4",
                transcript=transcript, provider="codex",
                contexte_id="23030", ref="r-parole")

            self.assertTrue(os.path.isfile(chemin))
            self.assertEqual(
                chambre.fil("gerardys", "23030"),
                os.path.dirname(chemin))
            with open(chemin, encoding="utf-8") as f:
                contenu = f.read()
            self.assertIn("contexte `23030`", contenu)
            self.assertIn("origine `r-parole`", contenu)

    def test_le_cast_place_son_log_dans_le_fil_du_contexte(self):
        contexte = "23030"
        with tempfile.TemporaryDirectory() as dossier, \
                mock.patch.object(chambre, "CHAMBRES", dossier), \
                mock.patch.object(runtime, "configuration",
                                  return_value={"fournisseur": "codex"}), \
                mock.patch.object(mission_module.tempfile, "mkdtemp",
                                  return_value=dossier), \
                mock.patch.object(mission_module, "poser_la_memoire"), \
                mock.patch.object(mission_module, "archiver_le_prompt"), \
                mock.patch.object(runtime, "lancer_cast",
                                  return_value={"cast": True}) as lancer:
            mission_module.appeler(
                "gerardys", "manuel", "mission", "session-item", None, 15,
                attendre=False, contexte_id=contexte, ref="r-parole")

            log = lancer.call_args.args[0]
            self.assertEqual(chambre.fil("gerardys", contexte),
                             os.path.dirname(log))
            self.assertEqual(contexte,
                             lancer.call_args.kwargs["trace"]["contexte_id"])
            self.assertEqual(contexte,
                             lancer.call_args.kwargs["env"][
                                 "LE_CONSEIL_CONTEXTE"])
            self.assertEqual("r-parole",
                             lancer.call_args.kwargs["env"]["LE_CONSEIL_REF"])
            self.assertEqual("r-parole",
                             lancer.call_args.kwargs["trace"]["ref"])
            mission_module.archiver_le_prompt.assert_called_once_with(
                "gerardys", "session-item", "manuel", "mission",
                contexte_id=contexte, ref="r-parole", mode="journee")

    def test_la_cli_transmet_le_contexte_a_l_appel_homme(self):
        argv = ["depecher.py", "--qui", "gerardys", "--sec",
                "--contexte", "n° 23030", "--ref", "r-parole",
                "--mode", "reponse"]
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(cli, "les_pj", return_value=set()), \
                mock.patch.object(cli, "date_du_monde", return_value=(129, 4, 4)), \
                mock.patch.object(cli, "depecher", return_value=True) as depecher:
            cli.main()

        self.assertEqual("23030",
                         depecher.call_args.kwargs["contexte_id"])
        self.assertEqual("r-parole", depecher.call_args.kwargs["ref"])
        self.assertEqual("reponse", depecher.call_args.kwargs["mode"])

    def test_les_modes_courts_verifient_concoivent_et_envoient(self):
        reponse = mission_module.instructions_mode("reponse")
        discussion = mission_module.instructions_mode("discussion")

        for texte in (reponse, discussion):
            self.assertIn("messages-au-joueur.md", texte)
            self.assertIn("# Ta chambre", texte)
            self.assertIn("brouillon, pas une source", texte)
            self.assertIn("revérifie les faits", texte)
            self.assertIn("nécessaires avant", texte)
        self.assertIn("Vérifie seulement", reponse)
        self.assertIn("Conçois une réponse", reponse)
        self.assertIn("dernière réponse de ce call", reponse)
        self.assertIn("Vérifie seulement", discussion)
        self.assertIn("Conçois une réponse", discussion)
        self.assertIn("commande de canal exacte", discussion)
        for texte in (reponse, discussion):
            self.assertIn("Ne modifie aucun fichier", texte)
            self.assertNotIn("journée EST ton retour", texte)

    def test_le_systeme_prepare_les_messages_seulement_comme_brouillons(self):
        manuel = os.path.join(
            SCRIPTS, "agents", "prompts", "metier.md")
        with open(manuel, encoding="utf-8") as f:
            texte = f.read()

        self.assertIn("mode `journee`", texte)
        self.assertIn("messages-au-joueur.md", texte)
        self.assertIn("Préparer n'est pas envoyer", texte)
        self.assertIn("modes `reponse` et `discussion`", texte)

        construit = mission_module.manuel_de("gerardys")
        attendu = os.path.abspath(os.path.join(
            chambre.chemin("gerardys"),
            chambre.MESSAGES_AU_JOUEUR)).replace("\\", "/")
        self.assertIn("# Ta chambre", construit)
        self.assertIn(attendu, construit)

    def test_ouvrir_une_chambre_seme_le_cahier_de_messages_une_fois(self):
        with tempfile.TemporaryDirectory() as dossier, \
                mock.patch.object(chambre, "CHAMBRES", dossier), \
                mock.patch.object(chambre, "_fiche", return_value={
                    "id": "gerardys", "nom": "Gerardys"}):
            domicile = chambre.ouvrir("gerardys")
            chemin = os.path.join(
                domicile, chambre.MESSAGES_AU_JOUEUR)
            with open(chemin, encoding="utf-8") as f:
                premier = f.read()
            self.assertIn("Préparer\nn'est pas envoyer", premier)

            personnel = premier + "\nMessage personnel.\n"
            with open(chemin, "w", encoding="utf-8", newline="\n") as f:
                f.write(personnel)
            chambre.ouvrir("gerardys")
            with open(chemin, encoding="utf-8") as f:
                self.assertEqual(personnel, f.read())

    def test_un_mode_inconnu_est_refuse(self):
        with self.assertRaises(ValueError):
            mission_module.instructions_mode("roman")

    def test_un_brief_court_ne_reinjecte_pas_la_journee_autonome(self):
        dossier = {"contexte_affaire": {"id": "23030", "volumes": []}}
        with mock.patch.object(mission_module, "contexte_message",
                              return_value="# Ton dossier\nFocus"):
            texte = mission_module.mission(
                "gerardys", "brief large", "Donne le chiffre.",
                contexte=dossier, contexte_id="23030", mode="reponse")

        self.assertIn("# Mode réponse", texte)
        self.assertIn("## La demande", texte)
        self.assertIn("Donne le chiffre.", texte)
        self.assertNotIn("# Cette journée", texte)
        self.assertNotIn("## Ta chambre", texte)
        self.assertNotIn("## Ton retour", texte)

    def test_les_formes_humaines_designent_le_meme_item(self):
        for entree in ("23030", "#23030", "n° 23030", "Nº23030",
                       "⚔️ **23030**", "affaire-entree-au-donjon#23030"):
            with self.subTest(entree=entree):
                self.assertEqual("23030", brief.id_item_affaire(entree))

    def test_un_contexte_sans_numero_ou_ambigu_est_refuse(self):
        with self.assertRaises(ValueError):
            brief.id_item_affaire("affaire-port#P.3")
        with self.assertRaises(ValueError):
            brief.id_item_affaire("23030 ou 23031")

    def test_le_brief_ne_garde_que_l_item_et_sa_chaine_ascendante(self):
        pieces = {
            "23030": {"genre": "action", "nom": "Repérer la garnison",
                      "affaire": "Entrée au Donjon", "vers": ["23020"],
                      "etat": "ouverte", "preuve": "Une liste de noms",
                      "cahier_sources": [{"volume_id": "affaire-donjon",
                                           "table": "⚔️ Actions"}]},
            "23020": {"genre": "clef", "nom": "Retourner un garde",
                      "affaire": "Entrée au Donjon", "vers": ["23010"]},
            "23010": {"genre": "verrou", "nom": "Aucun contact",
                      "affaire": "Entrée au Donjon", "vers": ["23000"]},
            "23000": {"genre": "etat", "nom": "Le Donjon change de main",
                      "affaire": "Entrée au Donjon", "vers": ["600"]},
            "600": {"genre": "etat", "nom": "Guerre gagnée",
                    "affaire": "Grande guerre", "vers": []},
            "99999": {"genre": "action", "nom": "Affaire étrangère",
                      "affaire": "Autre", "vers": []},
        }
        dossier = {"affaires_du_jour": "tout le plan",
                   "travaux_ouverts": [{"id": "99999"}]}

        focalise = contexte_affaire.focaliser(
            dossier, "#23030", chargeur=lambda: pieces)

        self.assertEqual(["23030", "23020", "23010", "23000"],
                         focalise["contexte_affaire"]["chaine"])
        self.assertIn("Une liste de noms", focalise["affaires_du_jour"])
        self.assertIn("affaire-donjon", focalise["affaires_du_jour"])
        self.assertNotIn("99999", focalise["affaires_du_jour"])
        self.assertNotIn("Guerre gagnée", focalise["affaires_du_jour"])
        self.assertEqual([], focalise["travaux_ouverts"])

    def test_un_numero_absent_du_plan_est_refuse(self):
        with self.assertRaisesRegex(ValueError, "n'existe pas"):
            contexte_affaire.resoudre("#99999", chargeur=lambda: {})

    def test_une_collision_entre_deux_cahiers_est_refusee(self):
        pieces = {"23030": {
            "genre": "action", "nom": "Deux fois", "affaire": "Une",
            "vers": [], "cahier_sources": [
                {"volume_id": "affaire-une", "table": "Actions"},
                {"volume_id": "affaire-deux", "table": "Actions"},
            ]}}
        with self.assertRaisesRegex(ValueError, "collision"):
            contexte_affaire.resoudre("23030", chargeur=lambda: pieces)

    def test_la_cli_refuse_un_contexte_vide(self):
        argv = ["depecher.py", "--qui", "gerardys", "--contexte", "   "]
        with mock.patch.object(sys, "argv", argv), \
                self.assertRaises(SystemExit):
            cli.main()


if __name__ == "__main__":
    unittest.main()
