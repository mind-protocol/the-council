# `monde/` — engendrer la ville

Un seul métier ici : **la CHAÎNE** fabrique le monde 3D — le relief, la voirie,
les maisons, les habitants, le plan 2D.

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

## Les commandes descendues (lot 2) — le monde qu'on interroge

À côté de la CUISSON (la chaîne ci-dessus), le container porte depuis le lot 2
la matière des quatre commandes racine du monde. **La porte** : `expose.py` —
`from monde.expose import ...`, jamais un module interne. Chaque commande
racine est une façade gelée (chemin et CLI inchangés).

| module | ce qu'il possède | commande façade |
|---|---|---|
| `geographie.py` + `geographie_traces.py` + `geographie_sortie.py` | la carte de Westeros depuis le mod AGOT : constantes et lecteur du mod / masques, contours, routes / assemblage et écriture de `ecrans/modules/geo.js` | `scripts/carte_geo.py` |
| `arpentage.py` | lever une carte au pas et à l'œil — le brouillard s'applique | `scripts/arpenter.py` |
| `corps.py` + `corps_metiers.py` | lister, lier, promouvoir les corps ; la matière sociale de l'incarnation | `scripts/corps.py` |
| `trajets.py` | combien de temps pour aller là-bas, à pied, par les rues (mêmes règles que `journee.js`) | `scripts/marche.py` |

## Blender

`batir.py` se lance PAR Blender, sans interface :
`blender -b --python scripts/monde/batir.py`. Il lit le graphe et le terrain, il ne
les calcule pas.

## Les noms cités dans les cahiers

**`plan_ville.py` et `besoins.py` sont cités dans les cahiers in-fiction de
`etat/maisons/*/documents/books/`.** Ces noms-là ne se renomment pas sans casser la journée d'un homme
dépêché qui suit son cahier.

> Le four de bataille qui vivait ici — `sac.js` et ses mesures — a été supprimé du
> dépôt le 30 août 2026 ; le remplacement passera par des appels au dépôt voisin
> `batailles`. Les cahiers qui citaient `scripts/monde/sac.js` pointent donc, pour
> l'instant, sur un chemin mort : c'est exactement le mal que cette section
> nommait, et il est ici constaté plutôt que découvert par un dépêché.

## Deux plumes sur le même monde

Ces fichiers sont gros et se réécrivent en entier. À deux sessions, une chaîne
lancée pendant qu'une autre lit produit un résultat cohérent et mort. Figer ses
lectures avant de lancer, et recompter après.
