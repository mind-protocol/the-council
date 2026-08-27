# Le brouillard

**Nul acteur ne lit ce qu'il n'a pas perçu.** C'est la règle qui sépare une
simulation d'un tableau de bord, et c'est celle qu'il est le plus facile de
trahir sans s'en apercevoir.

## Ce qu'elle interdit

- Un combattant ne connaît pas la position d'un ennemi qu'il n'a pas vu.
- Un chef ne lit pas l'état réel du camp adverse. Il lit **ses croyances**, qui
  peuvent être fausses, vieilles, ou héritées d'un rapport déformé.
- Un module de décision ne consulte jamais l'état global. Il consulte la mémoire
  de l'acteur qui décide.
- Une unité ne sait pas qu'une autre a rompu, sauf si quelqu'un l'a vu ou le lui
  a dit.

## Ce qui fait changer une croyance

Une croyance ne change que par un **fait** : vu, entendu, touché, rapporté, ou
déduit d'un raisonnement lui-même enregistré. Jamais parce que le moteur, lui,
sait la chose.

Un fait porte toujours : qui l'a produit, quand, où, par quel sens, avec quelle
confiance, et — quand il s'agit d'un effectif — **un intervalle et non un
nombre**. Un homme qui voit une colonne n'en connaît pas le compte. Un fait sans
intervalle est une omniscience déguisée, et c'est le premier endroit où le
brouillard se trahit.

## Le vieillissement

Une croyance perd de sa valeur avec le temps, à une vitesse qui dépend de sa
source : ce qu'on a vu soi-même tient plus longtemps que ce qu'on nous a
rapporté. Une position perdue de vue reste **là où on l'a vue**, avec sa date, et
non là où elle est réellement.

## Ce que le brouillard coûte, et pourquoi c'est le sujet

Un acteur qui décide sur des croyances fausses prend des décisions fausses **et a
raison de les prendre**. C'est ce qui rend une bataille racontable : un chef qui
n'a pas reçu le message agit sur ce qu'il croyait hier, et il n'a pas tort.

## Le défaut à ne pas reproduire

L'ancien moteur tenait bien la règle **côté perception** : les croyances étaient
signées, datées, avec une confiance qui décroît, et une sonde confirmait qu'un
chef ne voyait pas à travers les murs.

Ce qui manquait, c'est un **consommateur**. Le seul module qui déduisait une
posture depuis les croyances écrivait son résultat dans un champ que personne ne
lisait. Et aucun chemin n'existait pour qu'un chef change son ordre à partir d'un
renseignement : tous les ordres venaient de l'extérieur du moteur.

Mesuré : sur quinze chefs, **zéro** ordre adapté à une observation, alors que le
renseignement circulait bien — quarante et une observations typées transmises,
plus de quatre cents communications.

**Le brouillard ne sert à rien si rien ne décide au travers.** Une croyance qui
n'alimente aucune décision est un ornement coûteux.
