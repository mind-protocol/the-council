# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest
from pathlib import Path

_d = os.path.dirname(os.path.abspath(__file__))
while os.path.basename(_d) != "scripts" and os.path.dirname(_d) != _d:
    _d = os.path.dirname(_d)
for _p in (_d, os.path.join(_d, "noyau")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agents.expose import copier_claude_vers_agents


class CopierClaudeVersAgentsTest(unittest.TestCase):
    def test_copie_tous_les_etages_et_ecrase(self):
        with tempfile.TemporaryDirectory() as brut:
            racine = Path(brut)
            (racine / "CLAUDE.md").write_bytes(b"racine\n")
            (racine / "AGENTS.md").write_bytes(b"ancien\n")
            chambre = racine / "chambres" / "mj"
            chambre.mkdir(parents=True)
            (chambre / "claude.md").write_bytes("manière\n".encode("utf-8"))

            compte = copier_claude_vers_agents.synchroniser(racine)

            self.assertEqual(2, compte["sources"])
            self.assertEqual(b"racine\n", (racine / "AGENTS.md").read_bytes())
            self.assertEqual("manière\n".encode("utf-8"),
                             (chambre / "AGENTS.md").read_bytes())

    def test_verifier_necrit_rien(self):
        with tempfile.TemporaryDirectory() as brut:
            racine = Path(brut)
            (racine / "CLAUDE.md").write_bytes(b"neuf")
            (racine / "AGENTS.md").write_bytes(b"vieux")

            compte = copier_claude_vers_agents.synchroniser(
                racine, verifier=True)

            self.assertEqual(1, len(compte["divergents"]))
            self.assertEqual(b"vieux", (racine / "AGENTS.md").read_bytes())


if __name__ == "__main__":
    unittest.main()
