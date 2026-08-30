# -*- coding: utf-8 -*-
"""MIGRER LE PARLOIR — facade (docs/habitant.md pas 7).

    python scripts/migrer_parloir.py             a sec : le plan, rien d'ecrit
    python scripts/migrer_parloir.py --vraiment  migre, pose les curseurs,
                                                 supprime les fils migres

Les fils ~mj et homme~homme d'etat/parloir/ deviennent les discussion.json
des canaux de chambres. Voir agents/parloir_migration.py pour les regles.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agents.expose import parloir_migration  # noqa: E402


def main():
    vraiment = "--vraiment" in sys.argv
    print("MIGRATION DU PARLOIR — %s" % ("POUR DE VRAI" if vraiment else "a sec"))
    bilan = parloir_migration.migrer(vraiment=vraiment)
    print("  = %(canaux)d canaux · %(entrees)d entrees · %(fils)d fils sources"
          % bilan)
    if not vraiment:
        print("  Rien n'a ete ecrit. --vraiment pour executer.")


if __name__ == "__main__":
    main()
