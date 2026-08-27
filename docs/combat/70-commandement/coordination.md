# Coordination

## 1. Ce que c'est

Ce qui se passe quand deux chefs de même rang se trouvent en mesure de se
parler : ce qu'ils échangent, ce qui s'enregistre chez chacun, et ce qui peut
être réalloué entre eux sans passer par le dessus.

## 2. Ce qu'il possède

- **La rencontre** : deux chefs de même rang, un canal ouvert entre eux, un
  instant, une durée. Sans canal, il n'y a pas de coordination — seulement deux
  chefs qui s'ignorent.
- **Ce qui s'échange**, et rien d'autre :
  - **des faits** — ce que chacun croit, avec son âge, sa source, sa confiance ;
  - **des intentions déclarées** — ce que chacun compte faire et quand ;
  - **des demandes** — un appui, une couverture de flanc, un délai ;
  - **des engagements** — ce que l'un promet à l'autre, avec une échéance.
- **L'engagement**, qui est la seule chose que ce module crée en propre : une
  obligation datée entre deux chefs, opposable, et qui peut être tenue ou rompue.
- **La réallocation locale** : ce que deux chefs de même rang peuvent se
  transférer d'eux-mêmes — un corps prêté pour une durée bornée, la charge d'un
  seuil, la responsabilité d'un flanc. La borne est écrite : au-delà, c'est une
  affaire de couche 80.
- **La trace de la rencontre**, chez chacun des deux, et non dans un objet commun.

## 3. Ce qu'il lit

- Du socle : horloge, identité.
- De l'unité : quels corps existent chez chacun, qui les mène.
- De la transmission : le canal — c'est lui qui dit si les deux peuvent se
  parler, ce que le moyen employé permet de faire passer, et combien ça coûte.
- Des croyances, de l'estimation et de la décision de **chacun des deux
  séparément**.

Il ne lit **aucun état réel adverse**. Et il ne lit **pas la carte de l'autre
chef directement** : ce qui passe de l'un à l'autre passe par des messages, avec
leurs déformations et leur âge. Deux chefs qui se parlent ne fusionnent pas leurs
cartes ; ils s'en racontent des morceaux.

## 4. Ce qu'il produit

- **Des faits reçus** chez chacun, à intégrer dans sa carte comme n'importe quel
  rapport — avec la confiance due à la source, qui n'est pas maximale sous
  prétexte que c'est un pair.
- **Des engagements** enregistrés des deux côtés, avec leur échéance.
- **Une réallocation effective**, quand elle est dans les bornes : un corps change
  de chef, et les deux le savent.
- **Le désaccord**, qui est une sortie normale : deux chefs peuvent se quitter
  sans engagement, chacun sur son estimation, et cela s'enregistre.

## 5. Invariants

- **Aucune fusion de cartes.** Une sonde extérieure vérifie qu'après une
  rencontre, les deux cartes restent différentes.
- Ce qui est reçu d'un pair porte la confiance d'un rapport, jamais celle d'une
  observation propre, et vieillit depuis la date d'observation d'origine — pas
  depuis la rencontre.
- **Un engagement n'oblige à rien mécaniquement.** Il est enregistré ; un chef
  peut le rompre, et la rupture est un fait que l'autre apprendra — ou pas.
- Toute réallocation est bornée en durée et en volume, et laisse une trace des
  deux côtés. Un corps a toujours exactement un chef.
- La coordination ne crée pas de rang. Deux chefs de même rang restent de même
  rang après s'être parlé.
- Un chef isolé, sans canal, décide seul et sans pénalité artificielle : la
  coordination est un gain possible, pas un dû.

## 6. Ce qu'il ne fait pas

- **Il ne commande pas.** Aucun des deux ne donne d'ordre à l'autre ; ce qui
  ressemblerait à un ordre est une demande, refusable.
- **Il n'arbitre pas les désaccords.** Deux chefs qui ne s'entendent pas ne sont
  pas départagés ici ; l'arbitrage remonte, et remonter est une affaire de
  transmission et de couche 80.
- **Il ne synchronise pas les décisions.** Chacun redécide chez lui, avec ce
  qu'il a reçu.
- **Il ne crée pas de canal.** Si les deux ne peuvent pas se parler, il ne se
  passe rien — et c'est la situation ordinaire d'une bataille.
- **Il ne réalloue pas au-delà de sa borne**, et ne touche jamais à la mission
  générale.
- **Il ne garantit pas la réciprocité.** Un chef peut donner un fait et n'en
  recevoir aucun.

## 7. Ce que l'ancien moteur faisait mal ici

Le trafic entre pairs existait, et en volume : **478 communications entre chefs**
sur une seule bataille, transportant du renseignement typé — **41 observations de
cavalerie**, **94 de longues hampes**. Rien ne manquait au canal.

Ce qui manquait est l'objet même de cette fiche : **aucune de ces 478
communications n'a jamais changé un ordre**. Sur quinze chefs, **zéro ordre
adapté** ; sur la bataille entière, **deux changements d'ordre d'unité**, posés
par le scénario. Deux chefs qui se parlaient échangeaient donc des lignes de
journal, jamais un engagement, jamais un corps, jamais une intention opposable.

Trois choses n'ont **pas** été mesurées et le seront cette fois : la part des
rencontres qui produisent un engagement, la part des engagements tenus, et
l'effet d'une réallocation locale sur l'issue. Aucune n'avait d'objet dans
l'ancien moteur, faute d'engagement et faute de réallocation.

La contrainte de construction qui en découle est la même que partout dans cette
couche : **on ne livre pas la coordination avant que la décision consomme ce
qu'elle produit.** Sinon on obtient 478 communications de plus, et le même zéro.
