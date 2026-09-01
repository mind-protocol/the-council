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

from agents import runtime_worker


class RuntimeWorkerIdentityTest(unittest.TestCase):
    def test_cast_ecrit_un_terme_seulement_apres_depot_du_vecu(self):
        identity = {
            "work_id": "9ca2832a-bad4-5e71-af6b-326521708d9e",
            "attempt_id": "9ca2832a-bad4-5e71-af6b-326521708d9e:attempt:1",
            "attempt_number": 1,
            "effect_key": "effect:9ca2832a-bad4-5e71-af6b-326521708d9e",
        }
        charge = {
            "fournisseur": "codex",
            "appel": {"session_id": "session", "work_identity": identity},
            "trace": {"qui": "elisabetta", "contexte_id": "52140"},
        }
        with tempfile.TemporaryDirectory() as d:
            requete = os.path.join(d, "request.json")
            with open(requete, "w", encoding="utf-8") as f:
                json.dump(charge, f)
            rep = dict(identity=identity)
            rep = {"continuous_work_identity": identity,
                   "compute_event_id": "event-1", "provider": "codex"}
            with mock.patch.object(sys, "argv", ["runtime_worker", requete]), \
                    mock.patch.object(runtime_worker.runtime, "appeler",
                                      return_value=rep), \
                    mock.patch("agents.trace.deposer",
                               return_value=os.path.join(d, "vecu.md")), \
                    mock.patch.object(runtime_worker.work_identity,
                                      "terminer_attempt") as terminer:
                self.assertEqual(0, runtime_worker.main())
        terminer.assert_called_once_with(
            identity, "event-1", "succeeded", term=True,
            artifact=os.path.join(d, "vecu.md"))


if __name__ == "__main__":
    unittest.main()
