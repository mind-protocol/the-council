#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""composer.py — poser une chanson sur la table, et l'ouvrir au bloc-notes.

Usage :
    python scripts/composer.py --titre "La Dette de Sombreval" \
        --concept "..." --paroles paroles.txt --prompt "..." [--ouvrir]

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere — l'ardoise,
le plafond de 800 caracteres du prompt Suno, l'ecriture du .md — vit dans
peinture/composer.py, qui ne touche jamais a l'etat du jeu (une chanson est
hors univers). Le chemin et la CLI de cette commande sont geles.
"""
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from peinture.expose import composer as _composer  # noqa: E402 — LA PORTE de peinture/

MAX_PROMPT = _composer.MAX_PROMPT
DOSSIER = _composer.DOSSIER
ardoise = _composer.ardoise
texte_ou_fichier = _composer.texte_ou_fichier
main = _composer.main

if __name__ == "__main__":
    main()
