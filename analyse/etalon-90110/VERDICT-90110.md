# Verdict de 🔒 90110 — laquelle des deux causes a bougé les quatre comptes

Toll Œil-Noir, l'eau. 129.4.3, à la Souche. Quatre bras, un seul chiffre change
à la fois.

## La condition du chiffre — six lignes, et sans elles le chiffre ne vaut rien

- **graine** 20161219, `bataille/hasard.js` l.32, tenue par `H` — le repli
  `Math.random()` de `corps-adapt.js` l.350 n'a pas servi.
- **la ville** an 129, 4e lune, jour 3, minute 721 (12h01), lue en direct dans
  `etat/monde.json` (`sac.js` l.614-615).
- **peuple 0, tournée 0, planches 0** — le banc monte la chaîne seule et ne
  passe pas par `sac.js` : ces trois-là sont des chiffres du four, pas du banc.
- **empreintes** (sha256, 12 premiers) : hasard `23fdcd8a79ef` · mesures
  `276ac2005d44` · 1-corps `6a5931973375` · corps-adapt `2986fe65a2c9` ·
  4-envie `76a2c6fbc4dd` · 3-interpretation `0f0e474a453e` · bataille2d
  `594eba8429bc`.
- **drapeaux** : `PORTE_OUVERTE_ESSAI` = `false` (`bataille2d.js` l.318) ;
  `3-interpretation.js` branchée ; `4-envie.js` branchée.
- **1700 hommes, 150 s** — ce ne sont PAS les 600 s de la référence du 14 août.
  Ce verdict porte sur des PARTS, pas sur les 5, 5, 14 et 54.

## Les quatre bras

| bras | ordres déf. | déclench. | initiatives | coureurs |
| --- | --- | --- | --- | --- |
| tel-quel (drapeau `false`, 3 et 4 branchées) | **3** | **5** | **4** | **47** |
| `--porte-ouverte` (drapeau `true`) | 0 | 0 | 5 | 27 |
| `--sans-interpretation` (4 seule) | 3 | 5 | 3 | 48 |
| `--sans-couches` | — | — | — | — |

Le bras tel-quel a été cuit deux fois, à deux heures de machine différentes :
3, 5, 4, 47 les deux fois. La graine tient.

## Le verdict

**Le drapeau a bougé trois comptes sur quatre, et à lui seul.**

- **Ordres déformés (3) et déclencheurs tombés (5)** : entièrement le drapeau.
  Porte ouverte, ils tombent à 0 et 0 — la branche « verrou ouvert » avalait la
  consigne. Ôter `3-interpretation` ne les bouge pas d'une unité (3 et 5
  encore).
- **Coureurs (47)** : entièrement le drapeau. 47 → 27 quand la porte se
  rouvre ; 47 → 48 sans interprétation, c'est-à-dire rien.
- **Initiatives (4)** : NI l'un NI l'autre proprement. 4 tel-quel, 5 porte
  ouverte, 3 sans interprétation. L'interprétation en vaut une sur quatre, le
  drapeau en vaut moins une. Le compte des initiatives est le plus petit des
  quatre et le seul qu'aucune des deux causes n'explique : à 150 s il ne porte
  pas de verdict, et c'est lui qu'il faut recuire à 600 s.

## Ce que la mesure a trouvé et que personne ne cherchait

**Les deux couches hautes ne sont pas symétriques : l'une se débranche, l'autre
non.**

- `3-interpretation` est GARDÉE — `bataille2d.js` l.3451 `if
  (window.Interpretation && e)`, et l.4557 passe par `chef.l3`, qui n'existe
  pas sans la couche. On peut donc la retirer et cuire.
- `4-envie` ne l'est PAS — l.1458, 3626, 3643, 4531 appellent `window.Envie`
  sans garde. La première tombe dans `homme()`, au DRESSAGE, avant le premier
  pas : la cuisson meurt en trois secondes, elle ne rend pas un mauvais
  chiffre, elle n'en rend aucun.

Conséquence, et elle est dure : **la part de `4-envie` dans les quatre comptes
n'est pas mesurable en l'état**, ni aujourd'hui ni le jour où l'étalon bougera.
Elle ne se lit que par soustraction, et une soustraction n'est pas une mesure.
Quatre gardes à poser dans `bataille2d.js` — ce n'est pas mon office, c'est
celui qui tient la chaîne.
