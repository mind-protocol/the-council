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
import partie_marques  # noqa: E402
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

    # Depuis le 5.9 une pièce se pose SUR un état : un verrou s'il est à eux, une
    # clef qui le sert s'il est à nous. Avant, une partie qui s'ouvre — deux
    # racines, aucun verrou — n'offrait aucun geste à l'écran.
    def test_piece_sur_notre_etat_pose_une_clef_qui_le_sert(self):
        r = partie_gestes.poser(self.p, "noir", ["caraxes"], "49000", "Caraxes au-dessus de la salle")
        self.assertTrue(r["ok"], r["refus"])
        self.assertEqual(r["ligne"]["coup"], "lever")
        self.assertEqual(r["ligne"]["sert"], "49000")
        self.assertNotIn("ouvre", r["ligne"])
        self.assertEqual(r["ligne"]["engage"], ["caraxes"])
        self.assertIn("clef posée pour", r["dit"])

    def test_piece_sur_un_etat_adverse_pose_un_verrou(self):
        r = partie_gestes.poser(self.p, "noir", ["caraxes"], "70000", "Caraxes tient le ciel")
        self.assertTrue(r["ok"], r["refus"])
        self.assertEqual(r["ligne"]["coup"], "bloquer")
        self.assertEqual(r["ligne"]["sur"], "70000")
        self.assertEqual(r["ligne"]["camp"], "noir")
        self.assertIn("verrou posé sur", r["dit"])
        # et la vue le sert aussitôt comme un front contre eux
        v = partie_cartes.vue(self.relire(), "noir")
        self.assertTrue(any(f["id"] == r["ligne"]["id"] for f in v["fronts"]))

    def test_viser_sous_notre_etat(self):
        r = partie_gestes.viser(self.p, "noir", "49000", "Une porte de Port-Réal est acquise")
        self.assertTrue(r["ok"], r["refus"])
        self.assertEqual(r["ligne"]["coup"], "viser")
        self.assertEqual(r["ligne"]["sert"], "49000")
        self.assertEqual(self.relire().etats[r["ligne"]["id"]]["texte"], "Une porte de Port-Réal est acquise")

    def test_demander_une_piece_l_ecrit_en_attente(self):
        r = partie_gestes.demander(self.p, "noir", "un comptage de la réserve", "pavillon-b", "costa")
        self.assertTrue(r["ok"], r["refus"])
        self.assertEqual(r["ligne"]["coup"], "demander")
        self.assertEqual(r["ligne"]["lieu"], "pavillon-b")
        self.assertEqual(r["ligne"]["tenu_par"], "costa")
        self.assertIn("demande portée", r["dit"])
        pr = self.relire()
        self.assertTrue(pr.ressources[r["ligne"]["id"]].get("en_attente"))
        # et elle se voit, en route vers l'arbitre, sans compter pour le tour
        v = partie_cartes.vue(pr, "noir")
        self.assertIn(r["ligne"]["id"], [c["id"] for c in v["deck"]["route"]])
        self.assertFalse(r.get("avertissements"))

    def test_demander_sans_phrase_est_refuse(self):
        avant = len(self.lignes())
        self.assertFalse(partie_gestes.demander(self.p, "noir", "  ")["ok"])
        self.assertEqual(len(self.lignes()), avant)

    def test_viser_sous_un_etat_adverse_ou_sans_phrase_est_refuse(self):
        avant = len(self.lignes())
        self.assertFalse(partie_gestes.viser(self.p, "noir", "70000", "Quelque chose")["ok"])
        self.assertFalse(partie_gestes.viser(self.p, "noir", "49000", "   ")["ok"])
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

    # ---- justifier -------------------------------------------------------
    def test_question_sur_une_piece_d_en_face_suspend_et_ne_coute_pas_le_tour(self):
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        r = partie_gestes.justifier(self.p, "noir", bid, "Par où entrent-ils ?")
        self.assertTrue(r["ok"], r["refus"])
        self.assertEqual(r["ligne"]["coup"], "justifier")
        self.assertEqual(r["ligne"]["sur"], bid)
        self.assertEqual(r["ligne"]["texte"], "Par où entrent-ils ?")
        # la cible est suspendue au grand livre, et le coup n'a rien coûté
        relu = self.relire()
        self.assertTrue(relu.blocages[bid].get("suspendue_par"))
        self.assertTrue(relu.blocages[bid].get("justifiee"))

    def test_question_sans_phrase_refusee(self):
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        r = partie_gestes.justifier(self.p, "noir", bid, "   ")
        self.assertFalse(r["ok"])
        self.assertIn("phrase", " ".join(r["refus"]))
        self.assertEqual(self.lignes()[-1].count('"justifier"'), 0)

    def test_une_seule_question_par_piece(self):
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        self.assertTrue(partie_gestes.justifier(self.p, "noir", bid, "Par où ?")["ok"])
        r = partie_gestes.justifier(self.relire(), "noir", bid, "Et par où encore ?")
        self.assertFalse(r["ok"])
        self.assertIn("déjà", " ".join(r["refus"]))

    def test_on_n_exige_pas_sa_propre_chaine(self):
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        r = partie_gestes.justifier(self.p, "vert", bid, "Par où entrent-ils ?")
        self.assertFalse(r["ok"])

    def marquee(self, part, camp):
        """La vue telle que l'écran la reçoit : les marques y sont posées par
        `partie_marques`, comme le fait `partie.py --cartes`."""
        return partie_marques.poser(partie_cartes.vue(part, camp), part, camp)

    def test_la_vue_dit_ce_qui_est_encore_questionnable(self):
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        cartes = self.marquee(self.p, "noir")
        tetes = dict((f["tete"]["id"], f["tete"]) for f in cartes["fronts"])
        self.assertTrue(tetes[bid].get("questionnable"))
        # une fois la question posée, la poignée disparaît de la vue
        partie_gestes.justifier(self.p, "noir", bid, "Par où entrent-ils ?")
        apres = self.marquee(self.relire(), "noir")
        tetes = dict((f["tete"]["id"], f["tete"]) for f in apres["fronts"])
        self.assertFalse(tetes[bid].get("questionnable"))
        # et nos propres cartes ne l'ont jamais portée
        for f in apres["fronts"]:
            if f["tete"]["camp"] == "noir":
                self.assertFalse(f["tete"].get("questionnable"))

    # ---- le maillon, qui répond au ❓ -------------------------------------
    def test_le_maillon_leve_la_suspension_et_repond_a_la_question(self):
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        q = partie_gestes.justifier(self.p, "noir", bid, "Par où entrent-ils ?")
        self.assertTrue(q["ok"], q["refus"])
        p2 = self.relire()
        self.assertTrue(p2.blocages[bid]["suspendue_par"])
        r = partie_gestes.maillon(p2, "vert", bid, "Par la poterne, ser Rulf, la nuit du 3")
        self.assertTrue(r["ok"], r["refus"])
        self.assertEqual(r["ligne"]["coup"], "agir")
        self.assertEqual(r["ligne"]["realise"], bid)
        self.assertEqual(r["ligne"]["repond"], q["ligne"]["n"])   # gratuit : il répond
        self.assertFalse(self.relire().blocages[bid]["suspendue_par"])

    def test_le_maillon_veut_une_phrase(self):
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        r = partie_gestes.maillon(self.p, "vert", bid, "  ")
        self.assertFalse(r["ok"])
        self.assertIn("phrase", " ".join(r["refus"]))

    def test_on_n_ecrit_pas_le_maillon_d_un_autre_camp(self):
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        r = partie_gestes.maillon(self.p, "noir", bid, "Par la poterne")
        self.assertFalse(r["ok"])

    def test_la_vue_dit_quelle_carte_attend_son_maillon(self):
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        partie_gestes.justifier(self.p, "noir", bid, "Par où entrent-ils ?")
        p2 = self.relire()
        # celui dont c'est la pièce voit la poignée ; l'autre camp, jamais
        tetes = dict((f["tete"]["id"], f["tete"]) for f in self.marquee(p2, "vert")["fronts"])
        self.assertTrue(tetes[bid].get("suspendue"))
        self.assertEqual(tetes[bid].get("repondre"), bid)
        # et la QUESTION elle-meme repond, parce que c'est la qu'on clique
        q = [c for f in self.marquee(p2, "vert")["fronts"]
             for c in f["pile"] if c["type"] == "question"]
        self.assertEqual([x.get("repondre") for x in q], [bid])
        # jamais chez l'autre camp : ce n'est pas sa chaine a ecrire
        q = [c for f in self.marquee(p2, "noir")["fronts"]
             for c in f["pile"] if c["type"] == "question"]
        self.assertEqual([x.get("repondre") for x in q], [None])
        tetes = dict((f["tete"]["id"], f["tete"]) for f in self.marquee(p2, "noir")["fronts"])
        self.assertFalse(tetes[bid].get("suspendue"))

    def test_la_question_sur_un_verrou_se_voit_puis_se_marque_repondue(self):
        """Elle ne se voyait NULLE PART : la carte ❓ n'était accrochée qu'aux
        clefs, aux frappes et aux états. Et une fois répondue elle disparaissait,
        ce qui ressemble à ne l'avoir jamais posée."""
        bid = [b for b, x in self.p.blocages.items() if x["camp"] == "vert"][0]
        partie_gestes.justifier(self.p, "noir", bid, "Par où entrent-ils ?")
        q = [c for f in self.marquee(self.relire(), "noir")["fronts"]
             for c in f["pile"] if c["type"] == "question"]
        self.assertEqual(len(q), 1, "la question doit paraître sur le verrou")
        self.assertEqual(q[0]["pied"]["droite"], "en attente")

        partie_gestes.maillon(self.relire(), "vert", bid, "Par la poterne, ser Rulf")
        q = [c for f in self.marquee(self.relire(), "noir")["fronts"]
             for c in f["pile"] if c["type"] == "question"]
        self.assertEqual(len(q), 1, "elle reste sur la table après la réponse")
        self.assertEqual(q[0]["pied"]["droite"], "répondue")
        self.assertEqual(q[0]["apparence"], "repondue")

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
