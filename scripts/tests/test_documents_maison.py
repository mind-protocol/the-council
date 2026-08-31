# -*- coding: utf-8 -*-
import json
import os
import sys
import tempfile
import unittest


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOYAU = os.path.join(SCRIPTS, "noyau")
for chemin in (SCRIPTS, NOYAU):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

import documents_maison


def ecrire(chemin, valeur):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(valeur, f, ensure_ascii=False)


class DocumentsMaisonTests(unittest.TestCase):
    def test_un_membre_recoit_tous_les_documents_de_sa_maison_seulement(self):
        with tempfile.TemporaryDirectory() as etat:
            ecrire(os.path.join(etat, "maisons.json"),
                   [{"id": "maison-a"}, {"id": "maison-b"}])
            ecrire(os.path.join(etat, "personnages.json"), [
                {"id": "alice", "maison_id": "maison-a"},
                {"id": "sans", "maison_id": None},
            ])
            for mid in ("maison-a", "maison-b"):
                base = documents_maison.dossier_livres(etat, mid)
                ecrire(os.path.join(base, "_ordre.json"), ["livre-" + mid[-1]])
                ecrire(os.path.join(base, "livre-" + mid[-1] + ".json"),
                       {"id": "livre-" + mid[-1], "maison_id": mid})
                ecrire(os.path.join(documents_maison.dossier(etat, mid), "mains.json"),
                       {"maison_id": mid, "mains": []})

            maison, chemins = documents_maison.documents_pour(etat, "alice")
            self.assertEqual("maison-a", maison)
            self.assertEqual({"mains.json", "livre-a.json"},
                             {os.path.basename(p) for p in chemins})
            self.assertEqual((None, []),
                             documents_maison.documents_pour(etat, "sans"))

    def test_un_porteur_sans_lignage_rejoint_la_maison_de_son_document(self):
        with tempfile.TemporaryDirectory() as etat:
            ecrire(os.path.join(etat, "maisons.json"), [{"id": "maison-a"}])
            ecrire(os.path.join(etat, "personnages.json"),
                   [{"id": "clerc", "maison_id": None}])
            base = documents_maison.dossier_livres(etat, "maison-a")
            ecrire(os.path.join(base, "_ordre.json"), ["compte"])
            ecrire(os.path.join(base, "compte.json"),
                   {"id": "compte", "maison_id": "maison-a",
                    "acteur_id": "clerc"})
            ecrire(os.path.join(documents_maison.dossier(etat, "maison-a"),
                                "mains.json"),
                   {"maison_id": "maison-a", "mains": []})
            self.assertEqual("maison-a",
                             documents_maison.maison_de(etat, "clerc"))

    def test_l_agregat_refuse_deux_mains_du_meme_id(self):
        with tempfile.TemporaryDirectory() as etat:
            ecrire(os.path.join(etat, "maisons.json"),
                   [{"id": "maison-a"}, {"id": "maison-b"}])
            for mid in ("maison-a", "maison-b"):
                ecrire(os.path.join(documents_maison.dossier(etat, mid), "mains.json"),
                       {"maison_id": mid, "mains": [{"id": "meme"}]})
            with self.assertRaisesRegex(
                    documents_maison.DocumentsMaisonInvalides, "main en double"):
                documents_maison.charger_mains(etat)


if __name__ == "__main__":
    unittest.main()
