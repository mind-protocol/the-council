# -*- coding: utf-8 -*-
"""Les gestes du joueur (partie_gestes.py) : ce qu'une carte posée sur une
carte devient au grand livre, et ce qui est refusé en clair.

Chaque cas travaille sur une COPIE du duel dans un dossier jetable — le module
écrit pour de vrai, et un test qui écrirait dans etat/parties/ abîmerait une
partie en cours."""
import io
import os
import shutil
import sys
import tempfile
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOYAU = os.path.join(SCRIPTS, "noyau")
for p in (SCRIPTS, NOYAU):
    if p not in sys.path:
        sys.path.insert(0, p)

from partie_greffe import Partie  # noqa: E402
import partie_cartes  # noqa: E402
import partie_gestes  # noqa: E402

DUEL = os.path.join(SCRIPTS, "tests", "donnees", "partie-duel.jsonl")

NOMS = {"steffon-darklyn": "Ser Steffon Darklyn", "daemon": "Daemon Targaryen",
        "aemond": "Aemond Targaryen", "rulf-corne": "Rulf Corne",
        "criston-cole": "Criston Cole", "aegon-ii": "Aegon II"}


class GestesTest(unittest.TestCase):
    def setUp(self):
        partie_cartes._NOMS = dict(NOMS)
        self.dossier = tempfile.mkdtemp(prefix="partie-gestes-")
        self.chemin = os.path.join(self.dossier, "duel.jsonl")
        shutil.copyfile(DUEL, self.chemin)
        self.p = Partie(self.chemin)

    def tearDown(self):
        partie_cartes._NOMS = None
        shutil.rmtree(self.dossier, ignore_errors=True)

    def relire(self):
        return Partie(self.chemin)

    def lignes(self):
        with io.open(self.chemin, encoding="utf-8") as f:
            return [x for x in f.read().splitlines() if x.strip()]

    # ---- poser -----------------------------------------------------------
    def test_piece_sur_obstacle_adverse_ouvre_un_ordre(self):
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        r = partie_gestes.poser(self.p, "noir", ["caraxes"], bid, "Caraxes brûle la chaîne")
        self.assertTrue(r["ok"], r["refus"])
        self.assertEqual(r["ligne"]["coup"], "lever")
        self.assertEqual(r["ligne"]["ouvre"], [bid])
        self.assertEqual(r["ligne"]["engage"], ["caraxes"])
        self.assertEqual(r["ligne"]["texte"], "Caraxes brûle la chaîne")
        # écrit sur le disque, et relu tel quel
        self.assertIn(r["ligne"]["id"], self.relire().cles)

    def test_le_texte_manquant_prend_un_defaut_lisible(self):
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        r = partie_gestes.poser(self.p, "noir", ["caraxes"], bid)
        self.assertTrue(r["ok"], r["refus"])
        self.assertIn("Caraxes", r["ligne"]["texte"])
        self.assertNotIn(bid, r["ligne"]["texte"])   # aucun id nu dans ce qui s'affiche

    def test_seconde_piece_sur_le_meme_obstacle_renforce_l_ordre(self):
        """Deux ordres qui disent la même chose contre un même obstacle sont un
        bug d'écran, pas un coup : la seconde pièce va renforcer le premier."""
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        a = partie_gestes.poser(self.p, "noir", ["caraxes"], bid)
        self.assertTrue(a["ok"], a["refus"])
        b = partie_gestes.poser(self.p, "noir", ["coques-est"], bid)
        self.assertTrue(b["ok"], b["refus"])
        self.assertEqual(b["ligne"]["coup"], "rearmer")
        self.assertEqual(b["ligne"]["id"], a["ligne"]["id"])
        self.assertIn("coques-est", self.relire().cles[a["ligne"]["id"]]["engage"])

    def test_piece_deja_posee_est_refusee_en_clair(self):
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        r = partie_gestes.poser(self.p, "noir", ["steffon-darklyn"], bid)
        self.assertFalse(r["ok"])
        self.assertTrue(r["refus"])
        self.assertNotIn("steffon-darklyn", " ".join(r["refus"]))   # rhabillé
        self.assertIn("Ser Steffon Darklyn", " ".join(r["refus"]))
        self.assertEqual(len(self.lignes()), len(self.relire().lignes))

    def test_piece_sur_un_etat_cible_est_refusee_sans_rien_ecrire(self):
        avant = len(self.lignes())
        r = partie_gestes.poser(self.p, "noir", ["caraxes"], "49000")
        self.assertFalse(r["ok"])
        self.assertIn("état cible", r["refus"][0])
        self.assertEqual(len(self.lignes()), avant)

    def test_piece_inconnue_du_grand_livre(self):
        r = partie_gestes.poser(self.p, "noir", ["vermithor"], "49001")
        self.assertFalse(r["ok"])
        self.assertIn("grand livre", r["refus"][0])

    def test_piece_sur_notre_propre_ordre_renforce(self):
        kid = [k for k, x in self.p.cles.items() if x["camp"] == "noir"][0]
        r = partie_gestes.poser(self.p, "noir", ["caraxes"], kid)
        self.assertTrue(r["ok"], r["refus"])
        self.assertEqual(r["ligne"]["coup"], "rearmer")
        self.assertEqual(r["ligne"]["id"], kid)

    # ---- reprendre -------------------------------------------------------
    def test_reprendre_un_ordre_libere_et_gele_la_piece(self):
        kid = [k for k, x in self.p.cles.items() if x["camp"] == "noir"][0]
        engagees = list(self.p.cles[kid]["engage"])
        r = partie_gestes.reprendre(self.p, "noir", kid)
        self.assertTrue(r["ok"], r["refus"])
        self.assertEqual(r["ligne"]["coup"], "retirer")
        q = self.relire()
        self.assertTrue(q.cles[kid]["retiree"])
        for pc in engagees:
            self.assertGreater(q.ressources[pc]["gel_jusqu"], q.tour)

    def test_on_ne_reprend_pas_la_carte_d_en_face(self):
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        r = partie_gestes.reprendre(self.p, "noir", bid)
        self.assertFalse(r["ok"])
        self.assertIn("pas le vôtre", r["refus"][0])

    # ---- le jour ---------------------------------------------------------
    def test_le_jour_passe_avance_le_tour(self):
        t = self.p.tour
        r = partie_gestes.jour(self.p)
        self.assertTrue(r["ok"], r["refus"])
        self.assertEqual(r["ligne"]["coup"], "tour")
        self.assertEqual(self.relire().tour, t + 1)

    # ---- l'entrée --------------------------------------------------------
    def test_geste_inconnu_ne_devine_rien(self):
        avant = len(self.lignes())
        r = partie_gestes.jouer(self.p, {"quoi": "brûler", "camp": "noir"})
        self.assertFalse(r["ok"])
        self.assertEqual(len(self.lignes()), avant)

    def test_l_avertissement_du_second_coup_remonte_sans_bloquer(self):
        """« Un coup par camp et par tour » est un contrôle gradué : le second
        coup passe, mais il se dit."""
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"]
        a = partie_gestes.jouer(self.p, {"quoi": "poser", "camp": "noir",
                                         "piece": "caraxes", "sur": bid[0]})
        self.assertTrue(a["ok"], a["refus"])
        b = partie_gestes.jouer(self.p, {"quoi": "poser", "camp": "noir",
                                         "piece": "coques-est", "sur": bid[1]})
        self.assertTrue(b["ok"], b["refus"])
        self.assertTrue(b["avertissements"])


if __name__ == "__main__":
    unittest.main()
