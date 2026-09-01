import os
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents import work_identity, work_oracle


class WorkOracleTest(unittest.TestCase):
    def test_relit_un_effet_sans_croire_le_verdict_fournisseur(self):
        with tempfile.TemporaryDirectory() as root:
            db_path = os.path.join(root, "registry.json")
            artifact = os.path.join(root, "effect.txt")
            with open(artifact, "wb") as f:
                f.write(b"effet durable\n")
            with mock.patch.object(work_identity, "REGISTRE", db_path):
                identity = work_identity.admettre("sentinelle:seule")
                work_identity.terminer_attempt(
                    identity, "event-0", "failed", False, None)
                identity = work_identity.admettre("sentinelle:seule")
                work_identity.terminer_attempt(
                    identity, "event-1", "succeeded", True, artifact)
                with mock.patch.object(work_oracle.work_identity, "REGISTRE", db_path):
                    seen = work_oracle.observer(identity["work_id"])
            self.assertEqual(1, seen["effect_count"])
            self.assertEqual(14, seen["bytes"])
            self.assertEqual(identity["effect_key"], seen["effect_key"])
            self.assertEqual(["failed", "succeeded"],
                             [a["state"] for a in seen["attempts"]])
            self.assertEqual(["event-0", "event-1"],
                             [a["compute_event_id"]
                              for a in seen["attempts"]])

    def test_absence_de_fichier_ne_devient_pas_un_effet(self):
        with tempfile.TemporaryDirectory() as root:
            db_path = os.path.join(root, "registry.json")
            with mock.patch.object(work_identity, "REGISTRE", db_path):
                identity = work_identity.admettre("sentinelle:perdue")
                work_identity.terminer_attempt(
                    identity, "event-2", "succeeded", True,
                    os.path.join(root, "absent"))
                with mock.patch.object(work_oracle.work_identity, "REGISTRE", db_path):
                    seen = work_oracle.observer(identity["work_id"])
            self.assertEqual(0, seen["effect_count"])
            self.assertNotIn("sha256", seen)


if __name__ == "__main__":
    unittest.main()
