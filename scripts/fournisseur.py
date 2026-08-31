# -*- coding: utf-8 -*-
"""Choisir le fournisseur global des reveils Claude/Codex.

Usage :
    python scripts/fournisseur.py
    python scripts/fournisseur.py codex --modele gpt-5.3-codex-spark --effort low
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
    ap.add_argument("fournisseur", nargs="?", choices=("claude", "codex", "chatgpt"))
    ap.add_argument("--modele")
    ap.add_argument("--effort")
    a = ap.parse_args()
    d = (runtime.choisir(a.fournisseur, a.modele, a.effort)
         if a.fournisseur else runtime.configuration())
    print(json.dumps(d, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
