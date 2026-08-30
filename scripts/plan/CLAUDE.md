# `plan/` — le Grand Plan, ses colonnes et ses réparations

Le plan de la Prise de Port-Réal vit dans les cahiers de `etat/books.json`. Ces
scripts-là le lisent, le corrigent, et normalisent ses colonnes. **Aucun ne tourne
au tour de jeu** : on les sort quand une colonne est partie de travers, jamais dans
la boucle.

**Tous écrivent dans les cahiers, et tous ont un mode à blanc.** La règle sans
exception : on lance sans `--vraiment`, **on LIT le rapport**, et on relance avec.
Un cahier réécrit de travers ne se voit qu'à la lecture suivante, des jours après.

| Script | Ce qu'il fait |
|---|---|
| `corriger_plan.py` | applique une proposition de correction — remplacement par fragment, refusé si ambigu |
| `normaliser_etats.py` | la colonne « ⏳ État » : un mot d'état, la prose versée en « Note » |
| `porter_jour_du.py` | remonte les dates ABSOLUES de la note vers « 📅 Jour dû » |
| `dater_plan.py` | porte l'échelle J−N là où `porter_jour_du` a laissé du relatif |
| `reparer_renvois.py` | écrit le NUMÉRO de l'office là où le cahier n'a qu'un nom d'homme |
| `scinder_moyens.py` | sépare « 🧰 Moyens » en numéros d'un côté, prose de l'autre |
| `normaliser.py` | le vocabulaire des liens du tissu — 34 natures pour 15 intentions |
| `lacunes.py` | qui compte dans l'histoire sans avoir de quoi y travailler |
| `plan_leves.py` | les marches de Marlo en carte de métro — un SVG |

`corriger_plan.py` est couvert par `../tests/test_corriger_plan.py`, qui l'importe
par un chemin explicite vers ce dossier. Le renommer casse ce test.
