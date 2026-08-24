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

    def test_deux_sessions_peuvent_ecrire_deux_volumes_distincts(self):
        with tempfile.TemporaryDirectory() as etat:
            ecrire_json(os.path.join(etat, "books", "_ordre.json"), ["a", "b"])
            ecrire_json(os.path.join(etat, "books", "a.json"), {"id": "a", "n": 0})
            ecrire_json(os.path.join(etat, "books", "b.json"), {"id": "b", "n": 0})
            une, deux = B.ouvrir(etat), B.ouvrir(etat)
            une.livres[0]["n"] = 1
            deux.livres[1]["n"] = 2
            une.sauver()
            deux.sauver()
            self.assertEqual([1, 2], [x["n"] for x in B.charger(etat)])

    def test_deux_sessions_ne_recouvrent_pas_le_meme_volume(self):
        with tempfile.TemporaryDirectory() as etat:
            ecrire_json(os.path.join(etat, "books", "_ordre.json"), ["a"])
            ecrire_json(os.path.join(etat, "books", "a.json"), {"id": "a", "n": 0})
            une, deux = B.ouvrir(etat), B.ouvrir(etat)
            une.livres[0]["n"] = 1
            deux.livres[0]["n"] = 2
            une.sauver()
            with self.assertRaisesRegex(B.BibliothequeModifiee, "volume modifié"):
                deux.sauver()
            self.assertEqual(1, B.charger(etat)[0]["n"])

    def test_le_monolithe_refuse_toute_ecriture_concurrente(self):
        with tempfile.TemporaryDirectory() as etat:
            ecrire_json(os.path.join(etat, "books.json"), [{"id": "a", "n": 0}])
            une, deux = B.ouvrir(etat), B.ouvrir(etat)
            une.livres[0]["n"] = 1
            deux.livres[0]["n"] = 2
            une.sauver()
            with self.assertRaisesRegex(B.BibliothequeModifiee, "a changé"):
                deux.sauver()


if __name__ == "__main__":
    unittest.main()
