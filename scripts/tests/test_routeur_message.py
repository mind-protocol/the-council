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

from agents import expose  # noqa: F401 — lie la porte avant les cycles de depeche
from agents import mj, parloir, portage, routeur_message as routeur


class RouteurMessageTests(unittest.TestCase):
    def _document(self):
        return {
            "joueur_id": "rhaenyra", "ref": "r-parole",
            "selection": {
                "decision": "selection",
                "pointeurs": ["affaire-port#23030"],
                "joueurs_concernes": ["rhaenyra"],
                "hommes": ["gerardys"],
                "routes_hommes": [{"homme": "gerardys",
                                    "pointeur": "affaire-port#23030",
                                    "contexte_id": "23030"}],
            },
        }

    def test_parler_va_a_l_homme_par_id_puis_au_mj_sur_la_ref(self):
        document = self._document()
        action = {"ref": "r-parole", "type": "libre", "mode": "dire",
                  "texte": "Gerardys, dites-moi le chiffre."}
        retour_homme = {"homme": "gerardys", "pointeur": "affaire-port#23030",
                        "contexte_id": "23030", "servi": True}
        with mock.patch.object(routeur, "_servir_route",
                               return_value=retour_homme) as servir, \
                mock.patch.object(mj, "appeler_mj",
                                  return_value="fait") as appeler_mj:
            resultat = routeur.router_message(document, action)

        servir.assert_called_once()
        args = appeler_mj.call_args
        self.assertEqual(["r-parole"], args.kwargs["refs"])
        self.assertTrue(args.kwargs["routage"]["routes_hommes"][0]["servi"])
        self.assertTrue(resultat["parole"])

    def test_un_geste_ne_part_pas_directement_aux_hommes(self):
        action = {"ref": "r-geste", "type": "libre", "mode": "agir",
                  "texte": "Elle retourne la piece."}
        with mock.patch.object(routeur, "_servir_route") as servir, \
                mock.patch.object(mj, "appeler_mj", return_value="fait"):
            resultat = routeur.router_message(self._document(), action)
        servir.assert_not_called()
        self.assertFalse(resultat["parole"])
        self.assertEqual([], resultat["hommes"])

    def test_jump_ne_depeche_pas_avant_le_choix_du_mj(self):
        document = {
            "joueur_id": "rhaenyra", "ref": "r-jump",
            "selection": {"decision": "jump", "routes_hommes": []},
            "contexte_fourni": {"jump": {
                "version": "jump/1", "event": {"id": "prochain"},
                "contexte_id": "84502"}},
        }
        action = {"ref": "r-jump", "type": "libre", "mode": "jump",
                  "texte": ""}
        with mock.patch.object(routeur, "_servir_route") as servir, \
                mock.patch.object(mj, "appeler_mj",
                                  return_value="scène jouée") as appeler:
            resultat = routeur.router_message(document, action)
        servir.assert_not_called()
        routage = appeler.call_args.kwargs["routage"]
        self.assertEqual("jump", routage["decision"])
        self.assertEqual("prochain", routage["jump"]["event"]["id"])
        self.assertIn("skill système jump-scene", routage["consigne"])
        self.assertIn("meuble le flux", routage["consigne"])
        self.assertIn("avance réellement la clock", routage["consigne"])
        self.assertIn("ne rends pas la main", routage["consigne"])
        self.assertTrue(resultat["jump"])

    def test_la_depeche_recoit_le_numero_brut_et_les_mots_exacts(self):
        route = self._document()["selection"]["routes_hommes"][0]
        with mock.patch.object(routeur, "depecher", return_value=True) as depecher:
            resultat = routeur._servir_route(
                "rhaenyra", "Le chiffre, maintenant.", route,
                ref="r-parole")
        args = depecher.call_args
        self.assertEqual("gerardys", args.args[0])
        self.assertIn("Le chiffre, maintenant.", args.args[1])
        self.assertIn(
            "scripts/parloir.py --dire --de gerardys --a rhaenyra "
            "--contexte 23030 --ref r-parole", args.args[1])
        self.assertEqual("23030", args.kwargs["contexte_id"])
        self.assertEqual("r-parole", args.kwargs["ref"])
        self.assertEqual("discussion", args.kwargs["mode"])
        self.assertTrue(resultat["servi"])

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
