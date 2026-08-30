# Décision

## 1. Ce que c'est

Le moment où un chef retient une option, dit pourquoi, en fait un ordre, et fixe
l'heure à laquelle il réexaminera.

## 2. Ce qu'il possède

- **Le choix** : l'option retenue, son paramétrage, l'ordre qu'elle produit.
- **La justification** : les grandeurs qui ont pesé, dans quel sens, et les motifs
  de rejet des écartées. Sans eux, on ne critiquera pas la décision.
- **La pondération du chef** : ce à quoi il tient — préserver ses hommes, gagner
  du terrain, obéir à la lettre. C'est ici, et seulement ici, que deux chefs
  divergent devant la même situation.
- **L'heure du prochain examen**, toujours fixée, jamais absente.
- **Les conditions de réexamen anticipé** : les faits qui rouvrent la décision
  avant l'heure — contact, perte d'un appui, ordre nouveau.
- **La trace complète** : croyances, estimation, options, projections, rejets,
  choix, raison, prochain examen. Produite ici, lue par la couche 90. La décision
  de ne rien changer s'y enregistre comme les autres.

## 3. Ce qu'il lit

Du socle : horloge, identité. De la transmission : l'ordre courant reçu et les
canaux ouverts — un ordre qu'aucun canal ne peut porter n'est pas une décision.
Les croyances, l'estimation, les options et les projections du même chef.

Il ne lit **rien de l'état réel adverse** et **aucune croyance d'un autre chef**.

## 4. Ce qu'il produit

- **Un ordre** rédigé dans le vocabulaire de la couche 60, remis à un canal.
- **La trace de décision**, et **l'heure du prochain examen**, opposable : on
  vérifie qu'elle a été tenue.

## 5. Invariants

- **Toute décision fixe une heure de réexamen** ; une sonde refuse le contraire.
- **Un commandant n'attend jamais sans raison quand son ordre courant est fini.**
  Ordre accompli, périmé ou impossible : il réexamine dans le battement. C'est le
  défaut silencieux le plus coûteux d'un moteur de commandement.
- Toute décision cite un élément de la carte du chef ; sans croyance, c'est un
  ordre venu d'ailleurs.
- Le nombre de réexamens par minute est borné : qui redécide à chaque battement
  ne commande plus, il oscille.
- Mêmes entrées, même décision ; aucun tirage. Tout changement d'ordre est
  attribuable à une cause nommée : fait reçu, échéance, ordre supérieur.

## 6. Ce qu'il ne fait pas

- **Il ne transmet pas** : il remet l'ordre à un canal, sans garantie, et **ne
  vérifie pas l'exécution** — le chef l'apprendra par un fait, ou pas.
- **Il ne consulte pas la mission d'armée** : ce qui vient de 80 est un ordre reçu.
- **Il ne se déjuge pas sans cause** : une décision tient jusqu'à son échéance ou
  jusqu'au fait qui la rouvre ; l'hésitation continue est un défaut mesurable.

## 7. Ce que l'ancien moteur faisait mal ici

Il n'y avait pas de décision : **zéro ordre adapté sur quinze chefs**, **deux
changements d'ordre d'unité** sur une bataille entière — aux instants où le
scénario les posait — et **un seul changement littéral** après l'ouverture. Ni
réexamen, ni échéance, ni trace.

Le cas à garder en mémoire est celui de l'unité qui avait reçu « marchez sur
cette porte » : elle a gardé cet ordre **inchangé du début à la fin, et reculé
quand même**. La faute n'était pas la décision, c'était le mouvement — une
décision juste ne garantit pas un comportement, et l'on ne diagnostique rien tant
qu'on ne sépare pas les deux.

**Le piège de mesure, enfin, est exemplaire.** Une sonde exigeait qu'un ordre soit
postérieur à la première observation typée. Mesuré : les ordres tombaient à **0 et
180 secondes**, la première croyance typée à **205 secondes**. La sonde était
**structurellement inatteignable** — aucune amélioration du moteur n'aurait pu la
satisfaire — **et elle ne le disait pas** : elle rendait un échec, comme un moteur
défaillant.

Ce qu'on en tire : une sonde sur la décision doit vérifier qu'elle est
**atteignable dans la condition mesurée** avant de juger le moteur — soit ici
qu'un examen existe **après** l'arrivée du premier renseignement. C'est ce que
garantit l'invariant sur l'heure de réexamen, et c'est pourquoi il est en tête.
