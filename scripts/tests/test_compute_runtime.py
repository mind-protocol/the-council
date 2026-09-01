# -*- coding: utf-8 -*-
import io
import json
import os
import sys
import tempfile
import unittest


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents import compute


class ComputeRuntimeTests(unittest.TestCase):
    def test_transcript_mesure_dequeue_jusqu_a_fin_sans_compter_le_trou(self):
        lignes = [
            {"type": "queue-operation", "operation": "dequeue",
             "timestamp": "2026-08-31T08:00:00Z"},
            {"type": "assistant", "message": {"stop_reason": "end_turn"},
             "timestamp": "2026-08-31T08:10:00Z"},
            {"type": "queue-operation", "operation": "dequeue",
             "timestamp": "2026-08-31T09:00:00Z"},
            {"type": "assistant",
             "message": {"stop_reason": "stop_sequence"},
             "timestamp": "2026-08-31T09:05:00Z"},
        ]
        with tempfile.TemporaryDirectory() as d:
            chemin = os.path.join(d, "session.jsonl")
            with io.open(chemin, "w", encoding="utf-8") as f:
                for ligne in lignes:
                    f.write(json.dumps(ligne) + "\n")
            segments = compute._segments_transcript(chemin, "rulf", 0)
        self.assertEqual(len(segments), 2)
        self.assertEqual([x["duree_secondes"] for x in segments],
                         [600.0, 300.0])

    def test_registre_conserve_aussi_un_echec(self):
        ancien = compute.DEPOT
        try:
            with tempfile.TemporaryDirectory() as d:
                compute.DEPOT = d
                compute.enregistrer("rulf", None, "s", "claude",
                                    100.0, 1000.0, False, "expiration")
                evenements = compute.lire_evenements()
        finally:
            compute.DEPOT = ancien
        self.assertEqual(len(evenements), 1)
        self.assertEqual(evenements[0]["duree_secondes"], 900.0)
        self.assertFalse(evenements[0]["succes"])
        self.assertEqual(evenements[0]["compte_pour"], "rulf")

    def test_identite_explicite_propagee_et_bordereau_atomique(self):
        ancien_depot, ancien_map = compute.DEPOT, compute.WORK_MAP
        identity = {
            "work_id": "9ca2832a-bad4-5e71-af6b-326521708d9e",
            "attempt_id": "9ca2832a-bad4-5e71-af6b-326521708d9e:attempt:3",
            "attempt_number": 3,
            "effect_key": "effect:9ca2832a-bad4-5e71-af6b-326521708d9e",
        }
        try:
            with tempfile.TemporaryDirectory() as d:
                compute.DEPOT = os.path.join(d, "compute")
                compute.WORK_MAP = os.path.join(d, "work-map")
                entree = compute.enregistrer(
                    "rulf", None, "conversation", "fixture", 1.0, 2.0,
                    True, work_identity=identity)
                with io.open(entree["work_bordereau"], encoding="utf-8") as f:
                    bordereau = json.load(f)
        finally:
            compute.DEPOT, compute.WORK_MAP = ancien_depot, ancien_map
        self.assertEqual(identity["work_id"], entree["work_id"])
        self.assertEqual(identity, bordereau[entree["id"]])
        self.assertEqual("conversation", entree["session"])

    def test_session_ne_devient_jamais_une_identite_de_travail(self):
        ancien = compute.DEPOT
        try:
            with tempfile.TemporaryDirectory() as d:
                compute.DEPOT = d
                entree = compute.enregistrer(
                    "rulf", None, "session-seule", "fixture",
                    1.0, 2.0, True)
        finally:
            compute.DEPOT = ancien
        self.assertNotIn("work_id", entree)


if __name__ == "__main__":
    unittest.main()
