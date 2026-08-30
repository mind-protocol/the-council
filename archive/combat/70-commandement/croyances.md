# Croyances

## 1. Ce que c'est

La carte que porte un chef dans sa tête, à son échelle, avec ses trous déclarés —
la seule chose qu'il ait le droit de consulter pour décider.

## 2. Ce qu'il possède

Une carte par commandant, et personne d'autre ne l'écrit. Elle porte :

- **Les positions amies connues** : ses corps, leur dernière position rapportée,
  leur effectif estimé, leur état apparent — il ne les voit pas mieux que
  l'ennemi s'il ne les voit pas.
- **Les positions ennemies possibles** : non un point, mais **une zone**, qui
  s'élargit avec le temps écoulé depuis la dernière observation.
- **Les effectifs en intervalles** : « entre trois et six cents » est une
  croyance, « quatre cent douze » une omniscience.
- **Les signatures observables** : hampes longues, poussière, bannière, bruit de
  sabots, densité, allure. On croit une signature avant de croire une nature.
- **Les zones explicitement inconnues** : les endroits d'où rien n'est venu. Une
  carte sans trous déclarés ment par silence.
- **L'âge et la confiance** de chaque élément : quand, par qui, par quel canal,
  et combien on y croit maintenant.

## 3. Ce qu'il lit

Du socle : horloge, identité, mesures. Du monde : le terrain, pour savoir ce qui
est visible depuis où il est et pour que ses zones d'incertitude respectent le
relief. De la perception : ce que lui-même perçoit. De l'unité : l'état de ses
corps, quand ils sont à portée de vue. De la transmission : les messages
**remis** — jamais ceux qui sont en route, perdus, ou dans la version d'origine.

**Il ne lit jamais l'état réel du camp adverse** : ni positions, ni effectifs,
ni ordres, ni cohésion. Si cette règle tombe, tout le reste de la couche 70
devient décoratif.

## 4. Ce qu'il produit

- **Sa carte à cet instant**, avec l'âge et la confiance de chaque élément.
- **Ce qu'il croit d'un endroit** : occupé, libre, ou inconnu — trois réponses.
- **L'intégration d'un fait** : la carte après son arrivée, et ce qui a changé.

## 5. Invariants

- **Une croyance ne change que par un fait** : perçu, reçu par un message remis,
  ou déduit d'un raisonnement enregistré. Jamais parce que le moteur sait.
- Tout effectif est un intervalle ; une sonde refuse un effectif ennemi exact.
- Toute position perdue de vue reste **là où on l'a vue**, avec sa date ; son
  incertitude croît, elle ne suit pas la position réelle.
- Une sonde extérieure vérifie qu'aucun commandant ne croit un corps qu'aucun
  fait ne lui a signalé, et qu'il ne voit pas à travers un mur.
- Deux commandants du même camp ont deux cartes différentes.

## 6. Ce qu'il ne fait pas

- **Il ne déduit rien.** Rapport de force, menace, intention prêtée à l'ennemi :
  c'est l'estimation, ailleurs.
- **Il ne se corrige pas tout seul.** Une croyance reste fausse tant qu'un fait
  ne l'a pas remplacée — et un chef peut s'entêter.
- **Il ne fusionne pas les cartes du camp.** Pas de carte d'état-major
  omnisciente ; ce qu'un chef sait passe par un message.
- **Il ne comble pas ses trous par vraisemblance** : on va voir, on ne suppose pas.

## 7. Ce que l'ancien moteur faisait mal ici

**C'est le seul endroit de ces deux couches où l'ancien moteur tenait.** Les
croyances étaient **signées, datées, avec une confiance qui décroît selon la
source**, et une sonde confirmait qu'**un chef ne voyait pas à travers les
murs**. La discipline de perception était réelle, pas déclarative.

La leçon n'est pas de refaire ce module autrement, mais de savoir ce qu'il ne
suffit pas de faire. Ces croyances justes n'avaient **aucun consommateur** : le
seul module qui en déduisait quelque chose écrivait un champ que personne ne
lisait, et sur quinze chefs, **zéro** ordre n'a changé à cause d'une croyance. Un
renseignement abondant — **41 observations typées de cavalerie**, **94 de longues
hampes** — alimentait pour rien une carte tenue avec soin.

Contrainte : **ce module ne se livre pas seul.** Tant qu'une décision ne le lit
pas, on n'a pas construit du brouillard, on a construit un ornement coûteux.
