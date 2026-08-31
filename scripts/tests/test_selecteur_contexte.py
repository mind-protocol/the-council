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

from agents.expose import selectionner_contexte_main  # noqa: F401
from agents import portage, selecteur_contexte as selecteur


class SelecteurContexteTests(unittest.TestCase):
    CORPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "donnees", "selecteur_reine_10.json")
    def test_message_joint_exactement_cinq_items_visibles(self):
        with tempfile.TemporaryDirectory() as dossier:
            flux = os.path.join(dossier, "flux.jsonl")
            with open(flux, "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps({"type": "recit", "pour": "daemon",
                                    "texte": "cache"}) + "\n")
                for i in range(7):
                    f.write(json.dumps({"type": "recit", "pour": "rhaenyra",
                                        "texte": "visible-%d" % i}) + "\n")
            action = os.path.join(dossier, "action.json")
            with open(action, "w", encoding="utf-8") as f:
                json.dump({"ref": "r1", "mode": "dire", "texte": "Maintenant"}, f)
            with mock.patch.object(portage, "FLUX", flux):
                message = selecteur.message_enrichi(
                    "rhaenyra", action,
                    {"ref": "r1", "mode": "dire", "texte": "Maintenant"})

        self.assertNotIn("visible-0", message)
        self.assertNotIn("visible-1", message)
        for i in range(2, 7):
            self.assertIn("visible-%d" % i, message)
        self.assertNotIn("cache", message)

    def test_appel_est_une_session_neuve_sans_reprise(self):
        etats = [{"pointeur": "affaire-a#100", "numero": "100",
                  "affaire": "A", "nom": "But", "vers": []}]
        hommes = [{"id": "gerardys", "nom": "Gerardys", "titre": "Mestre"}]
        plan = {"pieces": {}}
        with tempfile.TemporaryDirectory() as dossier, \
                mock.patch.object(selecteur, "SORTIES", dossier), \
                mock.patch.object(selecteur, "action_par_ref",
                                  return_value=(os.path.join(dossier, "action.json"),
                                                {"ref": "r1", "texte": "Le port"})), \
                mock.patch.object(selecteur, "modele_du_plan",
                                  return_value=plan), \
                mock.patch.object(selecteur, "index_du_plan",
                                  return_value=(etats, [])), \
                mock.patch.object(selecteur, "index_des_hommes",
                                  return_value=hommes), \
                mock.patch.object(selecteur, "index_des_joueurs",
                                  return_value=[]), \
                mock.patch.object(selecteur, "joueurs_dans_la_salle",
                                  return_value={"salle": "table", "joueurs": []}), \
                mock.patch.object(selecteur, "texte_recent",
                                  return_value="le port"), \
                mock.patch.object(selecteur, "detecter_pieces",
                                  return_value=[]), \
                mock.patch.object(selecteur, "arbres_des_detectes",
                                  return_value={"items_detectes": [], "arbres": []}), \
                mock.patch.object(selecteur, "message_enrichi",
                                  return_value="message + cinq items"), \
                mock.patch.object(selecteur.runtime, "appeler",
                                  return_value={"result": json.dumps({
                                      "decision": "selection",
                                      "pointeurs": ["affaire-a#100"],
                                      "ancrages": [{
                                          "pointeur": "affaire-a#100",
                                          "citation": "Le port",
                                          "lien": "Le traitement avance le but"}],
                                      "joueurs_concernes": [],
                                      "hommes": ["gerardys"],
                                      "routes_hommes": [{
                                          "homme": "gerardys",
                                          "pointeur": "affaire-a#100"}],
                                      "motif": "le port"}),
                                      "provider": "faux", "model": "faux"}) as appeler, \
                mock.patch("agents.routeur_message.router_message",
                           return_value={"mj": {"appele": True}}) as router:
            document = selecteur.selectionner("rhaenyra", "r1")

        args = appeler.call_args.kwargs
        self.assertFalse(args["reprendre"])
        self.assertEqual("selecteur-contexte", args["role"])
        self.assertEqual("message + cinq items", args["message"])
        self.assertRegex(args["session_id"], r"^[0-9a-f-]{36}$")
        self.assertEqual(["affaire-a#100"],
                         document["selection"]["pointeurs"])
        self.assertEqual(["gerardys"], document["selection"]["hommes"])
        self.assertEqual("100", document["selection"]["routes_hommes"][0]
                         ["contexte_id"])
        router.assert_called_once()
        self.assertIn("contexte_fourni", document)
        self.assertEqual("table", document["contexte_fourni"]["presence"]["salle"])

    def test_les_ids_inventes_sont_rejetes(self):
        with self.assertRaisesRegex(ValueError, "inconnus"):
            selecteur.valider_selection(
                {"decision": "selection",
                 "pointeurs": ["affaire-a#100", "fantome#9"],
                 "hommes": ["gerardys", "invente"], "motif": "x"},
                [{"pointeur": "affaire-a#100"}], [{"id": "gerardys"}])

    def test_liste_les_joueurs_occupes_dans_la_meme_salle(self):
        joueurs = [
            {"personnage_id": "rhaenyra", "nom": "Rhaenyra",
             "role": "principal", "occupe": True},
            {"personnage_id": "aurore", "nom": "Aurore",
             "role": "second", "occupe": True},
            {"personnage_id": "marlo", "nom": "Marlo",
             "role": "second", "occupe": False},
        ]
        presence = {"presence": {
            "rhaenyra": {"salle": "table-peinte", "lieu": "Peyredragon"},
            "aurore": {"salle": "table-peinte", "lieu": "Peyredragon"},
            "marlo": {"salle": "table-peinte", "lieu": "Peyredragon"},
        }}
        resultat = selecteur.joueurs_dans_la_salle(
            "rhaenyra", joueurs=joueurs, presence=presence)
        self.assertEqual("table-peinte", resultat["salle"])
        self.assertEqual(["rhaenyra", "aurore"],
                         [j["id"] for j in resultat["joueurs"]])

    def test_arbre_complet_de_l_item_detecte(self):
        pieces = {
            "100": {"genre": "etat", "nom": "Port tenu", "affaire": "A",
                    "vers": [], "moyens": [], "office": "", "etat": "",
                    "cahier_sources": [{"volume_id": "affaire-a"}]},
            "110": {"genre": "verrou", "nom": "Porte fermee", "affaire": "A",
                    "vers": ["100"], "moyens": [], "office": "", "etat": "",
                    "cahier_sources": [{"volume_id": "affaire-a"}]},
            "120": {"genre": "clef", "nom": "Le guet", "affaire": "A",
                    "vers": ["110"], "moyens": [], "office": "", "etat": "",
                    "cahier_sources": [{"volume_id": "affaire-a"}]},
            "130": {"genre": "action", "nom": "Parler au capitaine", "affaire": "A",
                    "vers": ["120"], "moyens": ["M1"], "office": "O3",
                    "etat": "en cours",
                    "cahier_sources": [{"volume_id": "affaire-a"}]},
        }
        resultat = selecteur.arbres_des_detectes(["130"], {"pieces": pieces})
        self.assertEqual("130", resultat["items_detectes"][0]["numero"])
        action = resultat["arbres"][0]["verrous"][0]["clefs"][0]["actions"][0]
        self.assertEqual("Parler au capitaine", action["nom"])
        self.assertEqual("O3", action["office"])
        self.assertEqual(["M1"], action["moyens"])

    def test_creation_de_contexte_est_une_sortie_valide(self):
        selection = selecteur.valider_selection({
            "decision": "creation", "pointeurs": ["affaire-a#100"],
            "creation": {"titre": "Le mariage", "etat_cible": "Un accord existe",
                         "raison": "aucune affaire ne le porte"},
            "hommes": ["gerardys"], "motif": "nouvelle affaire"},
            [{"pointeur": "affaire-a#100"}], [{"id": "gerardys"}])
        self.assertEqual("creation", selection["decision"])
        self.assertEqual([], selection["pointeurs"])
        self.assertEqual("Le mariage", selection["creation"]["titre"])

    def test_systeme_decrit_le_modele_d_affaire(self):
        manuel = selecteur.manuel_selecteur([], [], [])
        self.assertIn("ACTION -> CLEF -> VERROU -> ETAT CIBLE", manuel)
        self.assertIn('"decision":"creation"', manuel)

    def test_selection_vide_est_interdite(self):
        with self.assertRaisesRegex(ValueError, "au moins un pointeur"):
            selecteur.valider_selection(
                {"decision": "selection", "pointeurs": [], "hommes": []},
                [{"pointeur": "affaire-a#100"}], [])

    def test_message_faible_herite_du_contexte_sans_reprendre_la_session(self):
        precedent = {"ref": "avant", "selection": {
            "decision": "creation", "pointeurs": [], "ancrages": [],
            "creation": {"titre": "Provenance", "etat_cible": "Chaque réponse",
                         "raison": "transversal"},
            "joueurs_concernes": ["rhaenyra", "aurore-inchauspe"],
            "hommes": ["alys-grive"],
            "routes_hommes": []}}
        resultat = selecteur.valider_selection(
            {"decision": "selection", "pointeurs": ["affaire-a#100"],
             "hommes": [], "motif": "choix du modele"},
            [{"pointeur": "affaire-a#100"}], [{"id": "alys-grive"}],
            joueurs=[{"id": "rhaenyra"}, {"id": "aurore-inchauspe"}],
            precedent=precedent, continuation_requise=True)
        self.assertEqual("continuer", resultat["decision"])
        self.assertEqual("Provenance", resultat["creation"]["titre"])
        self.assertEqual("avant", resultat["heritage_ref"])

    def test_un_nom_dans_un_message_faible_force_un_nouveau_routage(self):
        hommes = [{"id": "gerardys", "nom": "Mestre Gerardys"}]
        nommes = selecteur.detecter_personnes(
            "Gerardys, réponds-moi : es-tu là ?", hommes, [])
        self.assertEqual(["gerardys"], nommes["hommes"])
        self.assertFalse(selecteur.doit_continuer(
            "Gerardys, réponds-moi : es-tu là ?",
            {"ref": "avant", "selection": {"pointeurs": ["a#100"]}},
            personnes_nommees=nommes))
        self.assertTrue(selecteur.doit_continuer(
            "Tu es là ?",
            {"ref": "avant", "selection": {"pointeurs": ["a#100"]}},
            personnes_nommees={"joueurs": [], "hommes": []}))

    def test_la_validation_refuse_d_oublier_le_pnj_nomme(self):
        commun = dict(
            etats=[{"pointeur": "affaire-a#100"}],
            hommes=[{"id": "gerardys"}],
            personnes_requises={"joueurs": [], "hommes": ["gerardys"]})
        with self.assertRaisesRegex(ValueError, "interdit.*continuation"):
            selecteur.valider_selection(
                {"decision": "continuer", "pointeurs": [], "hommes": []},
                precedent={"ref": "avant", "selection": {
                    "pointeurs": ["affaire-a#100"]}}, **commun)
        with self.assertRaisesRegex(ValueError, "PNJ nomme absent"):
            selecteur.valider_selection({
                "decision": "selection",
                "pointeurs": ["affaire-a#100"],
                "ancrages": [{"pointeur": "affaire-a#100",
                               "citation": "Gerardys",
                               "lien": "Gerardys porte ce traitement"}],
                "hommes": [], "routes_hommes": []},
                texte_source="Gerardys, es-tu là ?", **commun)

    def test_ancrage_doit_citer_le_message_ou_le_fil(self):
        valeur = {"decision": "selection", "pointeurs": ["affaire-a#100"],
                  "ancrages": [{"pointeur": "affaire-a#100",
                                 "citation": "quai ouvert",
                                 "lien": "Le quai conditionne le but"}],
                  "hommes": [], "joueurs_concernes": []}
        resultat = selecteur.valider_selection(
            valeur, [{"pointeur": "affaire-a#100"}], [],
            texte_source="Ne supposez pas son quai ouvert")
        self.assertEqual("quai ouvert",
                         resultat["ancrages"][0]["citation"])
        valeur["ancrages"][0]["citation"] = "une armée victorieuse"
        with self.assertRaisesRegex(ValueError, "absente"):
            selecteur.valider_selection(
                valeur, [{"pointeur": "affaire-a#100"}], [],
                texte_source="Ne supposez pas son quai ouvert")

    def test_joueurs_et_pnj_sont_deux_listes_disjointes(self):
        personnages = [{"id": "rhaenyra", "nom": "Rhaenyra"},
                       {"id": "gerardys", "nom": "Gerardys"}]
        joueurs = [{"personnage_id": "rhaenyra", "nom": "Rhaenyra"}]
        self.assertEqual(["gerardys"], [h["id"] for h in
                         selecteur.index_des_hommes(personnages, joueurs)])

    def test_incident_multi_sieges_exige_une_creation(self):
        joueurs = [{"id": "rhaenyra", "nom": "Rhaenyra"},
                   {"id": "aurore-inchauspe", "nom": "Aurore"}]
        texte = ("mauvaise sélection de source : la réponse destinée à dame "
                 "Aurore a été poussée dans le flux de Rhaenyra")
        self.assertTrue(selecteur.creation_transversale_requise(texte, joueurs))

    def test_corpus_des_dix_messages_fige_les_regles_deterministes(self):
        with open(self.CORPUS, encoding="utf-8") as f:
            corpus = json.load(f)
        self.assertEqual(10, len(corpus))
        par_ligne = {item["ligne"]: item for item in corpus}
        self.assertTrue(selecteur.message_faible(par_ligne[11311]["texte"]))
        self.assertFalse(selecteur.message_faible(par_ligne[11313]["texte"]))
        self.assertTrue(selecteur.message_faible(par_ligne[11315]["texte"]))
        self.assertTrue(selecteur.message_faible(par_ligne[11318]["texte"]))
        joueurs = [{"id": "rhaenyra", "nom": "Rhaenyra"},
                   {"id": "aurore-inchauspe", "nom": "Aurore"}]
        self.assertTrue(selecteur.creation_transversale_requise(
            par_ligne[11310]["texte"], joueurs))
        hommes = [{"id": "alys-grive", "nom": "Alys Grive"}]
        personnes = selecteur.detecter_personnes(
            par_ligne[11310]["texte"], hommes, joueurs)
        self.assertEqual(["rhaenyra", "aurore-inchauspe"],
                         personnes["joueurs"])
        self.assertEqual(["alys-grive"], personnes["hommes"])

    def test_corpus_met_les_affaires_manuelles_dans_les_candidats(self):
        with open(self.CORPUS, encoding="utf-8") as f:
            par_ligne = {item["ligne"]: item for item in json.load(f)}
        modele = selecteur.modele_du_plan()

        def pointeurs(ligne):
            classement = selecteur.classer_pieces(
                par_ligne[ligne]["texte"], "", modele)
            return [c["pointeur"] for c in
                    selecteur.candidats_etats(classement, modele)]

        opinion = pointeurs(11306)
        self.assertIn("affaire-opinion-populaire-port-real#6000", opinion)
        self.assertIn("affaire-opinion-populaire-port-real#6200", opinion)
        sombreval = pointeurs(11327)
        self.assertEqual("affaire-deplacement-armee#20100", sombreval[0])
        self.assertIn("affaire-jour-dentree#11000", sombreval[:3])


if __name__ == "__main__":
    unittest.main()
