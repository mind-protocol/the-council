# -*- coding: utf-8 -*-
"""VECU — la vue lisible du fil d'un habitant (facade ; docs/habitant.md pas 6).

    python scripts/vecu.py <qui>                      la liste de son fil/
    python scripts/vecu.py <qui> --md <fichier>       un depot du fil, entier
    python scripts/vecu.py <qui> --session <id> [--etiquette 129.4.4]
                                                      depouille et depose ce vecu
"""
import argparse
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from agents.expose import chambre, trace  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("qui")
    ap.add_argument("--md", default=None, help="afficher ce depot du fil")
    ap.add_argument("--session", default=None, help="depouiller cette session")
    ap.add_argument("--etiquette", default=None, help="le moment du monde (129.4.4)")
    a = ap.parse_args()

    if a.session:
        chemin = trace.deposer(a.qui, a.session, a.etiquette)
        print(chemin or "transcript introuvable pour %s" % a.session)
        return
    fil = os.path.join(chambre.chemin(a.qui), "fil")
    if a.md:
        with io.open(os.path.join(fil, a.md), encoding="utf-8") as f:
            print(f.read())
        return
    if not os.path.isdir(fil):
        print("(fil vide — aucune session déposée pour %s)" % a.qui)
        return
    for nom in sorted(os.listdir(fil)):
        plein = os.path.join(fil, nom)
        premiere = ""
        with io.open(plein, encoding="utf-8", errors="replace") as f:
            for l in f:
                if l.strip() and not l.startswith("#"):
                    premiere = l.strip()[:80]
                    break
        print("%-40s %6d o  %s" % (nom, os.path.getsize(plein), premiere))


if __name__ == "__main__":
    main()
