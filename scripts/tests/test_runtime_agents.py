# -*- coding: utf-8 -*-
import json
import os
import tempfile
import unittest
from unittest import mock
import sys
import contextlib

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents import runtime, trace


class RuntimeAgentsTest(unittest.TestCase):
    def test_deux_reveils_ne_passent_pas_par_un_verrou_de_session(self):
        resultat = {"result": "fait", "provider": "codex"}
        with tempfile.TemporaryDirectory() as dossier, \
                mock.patch.object(runtime, "fournisseur", return_value="codex"), \
                mock.patch.object(runtime, "_modele", return_value="modele"), \
                mock.patch.object(runtime, "_effort", return_value="low"), \
                mock.patch.object(runtime, "_appel_codex",
                                  return_value=resultat), \
                mock.patch.object(runtime, "_activite",
                                  return_value=contextlib.nullcontext()):
            rep = runtime.appeler(
                role="mj", manuel="manuel", message="mot",
                session_id="session-partagee", cwd=dossier)

        self.assertEqual(resultat, rep)
        self.assertFalse(hasattr(runtime, "_verrou"))

    def test_runtime_propage_une_identite_explicite_jusqu_au_compute(self):
        resultat = {"result": "fait", "provider": "codex"}
        identity = {
            "work_id": "9ca2832a-bad4-5e71-af6b-326521708d9e",
            "attempt_id": "9ca2832a-bad4-5e71-af6b-326521708d9e:attempt:1",
            "attempt_number": 1,
            "effect_key": "effect:9ca2832a-bad4-5e71-af6b-326521708d9e",
        }
        evenement = dict(identity, id="event-1")
        with tempfile.TemporaryDirectory() as dossier, \
                mock.patch.object(runtime, "fournisseur", return_value="codex"), \
                mock.patch.object(runtime, "_modele", return_value="modele"), \
                mock.patch.object(runtime, "_effort", return_value="low"), \
                mock.patch.object(runtime, "_appel_codex", return_value=resultat), \
                mock.patch.object(runtime, "_activite",
                                  return_value=contextlib.nullcontext()), \
                mock.patch("agents.compute.enregistrer",
                           return_value=evenement) as enregistrer:
            rep = runtime.appeler(
                role="mj", manuel="manuel", message="mot",
                session_id="conversation", cwd=dossier,
                work_identity=identity)
        self.assertEqual(identity, rep["continuous_work_identity"])
        self.assertEqual("event-1", rep["compute_event_id"])
        self.assertEqual(identity,
                         enregistrer.call_args.kwargs["work_identity"])

    def test_voyant_actif_exactement_pendant_le_calcul(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(runtime, "ACTIVITES", os.path.join(d, "active")):
            with runtime._activite("mestre-gerardys", "jour-12"):
                fichiers = os.listdir(runtime.ACTIVITES)
                self.assertEqual(1, len(fichiers))
                with open(os.path.join(runtime.ACTIVITES, fichiers[0]),
                          encoding="utf-8") as f:
                    marqueur = json.load(f)
                self.assertEqual("mestre-gerardys", marqueur["homme"])
                self.assertEqual("jour-12", marqueur["session"])
                self.assertEqual(os.getpid(), marqueur["pid"])
                self.assertEqual(runtime._identite_processus(os.getpid()),
                                 marqueur["processus"])
            self.assertEqual([], os.listdir(runtime.ACTIVITES))

    def test_la_garde_refuse_atomiquement_le_seizieme_slot(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(runtime, "ACTIVITES", os.path.join(d, "active")):
            self.assertEqual(15, runtime.MAX_SESSIONS_ACTIVES)
            slots = [runtime._essayer_reserver(
                "homme-%d" % i, "session-%d" % i, pid=os.getpid())
                for i in range(15)]
            self.assertTrue(all(slots))
            self.assertIsNone(runtime._essayer_reserver(
                "seizieme", "session-16", pid=os.getpid()))
            for chemin in slots:
                runtime._liberer_slot(chemin)

    def test_un_worker_adopte_le_slot_reserve_sans_en_prendre_un_second(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(runtime, "ACTIVITES", os.path.join(d, "active")):
            reserve = runtime._essayer_reserver(
                "gerardys", "jour-12", pid=None)
            with mock.patch.dict(os.environ, {
                    runtime.RESERVATION_ENV: os.path.basename(reserve)}):
                with runtime._activite("gerardys", "jour-12"):
                    fichiers = [p for p in os.listdir(runtime.ACTIVITES)
                                if p.endswith(".json")]
                    self.assertEqual([os.path.basename(reserve)], fichiers)
                    with open(reserve, encoding="utf-8") as f:
                        marqueur = json.load(f)
                    self.assertFalse(marqueur["reserve"])
                    self.assertEqual(os.getpid(), marqueur["pid"])
            self.assertEqual([], [p for p in os.listdir(runtime.ACTIVITES)
                                  if p.endswith(".json")])

    def test_un_pid_recycle_ne_garde_pas_un_faux_slot(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(runtime, "ACTIVITES", os.path.join(d, "active")), \
                mock.patch.object(runtime, "MAX_SESSIONS_ACTIVES", 1):
            os.makedirs(runtime.ACTIVITES)
            faux = os.path.join(runtime.ACTIVITES, "mort.json")
            with open(faux, "w", encoding="utf-8") as f:
                json.dump({"homme": "mort", "session": "s", "pid": os.getpid(),
                           "processus": "autre-naissance", "t": 1}, f)
            slot = runtime._essayer_reserver(
                "vivant", "nouveau", pid=os.getpid())
            self.assertIsNotNone(slot)
            self.assertFalse(os.path.exists(faux))
            runtime._liberer_slot(slot)

    def test_switch_global_et_alias_chatgpt(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(runtime, "DOSSIER_RUNTIME", d), \
                mock.patch.object(runtime, "CONFIG", os.path.join(d, "config.json")), \
                mock.patch.dict(os.environ, {
                    "LE_CONSEIL_FOURNISSEUR": "",
                    "LE_CONSEIL_AGENT_PROVIDER": "",
                }, clear=False):
            cfg = runtime.choisir("chatgpt", "gpt-5.3-codex-spark", "low",
                                  fast=True)
            self.assertEqual("codex", cfg["fournisseur"])
            self.assertEqual("gpt-5.3-codex-spark", cfg["modele_codex"])
            self.assertEqual("low", cfg["effort_codex"])
            self.assertEqual("fast", cfg["service_tier_codex"])
            self.assertEqual("codex", runtime.fournisseur())

    def test_commande_codex_neuve_et_reprise(self):
        neuve = runtime._commande_codex(
            "C:\\neutre", "gpt-5.3-codex-spark", "low",
            ["C:\\chambre"], "C:\\fin.txt")
        self.assertEqual(["codex", "exec"], neuve[:2])
        self.assertIn("--ignore-user-config", neuve)
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", neuve)
        self.assertNotIn("--approve-for-me", neuve)
        self.assertIn("project_doc_max_bytes=524288", neuve)
        rapide = runtime._commande_codex(
            "C:\\neutre", "gpt-5.3-codex-spark", "low", [],
            "C:\\fin.txt", service_tier="fast")
        self.assertIn('service_tier="fast"', rapide)
        self.assertNotIn("--sandbox", neuve)
        self.assertNotIn("read-only", neuve)
        self.assertNotIn("resume", neuve)
        self.assertEqual("-", neuve[-1])

        reprise = runtime._commande_codex(
            "C:\\neutre", "gpt-5.3-codex-spark", "low", [],
            "C:\\fin.txt", "thread-123")
        self.assertEqual(["resume", "thread-123", "-"], reprise[-3:])
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", reprise)
        self.assertNotIn("--approve-for-me", reprise)
        self.assertNotIn("--sandbox", reprise)
        self.assertNotIn("read-only", reprise)

    def test_manuel_codex_n_est_injecte_qu_a_la_creation_ou_si_change(self):
        with tempfile.TemporaryDirectory() as dossier:
            manuel = "MANUEL V1"
            empreinte, injecte = runtime._preparer_prompt_codex(
                manuel, dossier, None, {})
            self.assertTrue(injecte)
            self.assertTrue(os.path.exists(os.path.join(dossier, "AGENTS.md")))

            runtime._retirer_prompt_codex(dossier)
            meme, injecte = runtime._preparer_prompt_codex(
                manuel, dossier, "thread-1",
                {"manuel_sha256_codex": empreinte})
            self.assertEqual(empreinte, meme)
            self.assertFalse(injecte)
            self.assertFalse(os.path.exists(os.path.join(dossier, "AGENTS.md")))

            autre, injecte = runtime._preparer_prompt_codex(
                "MANUEL V2", dossier, "thread-1",
                {"manuel_sha256_codex": empreinte})
            self.assertNotEqual(empreinte, autre)
            self.assertTrue(injecte)
            self.assertTrue(os.path.exists(os.path.join(dossier, "AGENTS.md")))

    def test_commande_claude_ne_peut_plus_etre_read_only(self):
        commande = runtime._commande_claude(
            "C:\\systeme.md", None, None, [], [], None,
            "session-juge", False, False)
        outils = commande[commande.index("--tools") + 1].split(",")
        for outil in ("Read", "Grep", "Glob", "Bash", "Write", "Edit"):
            self.assertIn(outil, outils)

    def test_manuel_claude_n_est_injecte_qu_a_la_creation_ou_si_change(self):
        with tempfile.TemporaryDirectory() as dossier:
            manuel = "MANUEL V1"
            empreinte, prompt, injecte = runtime._preparer_prompt_claude(
                manuel, dossier, False, {})
            self.assertTrue(injecte)
            self.assertIsNotNone(prompt)
            self.assertTrue(os.path.exists(prompt))

            runtime._retirer_prompt_claude(dossier)
            meme, prompt, injecte = runtime._preparer_prompt_claude(
                manuel, dossier, True,
                {"manuel_sha256_claude": empreinte})
            self.assertEqual(empreinte, meme)
            self.assertFalse(injecte)
            self.assertIsNone(prompt)

            autre, prompt, injecte = runtime._preparer_prompt_claude(
                "MANUEL V2", dossier, True,
                {"manuel_sha256_claude": empreinte})
            self.assertNotEqual(empreinte, autre)
            self.assertTrue(injecte)
            self.assertTrue(os.path.exists(prompt))

    def test_reprise_claude_sans_changement_omet_le_prompt_systeme(self):
        commande = runtime._commande_claude(
            None, None, None, [], [], None,
            "session-homme", True, False)
        self.assertNotIn("--system-prompt-file", commande)

    def test_commande_claude_homme_n_est_pas_restreinte(self):
        commande = runtime._commande_claude(
            "C:\\systeme.md", None, None, ["C:\\depot"], [], None,
            "session-homme", False, False)
        self.assertIn("--dangerously-skip-permissions", commande)
        self.assertNotIn("--restricted", commande)
        self.assertNotIn("--permission-mode", commande)

    def test_normalise_le_jsonl_codex_dans_le_contrat_historique(self):
        rep = runtime._normaliser_codex([
            {"type": "thread.started", "thread_id": "t-1"},
            {"type": "item.completed", "item": {
                "type": "command_execution", "command": "python porte.py"}},
            {"type": "item.completed", "item": {
                "type": "agent_message", "text": "le verdict"}},
            {"type": "turn.completed", "usage": {
                "input_tokens": 12, "cached_input_tokens": 8,
                "output_tokens": 3}},
        ], "gpt-5.3-codex-spark", 1.25, "logique", "trace.jsonl")
        self.assertEqual("le verdict", rep["result"])
        self.assertEqual("t-1", rep["session_id"])
        self.assertEqual("logique", rep["logical_session_id"])
        self.assertEqual(12, rep["usage"]["input_tokens"])
        self.assertIn("python porte.py", rep["gestes"][0])

    def test_trace_codex_devient_un_vecu(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = os.path.join(d, "codex.jsonl")
            with open(chemin, "w", encoding="utf-8") as f:
                for ev in (
                    {"type": "le_conseil.user", "message": "Debout."},
                    {"type": "item.completed", "item": {
                        "type": "command_execution", "command": "python agir.py"}},
                    {"type": "item.completed", "item": {
                        "type": "agent_message", "text": "J'ai agi."}},
                ):
                    f.write(json.dumps(ev, ensure_ascii=False) + "\n")
            self.assertEqual([
                ("reveil", "Debout."),
                ("geste", "command_execution python agir.py"),
                ("parole", "J'ai agi."),
            ], trace.depouiller_fil(chemin))


if __name__ == "__main__":
    unittest.main()
