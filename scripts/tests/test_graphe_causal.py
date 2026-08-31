# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOYAU = os.path.join(SCRIPTS, "noyau")
for chemin in (SCRIPTS, NOYAU):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

from plan import graphe_causal as G  # noqa: E402


class GrapheCausalTest(unittest.TestCase):
    def setUp(self):
        self.noeuds = {
            "ev:racine": {"genre": "evenement", "quoi": "Racine"},
            "ev:milieu": {"genre": "evenement", "quoi": "Milieu"},
            "ev:cible": {"genre": "evenement", "quoi": "Cible"},
            "action:1": {"genre": "action", "quoi": "Préparer"},
            "moment:1": {"genre": "moment_mj", "quoi": "Voir"},
        }
        self.aretes = [
            {"de": "ev:racine", "vers": "ev:milieu", "nature": "amont",
             "source": "test", "flou": False, "texte": "cause"},
            {"de": "ev:milieu", "vers": "ev:cible", "nature": "amont",
             "source": "test", "flou": False, "texte": "cause"},
            # Écrit action -> prérequis ; causalement prérequis -> action.
            {"de": "action:1", "vers": "ev:milieu", "nature": "depend_de",
             "source": "test", "flou": False, "texte": "attend"},
            # Le moment dépend de l'événement : il doit rester en aval.
            {"de": "moment:1", "vers": "ev:cible", "nature": "depend_de",
             "source": "test", "flou": False, "texte": "source"},
            {"de": "?", "vers": "ev:cible", "nature": "devie",
             "source": "conditions", "flou": True, "texte": "si la porte ferme"},
        ]

    def test_remonte_toute_la_chaine_sans_prendre_le_moment_aval(self):
        graphe = G.extraire("cible", self.noeuds, self.aretes)
        ids = {n["id"] for n in graphe["noeuds"]}
        self.assertEqual({"ev:racine", "ev:milieu", "ev:cible"}, ids)
        self.assertNotIn("moment:1", ids)
        self.assertEqual(2, graphe["stats"]["profondeur_max"])

    def test_inverse_depend_de(self):
        normalisees, _ = G.normaliser(self.noeuds, self.aretes)
        triplets = {(a["de"], a["vers"], a["type"]) for a in normalisees}
        self.assertIn(("ev:milieu", "action:1", "prerequis"), triplets)
        self.assertIn(("ev:cible", "moment:1", "prerequis"), triplets)

    def test_rend_condition_non_adressee_et_cause_absente(self):
        graphe = G.extraire("cible", self.noeuds, self.aretes)
        types = [t["type"] for t in graphe["trous"]]
        self.assertIn("condition_non_adressee", types)
        self.assertIn("cause_absente", types)  # ev:racine est une racine non déclarée
        self.assertFalse(graphe["complet"])

    def test_refuse_un_id_qui_n_est_pas_un_evenement(self):
        with self.assertRaisesRegex(ValueError, "événement inconnu"):
            G.extraire("action:1", self.noeuds, self.aretes)

    def test_tous_garde_un_graphe_par_evenement(self):
        rendu = G.extraire_tous(self.noeuds, self.aretes)
        self.assertEqual(3, rendu["stats"]["evenements"])
        self.assertEqual(3, len(rendu["graphes"]))

    def test_un_cycle_est_borne_et_conserve(self):
        aretes = list(self.aretes) + [{
            "de": "ev:cible", "vers": "ev:racine", "nature": "amont",
            "source": "cycle", "flou": False, "texte": "retour",
        }]
        graphe = G.extraire("cible", self.noeuds, aretes)
        self.assertEqual(3, graphe["stats"]["noeuds"])
        self.assertEqual(3, graphe["stats"]["aretes"])
        self.assertLessEqual(graphe["stats"]["profondeur_max"], 3)

    def test_complete_conditions_et_racines_sans_inventer_de_cause(self):
        avant = G.extraire("cible", self.noeuds, self.aretes)
        proposition = G.proposer_complements([avant], self.noeuds)
        genres = {n["genre"] for n in proposition["noeuds"].values()}
        self.assertIn("condition_causale", genres)
        self.assertIn("racine_causale", genres)

        noeuds = dict(self.noeuds)
        noeuds.update(proposition["noeuds"])
        aretes = list(self.aretes) + proposition["aretes"]
        apres = G.extraire("cible", noeuds, aretes)
        self.assertTrue(apres["complet"])
        self.assertEqual([], apres["trous"])
        racines = [a for a in proposition["aretes"]
                   if a.get("racine_declaree")]
        self.assertTrue(racines)
        self.assertIn("aucun antécédent", racines[0]["texte"])

    def test_ecrit_un_fichier_de_complements_rechargeable(self):
        proposition = G.proposer_complements(
            [G.extraire("cible", self.noeuds, self.aretes)], self.noeuds)
        with tempfile.TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "complements.json")
            G.ecrire_complements(proposition, chemin)
            with open(chemin, encoding="utf-8") as fichier:
                donnees = __import__("json").load(fichier)
            G.ecrire_complements({"noeuds": {}, "aretes": []}, chemin)
            with open(chemin, encoding="utf-8") as fichier:
                relu = __import__("json").load(fichier)
        self.assertEqual("graphe-causal-complements/1", donnees["schema"])
        self.assertEqual(len(proposition["noeuds"]), len(donnees["noeuds"]))
        self.assertEqual(donnees["noeuds"], relu["noeuds"])
        self.assertEqual(donnees["aretes"], relu["aretes"])


if __name__ == "__main__":
    unittest.main()
