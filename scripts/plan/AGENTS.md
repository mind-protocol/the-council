# 📋 `plan/` — le container du Grand Plan : cahiers, couverture, criticité, levées

Le plan de la Prise de Port-Réal vit dans les cahiers de `etat/books.json`. Ce
container possède tout ce qui le lit, le mesure et le répare — la matière des
neuf commandes racine (descendues au lot 2, `docs/organisation.md` §7) et les
scripts de réparation historiques.

**LA PORTE est `expose.py`** (`docs/organisation.md` §2) : on n'entre ici que
par `from plan.expose import ...` — jamais par un module direct. Les commandes
racine (`couverture.py`, `criticite.py`, `etat_du_plan.py`, `mesures.py`,
`tisser.py`, `fils.py`, `verser_cahier.py`, `exporter_plan.py`, `passer.py`)
sont des FAÇADES aux chemins gelés : elles passent elles aussi par la porte.

## Les modules du lot 2 — la matière des commandes

| Module | Descendu de | Ce qu'il sait |
|---|---|---|
| `couverture/` | `couverture.py` | la couverture d'une affaire, calculée jamais saisie — lecture, blocs, registres dérivés, écriture |
| `criticite/` | `criticite.py` | ce qu'on perd si ce pas-là rate — page, graphe, hommes, affaires, décisions, note, calcul, cli |
| `etat_du_plan/` | `etat_du_plan.py` | l'état du plan, toutes affaires confondues (lecture seule) — page, échéances, missions, sections, cli |
| `mesures/` | `mesures.py` | les adresses de mesure résolues contre `mains.json` — adresses, rapport, seuils |
| `tisser/` | `tisser.py` | tous les liens projetés dans UNE table d'arêtes — lecture, tissage |
| `graphe_causal.py` | `graphe_causal.py` | le sous-graphe amont d'un événement ou de tous, avec les trous typés |
| `affaires.py` | `fils.py` | ce qui court, et qui tient la plume dessus (le nom lève l'homonymie `fils.py`/`fils.js`) |
| `verser_cahier.py` | `verser_cahier.py` | verser les `cahier2` des rapports dans les registres — refuse, ne devine jamais |
| `exporter_plan.py` | `exporter_plan.py` | l'export texte brut des cahiers (n'exporte plus à l'import) |
| `passer.py` | `passer.py` | un livre change de main, ou se pose sur une table |

Les paquets (`couverture/`, `criticite/`, `etat_du_plan/`, `mesures/`,
`tisser/`) existent parce qu'un module naît sous 500 lignes (le cliquet de
`.claude/hooks/taille.js`) : la matière y est découpée par sections, les
commentaires ont voyagé avec leur code. Le découpage FIN (par consommateur
réel) reste au lot 2 tiré par les features (`docs/organisation.md` §5).

Entre modules du MÊME container, l'import est direct
(`from plan.couverture.lecture import nu`) ; seuls les façades et les autres
containers passent par la porte. `jours_relatifs` (container temps) n'a qu'un
point de contact : `etat_du_plan/echeances.py`.

## Les réparations — les scripts historiques du dossier

**Aucun ne tourne au tour de jeu** : on les sort quand une colonne est partie
de travers, jamais dans la boucle. **Tous écrivent dans les cahiers, et tous
ont un mode à blanc.** La règle sans exception : on lance sans `--vraiment`,
**on LIT le rapport**, et on relance avec.

| Script | Ce qu'il fait |
|---|---|
| `corriger_plan.py` | applique une proposition de correction — remplacement par fragment, refusé si ambigu |
| `normaliser_etats.py` | la colonne « ⏳ État » : un mot d'état, la prose versée en « Note » |
| `porter_jour_du.py` | remonte les dates ABSOLUES de la note vers « 📅 Jour dû » |
| `dater_plan.py` | porte l'échelle J−N là où `porter_jour_du` a laissé du relatif |
| `reparer_renvois.py` | écrit le NUMÉRO de l'office là où le cahier n'a qu'un nom d'homme |
| `scinder_moyens.py` | sépare « 🧰 Moyens » en numéros d'un côté, prose de l'autre |
| `normaliser.py` | le vocabulaire des liens du tissu — 34 natures pour 15 intentions |
| `plan_leves.py` | les marches de Marlo en carte de métro — un SVG |
| `cens.py` | compte les CELLULES pleines table par table, et refuse qu'une passe en fasse baisser le compte |

`cens.py` n'est pas une réparation : c'est le garde qu'on met **autour** d'une
passe qui va traverser plusieurs volumes. `--recenser <dossier>` avant (il
prend lui-même la copie), `--verifier <dossier>` après (sort 2 si une table a
perdu une cellule). Il compte les cellules et non les lignes : le 9e de la 4e
lune, une passe a vidé sept volumes de `chambres/mj/books/` en laissant une
cellule debout par ligne — le compte des lignes pleines n'avait pas bougé.
Écrit le 9e, **jamais exécuté** : personne n'a pu lui passer sa recette.

`corriger_plan.py` est couvert par `../tests/test_corriger_plan.py`, qui l'importe
par un chemin explicite vers ce dossier. Le renommer casse ce test.
