# -*- coding: utf-8 -*-
"""Ce qui tombe au passage du tour (partie_tour.py) et les cinq règles du 3.9 :
la réponse à un ❓ ne compte pas, la parade tient un tour, les états constatables
sont listés, un état vrai libère sa place au deck, chaque camp a sa racine."""
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
from partie_greffe import Partie, DECK_MAX  # noqa: E402


class TestPassageDuTour(unittest.TestCase):
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

    def tour(self):
        self.ok({"camp": "arbitre", "coup": "tour"})
        return self.p.lignes[-1]

    def test_repondre_a_un_justifier_ne_compte_pas(self):
        self.ok({"camp": "vert", "coup": "bloquer", "id": "b1", "sur": "200", "texte": "Tient", "engage": ["guet"]})
        self.tour()
        self.ok({"camp": "noir", "coup": "lever", "id": "k1", "ouvre": "b1", "texte": "Entre", "engage": ["ost"]})
        self.ok({"camp": "vert", "coup": "justifier", "sur": "k1", "texte": "Par où"})
        self.p.avertissements = []
        self.ok({"camp": "noir", "coup": "agir", "id": "a1", "realise": "k1", "qui": "steffon", "texte": "Par la poterne"})
        self.assertEqual(self.p.lignes[-1].get("repond"), self.p.cles["k1"].get("justifiee"))
        self.assertFalse(any("un coup par camp" in a for a in self.p.avertissements))
        self.assertIsNone(self.p.cles["k1"]["suspendue_par"])
        # un maillon qui ne répond à rien compte, lui
        self.ok({"camp": "noir", "coup": "agir", "id": "a2", "realise": "k1", "qui": "steffon", "texte": "Encore"})
        self.assertNotIn("repond", self.p.lignes[-1])

    def test_parade_tient_un_tour_puis_la_frappe_tombe(self):
        self.ok({"camp": "vert", "coup": "detruire", "id": "m1", "cible": "ost", "engage": ["guet"]})
        self.ok({"camp": "noir", "coup": "bloquer", "id": "pare", "sur": "m1", "texte": "S'interpose", "engage": ["barques"]})
        l = self.tour()                      # tour 2 : la frappe arrive
        self.assertNotIn("m1", l["parees"])
        l = self.tour()                      # tour 3 : parée, elle attend
        self.assertIn("m1", l["parees"])
        self.assertEqual(self.p.menaces["m1"]["paree_tour"], 3)
        l = self.tour()                      # tour 4 : la parade a tenu, la frappe tombe
        self.assertIn("m1", l["parades_tenues"])
        self.assertTrue(self.p.menaces["m1"]["tombee"])
        self.assertFalse(self.p.ressources["ost"]["detruite"])
        self.assertTrue(self.p.blocages["pare"]["tombe"])
        self.assertEqual(self.p.ressources["barques"]["engagee_par"], [])
        self.assertEqual(self.p.ressources["barques"].get("gel_jusqu", 0), 0)
        self.assertEqual(self.p.ressources["guet"]["engagee_par"], [])
        self.assertEqual(self.p.ressources["guet"]["gel_jusqu"], self.p.tour + 1)

    def test_arbitre_peut_trancher_avant_que_la_parade_tienne(self):
        self.ok({"camp": "vert", "coup": "detruire", "id": "m1", "cible": "ost", "engage": ["guet"]})
        self.ok({"camp": "noir", "coup": "bloquer", "id": "pare", "sur": "m1", "texte": "S'interpose", "engage": ["barques"]})
        self.tour()
        self.tour()
        self.ok({"camp": "arbitre", "coup": "arbitrer", "sur": "m1", "verdict": "tranche", "detruit": ["barques"],
                 "motif": "les deux y restent"})
        self.assertTrue(self.p.ressources["ost"]["detruite"])
        self.assertTrue(self.p.ressources["barques"]["detruite"])

    def test_constatables_listes_au_tour(self):
        self.ok({"camp": "vert", "coup": "bloquer", "id": "b1", "sur": "200", "texte": "Tient", "engage": ["guet"]})
        l = self.tour()
        self.assertNotIn("200", l["constatables"])
        self.ok({"camp": "noir", "coup": "lever", "id": "k1", "ouvre": "b1", "texte": "Entre", "engage": ["ost"]})
        l = self.tour()
        self.assertIn("200", l["constatables"])          # levé par une clé qui prévaut
        self.assertNotIn("49000", l["constatables"])     # rien ne le sert, rien ne le bloque
        self.ok({"camp": "vert", "coup": "justifier", "sur": "k1", "texte": "Par où"})
        l = self.tour()
        self.assertNotIn("200", l["constatables"])       # clé suspendue : le blocage prévaut
        self.ok({"camp": "arbitre", "coup": "constater", "etat": "200", "verdict": "vrai", "motif": "passé"})
        l = self.tour()
        self.assertNotIn("200", l["constatables"])       # déjà constaté

    def test_etat_vrai_libere_sa_place_au_deck(self):
        for i in range(DECK_MAX - 2):
            self.ok({"camp": "noir", "coup": "viser", "id": "e%d" % i, "sert": "49000", "texte": "x"})
        refus = self.p.ecrire({"camp": "noir", "coup": "viser", "id": "trop", "sert": "49000", "texte": "x"})
        self.assertTrue(refus and "plein" in refus[0], refus)
        self.ok({"camp": "arbitre", "coup": "constater", "etat": "200", "verdict": "vrai", "motif": "passé"})
        self.ok({"camp": "noir", "coup": "viser", "id": "trop", "sert": "49000", "texte": "x"})
        self.assertTrue(self.p.etats["200"]["deck"])     # il reste dans l'arbre

    def test_chaque_camp_a_sa_racine_et_le_trone_se_lit_sur_les_deux(self):
        self.assertIsNone(self.p.racine("vert"))
        self.assertIsNone(self.p.tenu_par())
        self.ok({"camp": "vert", "coup": "viser", "id": "v-trone", "texte": "Le roi est assis"})
        self.assertEqual(self.p.racine("vert"), "v-trone")
        self.ok({"camp": "arbitre", "coup": "constater", "etat": "49000", "verdict": "vrai", "motif": "assise"})
        self.assertEqual(self.p.tenu_par(), "noir")
        self.ok({"camp": "arbitre", "coup": "constater", "etat": "v-trone", "verdict": "vrai", "motif": "repris"})
        self.assertEqual(self.p.tenu_par(), "vert")
        self.ok({"camp": "arbitre", "coup": "constater", "etat": "v-trone", "verdict": "faux", "motif": "chassé"})
        self.assertIsNone(self.p.tenu_par())     # un constat faux retire, il ne donne à personne

    def test_camp_muet_trois_tours_signale(self):
        for _ in range(4):                               # le viser du tour 1 compte : on regarde les tours 2 à 4
            self.ok({"camp": "noir", "coup": "passer", "texte": "Rien"})
            self.ok({"camp": "vert", "coup": "bloquer", "id": "b%d" % self.p.tour, "sur": "200", "texte": "Tient",
                     "engage": ["guet"]} if self.p.tour == 2 else {"camp": "vert", "coup": "passer", "texte": "Rien"})
            l = self.tour()
        self.assertEqual(l["inactifs"], ["noir"])        # le Vert a joué au tour 2


if __name__ == "__main__":
    unittest.main()
