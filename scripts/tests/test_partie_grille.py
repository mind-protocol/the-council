# -*- coding: utf-8 -*-
"""La position en grille (partie_grille.py).

Deux choses à garder, et ce sont les deux raisons d'avoir une grille à côté de
l'arbre : que les COLONNES tombent juste — une grille désalignée d'une colonne
est illisible, et les emojis la désalignent —, et qu'elle dise les CREUX, les
états sur lesquels personne n'a rien posé, que l'arbre ne sait pas montrer.
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
import partie_grille  # noqa: E402

DUEL = os.path.join(SCRIPTS, "tests", "donnees", "partie-duel.jsonl")
PARTIES = os.path.join(SCRIPTS, "..", "etat", "parties")


def _vue(chemin, camp=None):
    return partie_cartes.vue(Partie(chemin), camp)


class TestLargeur(unittest.TestCase):
    """La mesure d'affichage. C'est le seul endroit où une erreur d'un caractère
    casse tout le dessin, donc c'est celui qu'on éprouve le plus."""

    def test_le_texte_nu_vaut_sa_longueur(self):
        self.assertEqual(partie_grille._larg(""), 0)
        self.assertEqual(partie_grille._larg("abc"), 3)

    def test_un_emoji_vaut_deux_colonnes(self):
        for e in ("⚫", "\U0001F409", "❓", "⛵"):
            self.assertEqual(partie_grille._larg(e), 2, repr(e))

    def test_un_signe_presente_en_emoji_vaut_deux_colonnes(self):
        """U+2694 seul vaut une colonne ; suivi du sélecteur U+FE0F il en vaut
        deux, et c'est la forme que le greffe écrit partout. Sans cette règle,
        toute ligne portant une troupe se décalait d'une colonne."""
        self.assertEqual(partie_grille._larg("⚔"), 1)
        self.assertEqual(partie_grille._larg("⚔️"), 2)
        self.assertEqual(partie_grille._larg("\U0001F5DD️"), 2)

    def test_poser_rend_toujours_la_largeur_demandee(self):
        for t in ("", "a", "⚫⚔️ 400", "\U0001F409 Caraxes", "x" * 80):
            for n in (5, 12, 26):
                self.assertEqual(partie_grille._larg(partie_grille._pose(t, n)), n,
                                 "%r posé sur %d" % (t, n))


class TestGrille(unittest.TestCase):
    def setUp(self):
        self.vue = _vue(os.path.join(PARTIES, "le-trone.jsonl"), "noir")
        self.lignes = partie_grille.grille(self.vue)

    def test_les_colonnes_sont_alignees(self):
        """Toutes les lignes d'un même paquet portent leurs barres aux mêmes
        colonnes d'affichage — c'est la définition d'une grille."""
        paquets, courant = [], []
        for l in self.lignes:
            if "│" in l and not l.startswith(" ─") and "┼" not in l:
                courant.append(l)
            elif courant:
                paquets.append(courant)
                courant = []
        if courant:
            paquets.append(courant)
        self.assertTrue(paquets)
        for paquet in paquets:
            reperes = None
            for l in paquet:
                cols = [partie_grille._larg(l[:i]) for i, c in enumerate(l) if c == "│"]
                if reperes is None:
                    reperes = cols
                self.assertEqual(cols, reperes, "barres décalées : %r" % l)

    def test_une_colonne_par_point_de_contact(self):
        cols = partie_grille.colonnes(self.vue)
        self.assertEqual(len(cols), len(self.vue["fronts"]),
                         "le-trone n'a que des fronts, pas de clé nue")
        for c in cols:
            self.assertIn(str(c["sur"]), "\n".join(self.lignes))

    def test_ce_qui_prevaut_est_devant(self):
        """La règle 8 décide du premier rang ; la grille ne fait que le poser."""
        for c in partie_grille.colonnes(self.vue):
            f = [x for x in self.vue["fronts"] if str(x["sur"]) == str(c["sur"])]
            if not f:
                continue
            self.assertEqual(c["prevaut"].get("camp"), f[0]["prevaut"],
                             "sur %s, ce n'est pas le camp qui prévaut qui est devant" % c["sur"])
            if c["derriere"]:
                self.assertNotEqual(c["derriere"].get("camp"), c["prevaut"].get("camp"))

    def test_les_creux_sont_dits(self):
        """CE QUE L'ARBRE NE MONTRE PAS : les états sur lesquels rien n'est posé."""
        trous = partie_grille.creux(self.vue)
        self.assertTrue(trous, "le-trone doit porter des états sans personne dessus")
        t = "\n".join(self.lignes)
        self.assertIn("sans personne", t)
        for c in trous:
            self.assertIn(str(c["id"]), t)

    def test_un_etat_contesté_n_est_pas_un_creux(self):
        pris = set(str(c["sur"]) for c in partie_grille.colonnes(self.vue))
        for c in partie_grille.creux(self.vue):
            self.assertNotIn(str(c["id"]), pris)

    def test_seules_les_pieces_engagees_sont_dans_la_grille(self):
        cols = partie_grille.colonnes(self.vue)
        dans = [p for c in cols for lot in c["pieces"].values() for p in lot]
        self.assertTrue(dans)
        for p in dans:
            self.assertTrue(p.get("engagee_par"), "%s n'est engagée par rien" % p["id"])

    def test_un_contact_unilateral_montre_la_moitie_vide(self):
        """noirs-verts n'a AUCUN blocage : ses deux colonnes sont des clés que
        rien ne contredit. La grille doit alors montrer un rang adverse vide —
        c'est le diagnostic de la partie, et l'arbre ne le donne pas."""
        vue = _vue(os.path.join(PARTIES, "noirs-verts.jsonl"), "noir")
        self.assertEqual(len(vue["fronts"]), 0)
        cols = partie_grille.colonnes(vue)
        self.assertTrue(cols, "des clés nues font quand même des points de contact")
        for c in cols:
            self.assertIsNone(c["derriere"], "personne n'est en face")
            self.assertEqual(c["pourquoi"], "rien en face")
            self.assertEqual(len(c["pieces"]), 1, "un seul camp est engagé sur %s" % c["sur"])

    def test_une_position_vraiment_vide_le_dit(self):
        vue = dict(_vue(DUEL, "noir"), fronts=[], cibles=[])
        self.assertIn("Aucun point de contact", "\n".join(partie_grille.grille(vue)))

    def test_toutes_les_parties_se_dessinent(self):
        for nom in ("le-trone", "duel-50", "noirs-verts", "enquete-vauthier",
                    "pont-et-moulin", "local-a-velos"):
            vue = _vue(os.path.join(PARTIES, nom + ".jsonl"))
            lignes = partie_grille.grille(vue)
            self.assertTrue(lignes, nom)
            for l in lignes:
                self.assertNotIn("\n", l)

    def test_le_banc_du_duel_se_dessine_aussi(self):
        lignes = partie_grille.grille(_vue(DUEL, "noir"))
        self.assertTrue(lignes)


if __name__ == "__main__":
    unittest.main()
