# -*- coding: utf-8 -*-
import json
import os
import tempfile
import unittest

import scripts.bibliotheque as B


def ecrire_json(chemin, valeur):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(valeur, f, ensure_ascii=False)


class BibliothequeTest(unittest.TestCase):
    def test_le_monolithe_reste_le_repli(self):
        with tempfile.TemporaryDirectory() as etat:
            ecrire_json(os.path.join(etat, "books.json"), [{"id": "a"}])
            self.assertEqual([{"id": "a"}], B.charger(etat))
            self.assertFalse(B.est_scindee(etat))

    def test_le_manifeste_active_les_volumes_et_leur_ordre(self):
        with tempfile.TemporaryDirectory() as etat:
            ecrire_json(os.path.join(etat, "books.json"), [{"id": "ancien"}])
            ecrire_json(os.path.join(etat, "books", "_ordre.json"), ["b", "a"])
            ecrire_json(os.path.join(etat, "books", "a.json"), {"id": "a"})
            ecrire_json(os.path.join(etat, "books", "b.json"), {"id": "b"})
            self.assertEqual(["b", "a"], [x["id"] for x in B.charger(etat)])
            self.assertTrue(B.est_scindee(etat))

    def test_un_volume_absent_ne_retombe_pas_sur_le_monolithe(self):
        with tempfile.TemporaryDirectory() as etat:
            ecrire_json(os.path.join(etat, "books.json"), [{"id": "ancien"}])
            ecrire_json(os.path.join(etat, "books", "_ordre.json"), ["absent"])
            with self.assertRaisesRegex(B.BibliothequeInvalide, "volume absent"):
                B.charger(etat)

    def test_le_fichier_doit_dire_son_propre_id(self):
        with tempfile.TemporaryDirectory() as etat:
            ecrire_json(os.path.join(etat, "books", "_ordre.json"), ["a"])
            ecrire_json(os.path.join(etat, "books", "a.json"), {"id": "b"})
            with self.assertRaisesRegex(B.BibliothequeInvalide, "porte l'id"):
                B.charger(etat)


if __name__ == "__main__":
    unittest.main()
