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

from agents import expose  # noqa: F401 — lie la porte avant les dépendances tardives
from agents import billet, jump, mj, parloir, portage, routeur_message as routeur


class RouteurMessageTests(unittest.TestCase):
    def test_la_piece_route_directement_vers_les_habitants_presents(self):
        positions = {
            "nlr": {"salle": "archives", "etat": "arrete"},
            "filippo": {"salle": "archives", "etat": "arrete"},
            "autre-joueur": {"salle": "archives", "etat": "arrete"},
            "marcheur": {"salle": "archives", "etat": "en-chemin"},
            "ailleurs": {"salle": "quai", "etat": "arrete"},
        }
        with mock.patch("agents.routeur_message.chambre.existe",
                        return_value=True):
            presents = routeur.gens_presents(
                "nlr", positions=positions,
                joueurs={"nlr", "autre-joueur"})
        self.assertEqual(["filippo"], presents)

    def test_une_parole_reveille_tous_les_presents_sans_mj(self):
        action = {"ref": "r-parole", "type": "libre", "mode": "dire",
                  "texte": "Vous êtes là ?"}
        with mock.patch.object(routeur, "gens_presents",
                               return_value=["filippo", "lucia"]), \
                mock.patch.object(billet, "ecrire",
                                  return_value=("canal.json", {"cast": True})) as ecrire, \
                mock.patch.object(mj, "appeler_mj") as appeler_mj:
            resultat = routeur._router_parole("nlr", "r-parole", action)
        self.assertEqual(2, ecrire.call_count)
        ecrire.assert_any_call("nlr", "filippo", "Vous êtes là ?",
                               modele=None, ref="r-parole")
        ecrire.assert_any_call("nlr", "lucia", "Vous êtes là ?",
                               modele=None, ref="r-parole")
        appeler_mj.assert_not_called()
        self.assertEqual(["filippo", "lucia"], resultat["presents"])

    def test_une_parole_servie_sort_de_l_inbox_et_laisse_un_recu(self):
        with tempfile.TemporaryDirectory() as dossier:
            inbox = os.path.join(dossier, "action.json")
            with open(inbox, "w", encoding="utf-8") as flux:
                json.dump({"ref": "r1", "mode": "dire", "texte": "Bonjour"}, flux)
            with mock.patch.object(routeur, "action_par_ref",
                                   return_value=(inbox, {"ref": "r1", "mode": "dire",
                                                        "texte": "Bonjour"})), \
                    mock.patch.object(routeur, "SORTIES", dossier), \
                    mock.patch.object(routeur, "_router_parole", return_value={
                        "mode": "parole", "presents": ["filippo"],
                        "hommes": [{"homme": "filippo", "servi": True}],
                        "mj": {"appele": False}}):
                document = routeur.router_ref("nlr", "r1")
            self.assertFalse(os.path.exists(inbox))
            self.assertTrue(os.path.exists(os.path.join(dossier, "nlr", "r1.json")))
            self.assertEqual("routage-presence/1", document["version"])

    def test_un_geste_va_directement_au_mj(self):
        action = {"ref": "r-geste", "type": "libre", "mode": "agir",
                  "texte": "Je retourne la pièce."}
        with mock.patch.object(mj, "appeler_mj", return_value="fait") as appeler:
            resultat = routeur._router_mj("rhaenyra", "r-geste", action)
        self.assertEqual(["r-geste"], appeler.call_args.kwargs["refs"])
        self.assertEqual("direct", appeler.call_args.kwargs["routage"]["decision"])
        self.assertTrue(resultat["mj"]["appele"])

    def test_jump_garde_sa_preparation_dediee(self):
        action = {"ref": "r-jump", "type": "libre", "mode": "jump",
                  "texte": ""}
        preparation = {"version": "jump/1", "event": {"id": "prochain"},
                       "contexte_id": "84502"}
        with mock.patch.object(jump, "preparer",
                               return_value=preparation), \
                mock.patch.object(routeur, "_joueurs", return_value={"rhaenyra"}), \
                mock.patch.object(mj, "appeler_mj",
                                  return_value="scène jouée") as appeler:
            resultat = routeur._router_jump("rhaenyra", "r-jump", action)
        routage = appeler.call_args.kwargs["routage"]
        self.assertEqual("jump", routage["decision"])
        self.assertEqual("prochain", routage["jump"]["event"]["id"])
        self.assertIn("skill système jump-scene", routage["consigne"])
        self.assertTrue(resultat["mj"]["appele"])

    def test_un_retour_au_joueur_va_au_web_et_au_flux_mj(self):
        faux_canal = os.path.join("chambres", "canal.json")
        with mock.patch("agents.billet.deposer",
                        return_value=(faux_canal, True)) as deposer, \
                mock.patch.object(parloir, "_pousser_au_flux_web") as web, \
                mock.patch.object(mj, "deposer_retour_parloir",
                                  return_value={"id": "retour-1"}) as flux_mj, \
                mock.patch("agents.chambre.marquer_lu") as marquer:
            canal, retour = parloir.rendre_au_joueur(
                "gerardys", "rhaenyra", "Voici le chiffre.", "23030",
                "r-parole")
        deposer.assert_called_once_with("gerardys", "rhaenyra",
                                        "Voici le chiffre.",
                                        contexte_id="23030", ref="r-parole",
                                        statut=True)
        web.assert_called_once_with("gerardys", "rhaenyra",
                                    "Voici le chiffre.",
                                    contexte_id="23030", ref="r-parole")
        flux_mj.assert_called_once_with(
            "gerardys", "rhaenyra", "Voici le chiffre.",
            contexte_id="23030", ref="r-parole")
        marquer.assert_called_once_with("rhaenyra", "gerardys")
        self.assertEqual(faux_canal, canal)
        self.assertEqual("retour-1", retour["id"])

    def test_un_retour_duplique_ne_repart_ni_au_web_ni_au_mj(self):
        with mock.patch("agents.billet.deposer",
                        return_value=("canal.json", False)), \
                mock.patch.object(parloir, "_pousser_au_flux_web") as web, \
                mock.patch.object(mj, "deposer_retour_parloir") as flux_mj:
            _, retour = parloir.rendre_au_joueur(
                "gerardys", "rhaenyra", "Voici.", "23030", "r-parole")
        self.assertTrue(retour["duplicate"])
        web.assert_not_called()
        flux_mj.assert_not_called()

    def test_flux_mj_append_only_garde_les_arrivees_pendant_un_reveil(self):
        with tempfile.TemporaryDirectory() as dossier, \
                mock.patch.object(mj, "FLUX_RETOURS_PARLOIR",
                                  os.path.join(dossier, "retours.jsonl")), \
                mock.patch.object(mj, "CURSEUR_RETOURS_PARLOIR",
                                  os.path.join(dossier, "retours.lu")):
            mj.deposer_retour_parloir(
                "gerardys", "rhaenyra", "premier", "23030", "r1")
            premiers, position = mj._retours_parloir_non_lus()
            mj.deposer_retour_parloir(
                "gunthor-darklyn", "rhaenyra", "second", "20100", "r2")
            mj._marquer_retours_parloir_lus(position)
            suivants, _ = mj._retours_parloir_non_lus()
        self.assertEqual(["premier"], [x["texte"] for x in premiers])
        self.assertEqual(["r1"], [x["ref"] for x in premiers])
        self.assertEqual(["second"], [x["texte"] for x in suivants])
        self.assertEqual(["r2"], [x["ref"] for x in suivants])

    def test_le_payload_web_conserve_contexte_et_ref(self):
        with mock.patch.object(parloir, "_nom_de", return_value="Gerardys"), \
                mock.patch.object(parloir.subprocess, "run") as lancer:
            parloir._pousser_au_flux_web(
                "gerardys", "rhaenyra", "Voici.", "23030", "r-parole")
        commande = lancer.call_args.args[0]
        item = json.loads(commande[2])
        self.assertEqual("23030", item["contexte_id"])
        self.assertEqual("r-parole", item["ref"])

    def test_le_brief_mj_isole_la_ref_routee(self):
        with tempfile.TemporaryDirectory() as dossier:
            inbox = os.path.join(dossier, "etat", "inbox", "rhaenyra")
            os.makedirs(inbox)
            chemins = []
            for i, ref in enumerate(("r1", "r2")):
                chemin = os.path.join(inbox, "action-%d.json" % i)
                with open(chemin, "w", encoding="utf-8") as f:
                    json.dump({"ref": ref, "mode": "dire",
                               "texte": "texte-%s" % ref}, f)
                chemins.append(chemin)
            with mock.patch.object(portage, "RACINE", dossier), \
                    mock.patch.object(portage, "FLUX",
                                      os.path.join(dossier, "etat", "flux.jsonl")):
                brief = portage.brief_message_joueur("rhaenyra", refs=["r2"])
            self.assertIn("texte-r2", brief)
            self.assertNotIn("texte-r1", brief)
            self.assertEqual([chemins[1]], mj._filtrer_actions_refs(
                chemins, ["r2"]))


if __name__ == "__main__":
    unittest.main()
