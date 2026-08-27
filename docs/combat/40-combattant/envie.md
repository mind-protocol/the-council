# L'envie — couche 4

## 1. Ce que c'est

Ce qu'un homme veut **pour son compte**, contre l'ordre s'il le faut : prendre,
fuir vers un abri qu'il a repéré, achever celui-là, rejoindre son frère, arracher
la bannière.

## 2. Ce qu'elle possède

- l'**objet convoité** courant, s'il y en a un : une chose, un lieu, un homme,
  toujours **désigné**, jamais abstrait ;
- l'**envie** elle-même : un geste voulu vers cet objet, avec sa force et sa
  raison ;
- la **satiété et le renoncement** : ce qu'il a déjà obtenu, ce qu'il a cessé de
  vouloir parce qu'un autre l'a pris ou parce que c'est devenu impossible.

## 3. Ce qu'elle lit

- `30-perception` : ce qu'il voit à portée — un corps tombé, une porte ouverte,
  une enseigne, un homme qu'il connaît ;
- `40-combattant/memoire` : ses pairs, et ce qu'il a vécu récemment ;
- `40-combattant/identite` : la trempe et le métier, qui décident de ce qui tente
  cet homme-là et de ce qui ne le tente pas.

## 4. Ce qu'elle produit

Une envie, ou **rien**. Et c'est ici que se joue la règle la plus importante de
la fiche :

**La convoitise n'existe pas sans objet.** Un homme au milieu d'un champ, sans
rien de désirable dans sa perception, ne veut rien — et ce n'est pas « veut
faiblement », c'est **rien**. La couche s'abstient : elle ne rend pas une envie
de force basse, elle ne rend pas d'envie du tout.

La distinction n'est pas cosmétique. Une envie faible reste un prétendant à
l'élection et peut gagner quand tout le reste est plus faible encore ; une
abstention ne peut pas gagner. C'est la différence entre une armée qui traverse
un champ vide en ordre et une armée dont un homme sur dix part de côté sans
raison nommable.

## 5. Invariants

- **Aucune envie sans objet désigné.** Une sonde peut vérifier que toute envie
  produite cite un objet que la perception de cet homme contenait à ce battement.
- Un objet hors de la perception ne peut pas être convoité, même s'il existe.
- La force d'une envie est comparable à celle des autres couches.
- L'abstention est majoritaire, et le fait qu'elle le soit est une mesure à
  suivre : une couche 4 qui parle tout le temps est une couche 4 fausse.
- Une envie satisfaite s'éteint et ne se rallume pas sur le même objet sans un
  fait nouveau.

## 6. Ce qu'elle ne fait pas

- Elle ne fabrique **aucun objet** pour avoir quelque chose à vouloir. Pas de
  cible générique, pas de « l'ennemi » en général, pas de direction attirante.
- Elle ne juge pas si l'envie est **sage** : ni la barre de l'ordre, ni le danger,
  ni le nombre. Céder à une envie idiote est le sujet, pas un défaut.
- Elle n'a pas d'humeur de fond, pas de compteur de moral qui monterait et
  descendrait tout seul. Ce qui n'a pas de source dans la perception ou la
  mémoire n'entre pas ici.
- Elle ne s'auto-limite pas pour laisser passer l'ordre : c'est l'arbitre qui
  tranche, et il a une barre pour ça.

## 7. Ce que l'ancien moteur faisait mal ici

**Non mesuré.** Aucun relevé ne dit à quelle fréquence cette couche produisait
une envie, ni si elle rendait une force basse là où elle aurait dû s'abstenir.
Le seul fait connexe est indirect : quand une couche manquait, l'arbitre traitait
son absence comme une valeur — et ce piège-là vaut pour la couche 4 autant que
pour la 3.

Les deux sondes à poser dès le premier jour : la part des envies citant un objet
réellement perçu (attendu : 100 %), et la part des battements où la couche
s'abstient (attendu : très haut, hors mêlée et hors pillage).
