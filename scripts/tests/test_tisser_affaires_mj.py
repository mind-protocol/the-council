# -*- coding: utf-8 -*-
import json
import os
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOYAU = os.path.join(SCRIPTS, "noyau")
for chemin in (SCRIPTS, NOYAU):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

from plan.tisser import (charger_affaires_mj, noeuds_affaires_mj,  # noqa: E402
                         aretes_affaires_mj, indexer, tisser)


def livre(ident, titre, tables):
    return {"id": ident, "titre": titre, "type": "plan", "tables": tables}


class TisserAffairesMjTest(unittest.TestCase):
    def setUp(self):
        self.alpha = livre("affaire-alpha", "Alpha", [
            {"titre": "🎯 États cibles", "colonnes": ["🎯 N°", "🏷️ L'état"],
             "lignes": [{"cellules": ["A.1", "Alpha tenue"]}]},
            {"titre": "🔒 Verrous", "colonnes": ["🔒 N°", "🏷️ Le verrou", "⛔ Bloque"],
             "lignes": [{"cellules": ["A.11", "Mur", "A.1"]}]},
            {"titre": "🗝️ Clefs", "colonnes": ["🗝️ N°", "🏷️ La clef", "🔓 Ouvre"],
             "lignes": [{"cellules": ["A.21", "Passe", "A.11"]}]},
            {"titre": "⚔️ Actions", "colonnes": ["⚔️ N°", "🏷️ L'action", "🗝️ Réalise", "⛓️ Dépend de"],
             "lignes": [{"cellules": ["A.31", "Agir", "A.21", "B.1"]}]},
            {"titre": "🔗 Affaires liées",
             "colonnes": ["🪢 Le lien", "🔗 L'affaire", "🔢 Notre pièce", "🔢 La leur", "📝 Pourquoi"],
             "lignes": [{"cellules": ["attend", "Beta (chambre)", "A.1", "B.1", "Même prise"]}]},
            {"titre": "🧭 Moments marquants prévus",
             "colonnes": ["🧭 N°", "🔗 Événement source", "🎬 Moment"],
             "lignes": [{"cellules": ["A.40", "ev-alpha", "Voir alpha"]}]},
            {"titre": "🔗 Liens causaux",
             "colonnes": ["De", "Relation", "Vers", "Statut du lien", "Preuve"],
             "lignes": [{"cellules": ["ev-alpha", "cause", "ev-beta", "Explicite", "Écrit"]}]},
        ])
        self.beta = livre("affaire-beta", "Beta", [
            {"titre": "🎯 États cibles", "colonnes": ["🎯 N°", "🏷️ L'état"],
             "lignes": [{"cellules": ["B.1", "Beta tenue"]}]},
        ])
        self.alpha["_plage_mj"] = {"de": 80000, "a": 80499}
        self.beta["_plage_mj"] = {"de": 80500, "a": 80999}
        self.affaires = [self.alpha, self.beta]
        self.evenements = [{"id": "ev-alpha", "description": "Alpha"},
                           {"id": "ev-beta", "description": "Beta"}]

    def test_charge_uniquement_les_affaires_actives(self):
        with tempfile.TemporaryDirectory(prefix="banc-tissu-mj-") as racine:
            books = os.path.join(racine, "chambres", "mj", "books")
            os.makedirs(books)
            with open(os.path.join(books, "_plages.json"), "w", encoding="utf-8") as f:
                json.dump({"plage": {"de": 80000, "a": 89999,
                                      "taille_bloc": 500},
                           "affaires": {"affaire-alpha": {"de": 80000,
                                                            "a": 80499}}}, f)
            for nom, objet in (("affaire-alpha.json", self.alpha),
                               ("dossier-ignore.json", {"id": "d", "type": "dossier"})):
                with open(os.path.join(books, nom), "w", encoding="utf-8") as f:
                    json.dump(objet, f, ensure_ascii=False)
            charges = charger_affaires_mj(racine)
        self.assertEqual(["affaire-alpha"], [x["id"] for x in charges])

    def test_refuse_une_affaire_active_sans_bloc(self):
        with tempfile.TemporaryDirectory(prefix="banc-tissu-mj-") as racine:
            books = os.path.join(racine, "chambres", "mj", "books")
            os.makedirs(books)
            with open(os.path.join(books, "_plages.json"), "w", encoding="utf-8") as f:
                json.dump({"plage": {"de": 80000, "a": 89999,
                                      "taille_bloc": 500},
                           "affaires": {}}, f)
            with open(os.path.join(books, "affaire-alpha.json"), "w",
                      encoding="utf-8") as f:
                json.dump(self.alpha, f, ensure_ascii=False)
            with self.assertRaisesRegex(ValueError, "sans bloc"):
                charger_affaires_mj(racine)

    def test_refuse_deux_blocs_superposes(self):
        with tempfile.TemporaryDirectory(prefix="banc-tissu-mj-") as racine:
            books = os.path.join(racine, "chambres", "mj", "books")
            os.makedirs(books)
            with open(os.path.join(books, "_plages.json"), "w", encoding="utf-8") as f:
                json.dump({"plage": {"de": 80000, "a": 89999,
                                      "taille_bloc": 500},
                           "affaires": {
                               "affaire-alpha": {"de": 80000, "a": 80499},
                               "affaire-beta": {"de": 80200, "a": 80699}}}, f)
            with self.assertRaisesRegex(ValueError, "superposés"):
                charger_affaires_mj(racine)

    def test_namespace_chaque_piece_et_pose_les_affaires(self):
        ids = {n["id"] for n in noeuds_affaires_mj(self.affaires)}
        self.assertIn("80000", ids)
        self.assertIn("80001", ids)
        self.assertIn("80501", ids)

    def test_tisse_structure_affaires_moments_et_causalite(self):
        aretes = aretes_affaires_mj(self.affaires, self.evenements)
        triplets = {(a["de"], a["vers"], a["nature"]) for a in aretes}
        self.assertIn(("80111", "80001", "bloque"), triplets)
        self.assertIn(("80221", "80111", "ouvre"), triplets)
        self.assertIn(("80331", "80501", "depend_de"), triplets)
        self.assertIn(("80001", "80501", "attend"), triplets)
        self.assertIn(("80040", "ev:ev-alpha",
                       "depend_de"), triplets)
        self.assertIn(("ev:ev-alpha", "ev:ev-beta", "amont"), triplets)

    def test_integration_resout_les_deux_bouts(self):
        with mock.patch("plan.tisser.lecture.charger", return_value=[]):
            noeuds, _ = indexer([], [], [], [], self.evenements, [], [],
                                self.affaires)
        aretes = tisser([], [], [], [], self.evenements,
                        affaires_mj=self.affaires)
        locales = [a for a in aretes if a["source"].startswith("chambres/mj")
                   and not a["flou"]]
        self.assertTrue(locales)
        self.assertTrue(all(a["de"] in noeuds and a["vers"] in noeuds
                            for a in locales))

    def test_cahier_canonique_precise_la_piece_du_registre_derive(self):
        derive = livre("plan-actions", "Registre dérivé", [{
            "titre": "Toutes les pièces",
            "colonnes": ["N°", "Action", "Affaire"],
            "lignes": [{"cellules": ["58300", "Cartographier", "Collaboration"]}],
        }])
        canonique = livre("affaire-collaboration", "Collaboration", [{
            "titre": "⚔️ Actions",
            "colonnes": ["⚔️ N°", "🏷️ L'action", "⛓️ Dépend de",
                           "⏳ État", "📅 Jour dû"],
            "lignes": [{"cellules": ["58300", "Cartographier les affaires",
                                        "58290", "en cours", "129.5.13"]}],
        }])
        with mock.patch("plan.tisser.lecture.charger", return_value=[]):
            noeuds, _ = indexer([derive, canonique], [], [], [], [], [])
        action = noeuds["58300"]
        self.assertEqual("action", action["genre"])
        self.assertEqual("affaire-collaboration", action["ou"])
        self.assertEqual(["58290"], action["depend_de"])
        self.assertEqual("en cours", action["etat"])
        self.assertEqual("129.5.13", action["jour_du"])

    def test_proprietaire_affaire_porte_les_buts_sans_prendre_les_actions(self):
        cahier = livre("affaire-ville", "Construire la ville", [
            {"titre": "🎯 États cibles",
             "colonnes": ["🎯 N°", "🎯 L'état cible"],
             "lignes": [{"cellules": ["53100", "Une ville habitable"]}]},
            {"titre": "⚔️ Actions",
             "colonnes": ["⚔️ N°", "🏷️ L'action", "🗝️ Réalise"],
             "lignes": [{"cellules": ["53300", "Tracer une rue", "53100"]}]},
        ])
        cahier["tenu_par"] = "nicolas-lester-reynolds"
        aretes = tisser([cahier], [], [], [], [],
                        personnages=[{"id": "nicolas-lester-reynolds",
                                      "nom": "Nicolas Lester Reynolds"}])
        triplets = {(a["de"], a["vers"], a["nature"]) for a in aretes}
        self.assertIn(("pers:nicolas-lester-reynolds", "53100", "porte"),
                      triplets)
        self.assertNotIn(("53300", "pers:nicolas-lester-reynolds", "tient"),
                         triplets)

    def test_identifiant_exact_distingue_les_homonymes_suffixes(self):
        cahier = livre("affaire-entree", "Entrée", [{
            "titre": "⚔️ Actions",
            "colonnes": ["⚔️ N°", "🏷️ L'action", "👤 Qui · 🪶 Office"],
            "lignes": [{"cellules": ["58500", "Entrer", "anchor-builder1"]}],
        }])
        personnes = [
            {"id": "anchor-builder", "nom": "Tommaso Morosini"},
            {"id": "anchor-builder1", "nom": "Tommaso Morosini"},
        ]
        aretes = tisser([cahier], [], [], [], [], personnages=personnes)
        triplets = {(a["de"], a["vers"], a["nature"]) for a in aretes}
        self.assertIn(("58500", "pers:anchor-builder1", "tient"), triplets)
        self.assertNotIn(("58500", "pers:anchor-builder", "tient"), triplets)


if __name__ == "__main__":
    unittest.main()
