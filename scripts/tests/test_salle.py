# -*- coding: utf-8 -*-
"""Le fil de salle et les relations qui s'ouvrent d'elles-memes.

Trois habitants dans une piece, un quatrieme sans chambre. On eprouve ce que
la doctrine promet, et surtout ce qu'elle INTERDIT :

  * ce qui se dit devant eux entre chez chacun ;
  * ce qui se CHUCHOTE n'entre que chez les nommes — c'est la garde qui
    protege le brouillard, et la seule qui casse quelque chose si elle lache ;
  * un present SANS chambre ne recoit rien et n'ouvre aucune relation : le
    filtre qui borne la charge ;
  * le hors-fiction (`pensee`) n'est entendu de personne ;
  * la co-presence ouvre les relations des DEUX cotes, avec un constat date et
    aucun jugement ;
  * rouvrir une chambre vivante n'ecrase ni le fil ni la fiche.
"""
import io
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

from agents import chambre, salle  # noqa: E402


PIECE = {"salle": "table-peinte", "lieu": "Chambre de la Table Peinte"}
QUAND = {"annee": 129, "lune": 4, "jour": 4, "minute": 531}


class BancSalle(unittest.TestCase):

    def setUp(self):
        self.vrai = chambre.CHAMBRES
        self.banc = tempfile.mkdtemp(prefix="banc-salle-")
        chambre.CHAMBRES = self.banc
        salle._tampon.clear()
        salle._rencontres.clear()
        for qui in ("gerardys", "rulf-corne", "aldon-hask"):
            chambre.ouvrir(qui)
        # `sans-chambre` n'en a pas, et c'est tout l'objet de son existence.

    def tearDown(self):
        chambre.CHAMBRES = self.vrai
        shutil.rmtree(self.banc, ignore_errors=True)

    def fil(self, qui):
        f = os.path.join(chambre.chemin(qui), "fil", "129.4.4-salle.md")
        if not os.path.exists(f):
            return ""
        with io.open(f, encoding="utf-8") as h:
            return h.read()

    def test_la_piece_entend_et_le_chuchotement_ne_fuit_pas(self):
        tous = ["gerardys", "rulf-corne", "aldon-hask", "sans-chambre"]
        salle.entendre({"type": "replique", "locuteur_id": "rulf-corne",
                        "texte": "Dix-sept jours, une nuit unique.",
                        "heure": "8h51"}, PIECE, tous, QUAND)
        # LE CHUCHOTEMENT : la salle en compte quatre, deux seulement entendent.
        salle.entendre({"type": "replique", "locuteur_id": "gerardys",
                        "texte": "Je n'ai pas brûlé la pièce d'Otto.",
                        "heure": "8h52"}, PIECE,
                       ["gerardys", "rulf-corne"], QUAND)
        # LE HORS-FICTION : nul ne l'entend, pas meme celui qui pense.
        salle.entendre({"type": "pensee", "texte": "Je devrais me taire.",
                        "heure": "8h53"}, PIECE, tous, QUAND)
        salle.deposer()

        for qui in ("gerardys", "rulf-corne"):
            self.assertIn(u"Dix-sept jours", self.fil(qui), qui)
            self.assertIn(u"pièce d'Otto", self.fil(qui), qui)
        self.assertIn(u"Dix-sept jours", self.fil("aldon-hask"))
        # LA GARDE : le tiers present n'a pas entendu ce qui s'est chuchote.
        self.assertNotIn(u"Otto", self.fil("aldon-hask"))
        # Personne n'a entendu la pensee.
        for qui in ("gerardys", "rulf-corne", "aldon-hask"):
            self.assertNotIn(u"me taire", self.fil(qui), qui)
        # Le present sans chambre n'a rien recu, et rien n'a ete cree pour lui.
        self.assertFalse(os.path.exists(chambre.chemin("sans-chambre")))

    def test_le_fil_se_lit_comme_une_scene(self):
        salle.entendre({"type": "geste", "acteur_id": "rulf-corne",
                        "texte": "Il pose son livre de marées sur la table.",
                        "heure": "8h50"}, PIECE, ["gerardys"], QUAND)
        texte = (salle.deposer(), self.fil("gerardys"))[1]
        self.assertIn(u"# Ce que j'ai entendu — 129.4.4", texte)
        self.assertIn(u"🏛 Chambre de la Table Peinte", texte)
        self.assertIn(u"*Il pose son livre de marées sur la table.*", texte)
        self.assertNotIn(u"{", texte)  # jamais du JSON : ca se relit

    def test_la_co_presence_ouvre_les_deux_cotes(self):
        salle.entendre({"type": "replique", "locuteur_id": "gerardys",
                        "texte": "Messire.", "heure": "9h00"}, PIECE,
                       ["gerardys", "rulf-corne", "sans-chambre"], QUAND)
        compte = salle.deposer()
        self.assertEqual(compte["relations"], 2)  # une paire, deux cotes
        for qui, autre in (("gerardys", "rulf-corne"),
                           ("rulf-corne", "gerardys")):
            fiche = os.path.join(chambre.chemin(qui), "relations", autre,
                                 "claude.md")
            self.assertTrue(os.path.exists(fiche), fiche)
            with io.open(fiche, encoding="utf-8") as h:
                texte = h.read()
            self.assertIn(u"Vu le 129.4.4", texte)
            self.assertIn(u"Chambre de la Table Peinte", texte)
            self.assertIn(u"rien écrit de lui", texte)
        # Celui qui n'a pas de chambre n'ouvre de relation chez personne.
        self.assertFalse(os.path.exists(os.path.join(
            chambre.chemin("gerardys"), "relations", "sans-chambre")))

    def test_la_rencontre_se_note_meme_sans_parole_rendue(self):
        # Un item qu'on ne sait pas rendre ne produit AUCUNE ligne — mais les
        # deux hommes se sont vus quand meme.
        salle.entendre({"type": "salle", "presents": []}, PIECE,
                       ["gerardys", "aldon-hask"], QUAND)
        compte = salle.deposer()
        self.assertEqual(compte["fils"], 0)
        self.assertEqual(compte["relations"], 2)

    def test_on_n_ecrase_ni_le_fil_ni_la_fiche(self):
        salle.entendre({"type": "replique", "locuteur_id": "gerardys",
                        "texte": "Premier mot.", "heure": "9h00"}, PIECE,
                       ["gerardys", "rulf-corne"], QUAND)
        salle.deposer()
        # sa main, par-dessus notre constat
        fiche = os.path.join(chambre.chemin("gerardys"), "relations",
                             "rulf-corne", "claude.md")
        with io.open(fiche, "w", encoding="utf-8") as h:
            h.write(u"# De ma main" + chr(10))
        salle.entendre({"type": "replique", "locuteur_id": "rulf-corne",
                        "texte": "Second mot.", "heure": "9h05"}, PIECE,
                       ["gerardys", "rulf-corne"], QUAND)
        compte = salle.deposer()
        texte = self.fil("gerardys")
        self.assertIn(u"Premier mot.", texte)   # la tranche d'avant tient
        self.assertIn(u"Second mot.", texte)    # la nouvelle s'ajoute
        self.assertEqual(texte.count(u"# Ce que j'ai entendu"), 1)
        with io.open(fiche, encoding="utf-8") as h:   # sa fiche est intouchee
            self.assertEqual(h.read(), u"# De ma main" + chr(10))
        self.assertEqual(compte["relations"], 0)

    def test_le_tampon_est_vide_apres_depot(self):
        salle.entendre({"type": "replique", "locuteur_id": "gerardys",
                        "texte": "Un mot.", "heure": "9h00"}, PIECE,
                       ["gerardys"], QUAND)
        salle.deposer()
        self.assertEqual(salle.deposer(), {"fils": 0, "relations": 0})


if __name__ == "__main__":
    unittest.main()
