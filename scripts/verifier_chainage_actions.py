# -*- coding: utf-8 -*-
"""Garde : chaque fermeture d'action neuve possède un fait lié."""
import os
import sys

# Console Windows en cp1252 : sans ça, le garde CRASHE sur la flèche de son
# propre message d'erreur et l'on ne lit jamais ce qu'il avait trouvé.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
NOYAU = os.path.join(SCRIPTS, "noyau")
for p in (SCRIPTS, NOYAU):
    if p not in sys.path:
        sys.path.insert(0, p)

import chainage_actions  # noqa: E402

ETAT = os.path.join(os.path.dirname(SCRIPTS), "etat")


def main():
    erreurs = chainage_actions.auditer(ETAT)
    if erreurs:
        print("NON — %d référence(s) action → acte invalide(s)" % len(erreurs))
        for e in erreurs[:20]:
            print("  " + e)
        return 1
    print("chainage-actions : OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
