# -*- coding: utf-8 -*-
"""Façade stable de la réception des décisions de collaboration."""
import os
import sys

DOSSIER = os.path.dirname(os.path.abspath(__file__))
if DOSSIER not in sys.path:
    sys.path.insert(0, DOSSIER)

from plan.expose import recevoir_decision_main as main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
