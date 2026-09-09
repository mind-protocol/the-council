# -*- coding: utf-8 -*-
"""La vue joueur d'une partie (partie_cartes.py), sur le duel joué au tour 2 :
ce que le Noir voit, ce qu'il ne voit pas, et l'apparence de chaque carte."""
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

DUEL = os.path.join(SCRIPTS, "tests", "donnees", "partie-duel.jsonl")


def _tous(cartes):
    for c in cartes:
        yield c
        for s in c.get("sous") or []:
            yield from _tous([s])


# Les noms en clair sont POSÉS ICI, et non lus dans etat/personnages.json : un
# test qui lit le vrai état est un test qui tombe le jour où la partie avance.
NOMS = {"steffon-darklyn": "Ser Steffon Darklyn", "daemon": "Daemon Targaryen",
        "aemond": "Aemond Targaryen", "rulf-corne": "Rulf Corne",
        "criston-cole": "Criston Cole", "aegon-ii": "Aegon II"}


class PartieCartesTest(unittest.TestCase):
    def setUp(self):
        partie_cartes._NOMS = dict(NOMS)
        self.v = partie_cartes.vue(Partie(DUEL), "noir")

    def tearDown(self):
        partie_cartes._NOMS = None

    def test_tour_et_trait(self):
        self.assertEqual(self.v["tour"], 2)
        self.assertEqual(self.v["jours"], 2)
        # LE TRAIT SUIT LE DERNIER COUP COMPTÉ, pas la dernière ligne écrite.
        # Dans le duel, noir a levé (ligne 17, compté) et vert n'a répondu que
        # par des demandes et une question — gratuites, hors compte. Le tour est
        # donc à VERT, qui n'a pas encore joué de coup compté. L'ancienne règle
        # rendait « noir » et lui donnait deux coups de suite.
        self.assertEqual(self.v["trait"], "vert")
        self.assertIsNone(self.v["trone"])      # rien n'a été constaté sur une racine

    def test_deux_fronts_verts_sur_le_trone(self):
        fronts = self.v["fronts"]
        self.assertEqual([f["id"] for f in fronts], ["49001", "49002"])
        for f in fronts:
            self.assertEqual(f["tete"]["camp"], "vert")
            self.assertEqual(f["tete"]["type"], "verrou")
            self.assertEqual(f["sur"], "49000")
            # Plus de « source : lieux.json … » au pied : le nom d'un fichier
            # d'état n'a rien à faire sous les yeux du joueur.
            self.assertEqual(f["tete"]["pied"]["gauche"], "")
            self.assertNotIn(".json", str(f["tete"]))

    def test_la_position_complete_est_servie_les_deux_camps(self):
        """PAS DE BROUILLARD sur le plateau (3.9) : les pièces d'en face sont
        servies comme les nôtres, engagées ou non. On ne joue pas contre un
        adversaire dont on ne voit jamais les coups."""
        eux = {c["id"] for c in self.v["eux"]}
        self.assertIn("vhagar", eux)          # engagée dans un blocage
        self.assertIn("ost-criston", eux)     # engagée dans rien du tout
        # et les nôtres ne sont pas dans leur rangée
        self.assertNotIn("caraxes", eux)
        # les pièces qui portent un blocage restent nommées dans le corps du 🔒
        self.assertIn("garnison", self.v["fronts"][0]["tete"]["corps"].lower())

    def test_la_clef_suspendue_porte_sa_question_et_sa_piece(self):
        """La pièce engagée est une CARTE posée sur l'ordre, pas une ligne de
        texte : on met des cartes sur des cartes, et l'engagement se lit là où
        il a lieu."""
        portes = self.v["fronts"][1]
        self.assertEqual(len(portes["pile"]), 1)
        clef = portes["pile"][0]
        self.assertEqual(clef["type"], "clef")
        self.assertEqual(clef["pied"]["droite"], "❓ suspendu")
        types = [s["type"] for s in clef["sous"]]
        self.assertEqual(types[0], "question")
        self.assertIn("piece", types)   # la pièce engagée se VOIT sur le front
        self.assertEqual(clef["sous"][0]["n"], 22)

    def test_apparences_du_deck(self):
        d = self.v["deck"]
        par_id = {c["id"]: c for r in d.values() for c in r}
        self.assertEqual(par_id["caraxes"]["apparence"], "libre")
        # le genre est le SIGNE de la carte, plus un préfixe du titre
        self.assertEqual(par_id["caraxes"]["emoji"], "🐉")
        self.assertTrue(par_id["caraxes"]["titre"].startswith("Caraxes"))
        self.assertEqual(par_id["coques-est"]["apparence"], "libre")
        self.assertEqual(par_id["coques-est"]["emoji"], "⛵")
        self.assertEqual(par_id["ost-noir"]["apparence"], "route")
        self.assertEqual(par_id["ost-noir"]["pied"]["droite"], "dans 4 j")
        self.assertEqual(par_id["steffon-darklyn"]["apparence"], "posee")
        self.assertEqual([c["id"] for c in d["route"]], ["ost-noir"])
        self.assertEqual(sorted(c["id"] for c in d["main"]), ["caraxes", "coques-est"])

    def test_la_piece_ne_repete_pas_son_porteur_ni_son_lieu(self):
        """Le lieu ne s'imprime plus sur chaque carte, et le porteur ne se dit
        qu'une fois : « Caraxes, monté par Daemon » ne se double pas d'un
        « tenue par Daemon Targaryen ». Mais un titre qui NE dit pas le porteur
        le garde — c'est une information, pas une répétition."""
        car = [c for r in self.v["deck"].values() for c in r if c["id"] == "caraxes"][0]
        self.assertEqual(car["corps"], "")          # plus de ligne « tenue par »
        self.assertEqual(car["pied"]["gauche"], "Daemon Targaryen")   # le titre est nu : on le dit

        p = Partie(DUEL)
        p.ressources["caraxes"]["texte"] = "Caraxes, monté par Daemon"
        c = partie_cartes.carte_piece(p, "caraxes")
        self.assertEqual(c["pied"]["gauche"], "")   # le titre le dit déjà

    def test_le_porteur_survit_quand_seul_son_titre_se_ressemble(self):
        """« Corlys Velaryon, le Serpent de Mer » tient « les coques du Serpent
        de Mer » : le surnom coïncide, l'homme reste nommé."""
        p = Partie(DUEL)
        p.ressources["coques-est"]["texte"] = "les coques du Serpent de Mer"
        p.ressources["coques-est"]["tenu_par"] = "corlys"
        partie_cartes._NOMS["corlys"] = "Corlys Velaryon, le Serpent de Mer"
        c = partie_cartes.carte_piece(p, "coques-est")
        self.assertEqual(c["pied"]["gauche"], "Corlys Velaryon, le Serpent de Mer")

    def test_aucun_id_nu_dans_les_titres(self):
        for f in self.v["fronts"]:
            for c in [f["tete"]] + list(_tous(f["pile"])):
                self.assertNotRegex(c["titre"], r"^\d+$")
                self.assertNotIn("-", c["titre"].split(" ")[-1] if c["type"] == "piece" else "")

    def test_l_etat_cible_compte_ses_verrous(self):
        self.assertEqual(self.v["cibles"][0]["corps"], "2 choses s'y opposent")

    def test_le_ruban_d_une_clef_qui_tient(self):
        """Le ruban d'un ordre non suspendu se calcule — il l'a un jour fait
        planter, faute d'avoir sous la main l'identité de la clé qu'il juge."""
        p = Partie(DUEL)
        p.cles["49010"]["suspendue_par"] = None
        v = partie_cartes.vue(p, "noir")
        clef = v["fronts"][1]["pile"][0]
        self.assertEqual(clef["pied"]["droite"], "⏳ prêt dans 4 j")

    def test_les_obstacles_se_comptent_en_descendant(self):
        """Ce qui barre un dessein barre celui qu'il sert : « rien ne s'y oppose »
        sur une racine dont les enfants sont bloqués serait un mensonge."""
        p = Partie(DUEL)
        p.etats["fille"] = {"camp": "noir", "texte": "Un dessein qu'on sert", "sert": "49000",
                            "vrai": None, "arrive_tour": None, "deck": True}
        p.blocages["b-fille"] = {"camp": "vert", "sur": "fille", "texte": "Un obstacle de plus",
                                 "engage": [], "tombe": False, "n": 99, "prete_tour": 0}
        v = partie_cartes.vue(p, "noir")
        racine = [d for d in v["cibles"] if d["id"] == "49000"][0]
        self.assertEqual(racine["corps"], "3 choses s'y opposent")

    def test_les_deux_camps_voient_la_meme_position_pas_le_meme_cote(self):
        """La position est la même pour les deux ; ce qui change est de quel
        côté de la table on est assis."""
        n = partie_cartes.vue(Partie(DUEL), "noir")
        v = partie_cartes.vue(Partie(DUEL), "vert")
        self.assertEqual([f["id"] for f in n["fronts"]], [f["id"] for f in v["fronts"]])
        # ce qui est « contre nous » s'inverse
        self.assertTrue(all(f["contre_nous"] for f in n["fronts"]))
        self.assertFalse(any(f["contre_nous"] for f in v["fronts"]))
        # et la main change de côté
        a_nous = {c["id"] for r in n["deck"].values() for c in r}
        self.assertIn("caraxes", a_nous)
        self.assertNotIn("vhagar", a_nous)
        self.assertIn("vhagar", {c["id"] for c in v["eux"]} ^ {c["id"] for r in v["deck"].values() for c in r})

    def test_ce_qui_est_neuf_se_dit_au_numero_de_ligne(self):
        """Le jsonl est append-only : le dernier numéro vu suffit à dire
        exactement ce qui a bougé, sans rien stocker d'autre."""
        p = Partie(DUEL)
        dernier = p.lignes[-1]["n"]
        tout_vu = partie_cartes.vue(p, "noir", vu=dernier)
        self.assertFalse(any(c["neuf"] for c in tout_vu["eux"]))
        self.assertEqual(tout_vu["dernier"], dernier)

        # PAS DE MARQUE-PAGE = rien de neuf. Une première ouverture ne peut
        # pas avoir « manqué » quoi que ce soit : sans cette porte, elle
        # marquait les trente-neuf cartes du plateau d'un coup.
        sans_marque = partie_cartes.vue(p, "noir", vu=0)
        self.assertFalse(any(c["neuf"] for c in sans_marque["eux"]))
        self.assertFalse(any(f["tete"]["neuf"] for f in sans_marque["fronts"]))

        # Une pièce demandée après notre dernier passage est neuve, les autres
        # non. On écrit dans une COPIE : `Partie.ecrire` appende pour de vrai,
        # et ce banc a pollué le fichier de donnée une fois — un test qui écrit
        # travaille sur du jetable, sans exception.
        dossier = tempfile.mkdtemp(prefix="partie-neuf-")
        try:
            copie = os.path.join(dossier, "duel.jsonl")
            shutil.copyfile(DUEL, copie)
            p2 = Partie(copie)
            avant = p2.lignes[-1]["n"]
            p2.ecrire({"camp": "vert", "coup": "demander", "id": "renfort-tardif",
                       "nombre": 900, "texte": "un renfort de plus, à Port-Réal"})
            v = partie_cartes.vue(p2, "noir", vu=avant)
            self.assertEqual([c["id"] for c in v["eux"] if c["neuf"]], ["renfort-tardif"])
        finally:
            shutil.rmtree(dossier, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()


class GenreTest(unittest.TestCase):
    """Le sous-signe d'une pièce hors de la Danse, et le faux ami « Costa »."""

    def g(self, texte, rid="x", **k):
        r = dict(texte=texte, tenu_par=k.get("tenu_par"), genre=k.get("genre"))
        return partie_cartes.genre_piece(r, rid)

    def test_le_vocabulaire_d_une_enquete(self):
        self.assertEqual(self.g("le journal de l armoire a pharmacie"), "📄")
        self.assertEqual(self.g("les tubes conserves en serotheque : dosages"), "🧪")
        self.assertEqual(self.g("le corps de M. Kessler"), "⚰️")
        self.assertEqual(self.g("la reserve de thymoglobuline et d ampoules"), "💊")
        self.assertEqual(self.g("les acces badges du pavillon"), "🔑")
        self.assertEqual(self.g("la mortalite du service : trois morts par trimestre"), "📊")
        self.assertEqual(self.g("les greffes du pavillon B, onze lits"), "🛏️")
        self.assertEqual(self.g("deux agents en faction de nuit"), "🛡️")
        self.assertEqual(self.g("quinze ans de service sans une plainte"), "🎖️")

    def test_un_mot_cle_ne_se_lit_qu_en_debut_de_mot(self):
        self.assertEqual(self.g("le brigadier Costa", rid="costa"), "📦")
        self.assertEqual(self.g("l ost de Peyredragon"), "⚔️")

    def test_la_danse_garde_ses_signes(self):
        self.assertEqual(self.g("Caraxes, monte par Daemon"), "🐉")
        self.assertEqual(self.g("les coques du Serpent de Mer"), "⛵")
        self.assertEqual(self.g("la caisse de Peyredragon", genre="or"), "💰")

    def test_le_genre_dit_par_la_ligne_prime(self):
        self.assertEqual(self.g("le brigadier Costa", genre="homme"), "👤")
        self.assertEqual(self.g("n importe quoi", genre="🩺"), "🩺")
