# -*- coding: utf-8 -*-
"""LES MUTATIONS D'UN MEME LOT S'EVALUENT DANS L'ORDRE ECRIT.

Deux defauts de porte, trouves le 129.4.3 par mj-accalmie et verifies par mj :

  1. valider() lisait l'etat INITIAL quand appliquer() s'execute dans l'ordre.
     Un retrait suivi d'un ajout sur la meme clef se voyait refuser une
     collision qui n'existe qu'entre deux lignes du meme fichier — et il n'y
     avait donc AUCUN moyen propre de corriger un declencheur.
  2. les deux voies filtraient `isinstance(d, dict)` : une chaine tombee dans
     `declencheurs` etait increvable.

Chaque cas porte ici son epreuve, et l'inverse — ce qui doit encore etre
refuse l'est toujours. Un lot n'a le droit de projeter que ce qu'il ecrit.
"""
import os
import sys
import unittest

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_SCRIPTS, os.path.join(_SCRIPTS, "noyau")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from etat.mutations.validation import valider  # noqa: E402
from etat.mutations.application import appliquer  # noqa: E402


def tables_avec(declencheurs, croyances=None):
    """Le minimum que valider() ouvre : une tete, son homme, et des tables vides."""
    tete = {
        "personnage_id": "mestre-hallis",
        "echelle": "figurant",
        "intention": "tenir la rookerie",
        "croyances": list(croyances or []),
        "ignore": [],
        "plan": [],
        "declencheurs": list(declencheurs),
        "date_maj": {"annee": 129, "lune": 4, "jour": 3},
    }
    return {
        "intentions": [tete],
        "evenements": [], "personnages": [{"id": "mestre-hallis"}],
        "monde": {}, "journal": {}, "lieux": [], "relations": [],
        "maisons": [], "plis": {"plis": []}, "jetons": {"jetons": []},
        "mains": {"mains": []}, "books": [],
    }


def mut(op, valeur):
    return {"table": "intentions", "operation": op,
            "cible": "mestre-hallis", "valeur": valeur}


NEUF = {"si": "SE PRESENTE A LA BARBACANE", "alors": "il monte au corbeau"}
ANCIEN = "arrive a Accalmie"


class OrdreDuLot(unittest.TestCase):

    def test_retrait_puis_ajout_sur_la_meme_condition_passe(self):
        """LE CAS DE MJ-ACCALMIE : modifier un declencheur en deux mutations."""
        t = tables_avec([{"si": ANCIEN, "alors": "il monte au corbeau"}])
        plan, erreurs = valider([mut("declencheur_retirer", ANCIEN),
                                 mut("declencheur_ajouter",
                                     dict(NEUF, si=ANCIEN))], t)
        self.assertEqual([], erreurs)
        self.assertEqual(2, len(plan))
        appliquer(plan, t)
        self.assertEqual([dict(NEUF, si=ANCIEN)],
                         t["intentions"][0]["declencheurs"])

    def test_la_collision_vraie_est_toujours_refusee(self):
        """L'INVERSE : sans le retrait, le doublon reste un refus."""
        t = tables_avec([{"si": ANCIEN, "alors": "x"}])
        plan, erreurs = valider([mut("declencheur_ajouter",
                                     dict(NEUF, si=ANCIEN))], t)
        self.assertEqual(1, len(erreurs))
        self.assertIn("deja un declencheur", erreurs[0])
        self.assertEqual([], plan)

    def test_deux_ajouts_jumeaux_dans_un_lot_sont_refuses(self):
        """La projection ne doit pas OUVRIR une porte : le lot se voit lui-meme."""
        t = tables_avec([])
        plan, erreurs = valider([mut("declencheur_ajouter", NEUF),
                                 mut("declencheur_ajouter", NEUF)], t)
        self.assertEqual(1, len(erreurs))
        self.assertEqual(1, len(plan))

    def test_valider_ne_touche_pas_la_table(self):
        """valider() DECRIT. S'il ecrivait, appliquer() poserait deux fois."""
        t = tables_avec([])
        valider([mut("declencheur_ajouter", NEUF)], t)
        self.assertEqual([], t["intentions"][0]["declencheurs"])

    def test_une_chaine_malformee_peut_etre_retiree(self):
        """LE PIEGE : mestre-hallis.declencheurs[0] est une CHAINE."""
        t = tables_avec([ANCIEN])
        plan, erreurs = valider([mut("declencheur_retirer", ANCIEN)], t)
        self.assertEqual([], erreurs)
        appliquer(plan, t)
        self.assertEqual([], t["intentions"][0]["declencheurs"])

    def test_une_chaine_malformee_bloque_le_meme_si(self):
        """Elle vaut collision : sinon on remplace un dechet par un doublon."""
        t = tables_avec([ANCIEN])
        _plan, erreurs = valider(
            [mut("declencheur_ajouter", {"si": ANCIEN, "alors": "x"})], t)
        self.assertEqual(1, len(erreurs))

    def test_croyance_ajoutee_puis_retiree_dans_le_lot(self):
        """La symetrique, du meme bois : l'ajout precede se voit."""
        t = tables_avec([], croyances=[])
        plan, erreurs = valider([mut("croyance_ajouter", "le pli est parti"),
                                 mut("croyance_retirer", "le pli est parti")], t)
        self.assertEqual([], erreurs)
        appliquer(plan, t)
        self.assertEqual([], t["intentions"][0]["croyances"])

    def test_retirer_deux_fois_la_meme_croyance_est_refuse(self):
        t = tables_avec([], croyances=["le pli est parti"])
        _plan, erreurs = valider([mut("croyance_retirer", "le pli est parti"),
                                  mut("croyance_retirer", "le pli est parti")], t)
        self.assertEqual(1, len(erreurs))


if __name__ == "__main__":
    unittest.main()
