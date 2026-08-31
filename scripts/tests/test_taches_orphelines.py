# -*- coding: utf-8 -*-
"""L'action « a designer » : a personne en passant, a son maitre d'affaire.

Deux regles qui se tiennent, et l'une sans l'autre est un defaut :

  * le noeud `vacant` est une FRONTIERE — on n'herite pas d'une charge en
    traversant l'ecriteau qui dit que personne ne la tient. Sans cela, le seul
    noeud `vacant` du tissu (46 voisins) servait de moyeu : 54 personnes sur
    114 l'atteignaient, et deux d'entre elles convergeaient sur la meme action
    orpheline a distance 4.
  * mais une action a designer n'est pas SANS MAITRE : elle est dans une
    affaire, et l'affaire a quelqu'un qui la porte. Elle lui RETOMBE dessus.
    Sans cette moitie-la, la frontiere troque une injustice contre un
    immobilisme : plus personne n'avance jamais ces actions.
"""
import collections
import os
import sys
import unittest

_d = os.path.dirname(os.path.abspath(__file__))
while os.path.basename(_d) != "scripts" and os.path.dirname(_d) != _d:
    _d = os.path.dirname(_d)
for _p in (_d, os.path.join(_d, "noyau")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Le paquet `agents.activation` relit la porte pendant son chargement : on
# passe donc par la facade, qui lie tout dans le bon ordre, puis on prend
# le module dans sys.modules. C'est la meme contrainte que celle notee
# dans agents/CLAUDE.md pour les bancs.
import boucle_activation  # noqa: E402,F401 — l'ordre des imports de la porte
taches = sys.modules["agents.activation.taches"]  # noqa: E402
from plan.expose import tisser as tisser_plan  # noqa: E402


def tissu():
    """Un tissu jouet : deux affaires, un maitre chacune, une orpheline par
    affaire, et un tiers qui n'a rien a y voir mais qui passe a cote."""
    n = {
        "pers:otto": {"genre": "personne"},
        "pers:hallis": {"genre": "personne"},
        "pers:gerardys": {"genre": "personne"},
        "a_designer": {"genre": "vacant", "quoi": "à désigner"},
        # affaire A — Otto en tient deux
        "A1": {"genre": "action", "ou": "plan:a", "quoi": "la premiere d'Otto"},
        "A2": {"genre": "action", "ou": "plan:a", "quoi": "la seconde d'Otto"},
        "Averrou": {"genre": "verrou", "ou": "plan:a", "quoi": "le verrou de A"},
        "Aorph": {"genre": "action", "ou": "plan:a", "quoi": "l'orpheline de A"},
        # affaire B — Hallis en tient une
        "B1": {"genre": "action", "ou": "plan:b", "quoi": "celle de Hallis"},
        "Bclef": {"genre": "clef", "ou": "plan:b", "quoi": "la clef de B"},
        "Borph": {"genre": "action", "ou": "plan:b", "quoi": "l'orpheline de B"},
    }
    a = [
        {"de": "A1", "vers": "pers:otto", "nature": "tient"},
        {"de": "A2", "vers": "pers:otto", "nature": "tient"},
        {"de": "B1", "vers": "pers:hallis", "nature": "tient"},
        # les orphelines : un `tient` vers l'ecriteau, et un chemin par le plan
        {"de": "Aorph", "vers": "a_designer", "nature": "tient"},
        {"de": "Borph", "vers": "a_designer", "nature": "tient"},
        {"de": "A1", "vers": "Averrou", "nature": "realise"},
        {"de": "Averrou", "vers": "Aorph", "nature": "realise"},
        {"de": "B1", "vers": "Bclef", "nature": "realise"},
        {"de": "Bclef", "vers": "Borph", "nature": "realise"},
        # le tiers touche l'ecriteau, et rien d'autre
        {"de": "pers:gerardys", "vers": "a_designer", "nature": "realise"},
    ]
    return n, a


def adjacence(n, a):
    adj = {k: [] for k in n}
    for x in a:
        adj[x["de"]].append(x["vers"])
        adj[x["vers"]].append(x["de"])
    return adj


class BancOrphelines(unittest.TestCase):

    def setUp(self):
        self.n, self.a = tissu()
        self.adj = adjacence(self.n, self.a)
        self.E = {k: 100.0 for k in self.n}

    def elit(self, qui, energies=None):
        t = taches.choisir_tache("pers:" + qui, self.n, self.a, self.adj,
                                 energies or self.E)
        return t and t["id"]

    def test_le_tiers_ne_ramasse_pas_en_passant(self):
        # LA GARDE : Gerardys touche l'ecriteau, donc les deux orphelines
        # etaient a deux crans de lui. Il n'en prend aucune.
        self.assertNotIn(self.elit("gerardys"), ("Aorph", "Borph"))

    def test_l_orpheline_retombe_sur_le_maitre_de_son_affaire(self):
        # Otto tient deux actions de l'affaire A : l'orpheline de A est a lui.
        pauvre = {k: 0.0 for k in self.n}
        pauvre["Aorph"] = 100.0
        self.assertEqual(self.elit("otto", pauvre), "Aorph")
        # Et elle n'est a personne d'autre, meme si Hallis l'atteignait.
        # (Il ne rend pas None mais une tache CREEE depuis son intention : la
        # branche de repli documentee. Ce qui compte est qu'il ne prenne pas
        # l'orpheline d'Otto.)
        self.assertNotEqual(self.elit("hallis", pauvre), "Aorph")

    def test_chacun_son_affaire(self):
        pauvre = {k: 0.0 for k in self.n}
        pauvre["Borph"] = 100.0
        self.assertEqual(self.elit("hallis", pauvre), "Borph")
        self.assertNotEqual(self.elit("otto", pauvre), "Borph")

    def test_le_maitre_fait_d_abord_ce_qui_lui_est_assigne(self):
        # La retombee ne PASSE PAS devant une assignation : a energie egale,
        # Otto prend l'une de ses deux actions declarees, pas l'orpheline.
        self.assertIn(self.elit("otto"), ("A1", "A2"))

    def test_une_action_faite_n_est_plus_elue(self):
        self.n["A1"]["etat"] = "faite"
        pauvre = {k: 0.0 for k in self.n}
        pauvre["A1"] = 100.0
        self.assertNotEqual(self.elit("otto", pauvre), "A1")

    def test_une_dependance_ouverte_bloque_l_action(self):
        self.n["A1"]["depend_de"] = ["A2"]
        self.n["A2"]["etat"] = "en cours"
        pauvre = {k: 0.0 for k in self.n}
        pauvre["A1"] = 100.0
        self.assertNotEqual(self.elit("otto", pauvre), "A1")

    def test_une_dependance_faite_libere_l_action(self):
        self.n["A1"]["depend_de"] = ["A2"]
        self.n["A2"]["etat"] = "faite"
        pauvre = {k: 0.0 for k in self.n}
        pauvre["A1"] = 100.0
        self.assertEqual(self.elit("otto", pauvre), "A1")

    def test_le_tissu_garde_etat_et_dependances_des_plans(self):
        plans = [{
            "id": "essai",
            "actions": [{
                "id": "A1", "quoi": "agir", "etat": "a faire",
                "depend_de": ["A0"], "office": "otto",
                "jour_du": {"annee": 129, "lune": 4, "jour": 9},
            }],
        }]
        noeuds, _doubles = tisser_plan.indexer(
            [], [], [], plans, [], [])
        self.assertEqual("a faire", noeuds["A1"]["etat"])
        self.assertEqual(["A0"], noeuds["A1"]["depend_de"])
        self.assertEqual("otto", noeuds["A1"]["office"])

    def test_une_action_tenue_par_un_office_va_a_son_titulaire(self):
        n = {
            "pers:tobb": {"genre": "personne"},
            "pers:tiers": {"genre": "personne"},
            "plan-offices:O04": {"genre": "office"},
            "courir": {"genre": "action", "quoi": "porter le pli"},
        }
        a = [
            {"de": "courir", "vers": "plan-offices:O04", "nature": "tient"},
            {"de": "plan-offices:O04", "vers": "pers:tobb", "nature": "tient"},
            # Le tiers passe pres de l'office, mais ne le tient pas.
            {"de": "pers:tiers", "vers": "plan-offices:O04", "nature": "lie"},
        ]
        adj = adjacence(n, a)
        energies = {k: 100.0 for k in n}
        elu = taches.choisir_tache("pers:tobb", n, a, adj, energies)
        self.assertEqual("courir", elu and elu["id"])
        elu = taches.choisir_tache("pers:tiers", n, a, adj, energies)
        self.assertNotEqual("courir", elu and elu["id"])

    def test_le_tissage_lie_un_office_a_tous_ses_titulaires(self):
        books = [{
            "id": "plan-offices", "titre": "Offices",
            "colonnes": ["N°", "🏷️ L'office", "👤 Le titulaire"],
            "lignes": [{"cellules": [
                "O04", "Coureurs", "Tobb, de la Claie ; Nesse, du Marais",
            ]}],
        }]
        personnages = [
            {"id": "tobb", "nom": "Tobb"},
            {"id": "nesse", "nom": "Nesse"},
        ]
        aretes = tisser_plan.tisser(
            books, [], [], [], [], personnages=personnages)
        liens = {(a["de"], a["vers"], a["nature"]) for a in aretes}
        self.assertIn(("plan-offices:O04", "pers:tobb", "tient"), liens)
        self.assertIn(("plan-offices:O04", "pers:nesse", "tient"), liens)


if __name__ == "__main__":
    unittest.main()
