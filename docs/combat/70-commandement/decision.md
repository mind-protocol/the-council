# Décision

## 1. Ce que c'est

Le moment où un chef retient une option, dit pourquoi, en fait un ordre, et fixe
l'heure à laquelle il réexaminera.

## 2. Ce qu'il possède

- **Le choix** : l'option retenue, son paramétrage, et l'ordre qu'elle produit.
- **La justification** : les grandeurs projetées qui ont pesé, dans quel sens, et
  les motifs de rejet des options écartées. Une décision sans motifs de rejet est
  une décision qu'on ne saura pas critiquer.
- **La pondération du chef** : ce à quoi celui-ci tient — préserver ses hommes,
  gagner du terrain, obéir à la lettre, ne pas se découvrir. C'est ici, et
  seulement ici, que deux chefs devant la même situation divergent. Elle dérive
  de l'identité du chef, elle ne se tire pas au hasard.
- **L'heure du prochain examen**, toujours fixée, jamais absente.
- **Les conditions de réexamen anticipé** : les faits qui, s'ils arrivent avant
  l'heure, rouvrent la décision — le contact, la perte d'un appui, un ordre
  nouveau, une croyance démentie.
- **La trace complète** : croyances utilisées, estimation, options, projections,
  rejets, choix, raison, prochain examen. Elle est produite ici et lue par la
  couche 90.

## 3. Ce qu'il lit

- Du socle : horloge, identité.
- De la transmission : l'ordre courant reçu, les canaux ouverts — un ordre décidé
  qu'aucun canal ne peut porter n'est pas une décision.
- Des croyances, de l'estimation, des options et des projections du même chef.

Il ne lit **rien de l'état réel adverse** et **aucune croyance d'un autre chef**.

## 4. Ce qu'il produit

- **Un ordre** rédigé dans le vocabulaire de la couche 60, remis à un canal.
- **La trace de décision.**
- **L'heure du prochain examen**, opposable : on peut vérifier qu'elle a été
  tenue.
- **La décision de ne rien changer**, qui est une décision et s'enregistre comme
  telle, avec sa raison et son échéance.

## 5. Invariants

- **Toute décision fixe une heure de réexamen.** Une sonde extérieure refuse
  toute décision sans échéance.
- **Un commandant n'attend jamais sans raison quand son ordre courant est fini.**
  Ordre accompli, périmé ou impossible : il réexamine dans le battement, il ne
  reste pas en place par défaut. C'est le défaut silencieux le plus coûteux d'un
  moteur de commandement, et il ne se voit que si on le mesure.
- Toute décision cite au moins un élément de la carte du chef. Une décision qui
  ne s'appuie sur aucune croyance est un ordre venu d'ailleurs.
- Mêmes entrées, même décision. Aucun tirage : la variété vient des pondérations
  dérivées de l'identité.
- Le nombre de réexamens par chef et par minute est borné et mesuré : un chef qui
  redécide à chaque battement ne commande plus, il oscille.
- Un changement d'ordre est attribuable à une cause nommée : un fait reçu, une
  échéance, un ordre supérieur, l'accomplissement du précédent.

## 6. Ce qu'il ne fait pas

- **Il ne transmet pas.** Il remet l'ordre à un canal et n'a aucune garantie
  qu'il arrive.
- **Il ne vérifie pas l'exécution.** Ce que l'unité fait de l'ordre appartient
  aux couches basses ; le chef l'apprendra par un fait, ou pas.
- **Il ne corrige pas une croyance parce qu'elle a mené à une mauvaise décision.**
- **Il ne consulte pas la mission d'armée** : ce qui vient de la couche 80 lui
  parvient comme un ordre reçu, par la transmission, comme tout le reste.
- **Il ne décide pas pour un autre chef.**
- **Il ne se déjuge pas sans cause.** Une décision tient jusqu'à l'échéance ou
  jusqu'à un fait qui la rouvre ; l'hésitation continue n'est pas une prudence,
  c'est un défaut mesurable.

## 7. Ce que l'ancien moteur faisait mal ici

Il n'y avait pas de décision : **zéro ordre adapté sur quinze chefs**, **deux
changements d'ordre d'unité** sur une bataille entière — aux instants exacts où
le scénario les posait — et **un seul changement d'ordre littéral** après
l'ouverture. Ni réexamen, ni échéance, ni trace.

Le cas à garder en mémoire est celui de l'unité qui avait reçu « marchez sur
cette porte » : elle a gardé cet ordre **inchangé du début à la fin, et reculé
quand même**. La faute n'était pas la décision, c'était le mouvement. Une
décision juste n'est donc pas une garantie de comportement, et l'on ne diagnostique
rien tant qu'on ne sépare pas les deux.

**Le piège de mesure, enfin, et il est exemplaire.** Une sonde exigeait qu'un
ordre soit postérieur à la première observation typée. Mesuré : les ordres
tombaient à **0 et 180 secondes**, la première croyance typée à **205 secondes**.
La sonde était donc **structurellement inatteignable** — aucune amélioration du
moteur n'aurait pu la satisfaire — **et elle ne le disait pas** : elle rendait un
échec, comme un moteur défaillant l'aurait fait.

Ce qu'on en tire pour cette fiche : une sonde sur la décision doit vérifier
qu'elle est **atteignable dans la condition mesurée** avant de juger le moteur.
Ici, cela veut dire qu'un examen de décision doit exister **après** l'arrivée du
premier renseignement — c'est précisément ce que l'invariant sur l'heure de
réexamen garantit, et c'est pour cela qu'il est en tête de la liste.
