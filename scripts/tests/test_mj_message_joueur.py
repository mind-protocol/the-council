# -*- coding: utf-8 -*-
import json
import os
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

# La porte charge les paquets dans leur ordre canonique ; importer mj
# directement court-circuite cet ordre et cree une fausse boucle depeche/expose.
from agents.expose import reveiller_main  # noqa: F401
from agents import mj, portage


class MessageJoueurTests(unittest.TestCase):
    def test_message_joueur_n_est_pas_un_arbitrage(self):
        brief = ("== BRIEF MESSAGE JOUEUR — rhaenyra\n"
                 "ACTION C:\\inbox\\action-1.json · ref abc\n"
                 "FIL CANONIQUE DU PJ : C:\\etat\\flux.jsonl\n"
                 "  L42 · 13h07 · intervention · - | recommencons")
        with mock.patch.object(mj, "date_du_monde",
                               return_value=(129, 4, 4)):
            message = mj._message(
                "rhaenyra", brief, "JOUEUR")

        self.assertIn("[JOUEUR]", message)
        self.assertIn("FIL CANONIQUE DU PJ", message)
        self.assertIn("L42", message)
        self.assertIn("Traite toutes les ACTIONS", message)
        self.assertIn("jamais par billet ou parloir", message)
        self.assertIn("scripts/append_flux.py", message)
        self.assertNotIn("spool", message)
        self.assertNotIn("Tu es l'arbitre", message)

    def test_message_run_demande_du_substantiel_sans_imposer_suites(self):
        with mock.patch.object(mj, "date_du_monde",
                               return_value=(129, 4, 4)):
            message = mj._message(
                "rhaenyra", "je viens d'agir", "JOUEUR", modes=["run"])
        self.assertIn("RUN ACTIF", message)
        self.assertIn("ne sont PAS une reponse", message)
        self.assertIn("n'est jamais requis", message)
        self.assertNotIn("DERNIER item", message)

        with open(mj.MJ_SPECTACLE_MD, encoding="utf-8") as f:
            manuel = f.read()
        self.assertIn("Le garde mécanique porte sur le contenu, jamais sur `suites`",
                      manuel)
        self.assertNotIn("Le dernier item d'un « laisser faire » est un",
                         manuel)

    def test_message_permet_plusieurs_poussees_pendant_le_tour(self):
        with mock.patch.object(mj, "date_du_monde",
                               return_value=(129, 4, 4)):
            message = mj._message(
                "rhaenyra", "je viens d'agir", "JOUEUR")
        self.assertIn("des qu'une tranche est prete", message)
        self.assertIn("de nouveau plus tard dans le meme tour", message)
        self.assertIn("Un refus se corrige avant", message)

    def test_brief_joueur_pointe_inbox_et_lignes_du_fil(self):
        with tempfile.TemporaryDirectory() as dossier:
            inbox = os.path.join(dossier, "etat", "inbox", "rhaenyra")
            os.makedirs(inbox)
            action = os.path.join(inbox, "action-1.json")
            with open(action, "w", encoding="utf-8") as f:
                json.dump({"mode": "question", "ref": "ref-42",
                           "recu_a": "maintenant",
                           "texte": "Le texte exact"}, f)
            flux = os.path.join(dossier, "etat", "flux.jsonl")
            with open(flux, "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps({"type": "recit", "pour": "daemon",
                                    "texte": "cache"}) + "\n")
                for i in range(10):
                    f.write(json.dumps({"type": "recit",
                                        "pour": "rhaenyra",
                                        "ref": ("ref-42" if i == 9 else None),
                                        "texte": ("Le texte exact" if i == 9
                                                  else "item-%d" % i)}) + "\n")
            with mock.patch.object(portage, "RACINE", dossier), \
                    mock.patch.object(portage, "FLUX", flux), \
                    mock.patch.object(portage, "matiere_du_message",
                                      return_value="\nREGISTRE CIBLE\n"):
                brief = portage.brief_message_joueur("rhaenyra")

            self.assertIn(os.path.abspath(action), brief)
            self.assertIn("ref ref-42", brief)
            self.assertIn("TEXTE EXACT : Le texte exact", brief)
            self.assertIn("DANS LE FLUX : L11", brief)
            self.assertIn(os.path.abspath(flux), brief)
            self.assertIn("L4", brief)
            self.assertIn("L11", brief)
            self.assertNotIn("item-0", brief)
            self.assertNotIn("cache", brief)
            self.assertIn("REGISTRE CIBLE", brief)

    def test_message_habitant_reste_un_arbitrage(self):
        with mock.patch.object(mj, "date_du_monde",
                               return_value=(129, 4, 4)):
            message = mj._message("daemon", "mon rapport", "POST")

        self.assertIn("Tu es l'arbitre", message)
        self.assertIn("par billet", message)
        self.assertNotIn("[JOUEUR]", message)

    def test_le_lanceur_constate_les_items_pousses_directement(self):
        with tempfile.TemporaryDirectory() as dossier:
            flux = os.path.join(dossier, "flux.jsonl")
            with open(flux, "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps({"type": "question"}) + "\n")
            with mock.patch.object(mj, "FLUX", flux):
                position = mj._position_flux()
                with open(flux, "a", encoding="utf-8", newline="\n") as f:
                    f.write(json.dumps({"type": "recit"}) + "\n")
                    f.write(json.dumps({"type": "replique"}) + "\n")
                self.assertEqual(["recit", "replique"],
                                 mj._types_flux_depuis(position))

    def test_le_lanceur_reconnait_l_appel_direct_a_la_porte(self):
        self.assertTrue(mj._a_pousse_flux({
            "gestes": ["command_execution python scripts/append_flux.py {...}"]
        }))
        self.assertFalse(mj._a_pousse_flux({"gestes": []}))

    def test_retirer_actions_ne_touche_que_l_instantane(self):
        with tempfile.TemporaryDirectory() as dossier:
            anciens = [os.path.join(dossier, "action-1.json"),
                       os.path.join(dossier, "action-2.json")]
            nouveau = os.path.join(dossier, "action-3.json")
            for chemin in anciens + [nouveau]:
                with open(chemin, "w", encoding="utf-8") as f:
                    f.write("{}")

            mj._retirer_actions(anciens)

            self.assertFalse(any(os.path.exists(p) for p in anciens))
            self.assertTrue(os.path.exists(nouveau))

    def test_un_run_de_rapport_exige_une_replique(self):
        with tempfile.TemporaryDirectory() as dossier:
            action = os.path.join(dossier, "action-1.json")
            with open(action, "w", encoding="utf-8") as f:
                json.dump({"mode": "run",
                           "texte": "obtiens le rapport reel d'Alys"}, f)
            self.assertTrue(mj._actions_exigent_replique([action]))
            self.assertFalse(mj._actions_exigent_replique([]))

    def test_un_parloir_dans_les_gestes_exige_une_replique(self):
        self.assertTrue(mj._a_interroge_un_pnj({
            "gestes": ["command_execution python scripts/parloir.py --dire"]}))
        self.assertFalse(mj._a_interroge_un_pnj({"gestes": []}))

    def test_le_mj_principal_recoit_le_claude_racine_en_premier(self):
        contenus = {
            mj.MANUEL_MJ_RACINE: "CONSTITUTION RACINE",
            mj.MJ_SPECTACLE_MD: "MANUEL SPECTACLE",
        }
        with mock.patch.object(mj, "lire",
                               side_effect=lambda p: contenus.get(p)), \
                mock.patch.object(mj.chambre, "chemin",
                                  return_value="C:\\chambre-mj"):
            manuel = mj._manuel()

        self.assertLess(manuel.index("CONSTITUTION RACINE"),
                        manuel.index("MANUEL SPECTACLE"))


if __name__ == "__main__":
    unittest.main()
