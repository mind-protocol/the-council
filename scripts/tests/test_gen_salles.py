# -*- coding: utf-8 -*-
"""Le contrat de `scripts/peinture/gen_salles.py`, tel que sa docstring l'ecrit :
« Sortie : ecrans/salles/<id de la salle>.jpg, ou l'id est celui de plans.js.
Deposer le fichier SUFFIT. » Deux invariants en decoulent, et rien ne les tenait.

On LIT les fichiers au lieu d'importer le module : `gen_salles` tire `requests`
et `PIL`, et l'import couterait ces dependances a la suite de tests. Ces
fichiers-ci sont des SOURCES, pas de l'etat : les lire ne rend pas le test
fragile au fil de la partie (scripts/tests/CLAUDE.md interdit de lire `etat/`,
pas le code).
"""
import io
import os
import re
import unittest

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(RACINE, "scripts", "peinture", "gen_salles.py")
PLANS = os.path.join(RACINE, "ecrans", "modules", "plans.js")
SORTIE = os.path.join(RACINE, "ecrans", "salles")
VUE = os.path.join(RACINE, "ecrans", "modules", "vue-salle.js")


def lire(p):
    return io.open(p, encoding="utf-8").read()


def cles_salles():
    """Les ids peints, tels que le dictionnaire SALLES les ecrit."""
    return set(re.findall(r'^    "([a-z0-9\-]+)": \(', lire(GEN), re.M))


def ids_du_plan():
    return set(re.findall(r'\bid:\s*"([a-z0-9\-]+)"', lire(PLANS)))


def variantes():
    """Les salles dont vue-salle.js sert un fichier qui n'est pas <id>.jpg."""
    bloc = re.search(r"const VARIANTES = \{([^}]*)\}", lire(VUE))
    return dict(re.findall(r'(\w[\w\-]*)\s*:\s*"([^"]+)"', bloc.group(1))) if bloc else {}


class TestContratGenSalles(unittest.TestCase):
    def test_toute_cle_peinte_est_une_salle_du_plan(self):
        """Peindre un id absent de plans.js produit une toile que rien n'affichera."""
        orphelines = sorted(cles_salles() - ids_du_plan())
        self.assertEqual(orphelines, [], "peintes mais absentes de plans.js : %s" % orphelines)

    def test_toute_cle_peinte_a_son_fichier(self):
        """L'inverse : une entree du dictionnaire sans toile au depot est du travail
        annonce et pas fait. La variante compte comme la toile de sa salle."""
        var = variantes()
        presents = set(os.listdir(SORTIE)) if os.path.isdir(SORTIE) else set()
        manquantes = sorted(k for k in cles_salles()
                            if (var[k] if k in var else k + ".jpg") not in presents)
        self.assertEqual(manquantes, [], "entrees sans toile : %s" % manquantes)

    def test_une_variante_designe_une_salle_peinte(self):
        """Une variante qui ne correspond a aucune salle du plan masque une toile
        qui n'existe pas : le decor sert alors un 404 en silence."""
        inconnues = sorted(set(variantes()) - ids_du_plan())
        self.assertEqual(inconnues, [], "variantes hors plan : %s" % inconnues)


if __name__ == "__main__":
    unittest.main()
