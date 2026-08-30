# L'interprétation — couche 3

## 1. Ce que c'est

La manière dont **cet homme-là** tient l'ordre qu'il a reçu. Elle ne conduit pas
les jambes : elle fixe la **barre** que les autres prétendants doivent franchir
pour prendre la main.

## 2. Ce qu'elle possède

- la **barre** courante : un seuil comparable aux forces des quatre couches ;
- la **lecture de l'ordre** : ce que cet homme comprend qu'on lui demande, ce
  qu'il s'estime autorisé à faire au passage, et ce qu'il refuse ;
- la **tenue** : à quel point l'ordre le retient encore, compte tenu de son âge,
  de la distance au chef, et de ce qu'il a vu depuis.

## 3. Ce qu'elle lit

- `40-combattant/memoire` : l'ordre reçu, sa date, de qui il vient, et où le
  chef a été vu pour la dernière fois ;
- `40-combattant/identite` : la trempe et le métier, qui décident si un homme
  tient un ordre serré ou à sa façon ;
- `30-perception` : ce qui, autour de lui, rend l'ordre encore applicable ou déjà
  absurde.

## 4. Ce qu'elle produit

Une barre, et une phrase qui la justifie. Une barre haute veut dire : rien ne
détourne cet homme de ce qu'on lui a dit, sauf une raison forte. Une barre basse
veut dire : il tient l'ordre de loin, et le premier prétendant venu l'emporte.

**L'absence d'ordre est un cas explicite**, pas un cas par défaut. Un homme sans
ordre reçu rend une barre nulle, et cette nullité doit être *dite* — pas obtenue
en creux parce que la couche n'a pas tourné.

## 5. Invariants

- **Disponible pour tout homme qui a de quoi la calculer.** Si un homme porte un
  ordre et un chef, sa barre existe à ce battement. Une sonde compare le nombre
  d'hommes ayant les entrées au nombre d'hommes ayant la sortie : l'écart attendu
  est zéro.
- La barre est sur la même échelle que les forces des quatre couches, sinon
  l'arbitre compare des choses qui ne se comparent pas.
- **Barre nulle et barre absente sont distinctes**, et l'arbitre doit les
  distinguer.
- La lecture de l'ordre ne dépend d'aucune position réelle du chef : seulement de
  la dernière position **connue**.

## 6. Ce qu'elle ne fait pas

- Elle **ne propose aucun geste**. Elle n'a ni mot de jambes ni mot de bras ; elle
  ne peut pas gagner l'élection, seulement la rendre plus difficile aux autres.
- Elle ne **modifie pas l'ordre** ni ne le remplace : elle le comprend, et sa
  compréhension peut être fautive. Réécrire un ordre est le travail du
  commandement, deux couches plus haut, et l'homme n'y touche pas.
- Elle ne va pas chercher l'ordre à la source. Ce qui n'est pas dans sa mémoire
  n'existe pas pour lui, même si l'unité, elle, le sait.
- Elle n'arbitre pas et ne se déclare pas gagnante.

## 7. Ce que l'ancien moteur faisait mal ici

Elle n'était calculée que pour **135 hommes sur 239**, alors que **239 sur 239**
avaient tout ce qu'il fallait pour la calculer. La cause n'était pas un manque de
données : son calcul était enfoui à la **680e ligne d'une cascade de 855**, et
seuls les hommes dont le battement allait jusque-là l'obtenaient. Une couche de
délibération dépendait de la profondeur atteinte dans un fichier.

L'effet était pire que le manque. L'arbitre rend une barre de **zéro** quand
cette couche est absente, contre **0,50** pour un ordre ordinaire : **43 % de
l'armée était donc arbitrée comme n'ayant reçu aucun ordre, alors que tous en
avaient un.**

Après réparation — la couche calculée pour tous ceux qui ont les entrées, et non
pour ceux qui atteignent la ligne — la barre était disponible pour **97,9 %** des
hommes. La dispersion au chef (P90) tombait de **92,5 m à 68,8 m**, les vintaines
groupées passaient de **90 % à 97 %**, et l'on voyait les **premières déroutes
réelles : 6 contre 0**.

Une armée entière tenait mal parce qu'une couche était trop bas dans un fichier.
C'est l'argument le plus cher de ce dossier en faveur de la règle de dépendance.
