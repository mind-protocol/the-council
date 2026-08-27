# Le geste

## 1. Ce que c'est

**L'unique sortie d'un combattant vers le monde** : une intention corporelle,
avec sa raison. Le monde décide de ce qui arrive.

## 2. Ce qu'il possède

- l'**intention** du battement : ce que l'homme essaie de faire de ses jambes et
  de ses bras — la direction, l'allure voulue, la cible s'il y en a une ;
- sa **raison** : la couche qui a été élue, la force retenue, la barre franchie,
  reprises telles quelles de la trace d'arbitrage ;
- rien de plus. Le geste est un message, pas un état.

## 3. Ce qu'il lit

`40-combattant/arbitre` : l'élection des jambes et celle des bras, et la trace
qui les explique. Il traduit deux mots de répertoire en une intention que le
monde sait recevoir.

## 4. Ce qu'il produit

Un geste par homme et par battement, remis à `20-monde`. Le monde applique
l'accélération, teste le bâti, résout les collisions, et décide de la position et
de l'effet résultants. **L'homme peut vouloir et ne pas obtenir** — c'est ce qui
rend une bousculade, une venelle trop étroite ou une masse trop dense racontables
sans une ligne de code qui les raconte.

## 5. Invariants

- **Un seul canal.** Aucune autre voie ne va d'un combattant vers le monde : ni
  raccourci de déroute, ni cas particulier de porte, ni branche de mêlée.
- Tout geste porte sa raison, et cette raison est **lue** sur l'arbitrage, jamais
  réécrite ici. Une sonde peut comparer la couche citée par le geste à la couche
  élue : l'écart attendu est zéro.
- Un geste est une **intention**, jamais un résultat. Rien dans ce module ne dit
  que l'homme a bougé, ni de combien.
- Un homme vivant émet un geste à chaque battement, fût-ce celui de ne rien
  faire.

## 6. Ce qu'il ne fait pas

- Il **n'écrit aucune position, aucune vitesse, aucune orientation**. C'est
  l'invariant le plus dur du dossier : une seule fonction au monde écrit une
  position, et elle n'est pas ici.
- Il **ne teste rien** : ni le mur devant, ni le vide, ni la portée de l'arme. Un
  geste absurde part comme les autres et se fait refuser.
- Il ne résout **aucun coup** : la blessure, la mort et l'effet du fer sont
  écrits par le monde.
- Il ne **négocie pas** : il n'a pas de repli à proposer quand le premier geste
  est refusé. Un refus revient par la perception, au battement suivant, et c'est
  aux couches d'en tirer quelque chose.
- Il ne s'adresse à personne d'autre qu'au monde : ni à l'unité, ni à un pair, ni
  à un chef. Parler et signaler ne sont pas des gestes de ce module.

## 7. Ce que l'ancien moteur faisait mal ici

**Non mesuré pour ce module.** Aucun relevé ne compte les chemins par lesquels un
homme atteignait le monde, ni la part des gestes portant une raison lue sur
l'élection.

Deux faits mesurés ailleurs le cernent toutefois. L'arbitre était consulté à la
236e ligne d'une cascade de 855 avec **38 sorties anticipées** : ce qui atteignait
le monde avant lui l'atteignait donc **sans geste et sans raison**. Et la pensée
affichée était posée depuis **56 endroits**, dont **46 nommaient la branche de
code qui venait de déplacer l'homme** — ce qui suppose autant de branches capables
de le déplacer.

Le canal unique n'est pas une élégance : c'est le seul moyen de rendre la
première mesure possible. Tant qu'on ne peut pas compter les chemins, on ne peut
pas prouver qu'il n'y en a qu'un.
