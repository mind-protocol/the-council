# `monde/` — engendrer la ville, et cuire la bataille

Deux métiers cohabitent ici. **La CHAÎNE** fabrique le monde 3D — le relief, la
voirie, les maisons, les habitants, le plan 2D. **LE SAC** cuit une bataille à
l'avance, pour qu'elle ne se calcule pas sous les yeux du joueur.

Les fichiers produits vivent dans `monde/` à la racine du dépôt (`portreal.*.json`,
`peyredragon.*.json`), jamais dans `etat/` : ils se régénèrent, `etat/` non.

## La chaîne — 14 étapes, dans l'ordre

```bash
python scripts/monde/pipeline.py --liste     # l'ordre, la fraîcheur, les avertissements
python scripts/monde/pipeline.py             # tout Port-Réal
```

**La pipeline est l'autorité sur l'ordre, pas ce fichier.** Elle dit quelle étape
est périmée, ce que chacune écrit, et ce qu'elle emporte. `--liste` d'abord, avant
toute relance.

`relief` → `graphe` → `semis` → `coudre` → `usages` → `annexes` → `portes` →
`degager` → `infill` → `rues` → `peupler` → `besoins` → `plan` → `planches`.

**Trois pièges, mesurés et payés :**
- **`plan_ville.py` RÉÉCRIT `plan2d.json` en entier** et emporte sans un mot les
  trois couches posées après coup. Relancer ensuite, dans cet ordre :
  `toponymie.py --appliquer`, `cloches.py --appliquer`, `guet.py --appliquer`.
  On a cherché les cloches une demi-heure.
- **`peupler.py` change les index des corps.** Une partie en cours pointera les
  mauvaises maisons — et `etat/corps.json` recopie des coordonnées qui survivront à
  la régénération en étant devenues fausses. Vérifier après.
- **`combler_ilots.py` est append-only** pour les rangs existants, mais ses
  nouveaux habitants demandent ensuite `peupler` et `besoins`.

## Blender

`batir.py` se lance PAR Blender, sans interface :
`blender -b --python scripts/monde/batir.py`. Il lit le graphe et le terrain, il ne
les calcule pas.

## Le sac — la bataille cuite

`sac.js` cuit une bataille au lieu de la calculer en direct : on paie une fois, on
rejoue autant qu'on veut. `corps_mesure.js` mesure ce que la couche 1 rend sur une
bataille entière ; `annales.js` relit ce qui s'est produit.

**Le chemin `scripts/monde/sac.js` est cité une quarantaine de fois dans les cahiers
in-fiction de `etat/books/`**, et `plan_ville.py`, `corps_mesure.js` et `besoins.py`
le sont aussi. Ces noms-là ne se renomment pas sans casser la journée d'un homme
dépêché qui suit son cahier.

## Deux plumes sur le même monde

Ces fichiers sont gros et se réécrivent en entier. À deux sessions, une chaîne
lancée pendant qu'une autre lit produit un résultat cohérent et mort. Figer ses
lectures avant de lancer, et recompter après.
