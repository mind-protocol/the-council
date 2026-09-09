# -*- coding: utf-8 -*-
"""Les règles d'une partie (mj-partie.md §3-§4) tenues par le greffe, sur un fichier temporaire."""
import os
import shutil
import sys
import tempfile
import unittest

_d = os.path.dirname(os.path.abspath(__file__))
while os.path.basename(_d) != "scripts" and os.path.dirname(_d) != _d:
    _d = os.path.dirname(_d)
for _p in (_d, os.path.join(_d, "noyau")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from partie_greffe import Partie  # noqa: E402


class TestPartie(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.p = Partie(os.path.join(self.dossier, "t.jsonl"))
        self.ok({"camp": "noir", "coup": "viser", "id": "49000", "texte": "La reine est assise"})
        self.ok({"camp": "noir", "coup": "viser", "id": "200", "sert": "49000", "texte": "La porte est acquise"})
        for camp, rid in (("noir", "ost"), ("vert", "guet"), ("vert", "galeres"), ("noir", "barques")):
            self.ok({"camp": camp, "coup": "demander", "id": rid, "nombre": 3})
            self.ok({"camp": "arbitre", "coup": "arbitrer", "sur": rid, "verdict": "accorde", "motif": "test"})

    def tearDown(self):
        shutil.rmtree(self.dossier, ignore_errors=True)

    def ok(self, l):
        refus = self.p.ecrire(l)
        self.assertEqual(refus, [], refus)

    def refuse(self, l, mot):
        refus = self.p.ecrire(l)
        self.assertTrue(refus and mot in " ; ".join(refus), refus)

    def test_arbitrage_vise_un_id_meme_numerique(self):
        self.ok({"camp": "vert", "coup": "detruire", "id": "70040", "cible": "barques", "engage": ["galeres"]})
        self.ok({"camp": "arbitre", "coup": "arbitrer", "sur": "70040", "verdict": "reporte", "arrive_tour": 3, "motif": "t"})
        self.assertEqual(self.p.menaces["70040"]["arrive_tour"], 3)

    def test_un_id_na_quun_objet(self):
        self.ok({"camp": "vert", "coup": "bloquer", "id": "b1", "sur": "200", "texte": "Tient", "engage": ["guet"]})
        self.refuse({"camp": "vert", "coup": "bloquer", "id": "b1", "sur": "49000", "texte": "bis", "engage": []}, "déjà pris")
        self.refuse({"camp": "noir", "coup": "lever", "id": "b1", "ouvre": "b1", "engage": ["ost"]}, "déjà pris")
        self.assertEqual(self.p.blocages["b1"]["sur"], "200")

    def test_justifier_une_fois(self):
        self.ok({"camp": "vert", "coup": "bloquer", "id": "b1", "sur": "200", "texte": "Tient", "engage": ["guet"]})
        self.ok({"camp": "noir", "coup": "lever", "id": "k1", "ouvre": "b1", "texte": "Entre", "engage": ["ost"]})
        self.ok({"camp": "vert", "coup": "justifier", "sur": "k1", "texte": "Par où"})
        self.refuse({"camp": "vert", "coup": "justifier", "sur": "k1", "texte": "encore"}, "déjà")

    def test_cle_orpheline_tenue_et_pieces_rendues(self):
        self.ok({"camp": "vert", "coup": "bloquer", "id": "b1", "sur": "200", "texte": "Tient", "engage": ["guet"]})
        self.ok({"camp": "noir", "coup": "lever", "id": "k1", "ouvre": "b1", "texte": "Entre", "engage": ["ost"]})
        self.ok({"camp": "vert", "coup": "retirer", "id": "b1", "texte": "Lâche"})
        self.assertTrue(self.p.cles["k1"].get("tenue"))
        self.assertEqual(self.p.ressources["ost"]["engagee_par"], [])
        self.assertEqual(self.p.ressources["ost"].get("gel_jusqu", 0), 0)
        self.assertGreater(self.p.ressources["guet"]["gel_jusqu"], self.p.tour)

    def test_etat_date_entre_au_deck_a_son_tour(self):
        self.ok({"camp": "vert", "coup": "viser", "id": "v1", "arrive_tour": 3, "texte": "Criston devant Sombreval"})
        self.assertFalse(self.p.etats["v1"]["deck"])
        self.ok({"camp": "arbitre", "coup": "tour"})
        self.assertFalse(self.p.etats["v1"]["deck"])
        self.ok({"camp": "arbitre", "coup": "tour"})
        self.assertTrue(self.p.etats["v1"]["deck"])
        self.assertIn("v1", self.p.lignes[-1]["etats_arrives"])

    def test_menace_atterrit_au_tour_suivant_et_nest_pas_branche_morte(self):
        self.ok({"camp": "vert", "coup": "detruire", "id": "m1", "cible": "barques", "engage": ["galeres"]})
        self.ok({"camp": "arbitre", "coup": "tour"})
        self.assertFalse(self.p.ressources["barques"]["detruite"])
        self.ok({"camp": "arbitre", "coup": "tour"})
        self.assertTrue(self.p.ressources["barques"]["detruite"])
        self.assertNotIn("barques", self.p.lignes[-1]["branches_mortes"])

    def test_destruction_suspendue_se_leve_par_agir_ou_arbitrage(self):
        self.ok({"camp": "vert", "coup": "detruire", "id": "m1", "cible": "barques", "engage": ["galeres"]})
        self.ok({"camp": "noir", "coup": "justifier", "sur": "m1", "texte": "Par quelle mer"})
        self.assertTrue(self.p.menaces["m1"]["suspendue_par"])
        self.ok({"camp": "vert", "coup": "agir", "id": "a1", "realise": "m1", "qui": "capitaine", "texte": "Sort de nuit"})
        self.assertIsNone(self.p.menaces["m1"]["suspendue_par"])
        self.ok({"camp": "vert", "coup": "detruire", "id": "m2", "cible": "ost", "engage": ["guet"]})
        self.ok({"camp": "noir", "coup": "justifier", "sur": "m2", "texte": "Le Guet hors les murs ?"})
        self.ok({"camp": "arbitre", "coup": "arbitrer", "sur": "m2", "verdict": "refuse", "motif": "sans portée"})
        self.assertTrue(self.p.menaces["m2"]["tombee"])

    def test_menace_paree_natterrit_pas_et_libere_le_pare_quand_elle_tombe(self):
        self.ok({"camp": "vert", "coup": "detruire", "id": "m1", "cible": "ost", "engage": ["guet"]})
        self.ok({"camp": "noir", "coup": "bloquer", "id": "pare", "sur": "m1", "texte": "S'interpose", "engage": ["barques"]})
        self.ok({"camp": "arbitre", "coup": "tour"})
        self.ok({"camp": "arbitre", "coup": "tour"})
        self.assertFalse(self.p.ressources["ost"]["detruite"])
        self.assertNotIn("m1", self.p.lignes[-1]["menaces"])
        self.assertIn("m1", self.p.lignes[-1]["parees"])
        self.ok({"camp": "vert", "coup": "retirer", "id": "m1", "texte": "Rappelle"})
        self.assertTrue(self.p.blocages["pare"]["tombe"])
        self.assertEqual(self.p.ressources["barques"]["engagee_par"], [])
        self.assertEqual(self.p.ressources["barques"].get("gel_jusqu", 0), 0)

    def test_etat_constate_vrai_tient_la_cle_qui_le_sert(self):
        self.ok({"camp": "noir", "coup": "lever", "id": "k1", "sert": "200", "texte": "Traverse", "engage": ["ost", "barques"]})
        self.ok({"camp": "vert", "coup": "bloquer", "id": "b1", "sur": "200", "texte": "Tient", "engage": ["guet"]})
        self.ok({"camp": "arbitre", "coup": "constater", "etat": "200", "verdict": "vrai", "motif": "passé"})
        self.assertTrue(self.p.cles["k1"]["tenue"])
        self.assertEqual(self.p.ressources["ost"]["engagee_par"], [])
        self.assertTrue(self.p.blocages["b1"]["tombe"])

    def test_second_coup_dans_le_tour_signale_sans_refus(self):
        self.ok({"camp": "vert", "coup": "bloquer", "id": "b1", "sur": "200", "texte": "Tient", "engage": ["guet"]})
        self.ok({"camp": "vert", "coup": "detruire", "id": "m1", "cible": "barques", "engage": ["galeres"]})
        self.assertTrue(any("un coup par camp" in a for a in self.p.avertissements))

    def test_destruction_atterrie_ne_se_tranche_plus(self):
        """Règle 12 : atterrie sans arbitrage, elle est totale. Un « tranche » tardif
        rendait la pièce à la fois détruite et amputée d'un nombre (essai-1 :
        « ost-criston 1100 · DÉTRUITE »)."""
        self.ok({"camp": "vert", "coup": "detruire", "id": "m1", "cible": "ost", "engage": ["guet"]})
        self.ok({"camp": "arbitre", "coup": "tour"})
        self.ok({"camp": "arbitre", "coup": "tour"})
        self.assertTrue(self.p.ressources["ost"]["detruite"])
        self.refuse({"camp": "arbitre", "coup": "arbitrer", "sur": "m1", "verdict": "tranche",
                     "nombre": 1, "motif": "trop tard"}, "règle 12")
        self.assertTrue(self.p.ressources["ost"]["detruite"])
        self.assertEqual(self.p.ressources["ost"]["nombre"], 3)   # rien n'a été retranché

    def test_heurt_partiel_tranche_a_temps_laisse_la_piece_au_grand_livre(self):
        self.ok({"camp": "vert", "coup": "detruire", "id": "m1", "cible": "ost", "engage": ["guet"]})
        self.ok({"camp": "arbitre", "coup": "arbitrer", "sur": "m1", "verdict": "tranche",
                 "nombre": 1, "motif": "troupe contre bête posée"})
        self.assertFalse(self.p.ressources["ost"]["detruite"])
        self.assertEqual(self.p.ressources["ost"]["nombre"], 2)
        self.assertEqual(self.p.menaces["m1"]["realisee_tour"], self.p.tour)

    def test_arbitrer_ne_date_pas_une_arrivee_dans_le_passe(self):
        self.ok({"camp": "arbitre", "coup": "tour"})
        self.ok({"camp": "noir", "coup": "demander", "id": "cavaliers", "nombre": 200})
        self.refuse({"camp": "arbitre", "coup": "arbitrer", "sur": "cavaliers", "verdict": "accorde",
                     "arrive_tour": 1, "motif": "une arrivée d'hier"}, "déjà passé")

    def test_piece_qui_agit_nest_pas_une_branche_morte(self):
        """Le guetteur et le septon d'essai-1 ne figuraient que comme `qui` d'un
        maillon, et se voyaient signalés morts le tour même où ils agissaient."""
        self.ok({"camp": "noir", "coup": "lever", "id": "k1", "sert": "200", "texte": "Ouvre", "engage": ["ost"]})
        self.ok({"camp": "noir", "coup": "agir", "id": "a1", "realise": "k1",
                 "qui": "barques", "texte": "Passe la baie"})
        for _ in range(3):
            self.ok({"camp": "arbitre", "coup": "tour"})
        self.assertNotIn("barques", self.p.lignes[-1]["branches_mortes"])

    def test_constater_signale_un_etat_servant_resté_ouvert(self):
        self.ok({"camp": "noir", "coup": "viser", "id": "300", "sert": "49000", "texte": "La route est coupée"})
        self.ok({"camp": "arbitre", "coup": "constater", "etat": "49000", "verdict": "vrai", "motif": "assise"})
        self.assertTrue(any("300" in a and "ni constaté" in a for a in self.p.avertissements))
        self.assertTrue(self.p.etats["49000"]["vrai"])   # gradué : le constat passe

    def test_chemin_nu_sans_dossier(self):
        ici = os.getcwd()
        os.chdir(self.dossier)
        try:
            q = Partie("nu.jsonl")
            self.assertEqual(q.ecrire({"camp": "noir", "coup": "viser", "id": "1", "texte": "x"}), [])
        finally:
            os.chdir(ici)


if __name__ == "__main__":
    unittest.main()
