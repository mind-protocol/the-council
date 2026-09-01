import json
import tempfile
import unittest
from pathlib import Path

from registre_engagements import VERSION, ajouter, consulter, verifier


def document(type_: str = "proposition") -> dict:
    return {
        "version": VERSION,
        "type": type_,
        "engagement_id": "essai-1",
        "date": "129.5.12",
        "parties": ["Giovanni", "Nicolas"],
        "objet": "Eprouver le registre",
        "risque": "Prendre le sceau pour un jugement moral",
        "effet_civique": "Rendre la revision visible",
        "equilibre": "Chacun peut refuser",
    }


class RegistreEngagementsTest(unittest.TestCase):
    def test_revision_enchainee_et_falsification_detectee(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "registre.jsonl"
            proposition = ajouter(chemin, document())
            revision = document("revision")
            revision["revision_de"] = proposition["sceau"]
            revision["raison_revision"] = "Clarifier la portee"
            ajouter(chemin, revision)

            documents, erreurs = verifier(chemin)
            self.assertEqual(2, len(documents))
            self.assertEqual([], erreurs)

            lignes = chemin.read_text(encoding="utf-8").splitlines()
            falsifie = json.loads(lignes[0])
            falsifie["objet"] = "Objet change en silence"
            lignes[0] = json.dumps(falsifie, ensure_ascii=False, sort_keys=True)
            chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")
            _, erreurs = verifier(chemin)
            self.assertTrue(any("sceau invalide" in erreur for erreur in erreurs))

    def test_proposition_dupliquee_refusee_et_qualifiee(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "registre.jsonl"
            ajouter(chemin, document())
            with self.assertRaisesRegex(ValueError, "DOUBLON_EXACT"):
                ajouter(chemin, document())

    def test_alteration_refusee_sans_divulguer_les_valeurs(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "registre.jsonl"
            ajouter(chemin, document())
            altere = document()
            altere["equilibre"] = "Valeur sensible qui ne doit pas ressortir"
            with self.assertRaises(ValueError) as refus:
                ajouter(chemin, altere)
            diagnostic = str(refus.exception)
            self.assertIn("ALTERATION champs=equilibre", diagnostic)
            self.assertIn("empreinte_existante=", diagnostic)
            self.assertIn("empreinte_soumise=", diagnostic)
            self.assertNotIn(altere["equilibre"], diagnostic)

    def test_clause_manquante_refusee(self):
        with tempfile.TemporaryDirectory() as dossier:
            incomplet = document()
            incomplet["risque"] = ""
            with self.assertRaisesRegex(ValueError, "risque obligatoire"):
                ajouter(Path(dossier) / "registre.jsonl", incomplet)

    def test_consulter_rend_les_termes_publics_sans_ecrire(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "registre.jsonl"
            ajouter(chemin, document())
            avant = chemin.read_bytes()
            lecture = consulter(chemin)
            apres = chemin.read_bytes()
            self.assertEqual(avant, apres)
            self.assertIn("essai-1 — proposition", lecture)
            self.assertIn("Parties : Giovanni, Nicolas", lecture)
            self.assertIn("Objet : Eprouver le registre", lecture)
            self.assertIn("Aucun jugement", lecture)

    def test_consulter_refuse_de_blanchir_une_chaine_invalide(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "registre.jsonl"
            ajouter(chemin, document())
            lignes = chemin.read_text(encoding="utf-8").replace(
                "Eprouver le registre", "Objet falsifie"
            )
            chemin.write_text(lignes, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "registre invalide"):
                consulter(chemin)


if __name__ == "__main__":
    unittest.main()
