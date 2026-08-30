# -*- coding: utf-8 -*-
"""Ou se tient chacun DANS le chateau, a la minute pres — et par ou il y va.

    python scripts/presence.py                  — tout le chateau, maintenant
    python scripts/presence.py --json [--quand a.l.j.m | --a j:m]
    python scripts/presence.py --ou <qui>       — ou il est, et pourquoi
    python scripts/presence.py --chemin a b     — le chemin et son cout
    python scripts/presence.py --audit          — les fantomes de presence.json
    python scripts/presence.py --quartier       — qui le joueur peut atteindre
    python scripts/presence.py --creux <qui>    — le temps libre de sa journee

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — LA POSITION
NE SE STOCKE PAS, ELLE SE CALCULE : les routines-destinations, la carte des
pas, les exceptions datees (temps/presence.py), le quartier du joueur, les
creux et le main (temps/presence_quartier.py) — vit dans le container temps/,
avec tout son POURQUOI en tete. Le chemin et la CLI de cette commande sont
geles (le serveur appelle `--json` et `--quartier`) ; les reexports
ci-dessous gardent les anciens noms `presence.*` vivants (append_flux, bouche
et les gardes passent deja par la porte temps/expose).
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from temps.expose import presence as _presence  # noqa: E402 — LA PORTE de temps/

# Tout ce que l'ancien module offrait reste accessible sous les memes noms.
globals().update({n: getattr(_presence, n) for n in dir(_presence)
                  if not n.startswith("_")})
main = _presence.main

if __name__ == "__main__":
    sys.exit(main())
