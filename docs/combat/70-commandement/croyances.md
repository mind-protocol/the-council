# Croyances

## 1. Ce que c'est

La carte que porte un chef dans sa tête, à son échelle, avec ses trous déclarés —
la seule chose qu'il ait le droit de consulter pour décider.

## 2. Ce qu'il possède

Une carte par commandant, et personne d'autre ne l'écrit. Elle porte :

- **Les positions amies connues** : ses propres corps, leur dernière position
  rapportée, leur effectif estimé, leur état apparent. Il ne les voit pas mieux
  que l'ennemi s'il ne les voit pas.
- **Les positions ennemies possibles** : non pas un point, mais **une zone** où
  un corps est susceptible de se trouver, qui s'élargit avec le temps écoulé
  depuis la dernière observation.
- **Les effectifs en intervalles**, jamais en nombres. « Entre trois et six
  cents » est une croyance ; « quatre cent douze » est une omniscience.
- **Les signatures observables** : ce qu'on a vu et qui a un sens tactique — des
  hampes longues, de la poussière, une bannière, un bruit de sabots, une densité,
  une allure. On croit une signature avant de croire une nature.
- **Les zones explicitement inconnues** : les endroits d'où rien n'est venu. Ce
  troisième état est aussi important ici que sur le terrain — une carte sans
  trous déclarés est une carte qui ment par silence.
- **L'âge et la confiance** de chaque élément : quand, par qui, par quel canal, à
  quelle distance, et combien on y croit maintenant.
- **L'échelle** : un chef de bataille croit des corps, pas des hommes. Une croyance
  plus fine que son échelle est un défaut.

## 3. Ce qu'il lit

- Du socle : horloge, identité, mesures.
- Du monde : le terrain, pour savoir ce qui est visible depuis où il est, et pour
  que ses zones d'incertitude respectent le relief.
- De la perception : ce que lui-même perçoit, avec sa portée et ses obstacles.
- De l'unité : l'état de ses propres corps, quand ils sont à portée de vue.
- De la transmission : les messages **remis** — jamais ceux qui sont en route,
  perdus, ou dans la version d'origine.

**Il ne lit jamais l'état réel du camp adverse.** Ni ses positions, ni ses
effectifs, ni ses ordres, ni sa cohésion. C'est l'unique règle qui, si elle
tombe, rend tout le reste de la couche 70 décoratif.

## 4. Ce qu'il produit

- **Sa carte à cet instant**, avec l'âge et la confiance de chaque élément.
- **Ce qu'il croit d'un endroit** : occupé, libre, ou inconnu — trois réponses.
- **Ce qu'il ne sait pas** : la liste de ses trous, exploitable telle quelle par
  l'estimation et la décision.
- **L'intégration d'un fait** : la carte après qu'un fait est arrivé, et la trace
  de ce qui a changé.

## 5. Invariants

- **Une croyance ne change que par un fait** : perçu, reçu par un message remis,
  ou déduit d'un raisonnement lui-même enregistré. Jamais parce que le moteur
  sait la chose.
- Tout effectif est un intervalle. Une sonde extérieure refuse tout effectif
  ennemi porté comme un nombre exact.
- Toute position perdue de vue reste **là où on l'a vue**, avec sa date, et son
  incertitude croît ; elle ne suit pas la position réelle.
- La confiance décroît avec le temps, à une vitesse qui dépend de la source.
- Une sonde extérieure vérifie qu'aucun commandant ne croit un corps qu'aucun
  fait ne lui a signalé, et qu'il ne voit pas à travers un mur.
- Deux commandants du même camp ont deux cartes différentes. L'identité de leurs
  cartes est un défaut, pas une économie.

## 6. Ce qu'il ne fait pas

- **Il ne déduit rien.** Un rapport de force, une menace, une intention prêtée à
  l'ennemi : c'est l'estimation, et elle est ailleurs.
- **Il ne décide rien** et ne recommande rien.
- **Il ne se corrige pas tout seul.** Une croyance démentie par les faits reste
  fausse tant qu'un fait ne l'a pas remplacée — et un chef peut s'entêter.
- **Il ne fusionne pas les cartes du camp.** Il n'existe pas de carte d'état-major
  omnisciente ; ce qu'un chef sait passe par un message comme tout le reste.
- **Il ne comble pas ses trous par vraisemblance.** Un endroit inconnu reste
  inconnu ; on peut décider d'aller voir, pas de supposer.
- **Il n'oublie pas silencieusement.** Une croyance trop vieille est marquée
  telle, elle ne s'efface pas.

## 7. Ce que l'ancien moteur faisait mal ici

**C'est le seul endroit de ces deux couches où l'ancien moteur tenait.** Les
croyances étaient **signées, datées, avec une confiance qui décroît selon la
source**, et une sonde extérieure confirmait qu'**un chef ne voyait pas à travers
les murs**. La discipline de perception était réelle, pas déclarative.

La leçon n'est donc pas de refaire ce module autrement, mais de savoir ce qu'il ne
suffit pas de faire. Ces croyances justes n'avaient **aucun consommateur** : le
seul module qui en déduisait quelque chose écrivait un champ que personne ne
lisait, et sur quinze chefs, **zéro** ordre n'a jamais changé à cause d'une
croyance. Un renseignement abondant — **41 observations typées de cavalerie**,
**94 de longues hampes** — alimentait une carte tenue avec soin, pour rien.

Contrainte pour la reconstruction : **ce module ne se livre pas seul.** Tant
qu'une décision ne le lit pas, on n'a pas construit du brouillard, on a construit
un ornement coûteux.
