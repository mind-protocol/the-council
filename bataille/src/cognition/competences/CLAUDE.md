# 🧠 Cognition / Compétences — ✅

## Intention

Les **savoir-faire exécutables** — tout le if/else procédural, rangé. « Se
mettre rapidement en formation » est un if/else (tenir / ancre invisible /
en place / anti-churn) : il a le droit d'exister, mais ICI, jamais éparpillé
dans les brains. Division du travail stricte avec les machines :

> La machine décide **QUOI** (les transitions, justifiées, en donnée) ;
> la compétence décide **COMMENT** (l'exécution, en code).

## Contrat

Signature commune : `(ctx) → {intention, objectifHumain, cible, debug?}`
- `ctx` : représentation, params, zone, rng (pour les tirages d'exécution —
  flottements, périodes) ; une compétence STATEFULE (ancrages, anti-churn)
  s'expose en fabrique (`creerX(deps)` → `agir(...)`).
- `objectifHumain` : OBLIGATOIRE, en français (« me mettre derrière Paul ») —
  c'est lui que l'inspecteur et les calques affichent ; les descriptions de
  croyances passent par `langage/decrire.js`.
- `intention: null` = « rien de neuf » (anti-churn) ; l'intention sortante
  reste le vocabulaire fermé de `intentions.js`.

## Modules

- `se-mettre-en-formation.js` — fabrique statefule ; le repère vient de
  `langage/resoudre-lieu.js` (sur moi / première ligne auto-référente /
  amorçage), l'ancrage de `doctrine/formes/`, la cible du dressage.
- `se-regrouper.js` — le cercle : `rejoindre` / `ecarter` / `discuter`, plus
  `geometrieCercle` (pure) que les GARDES des machines consultent.
- `flaner.js` — le point aléatoire en zone.

## Frontières

- Une compétence ne transitionne JAMAIS (aucun accès à la machine) et ne lit
  que la Représentation — même verrou que les brains.
- Les `actions` des machines deviennent des appels de compétences : après la
  migration, plus un seul if/else métier dans `brains/`.
- Partagées entre tous les brains (soldat, grégaire, demain commandant) —
  c'est déjà le cas de fait, la migration l'assume.

## Croissance attendue

`suivre-le-chef`, `tenir-position`, `se-porter-a` (un lieu résolu),
`deborder` (un flanc résolu), `fuir-vers`, et les compétences de combat —
chacune arrivera avec sa ligne Observables et sa viz.
