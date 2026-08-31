# -*- coding: utf-8 -*-
"""Facade publique du selecteur de contexte d'un message joueur."""
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
NOYAU = os.path.join(ICI, "noyau")
for chemin in (ICI, NOYAU):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

from agents.expose import selectionner_contexte_main as main  # noqa: E402,F401


if __name__ == "__main__":
    main()
