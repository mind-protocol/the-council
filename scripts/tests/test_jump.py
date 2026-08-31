# -*- coding: utf-8 -*-
import os
import json
import sys
import tempfile
import unittest
import concurrent.futures
from unittest import mock


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents import expose  # noqa: E402,F401 — lie la porte avant le MJ
from agents import jump, jump_beats, mj  # noqa: E402
from agents.depeche.mission import instructions_mode  # noqa: E402


class JumpTests(unittest.TestCase):
    def setUp(self):
        self.evenements = [
            {"id": "plus-tard", "statut": "a-venir", "importance": 90,
             "date_prevue": {"annee": 129, "lune": 4, "jour": 6},
             "acteurs": ["daemon"]},
            {"id": "prochain", "statut": "a-venir", "importance": 40,
             "date_prevue": {"annee": 129, "lune": 4, "jour": 5},
             "acteurs": ["gerardys", "rhaenyra", "corlys", "rulf"]},
        ]
        self.monde = {"date": {"annee": 129, "lune": 4, "jour": 4}}

    def test_prend_un_seul_prochain_evenement_ou_l_id_nomme(self):
        self.assertEqual("prochain", jump.choisir_evenement(
            "", self.evenements, self.monde)["id"])
        self.assertEqual("plus-tard", jump.choisir_evenement(
            "jump plus-tard", self.evenements, self.monde)["id"])

    def test_impose_24_heures_meme_pour_une_cible_nommee(self):
        monde = {"date": {"annee": 129, "lune": 4, "jour": 4,
                          "minute": 600}}
        proche = {"id": "proche", "statut": "a-venir",
                  "date_prevue": {"annee": 129, "lune": 4, "jour": 5,
                                   "minute": 599}}
        limite = {"id": "limite", "statut": "a-venir",
                  "date_prevue": {"annee": 129, "lune": 4, "jour": 5,
                                   "minute": 600}}
        self.assertEqual("limite", jump.choisir_evenement(
            "", [proche, limite], monde)["id"])
        with self.assertRaisesRegex(ValueError, "au moins 24 heures"):
            jump.choisir_evenement("jump proche", [proche, limite], monde)
        with self.assertRaisesRegex(ValueError, "au moins 24 heures"):
            jump.choisir_evenement("", [proche], monde)

    def test_prepare_contexte_coupe_bornee_et_aucune_decision_joueur(self):
        noeuds = {
            "ev:prochain": {"genre": "evenement", "quoi": "Prochain"},
            "condition:porte": {"genre": "condition_causale",
                                 "quoi": "si la porte tient",
                                 "statut": "a_evaluer"},
            "racine:prochain": {"genre": "racine_causale", "quoi": "Racine"},
            "84501": {"genre": "moment_mj", "quoi": "Scène suivante"},
        }
        aretes = [
            {"de": "condition:porte", "vers": "ev:prochain",
             "nature": "devie", "source": "test", "flou": False},
            {"de": "racine:prochain", "vers": "ev:prochain",
             "nature": "amont", "source": "test", "flou": False},
            {"de": "84501", "vers": "ev:prochain",
             "nature": "depend_de", "source": "test", "flou": False},
        ]
        rendu = jump.preparer(
            "", self.evenements, self.monde, (noeuds, aretes),
            joueurs=["rhaenyra"])
        self.assertEqual("jump/1", rendu["version"])
        self.assertEqual("prochain", rendu["event"]["id"])
        self.assertEqual("84501", rendu["contexte_id"])
        self.assertEqual(3, len(rendu["coupe"]["hommes_candidats"]))
        self.assertNotIn("rhaenyra", rendu["coupe"]["hommes_candidats"])
        self.assertFalse(rendu["contrat"]["decision_joueur"])
        self.assertTrue(rendu["contrat"]["un_seul_evenement"])
        self.assertEqual(24, rendu["contrat"]["ecart_minimum_heures"])
        self.assertEqual("si la porte tient",
                         rendu["coupe"]["prompts"][0]["prompt"])

    def test_le_skill_complet_n_est_injecte_que_dans_un_brief_jump(self):
        ordinaire = mj._manuel(modes=["play"])
        brief_jump = mj._manuel(modes=["jump"])
        self.assertNotIn("name: jump-scene", ordinaire)
        self.assertIn("name: jump-scene", brief_jump)
        self.assertIn("Compléter le sous-graphe", brief_jump)
        self.assertIn("Mettre les PNJ concernés à jour", brief_jump)
        self.assertIn("Meubler pendant les appels", brief_jump)
        self.assertIn("sous-entendus", brief_jump)
        self.assertIn("Chaque signe doit pouvoir être relié à un nœud",
                      brief_jump)
        self.assertIn("clock doit avancer pour de vrai", brief_jump)
        self.assertIn("Ne rends pas la main au milieu du Jump", brief_jump)
        self.assertIn("au moins 24 heures", brief_jump)
        self.assertIn("jalons intermédiaires", brief_jump)
        self.assertIn("--beats-jump", brief_jump)
        self.assertIn("jump_beats.py --pousser", brief_jump)
        self.assertIn("--dire --sans-reveil --de mj", brief_jump)
        self.assertIn("ne lance aucune", brief_jump)
        self.assertIn("une seule commande parallèle", brief_jump)
        self.assertIn("--front 3", brief_jump)
        self.assertIn("Ne fais jamais trois commandes successives", brief_jump)

    def test_un_homme_prepare_des_beats_lies_et_la_file_n_en_pousse_qu_un(self):
        with tempfile.TemporaryDirectory() as depot:
            jump_beats.initialiser(
                "prochain", "84501", "ref-1", hommes=["gerardys"],
                noeuds=["ev:prochain", "condition:porte"], depot=depot)
            ajoutes = jump_beats.ajouter(
                "prochain", "84501", "ref-1", "gerardys", [
                    {"type": "replique", "texte": "Le total ne tombe pas.",
                     "duree": 1, "noeuds": ["condition:porte"]},
                    {"type": "recit", "texte": "Beat sans vraie adresse.",
                     "noeuds": ["condition:inventee"]},
                    {"type": "geste", "texte": "Il retourne le registre.",
                     "duree": 2, "noeuds": ["ev:prochain"]},
                ], depot=depot)
            self.assertEqual(2, len(ajoutes))
            with mock.patch("agents.jump_beats.subprocess.run") as lancer:
                item = jump_beats.pousser(
                    "84501", "ref-1", depot=depot, commande=["pousser"])
            self.assertEqual("replique", item["type"])
            self.assertEqual("gerardys", item["locuteur_id"])
            lancer.assert_called_once()
            restant = jump_beats.lire("84501", "ref-1", depot=depot)
            self.assertEqual(["pousse", "en-attente"],
                             [b["statut"] for b in restant["beats"]])
            jump_beats.fermer("84501", "ref-1", depot=depot)
            self.assertEqual("expire", jump_beats.lire(
                "84501", "ref-1", depot=depot)["beats"][1]["statut"])

    def test_les_retours_paralleles_ne_s_ecrasent_pas_dans_la_file(self):
        with tempfile.TemporaryDirectory() as depot:
            jump_beats.initialiser(
                "prochain", "84501", "ref-par", hommes=["a", "b", "c"],
                noeuds=["ev:prochain"], depot=depot)

            def ajouter(auteur):
                return jump_beats.ajouter(
                    "prochain", "84501", "ref-par", auteur,
                    [{"type": "geste", "texte": "beat " + auteur,
                      "noeuds": ["ev:prochain"]}], depot=depot)

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                list(pool.map(ajouter, ["a", "b", "c"]))
            file_beats = jump_beats.lire("84501", "ref-par", depot=depot)
            self.assertEqual(3, len(file_beats["beats"]))
            self.assertEqual({"a", "b", "c"},
                             {b["auteur"] for b in file_beats["beats"]})

    def test_mode_reponse_jump_demande_reponse_et_beats_structures(self):
        instructions = instructions_mode("reponse", beats_jump=True)
        self.assertIn("beats_attente", instructions)
        self.assertIn("identifiant exact du sous-graphe", instructions)
        self.assertIn("Tu es l'auteur", instructions)

    def test_le_reveil_jump_ordonne_d_executer_le_skill_entier(self):
        message = mj._message("rhaenyra", "brief", "JOUEUR",
                              modes=["jump"])
        self.assertIn("skill système `jump-scene`", message)
        self.assertIn("mises à jour des PNJ", message)
        self.assertIn("avance réellement la clock", message)
        self.assertIn("ne rends pas la main au milieu", message)

    def test_le_garde_refuse_le_meublage_avant_la_scene_cible(self):
        preparation = {"event": {"id": "prochain", "date_prevue": {
            "annee": 129, "lune": 4, "jour": 5, "minute": 600}},
            "contexte_id": "84501"}
        with tempfile.TemporaryDirectory() as dossier:
            etat = os.path.join(dossier, "etat")
            os.makedirs(etat)
            with open(os.path.join(etat, "evenements.json"), "w",
                      encoding="utf-8") as f:
                json.dump([{"id": "prochain", "statut": "a-venir"}], f)
            with open(os.path.join(etat, "monde.json"), "w",
                      encoding="utf-8") as f:
                json.dump({"date": {"annee": 129, "lune": 4, "jour": 4}}, f)
            flux = os.path.join(etat, "flux.jsonl")
            with open(flux, "w", encoding="utf-8") as f:
                f.write(json.dumps({"type": "recit", "texte": "La pluie.",
                                    "date": {"annee": 129, "lune": 4,
                                             "jour": 4, "minute": 800}}) + "\n")
            with mock.patch.object(mj, "RACINE", dossier), \
                    mock.patch.object(mj, "FLUX", flux), \
                    mock.patch("plan.graphe_causal.charger_tissu",
                               return_value=({}, [])), \
                    mock.patch("plan.graphe_causal.extraire",
                               return_value={"complet": True}):
                manques = mj._manques_jump({"jump": preparation}, 0)
        self.assertIn("événement cible pas encore résolu ou dévié", manques)
        self.assertIn("aucune scène substantielle estampillée à la cible",
                      manques)
        self.assertIn("clock encore antérieure à la cible", manques)

    def test_le_garde_accepte_evenement_clock_et_scene_cible(self):
        date = {"annee": 129, "lune": 4, "jour": 5, "minute": 600}
        preparation = {"event": {"id": "prochain", "date_prevue": date},
                       "contexte_id": "84501"}
        with tempfile.TemporaryDirectory() as dossier:
            etat = os.path.join(dossier, "etat")
            os.makedirs(etat)
            with open(os.path.join(etat, "evenements.json"), "w",
                      encoding="utf-8") as f:
                json.dump([{"id": "prochain", "statut": "resolu"}], f)
            with open(os.path.join(etat, "monde.json"), "w",
                      encoding="utf-8") as f:
                json.dump({"date": date}, f)
            flux = os.path.join(etat, "flux.jsonl")
            with open(flux, "w", encoding="utf-8") as f:
                f.write(json.dumps({"type": "evenement", "texte": "Cible",
                                    "date": date}) + "\n")
            with mock.patch.object(mj, "RACINE", dossier), \
                    mock.patch.object(mj, "FLUX", flux), \
                    mock.patch("plan.graphe_causal.charger_tissu",
                               return_value=({}, [])), \
                    mock.patch("plan.graphe_causal.extraire",
                               return_value={"complet": True}):
                manques = mj._manques_jump({"jump": preparation}, 0)
        self.assertEqual([], manques)


if __name__ == "__main__":
    unittest.main()
