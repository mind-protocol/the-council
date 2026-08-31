# -*- coding: utf-8 -*-
"""Choisir le fournisseur global des reveils Claude/Codex.

Usage :
    python scripts/fournisseur.py
    python scripts/fournisseur.py codex --modele gpt-5.3-codex-spark --effort low --fast
    python scripts/fournisseur.py claude
"""
import argparse
import json
import os
import sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents import runtime  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("fournisseur", nargs="?", choices=("claude", "codex", "chatgpt", "gemini"))
    ap.add_argument("--modele")
    ap.add_argument("--effort")
    vitesse = ap.add_mutually_exclusive_group()
    vitesse.add_argument("--fast", action="store_true",
                         help="service tier fast pour tous les appels Codex")
    vitesse.add_argument("--standard", action="store_true",
                         help="retirer le service tier fast")
    a = ap.parse_args()
    fast = True if a.fast else False if a.standard else None
    d = (runtime.choisir(a.fournisseur, a.modele, a.effort, fast=fast)
         if a.fournisseur else runtime.configuration())
    print(json.dumps(d, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
