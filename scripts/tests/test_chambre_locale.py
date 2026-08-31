# -*- coding: utf-8 -*-
"""Le brief donne a l'homme les chemins et les pas ouverts de son bureau."""
import io
import importlib.util
import json
import os
import sys
import tempfile
import unittest

_d = os.path.dirname(os.path.abspath(__file__))
while os.path.basename(_d) != "scripts" and os.path.dirname(_d) != _d:
    _d = os.path.dirname(_d)
for _p in (_d, os.path.join(_d, "noyau")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_module = os.path.join(_d, "agents", "depeche", "chambre_locale.py")
_spec = importlib.util.spec_from_file_location("chambre_locale_banc", _module)
chambre_locale = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(chambre_locale)


class BancChambreLocale(unittest.TestCase):

    def _ecrire(self, chemin, contenu):
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        with io.open(chemin, "w", encoding="utf-8") as f:
            if isinstance(contenu, dict):
                json.dump(contenu, f, ensure_ascii=False)
            else:
                f.write(contenu)

    def test_liste_tous_les_fichiers_et_seulement_les_actions_ouvertes(self):
        with tempfile.TemporaryDirectory(prefix="banc-chambre-brief-") as chambre:
            cahier = os.path.join(chambre, "claude.md")
            relation = os.path.join(chambre, "relations", "gerardys", "claude.md")
            affaire = os.path.join(chambre, "books", "affaire-test.json")
            casse = os.path.join(chambre, "books", "casse.json")
            self._ecrire(cahier, u"# Ma manière")
            self._ecrire(relation, u"# Gerardys")
            self._ecrire(casse, u"{ ceci n'est pas du json")
            self._ecrire(affaire, {
                "id": "affaire-test",
                "titre": "Le port",
                "type": "affaire",
                "tables": [{
                    "titre": "⚔️ Actions",
                    "colonnes": ["⚔️ N°", "🏷️ L'action", "⏳ État"],
                    "lignes": [
                        {"cellules": ["A.1", "Compter les nefs", "à faire"]},
                        {"cellules": ["A.2", "Armer la jetée", "en cours"]},
                        {"cellules": ["A.3", "Attendre le bois", "bloquée"]},
                        {"cellules": ["A.4", "Fermer le compte", "faite"]},
                        {"cellules": ["A.5", "Lever l'ancien plan", "abandonnée"]},
                    ],
                }],
            })

            texte = chambre_locale.rendre(chambre)

            for fichier in (cahier, relation, affaire, casse):
                self.assertIn(os.path.abspath(fichier).replace("\\", "/"), texte)
            for attendu in (u"`A.1` — Compter les nefs",
                             u"`A.2` — Armer la jetée",
                             u"`A.3` — Attendre le bois"):
                self.assertIn(attendu, texte)
            self.assertNotIn(u"A.4", texte)
            self.assertNotIn(u"A.5", texte)

    def test_reconnait_les_colonnes_reordonnees(self):
        with tempfile.TemporaryDirectory(prefix="banc-chambre-brief-") as chambre:
            affaire = os.path.join(chambre, "books", "chantier.json")
            self._ecrire(affaire, {
                "titre": "Chantier",
                "tables": [{
                    "titre": "Actions du jour",
                    "colonnes": ["Statut", "Nom", "Référence"],
                    "lignes": [
                        {"cellules": ["en cours", "Tailler les pierres", "C.7"]},
                        {"cellules": ["terminée", "Tracer le mur", "C.6"]},
                    ],
                }],
            })

            affaires = chambre_locale.affaires_de(chambre)

            self.assertEqual(len(affaires), 1)
            self.assertEqual(affaires[0]["actions"], [
                {"ref": "C.7", "nom": "Tailler les pierres"},
            ])


if __name__ == "__main__":
    unittest.main()
