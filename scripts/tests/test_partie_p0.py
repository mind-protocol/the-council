# -*- coding: utf-8 -*-
"""Le palier P0 de l'audit du 7.9 (docs/parties/audit-2026-09-07.md, sections A
et B), une régression par correction :

A1  retirer une pièce la retire aussi de la clef qui l'engageait ;
A2  retirer le frappeur fait tomber la frappe ;
A4  une parade suspendue ne pare plus ;
A5  une ligne de camp datée d'un autre tour est refusée ;
A6  deux greffes sur le même fichier ne produisent pas le même `n`, et une
    dernière ligne tronquée ne rend pas la partie illisible ;
A8  constater efface la question posée sur l'état ;
A10 le rejeu d'une ligne fausse ne lève pas ;
A11 une ligne que la position refuse n'est pas écrite ;
B2  « le jour passe » est refusé à un camp ;
B3  un camp déclaré en configuration compte avant d'avoir visé ;
B4  « au jour N » tombe dans le bon tour."""
import io
import json
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
import partie_greffe  # noqa: E402
import partie_gestes  # noqa: E402
from partie_greffe import Partie  # noqa: E402


class TestP0(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.chemin = os.path.join(self.dossier, "t.jsonl")
        self.p = Partie(self.chemin)
        self.ok({"camp": "noir", "coup": "viser", "id": "49000", "texte": "La reine est assise"})
        self.ok({"camp": "noir", "coup": "viser", "id": "200", "sert": "49000", "texte": "La porte est acquise"})
        for camp, rid in (("noir", "ost"), ("vert", "guet"), ("vert", "galeres"), ("noir", "barques")):
            self.ok({"camp": camp, "coup": "demander", "id": rid, "nombre": 3})
            self.ok({"camp": "arbitre", "coup": "arbitrer", "sur": rid, "verdict": "accorde", "motif": "test"})

    def tearDown(self):
        shutil.rmtree(self.dossier, ignore_errors=True)

    def ok(self, l, p=None):
        refus = (p or self.p).ecrire(l)
        self.assertEqual(refus, [], refus)

    def refuse(self, l, mot):
        refus = self.p.ecrire(l)
        self.assertTrue(refus and mot in refus[0], refus)

    def tour(self):
        self.ok({"camp": "arbitre", "coup": "tour"})
        return self.p.lignes[-1]

    # ---- A1 ------------------------------------------------------------
    def test_a1_retirer_la_piece_la_sort_de_sa_clef(self):
        self.ok({"camp": "vert", "coup": "bloquer", "id": "b1", "sur": "200", "texte": "Tient", "engage": ["guet"]})
        self.ok({"camp": "noir", "coup": "lever", "id": "k1", "ouvre": "b1", "texte": "Entre", "engage": ["ost"]})
        self.assertEqual(self.p.prevaut("b1")[0], "noir")
        self.ok({"camp": "noir", "coup": "retirer", "id": "ost"})
        self.assertNotIn("ost", self.p.cles["k1"]["engage"])
        self.assertEqual(self.p.ressources["ost"]["engagee_par"], [])
        for _ in range(3):
            self.tour()                          # le gel passe : la clef ne redevient pas valide
        camp, motif = self.p.prevaut("b1")
        self.assertEqual(camp, "vert")
        self.assertIn("sans ressource", motif)
        self.assertNotIn("200", self.p.lignes[-1]["constatables"])
        # la pièce rentrée est libre pour une clef neuve — et une seule
        self.ok({"camp": "noir", "coup": "lever", "id": "k2", "ouvre": "b1", "texte": "Encore", "engage": ["ost"]})
        self.assertEqual(self.p.ressources["ost"]["engagee_par"], ["k2"])
        self.assertNotIn("k1", self.p.prevaut("b1")[1].replace("k1 sans ressource", ""))   # k1 ne lève plus rien
        # (qu'une seconde clef valide fasse prévaloir le verrou est A3, hors P0)
        self.refuse({"camp": "noir", "coup": "rearmer", "id": "k1", "engage": ["ost"]}, "déjà engagée")
        # invariant : toute pièce citée par une clef vivante la porte dans engagee_par
        for kid, k in self.p.cles.items():
            if not k["retiree"] and not k.get("tenue"):
                for pc in k["engage"]:
                    self.assertIn(kid, self.p.ressources[pc]["engagee_par"])

    # ---- A2 ------------------------------------------------------------
    def test_a2_retirer_le_frappeur_fait_tomber_la_frappe(self):
        self.ok({"camp": "vert", "coup": "detruire", "id": "m1", "cible": "ost", "engage": ["guet"]})
        self.ok({"camp": "noir", "coup": "bloquer", "id": "pare", "sur": "m1", "texte": "S'interpose", "engage": ["barques"]})
        self.ok({"camp": "vert", "coup": "retirer", "id": "guet"})
        self.assertTrue(self.p.menaces["m1"]["tombee"])
        self.assertTrue(self.p.blocages["pare"]["tombe"])       # plus rien à parer
        self.assertEqual(self.p.ressources["barques"]["engagee_par"], [])
        self.assertEqual(self.p.ressources["guet"]["engagee_par"], [])
        self.assertEqual(self.p.ressources["guet"]["gel_jusqu"], 1 + partie_greffe.GEL_RETRAIT)
        self.tour()
        self.tour()
        self.assertFalse(self.p.ressources["ost"]["detruite"])
        self.assertFalse(any(m["engage"] and not m["realisee"] and not m["tombee"]
                             and any(self.p.ressources[x]["engagee_par"] == [] for x in m["engage"])
                             for m in self.p.menaces.values()))

    # ---- A4 ------------------------------------------------------------
    def test_a4_une_parade_suspendue_ne_pare_plus(self):
        self.ok({"camp": "vert", "coup": "detruire", "id": "m1", "cible": "ost", "engage": ["guet"]})
        self.ok({"camp": "noir", "coup": "bloquer", "id": "pare", "sur": "m1", "texte": "S'interpose", "engage": ["barques"]})
        self.ok({"camp": "vert", "coup": "justifier", "sur": "pare", "texte": "Avec quoi ?"})
        self.assertFalse(self.p._protegee("m1"))
        self.tour()                              # tour 2 : la frappe arrive
        l = self.tour()                          # tour 3 : rien ne la pare, elle atterrit
        self.assertIn("m1", l["menaces"])
        self.assertTrue(self.p.menaces["m1"]["realisee"])
        self.assertTrue(self.p.ressources["ost"]["detruite"])

    def test_a4_le_maillon_ecrit_rend_la_parade(self):
        self.ok({"camp": "vert", "coup": "detruire", "id": "m1", "cible": "ost", "engage": ["guet"]})
        self.ok({"camp": "noir", "coup": "bloquer", "id": "pare", "sur": "m1", "texte": "S'interpose", "engage": ["barques"]})
        self.ok({"camp": "vert", "coup": "justifier", "sur": "pare", "texte": "Avec quoi ?"})
        self.ok({"camp": "noir", "coup": "agir", "id": "a1", "realise": "pare", "qui": "steffon", "texte": "Les barques"})
        self.assertTrue(self.p._protegee("m1"))

    # ---- A5 ------------------------------------------------------------
    def test_a5_une_ligne_datee_d_un_autre_tour_est_refusee(self):
        self.refuse({"camp": "noir", "coup": "passer", "texte": "Rien", "tour": 7}, "tour")
        self.assertEqual(self.p.tour, 1)
        self.ok({"camp": "noir", "coup": "passer", "texte": "Rien", "tour": 1})
        self.refuse({"camp": "arbitre", "coup": "constater", "etat": "200", "verdict": "vrai",
                     "motif": "x", "tour": 2}, "tour")
        self.assertEqual(Partie(self.chemin).tour, 1)

    # ---- A6 ------------------------------------------------------------
    def test_a6_deux_greffes_sur_le_meme_fichier_ne_doublent_pas_n(self):
        a, b = Partie(self.chemin), Partie(self.chemin)
        self.ok({"camp": "noir", "coup": "passer", "texte": "a"}, a)
        self.ok({"camp": "vert", "coup": "passer", "texte": "b"}, b)
        ns = [x["n"] for x in Partie(self.chemin).lignes]
        self.assertEqual(ns, sorted(set(ns)))
        self.assertEqual(b.lignes[-2]["texte"], "a")     # b a rattrapé la ligne de a avant d'écrire
        self.assertTrue(os.path.exists(self.chemin + ".lock"))

    def test_a6_une_derniere_ligne_tronquee_est_ignoree(self):
        with io.open(self.chemin, "a", encoding="utf-8") as f:
            f.write('{"camp": "noir", "coup": "passer", "n": 99, "tex')
        p = Partie(self.chemin)
        self.assertEqual(len(p.lignes), len(self.p.lignes))
        self.assertTrue(any("tronqu" in a for a in p.avertissements), p.avertissements)
        self.ok({"camp": "noir", "coup": "passer", "texte": "après"}, p)
        q = Partie(self.chemin)
        self.assertEqual(q.lignes[-1]["texte"], "après")
        self.assertEqual(q.lignes[-1]["n"], self.p.lignes[-1]["n"] + 1)

    # ---- A8 ------------------------------------------------------------
    def test_a8_constater_efface_la_question_sur_l_etat(self):
        self.ok({"camp": "vert", "coup": "justifier", "sur": "200", "texte": "Quelle porte ?"})
        self.assertTrue(self.p.etats["200"]["suspendue_par"])
        self.ok({"camp": "arbitre", "coup": "constater", "etat": "200", "verdict": "faux", "motif": "aucune"})
        self.assertIsNone(self.p.etats["200"]["suspendue_par"])
        self.ok({"camp": "vert", "coup": "justifier", "sur": "49000", "texte": "Assise où ?"})
        self.ok({"camp": "arbitre", "coup": "constater", "etat": "49000", "verdict": "vrai", "motif": "sur le trône"})
        self.assertIsNone(Partie(self.chemin).etats["49000"]["suspendue_par"])

    # ---- A10 / A11 ------------------------------------------------------
    def test_a10_le_rejeu_d_une_ligne_fausse_ne_leve_pas(self):
        with io.open(self.chemin, "a", encoding="utf-8") as f:
            f.write(json.dumps({"camp": "noir", "coup": "sortir", "id": "nulle-part", "n": 50, "tour": 1}) + "\n")
            f.write(json.dumps({"camp": "noir", "coup": "rearmer", "id": "k-fantome", "engage": ["ost"], "n": 51, "tour": 1}) + "\n")
            f.write(json.dumps({"camp": "noir", "coup": "reconstruire", "id": "rien", "n": 52, "tour": 1}) + "\n")
            f.write(json.dumps({"camp": "noir", "coup": "passer", "texte": "après", "n": 53, "tour": 1}) + "\n")
        p = Partie(self.chemin)
        self.assertEqual(p.lignes[-1]["texte"], "après")
        self.assertEqual(len([a for a in p.avertissements if "inapplicable" in a]), 3)
        self.assertEqual(p.ressources["ost"]["engagee_par"], [])

    def test_a11_une_ligne_que_la_position_refuse_n_est_pas_ecrite(self):
        avant = len(self.p.lignes)
        brut = self.p._appliquer_brut

        def casse(l):
            if l.get("coup") == "passer":
                self.p.etats["200"]["deck"] = False   # une demi-application, à défaire
                raise KeyError("boum")
            return brut(l)
        self.p._appliquer_brut = casse
        refus = self.p.ecrire({"camp": "noir", "coup": "passer", "texte": "x"})
        self.assertTrue(refus and "rien n'est écrit" in refus[0], refus)
        self.assertEqual(len(self.p.lignes), avant)
        self.assertTrue(self.p.etats["200"]["deck"])                  # la position est remise
        self.assertEqual(len(Partie(self.chemin).lignes), avant)

    # ---- B2 ------------------------------------------------------------
    def test_b2_le_jour_ne_passe_que_par_l_arbitre(self):
        r = partie_gestes.jouer(self.p, {"quoi": "jour", "camp": "noir"})
        self.assertFalse(r["ok"])
        self.assertIn("arbitre", r["refus"][0])
        self.assertEqual(self.p.tour, 1)
        r = partie_gestes.jouer(self.p, {"quoi": "jour", "camp": "arbitre"})
        self.assertTrue(r["ok"], r["refus"])
        self.assertEqual(self.p.tour, 2)

    # ---- B3 ------------------------------------------------------------
    def test_b3_un_camp_declare_en_configuration_compte_avant_de_viser(self):
        dossier = partie_greffe.DOSSIER
        partie_greffe.DOSSIER = self.dossier
        try:
            with io.open(os.path.join(self.dossier, "t.json"), "w", encoding="utf-8") as f:
                json.dump({"camps": ["noir", "bleu"]}, f)
            p = Partie(self.chemin)
            self.assertEqual(p.camps(), ["noir", "vert", "bleu"])   # les lignes d'abord, puis la configuration
            self.assertIn("camps", partie_greffe.config.__doc__)
        finally:
            partie_greffe.DOSSIER = dossier

    # ---- B4 ------------------------------------------------------------
    def test_b4_au_jour_n_tombe_dans_le_bon_tour(self):
        attendu = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3}
        for jour, tour in sorted(attendu.items()):
            r = partie_gestes.viser(self.p, "noir", "49000", "Au jour %d" % jour, jour)
            self.assertTrue(r["ok"], r["refus"])
            self.assertEqual(r["ligne"]["arrive_tour"], tour, "jour %d" % jour)


if __name__ == "__main__":
    unittest.main()
