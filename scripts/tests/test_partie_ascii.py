# -*- coding: utf-8 -*-
"""Le plateau au terminal (partie_ascii.py), sur le duel joué au tour 2.

Le rendu ne calcule rien. Ce banc vérifie deux choses, et ce sont les deux
seuls défauts qu'un plateau texte puisse avoir : qu'il DIT tout ce que la vue
porte, et qu'il MONTRE les liens au lieu de les écrire — un verrou doit pendre
sous l'état qu'il barre, une pièce sous la clé qui l'engage.
"""
import os
import sys
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOYAU = os.path.join(SCRIPTS, "noyau")
for p in (SCRIPTS, NOYAU):
    if p not in sys.path:
        sys.path.insert(0, p)

from partie_greffe import Partie  # noqa: E402
import partie_cartes  # noqa: E402
import partie_ascii  # noqa: E402

DUEL = os.path.join(SCRIPTS, "tests", "donnees", "partie-duel.jsonl")


def _indent(ligne):
    """La profondeur d'une ligne dans l'arbre : ce qui précède son signe."""
    corps = ligne[1:]
    return len(corps) - len(corps.lstrip(" │├└─"))


class TestPlateau(unittest.TestCase):
    def setUp(self):
        self.vue = partie_cartes.vue(Partie(DUEL), "noir")
        # sans gras : ces cas éprouvent la STRUCTURE, et les codes ANSI
        # couperaient les ids que l'on cherche dans le texte
        self.lignes = partie_ascii.plateau(self.vue, gras=False)
        self.texte = "\n".join(self.lignes)

    def _ligne_de(self, bout):
        for i, l in enumerate(self.lignes):
            if bout in l:
                return i, l
        self.fail("rien ne porte %r dans le plateau" % bout)

    # ---- ce qui est dit ------------------------------------------------
    def test_rend_des_lignes_de_texte(self):
        self.assertTrue(self.lignes)
        for l in self.lignes:
            self.assertIsInstance(l, str)
            self.assertNotIn("\n", l)   # une ligne est une ligne : le CLI les joint

    def test_l_entete_porte_le_tour_et_le_trait(self):
        tete = "\n".join(self.lignes[:4])
        self.assertIn("tour %d" % self.vue["tour"], tete)
        self.assertIn("trait à", tete)

    def test_l_arbre_part_du_trone(self):
        self.assertIn("👑", self.texte)

    def test_aucun_etat_ne_manque_a_l_appel(self):
        for c in self.vue["cibles"]:
            self.assertIn(c["id"][:16], self.texte, "l'état %s n'est pas dessiné" % c["id"])

    def test_aucun_front_ne_manque_a_l_appel(self):
        self.assertTrue(self.vue["fronts"], "la fixture doit porter des fronts")
        for f in self.vue["fronts"]:
            self.assertIn(f["tete"]["id"][:16], self.texte)
            self.assertIn(f["pourquoi"], self.texte)   # qui prévaut, et pourquoi

    def test_aucune_piece_ne_manque_a_l_appel(self):
        pieces = [c for lot in self.vue["deck"].values() for c in lot] + self.vue["eux"]
        self.assertTrue(pieces)
        for c in pieces:
            self.assertIn(c["titre"][:20], self.texte, "la pièce %s n'est pas dessinée" % c["id"])

    # ---- ce qui est MONTRÉ ---------------------------------------------
    def test_l_arbre_porte_ses_traits(self):
        for trait in ("├─", "└─", "│"):
            self.assertIn(trait, self.texte)

    def test_un_verrou_pend_sous_l_etat_qu_il_barre(self):
        for f in self.vue["fronts"]:
            if str(f["sur"]) not in [str(c["id"]) for c in self.vue["cibles"]]:
                continue
            i_etat, l_etat = self._ligne_de("🎯 %s " % f["sur"])
            i_front, l_front = self._ligne_de("%s " % f["tete"]["id"][:16])
            self.assertGreater(i_front, i_etat, "%s doit venir après son état" % f["tete"]["id"])
            self.assertGreater(_indent(l_front), _indent(l_etat),
                               "%s doit pendre SOUS %s, pas à côté" % (f["tete"]["id"], f["sur"]))

    def test_une_piece_posee_pend_sous_ce_qui_l_engage(self):
        posees = [c for c in self.vue["deck"]["posees"] if c.get("engagee_par")]
        if not posees:
            self.skipTest("aucune pièce posée dans la fixture")
        for c in posees:
            i_p, l_p = self._ligne_de("%s  " % c["id"][:16])
            i_k, l_k = self._ligne_de("%s " % c["engagee_par"][0][:16])
            self.assertGreater(i_p, i_k)
            self.assertGreater(_indent(l_p), _indent(l_k),
                               "%s doit pendre sous %s" % (c["id"], c["engagee_par"][0]))

    def test_un_etat_fils_pend_sous_son_parent(self):
        fils = [c for c in self.vue["cibles"] if c.get("sert")]
        if not fils:
            self.skipTest("le duel de banc est plat : aucun état n'en sert un autre")
        for c in fils:
            i_f, l_f = self._ligne_de("🎯 %s " % c["id"])
            i_p, l_p = self._ligne_de("🎯 %s " % c["sert"])
            self.assertGreater(_indent(l_f), _indent(l_p))

    def test_seules_les_pieces_libres_sortent_de_l_arbre(self):
        queue = self.texte[self.texte.index("LIBRES"):]
        engagees = [c for lot in self.vue["deck"].values() for c in lot if c.get("engagee_par")]
        self.assertTrue(engagees, "la fixture doit porter une pièce engagée")
        for c in engagees:
            self.assertNotIn(c["titre"][:20], queue,
                             "%s est engagée : elle est dans l'arbre, pas en réserve" % c["id"])

    def test_une_piece_engagee_pend_sous_ce_qui_l_engage(self):
        """Y compris celles d'en face, et celles qui sont encore en route :
        c'est ce qui fait voir le face-à-face devant un verrou."""
        toutes = [c for lot in self.vue["deck"].values() for c in lot] + self.vue["eux"]
        engagees = [c for c in toutes if c.get("engagee_par")]
        self.assertTrue(engagees)
        for c in engagees:
            i_p, l_p = self._ligne_de(" %s  " % c["id"][:16])
            i_q, l_q = self._ligne_de("%s " % c["engagee_par"][0][:16])
            self.assertGreater(_indent(l_p), _indent(l_q),
                               "%s doit pendre sous %s" % (c["id"], c["engagee_par"][0]))

    # ---- ce que la position porte en plus de l'arbre --------------------
    def test_le_compte_du_deck_est_servi(self):
        self.assertTrue(self.vue["decks"])
        for c, d in self.vue["decks"].items():
            self.assertIn("%d/%d" % (d["pris"], d["max"]), self.texte)

    def test_les_cles_tenues_ne_disparaissent_pas(self):
        """Une clé tenue sort des fronts : sans son bloc, un duel gagné ne dit
        plus par quoi il a été gagné."""
        duel = Partie(os.path.join(SCRIPTS, "..", "etat", "parties", "duel-50.jsonl"))
        vue = partie_cartes.vue(duel, "noir")
        self.assertTrue(vue["tenues"], "duel-50 doit porter des clés tenues")
        t = chr(10).join(partie_ascii.plateau(vue, gras=False))
        self.assertIn("TENUES", t)
        for k in vue["tenues"]:
            self.assertIn(k["id"][:18], t, "la clé tenue %s n'est pas dite" % k["id"])

    def test_ce_que_le_dernier_tour_a_signale_est_servi(self):
        duel = Partie(os.path.join(SCRIPTS, "..", "etat", "parties", "noirs-verts.jsonl"))
        vue = partie_cartes.vue(duel, "noir")
        self.assertTrue(vue["signale"], "noirs-verts doit porter un signalement")
        t = chr(10).join(partie_ascii.plateau(vue, gras=False))
        for cle, lot in vue["signale"].items():
            self.assertIn(cle, t)
            self.assertIn(str(lot[0])[:20], t)

    def test_un_signalement_vide_ne_fait_pas_de_titre(self):
        t = chr(10).join(partie_ascii.plateau(dict(self.vue, signale={}, tenues=[]), gras=False))
        self.assertNotIn("DERNIER PASSAGE", t)
        self.assertNotIn("TENUES", t)

    def test_une_piece_perdue_est_dite(self):
        vue = dict(self.vue)
        vue["deck"] = dict(vue["deck"], detruites=[
            {"id": "meleys", "emoji": "🐉", "titre": "Meleys", "apparence": "detruite",
             "pied": {"gauche": "", "droite": "détruite"}}])
        self.assertIn("PERDUES", chr(10).join(partie_ascii.plateau(vue, gras=False)))

    # ---- statuts et décomptes ------------------------------------------
    def test_un_statut_porte_toujours_son_signe(self):
        """« faite », « posée », « dans 4 j » sortent du greffe chacun à sa
        façon : signés, ils se lisent sans être lus — et c'est ce qui distingue
        une ACTION ⚔️ d'une TROUPE ⚔️, qui partagent leur emoji."""
        self.assertEqual(partie_ascii._statut("faite"), "✅ faite")
        self.assertEqual(partie_ascii._statut("posée"), "📍 posée")
        self.assertEqual(partie_ascii._statut("dans 4 j"), "🕐 dans 4 j")
        self.assertEqual(partie_ascii._statut("détruite"), "💀 détruite")
        # un ruban qui porte déjà son signe n'est pas retouché
        self.assertEqual(partie_ascii._statut("✅ tient"), "✅ tient")
        self.assertEqual(partie_ascii._statut(""), "")

    def test_une_action_dit_si_elle_est_faite(self):
        v = partie_cartes.vue(Partie(os.path.join(SCRIPTS, "..", "etat", "parties",
                                                  "enquete-vauthier.jsonl")), None)
        actions = [c for c in partie_ascii._toutes(v) if c.get("type") == "action"]
        self.assertTrue(actions, "cette partie doit porter des actions")
        t = chr(10).join(partie_ascii.plateau(v, gras=False))
        for c in actions:
            i, l = None, None
            for j, x in enumerate(t.split(chr(10))):
                if c["id"] in x:
                    i, l = j, x
                    break
            self.assertIsNotNone(l, "l'action %s n'est pas dessinée" % c["id"])
            self.assertTrue("✅" in l or "⏳" in l,
                            "l'action %s ne dit pas si elle est faite : %r" % (c["id"], l))

    def test_les_decomptes_tiennent_dans_la_largeur(self):
        for nom in ("le-trone", "duel-50", "enquete-vauthier", "noirs-verts"):
            v = partie_cartes.vue(Partie(os.path.join(SCRIPTS, "..", "etat",
                                                      "parties", nom + ".jsonl")), None)
            lignes = partie_ascii.plateau(v, gras=False)
            trop = [l for l in lignes if len(l) > partie_ascii.LARGEUR]
            self.assertFalse(trop, "%s déborde : %r" % (nom, trop[:1]))

    def test_les_decomptes_comptent_juste(self):
        lignes = partie_ascii._decomptes(self.vue, gras=False)
        t = " ".join(lignes)
        contre_nous = len([f for f in self.vue["fronts"] if f.get("contre_nous")])
        self.assertIn("%d contre nous" % contre_nous, t)
        a_nous = len([c for lot in self.vue["deck"].values() for c in lot])
        self.assertIn("%d à nous" % a_nous, t)

    # ---- le mode entier -------------------------------------------------
    def test_le_mode_entier_ne_coupe_rien(self):
        """Aucun « … » : un plateau qui élide oblige à rouvrir le jsonl pour
        savoir ce qu'une carte disait."""
        for nom in ("le-trone", "noirs-verts", "enquete-vauthier", "duel-50"):
            v = partie_cartes.vue(Partie(os.path.join(SCRIPTS, "..", "etat",
                                                      "parties", nom + ".jsonl")), None)
            t = chr(10).join(partie_ascii.plateau(v, gras=False, entier=True))
            self.assertNotIn("…", t, "%s élide encore" % nom)

    def test_le_mode_entier_dit_tous_les_titres_en_toutes_lettres(self):
        v = partie_cartes.vue(Partie(os.path.join(SCRIPTS, "..", "etat", "parties",
                                                  "noirs-verts.jsonl")), None)
        # on dépouille la tuyauterie de l'arbre avant de recomposer : un titre
        # replié sur deux lignes a un « │ » de branche entre ses deux moitiés
        lignes = partie_ascii.plateau(v, gras=False, entier=True)
        t = " ".join(" ".join(l.lstrip(" │├└─") for l in lignes).split())
        for c in partie_ascii._toutes(v):
            titre = " ".join((c.get("titre") or "").split())
            if titre:
                self.assertIn(titre, t, "%s est encore tronqué" % c.get("id"))

    def test_le_mode_entier_tient_dans_la_largeur(self):
        v = partie_cartes.vue(Partie(os.path.join(SCRIPTS, "..", "etat", "parties",
                                                  "noirs-verts.jsonl")), None)
        for l in partie_ascii.plateau(v, gras=False, entier=True):
            self.assertLessEqual(len(l), partie_ascii.LARGEUR, repr(l))

    def test_une_carte_qui_tient_garde_sa_ligne(self):
        """Replier ce qui n'en avait pas besoin doublerait la hauteur pour rien."""
        v = partie_cartes.vue(Partie(os.path.join(SCRIPTS, "..", "etat", "parties",
                                                  "noirs-verts.jsonl")), None)
        t = chr(10).join(partie_ascii.plateau(v, gras=False, entier=True))
        self.assertIn("🎯 49000  La reine est assise sur le Trône de Fer", t)

    # ---- la couleur et le gras -----------------------------------------
    def test_chaque_carte_dit_son_camp(self):
        """Un verrou, une clé, une pièce doivent dire à qui ils sont sans qu'on
        ait à remonter la branche."""
        from partie_greffe import EMOJI_CAMP
        for f in self.vue["fronts"]:
            i, l = self._ligne_de(" " + f["tete"]["id"] + " ")
            self.assertIn(EMOJI_CAMP[f["tete"]["camp"]], l,
                          "le verrou %s ne dit pas son camp" % f["tete"]["id"])
        for c in [x for lot in self.vue["deck"].values() for x in lot] + self.vue["eux"]:
            i, l = self._ligne_de(c["titre"][:20])
            self.assertIn(EMOJI_CAMP[c["camp"]], l,
                          "la pièce %s ne dit pas son camp" % c["id"])

    def test_le_gras_ne_sort_que_si_on_le_demande(self):
        nu = chr(10).join(partie_ascii.plateau(self.vue, gras=False))
        orne = chr(10).join(partie_ascii.plateau(self.vue, gras=True))
        self.assertNotIn(partie_ascii.GRAS, nu)     # redirigé : aucun code parasite
        self.assertIn(partie_ascii.GRAS, orne)
        # le gras ne change QUE l'habillage : le texte nu est le même
        depouille = orne.replace(partie_ascii.GRAS, "").replace(partie_ascii.FIN, "")
        self.assertEqual(depouille, nu)

    # ---- le point de vue -----------------------------------------------
    def test_le_camp_regarde_change_le_dessin(self):
        autre = partie_ascii.plateau(partie_cartes.vue(Partie(DUEL), "vert"), gras=False)
        self.assertNotEqual(autre, self.lignes)

    def test_une_partie_vide_ne_ment_pas(self):
        vide = dict(self.vue, fronts=[], cibles=[], deck={}, eux=[], consignes={})
        lignes = partie_ascii.plateau(vide)
        self.assertIn("👑", "\n".join(lignes))
        self.assertNotIn("LIBRES", "\n".join(lignes))


if __name__ == "__main__":
    unittest.main()
