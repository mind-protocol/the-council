# -*- coding: utf-8 -*-
"""La physique de la diffusion — chargee, jamais recopiee.

Les constantes vivent dans `diffusion.json`, a cote. Le Python les lit ici ;
`serveur/domaine/regie.js` lit le MEME fichier et le sert a la page de regie
sous `graphe.physique`. C'est ce qui empeche les deux implementations de la
meme formule de deriver — elles l'ont fait, et personne ne l'a vu pendant que
la page annoncait une diffusion qui n'etait pas celle qui elit les acteurs.

Le fichier est obligatoire : on ne retombe sur aucun defaut code en dur, parce
qu'un defaut silencieux est exactement le mecanisme qu'on vient de retirer.
"""

import json
import os

CHEMIN = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "diffusion.json")

with open(CHEMIN, encoding="utf-8") as _f:
    _P = json.load(_f)

AMORTISSEMENT = float(_P["amortissement"])
TOURS_DIFFUSION = int(_P["tours"])
GENRES_RELAIS = frozenset(_P["genres_relais"])

if not GENRES_RELAIS or not (0.0 < AMORTISSEMENT < 1.0) or TOURS_DIFFUSION < 1:
    raise ValueError("diffusion.json hors bornes : %r" % (_P,))
