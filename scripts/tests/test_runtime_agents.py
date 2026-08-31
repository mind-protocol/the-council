# -*- coding: utf-8 -*-
import json
import os
import tempfile
import unittest
from unittest import mock
import sys

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents import runtime, trace


class RuntimeAgentsTest(unittest.TestCase):
    def test_switch_global_et_alias_chatgpt(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(runtime, "DOSSIER_RUNTIME", d), \
                mock.patch.object(runtime, "CONFIG", os.path.join(d, "config.json")), \
                mock.patch.dict(os.environ, {
                    "LE_CONSEIL_FOURNISSEUR": "",
                    "LE_CONSEIL_AGENT_PROVIDER": "",
                }, clear=False):
            cfg = runtime.choisir("chatgpt", "gpt-5.3-codex-spark", "low")
            self.assertEqual("codex", cfg["fournisseur"])
            self.assertEqual("gpt-5.3-codex-spark", cfg["modele_codex"])
            self.assertEqual("codex", runtime.fournisseur())

    def test_commande_codex_neuve_et_reprise(self):
        neuve = runtime._commande_codex(
            "C:\\neutre", "gpt-5.3-codex-spark", "low",
            ["C:\\chambre"], "C:\\fin.txt")
        self.assertEqual(["codex", "exec"], neuve[:2])
        self.assertIn("--ignore-user-config", neuve)
        self.assertIn("workspace-write", neuve)
        self.assertNotIn("resume", neuve)
        self.assertEqual("-", neuve[-1])

        reprise = runtime._commande_codex(
            "C:\\neutre", "gpt-5.3-codex-spark", "low", [],
            "C:\\fin.txt", "thread-123")
        self.assertEqual(["resume", "thread-123", "-"], reprise[-3:])

        lecture = runtime._commande_codex(
            "C:\\neutre", "gpt-5.3-codex-spark", "low", [],
            "C:\\fin.txt", ecriture=False)
        self.assertEqual("read-only", lecture[lecture.index("--sandbox") + 1])

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
