# `ville/` — Port-Réal, le tissu et sa région

**La ville s'engendre par la CIRCULATION, pas par les maisons** — et c'est toute
l'idée du dossier : nœuds → artères → rues → ruelles → parcelles → façades. Chaque
tracé porte sa `raison`, si bien que la forme de la ville dit son fonctionnement au
lieu de le décorer.

| Fichier | Ce qu'il fait |
|---|---|
| `engendrer_port_real.py` | engendre le tissu, de la circulation aux façades |
| `assembler_port_real.py` | assemble `etat/villes/port-real.json` depuis le tissu |
| `tissu.json` | le tissu engendré |
| `port-real-region.json` | la région autour des murs |
| `port-real-toponymie.json` | les noms |
| `port-real-cloches.json` | les cloches |
| `port-real-guet.json` | le Guet |

**Les trois couches nommées — toponymie, cloches, Guet — se posent APRÈS le plan
2D**, et `../monde/plan_ville.py` les emporte en silence quand il réécrit
`plan2d.json`. Les réappliquer dans cet ordre, avec les scripts de `../monde/` :
`toponymie.py --appliquer`, `cloches.py --appliquer`, `guet.py --appliquer`.

Ce que `assembler_port_real.py` écrit atterrit dans `etat/`, et non dans `monde/`.
C'est la frontière : le tissu se régénère, ce que la partie en connaît, non.

`docs/port-real-couronne-periurbaine.md` cite trois scripts de région
(`engendrer_region_port_real.py`, `assembler_region_port_real.py`,
`verifier_region_port_real.py`) qui n'existent pas sous ces noms ici — le doc est en
avance sur le dossier.
