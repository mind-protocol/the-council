# -*- coding: utf-8 -*-
import os
import sys
import unittest

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import plan_modele as M  # noqa: E402


def table(titre, lignes=1):
    return {"titre": titre, "colonnes": ["N°", "Nom"],
            "lignes": [{"cellules": ["1000", "Une chose"]}] if lignes else []}


def affaire(ident, **changements):
    b = {"id": ident, "type": "plan", "boite": "boite-maison",
         "titre": ident,
         "tables": [table("Ouverture de l'affaire"), table("États cibles")]}
    b.update(changements)
    return b


class PlanModeleTest(unittest.TestCase):
    def test_une_ligne_morte_ne_redevient_pas_une_adresse(self):
        self.assertIsNone(M.C.numero_de("— LIGNE MORTE (doublon de 22050)"))
        self.assertEqual("22050", M.C.numero_de("**22050** — le verrou").group(1))

    def test_une_affaire_complete_est_active(self):
        m = M.construire_depuis_livres([affaire("affaire-a")], "alice")
        self.assertEqual(["affaire-a"], [b["id"] for b in m["affaires"]])
        self.assertEqual([], m["brouillons"])

    def test_un_plan_sans_ouverture_est_un_brouillon(self):
        b = affaire("affaire-b", tables=[table("États cibles")])
        m = M.construire_depuis_livres([b], "alice")
        self.assertEqual([], m["affaires"])
        self.assertIn("sans ouverture", m["brouillons"][0]["raisons"])

    def test_un_plan_sans_place_ne_devient_pas_global(self):
        b = affaire("chantier-technique", boite=None)
        m = M.construire_depuis_livres([b], "alice")
        self.assertEqual([], m["affaires"])
        self.assertIn("sans place", m["brouillons"][0]["raisons"])

    def test_deux_etageres_donnent_deux_plans(self):
        a, b = affaire("affaire-a"), affaire("affaire-b")
        ma = M.construire_depuis_livres([a], "alice")
        mb = M.construire_depuis_livres([b], "bob")
        self.assertEqual(["affaire-a"], [x["id"] for x in ma["affaires"]])
        self.assertEqual(["affaire-b"], [x["id"] for x in mb["affaires"]])

    def test_une_preuve_canonique_exige_le_mot_action(self):
        pieces = {"22042": {"genre": "action", "etat": "faite"},
                  "22043": {"genre": "action", "etat": "faite"}}
        actes = [{"id": "acte-a", "quoi": "L'action 22042 est accomplie."},
                 {"id": "acte-b", "quoi": "22043 hommes sont partis."}]
        M.lier_preuves(pieces, actes=actes, evenements=[])
        self.assertEqual("acte-a", pieces["22042"]["preuves_canoniques"][0]["id"])
        self.assertEqual([], pieces["22043"]["preuves_canoniques"])

    def test_mesures_separent_declaration_et_preuve(self):
        modele = {"affaires": [{}], "brouillons": [], "collisions": [],
                  "pieces_hors_affaire": [], "pieces": {
                      "1": {"genre": "action", "etat": "faite", "preuve": "un sceau",
                            "preuves_canoniques": [{"id": "acte-a"}]},
                      "2": {"genre": "action", "etat": "à faire", "preuve": "un reçu",
                            "preuves_canoniques": []}}}
        m = M.mesures(modele)
        self.assertEqual(1, m["declaration"]["fait"])
        self.assertEqual(1, m["preuves"]["preuve_rattachee_a_un_registre_canonique"])


if __name__ == "__main__":
    unittest.main()
