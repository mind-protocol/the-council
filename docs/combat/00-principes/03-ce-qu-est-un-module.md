# Ce qu'est un module

## La définition

Un module est **une responsabilité, un fichier, une fabrique**. Il déclare sa
couche, ce qu'il reçoit, ce qu'il rend. Il ne pose aucune globale et ne connaît
aucun appelant.

## Sa taille

**Un module tient dans une tête.** L'ordre de grandeur visé est deux à trois
cents lignes ; au-delà de cinq cents, il faut soit le découper, soit écrire
pourquoi il ne se découpe pas.

Ce n'est pas une élégance : c'est la seule barrière qui ait jamais tenu contre un
fichier de onze mille lignes. Et elle ne tient que si une sonde la mesure et
qu'un dépassement se voie — sinon elle rejoint la table d'autorité au cimetière
des bonnes intentions.

## Ce qu'il reçoit

Tout ce qu'il ne peut pas importer : les mesures dont il a besoin, les services
des couches inférieures, et de quoi signaler vers le haut. Reçus **à la
création**, jamais cherchés à l'exécution.

**Un module qui reçoit l'état complet de la simulation n'a pas de frontière.**
C'est ce que faisaient les modules extraits du moteur précédent : ils recevaient
tout, avec le droit d'écrire partout. Un module reçoit la tranche qui le
concerne, et rien d'autre.

## Ce qu'il rend

Un objet de fonctions, dont chacune est une question ou une intention. Aucun
champ mutable exposé, aucun objet interne rendu par référence à qui pourrait
l'écrire.

## Ce qu'il n'a pas le droit de faire

- poser une globale ;
- garder un état qui appartient à un autre module ;
- appeler quoi que ce soit d'une couche supérieure ou égale ;
- tirer au hasard sans passer par l'urne du socle ;
- écrire dans le journal en le connaissant — il **signale**, quelqu'un écoute.

## Trois pièges de plateforme, payés comptant

Aucun n'est théorique : chacun a coûté une erreur de chargement ou une mesure
fausse.

**L'ordre de déclaration ne pardonne pas.** Une valeur lue avant d'être
initialisée fait tomber le moteur *au chargement*, avant qu'une bataille
commence. Un module ne doit donc jamais dépendre d'un ordre d'évaluation subtil :
ce qu'il reçoit doit être prêt, ou reçu paresseusement — c'est-à-dire enveloppé,
résolu au premier appel.

**Une liste de chargement tenue à la main diverge.** Il y en avait huit. Deux
avaient dérivé sans que personne le sache, et une pièce manquait au jeu sans
manquer aux bancs — donc les mesures jugeaient un moteur que le joueur ne voyait
pas. **Un seul manifeste**, lu par tous les consommateurs, sans exception.

**Un fichier servi au navigateur est mis en cache par son URL.** Changer le code
sans changer l'URL sert l'ancien code, et une mesure en ligne de commande ne le
voit jamais — elle lit le disque. Ce qui est servi porte une empreinte qui change
avec son contenu, et cette empreinte se dérive, elle ne se tient pas à la main.
