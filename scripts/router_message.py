#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Façade publique du routage direct des messages joueur."""
import os
import sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents.expose import routeur_message_main as main  # noqa: E402,F401


if __name__ == "__main__":
    main()
