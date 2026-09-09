# -*- coding: utf-8 -*-
"""Deux règles du greffe alignées le 3.9 : un blocage engage une pièce (§3, règle 2)
et un retournement rend ce qu'on y a mis, gelé un tour, comme une frappe (§4.4)."""
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


class TestBlocageEtRetourner(unittest.TestCase):
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

    def test_blocage_sans_piece_refuse(self):
        self.refuse({"camp": "vert", "coup": "bloquer", "id": "b0", "sur": "200", "texte": "Tient"}, "pas de ressource")
        self.refuse({"camp": "vert", "coup": "bloquer", "id": "b0", "sur": "200", "texte": "Tient", "engage": []}, "pas de ressource")
        self.ok({"camp": "vert", "coup": "bloquer", "id": "b0", "sur": "200", "texte": "Tient", "engage": ["guet"]})

    def test_retourner_change_le_camp_et_rend_la_piece_gelee(self):
        self.ok({"camp": "vert", "coup": "bloquer", "id": "b1", "sur": "200", "texte": "Tient", "engage": ["guet"]})
        self.ok({"camp": "noir", "coup": "retourner", "id": "r1", "cible": "guet", "engage": ["barques"], "texte": "Achète le Guet"})
        self.ok({"camp": "arbitre", "coup": "tour"})
        self.ok({"camp": "arbitre", "coup": "tour"})
        guet, barques = self.p.ressources["guet"], self.p.ressources["barques"]
        self.assertTrue(self.p.menaces["r1"]["realisee"])
        self.assertEqual(guet["camp"], "noir")
        self.assertFalse(guet["detruite"])
        self.assertEqual(guet["engagee_par"], [])
        self.assertTrue(self.p.blocages["b1"]["tombe"])
        # ce qu'on y a mis revient, gelé un tour, comme après une frappe
        self.assertEqual(barques["engagee_par"], [])
        self.assertEqual(barques["gel_jusqu"], self.p.tour + 1)
        # et le retourné est engageable par son nouveau camp
        self.ok({"camp": "vert", "coup": "bloquer", "id": "b2", "sur": "200", "texte": "Tient encore", "engage": ["galeres"]})
        self.ok({"camp": "noir", "coup": "lever", "id": "k1", "ouvre": ["b2"], "engage": ["guet"], "texte": "Le Guet ouvre"})

    def test_un_retournement_s_arbitre_comme_une_frappe(self):
        self.ok({"camp": "noir", "coup": "retourner", "id": "r1", "cible": "guet", "engage": ["barques"], "texte": "Achète"})
        self.ok({"camp": "vert", "coup": "justifier", "sur": "r1", "texte": "Avec quoi"})
        self.ok({"camp": "arbitre", "coup": "arbitrer", "sur": "r1", "verdict": "refuse", "motif": "sans portée"})
        self.assertTrue(self.p.menaces["r1"]["tombee"])
        self.assertEqual(self.p.ressources["barques"]["engagee_par"], [])
        self.assertEqual(self.p.ressources["guet"]["camp"], "vert")


if __name__ == "__main__":
    unittest.main()
