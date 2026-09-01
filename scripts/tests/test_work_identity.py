# -*- coding: utf-8 -*-
import concurrent.futures
import contextlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents import work_identity


class WorkIdentityTest(unittest.TestCase):
    def test_migration_json_est_repetable_et_quarantaine_les_collisions(self):
        ancien = work_identity.REGISTRE
        try:
            with tempfile.TemporaryDirectory() as d:
                work_identity.REGISTRE = os.path.join(d, "work.sqlite3")
                legacy = os.path.join(d, "work.json")
                work_id = "11111111-1111-4111-8111-111111111111"
                base = {
                    "works": {"legacy-key": {
                        "work_id": work_id,
                        "effect_key": "effect:" + work_id,
                        "created_at": 1.0}},
                    "attempts": {work_id: [{
                        "attempt_id": work_id + ":attempt:1",
                        "attempt_number": 1, "admitted_at": 2.0,
                        "state": "succeeded", "compute_event_id": "event-1",
                        "ended_at": 3.0}]},
                    "terms": {}, "states": {}, "rewakes": {}}
                with open(legacy, "w", encoding="utf-8") as f:
                    json.dump(base, f)
                with mock.patch.object(work_identity, "_chemin_legacy",
                                       return_value=legacy):
                    first = work_identity.observer(work_id)
                    base["attempts"][work_id].append({
                        "attempt_id": work_id + ":attempt:2",
                        "attempt_number": 2, "admitted_at": 4.0,
                        "state": "admitted", "compute_event_id": None,
                        "ended_at": None})
                    with open(legacy, "w", encoding="utf-8") as f:
                        json.dump(base, f)
                    second = work_identity.observer(work_id)
                    intrus = "22222222-2222-4222-8222-222222222222"
                    base["works"]["legacy-key"] = {
                        "work_id": intrus, "effect_key": "effect:" + intrus,
                        "created_at": 5.0}
                    base["attempts"][intrus] = []
                    with open(legacy, "w", encoding="utf-8") as f:
                        json.dump(base, f)
                    self.assertEqual(work_id,
                                     work_identity.courante("legacy-key")["work_id"])
                # Le context manager sqlite valide ou annule la transaction,
                # mais ne ferme pas la connexion. Sous Windows, le fichier
                # temporaire resterait donc verrouillé jusqu'au ramasse-miettes
                # et ferait accuser à tort work_identity d'une fuite.
                with contextlib.closing(
                        sqlite3.connect(work_identity.REGISTRE)) as conn:
                    conflits = conn.execute(
                        "SELECT existing_work_id,incoming_work_id FROM "
                        "migration_conflicts").fetchall()
        finally:
            work_identity.REGISTRE = ancien
        self.assertEqual(1, len(first["attempts"]))
        self.assertEqual(2, len(second["attempts"]))
        self.assertEqual([(work_id, intrus)], conflits)

    def test_meme_ref_garde_work_et_incremente_tentative(self):
        ancien = work_identity.REGISTRE
        try:
            with tempfile.TemporaryDirectory() as d:
                work_identity.REGISTRE = os.path.join(d, "work.json")
                key = work_identity.cle_depeche("elisabetta", "52140",
                                                "ref-1", "session")
                first = work_identity.admettre(key)
                retry = work_identity.admettre(key)
        finally:
            work_identity.REGISTRE = ancien
        self.assertEqual(first["work_id"], retry["work_id"])
        self.assertEqual(first["effect_key"], retry["effect_key"])
        self.assertEqual([1, 2], [first["attempt_number"],
                                 retry["attempt_number"]])
        self.assertNotEqual(first["attempt_id"], retry["attempt_id"])

    def test_admissions_concurrentes_ont_des_numeros_uniques(self):
        ancien = work_identity.REGISTRE
        try:
            with tempfile.TemporaryDirectory() as d:
                work_identity.REGISTRE = os.path.join(d, "work.json")
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                    results = list(pool.map(
                        lambda _i: work_identity.admettre("same-work"),
                        range(4)))
        finally:
            work_identity.REGISTRE = ancien
        self.assertEqual(1, len({r["work_id"] for r in results}))
        self.assertEqual([1, 2, 3, 4],
                         sorted(r["attempt_number"] for r in results))

    def test_session_seule_n_est_utilisee_que_sans_ref(self):
        avec_ref = work_identity.cle_depeche(
            "elisabetta", "52140", "ref-1", "session-1")
        autre_session = work_identity.cle_depeche(
            "elisabetta", "52140", "ref-1", "session-2")
        self.assertEqual(avec_ref, autre_session)

    def test_tentative_et_terme_se_relisent_apres_reouverture(self):
        ancien = work_identity.REGISTRE
        try:
            with tempfile.TemporaryDirectory() as d:
                work_identity.REGISTRE = os.path.join(d, "work.json")
                identity = work_identity.admettre("work-term")
                work_identity.terminer_attempt(
                    identity, "event-1", "succeeded", term=True,
                    artifact="rapport.json")
                logical = work_identity.etat(identity["work_id"])
                observed = work_identity.observer(identity["work_id"])
                attempt = observed["attempts"][-1]
                term = observed["term"]
        finally:
            work_identity.REGISTRE = ancien
        self.assertEqual(("succeeded", "event-1"),
                         (attempt["state"], attempt["compute_event_id"]))
        self.assertEqual((identity["attempt_id"], "succeeded", "event-1",
                          "rapport.json"),
                         (term["attempt_id"], term["state"],
                          term["compute_event_id"], term["artifact"]))
        self.assertEqual("completed", logical["state"])

    def test_progress_next_et_state_persistent(self):
        ancien = work_identity.REGISTRE
        try:
            with tempfile.TemporaryDirectory() as d:
                work_identity.REGISTRE = os.path.join(d, "work.json")
                identity = work_identity.admettre("persistent-state")
                work_identity.noter(identity, "3/5", "compiler", "waiting")
                seen = work_identity.etat(identity["work_id"])
        finally:
            work_identity.REGISTRE = ancien
        self.assertEqual(("3/5", "compiler", "waiting"),
                         (seen["progress"], seen["next"], seen["state"]))

    def test_relecture_courante_ne_cree_pas_de_tentative(self):
        ancien = work_identity.REGISTRE
        try:
            with tempfile.TemporaryDirectory() as d:
                work_identity.REGISTRE = os.path.join(d, "work.json")
                first = work_identity.admettre("current-no-attempt")
                current = work_identity.courante("current-no-attempt")
                retry = work_identity.admettre("current-no-attempt")
        finally:
            work_identity.REGISTRE = ancien
        self.assertEqual(first, current)
        self.assertEqual(2, retry["attempt_number"])

if __name__ == "__main__":
    unittest.main()
