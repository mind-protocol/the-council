# Ce qu'est un module

## La définition

Un module est **une responsabilité, un fichier, une fabrique**. Il déclare sa
couche, ce qu'il reçoit, ce qu'il rend. Il ne pose aucune globale et ne connaît
aucun appelant.

## Sa nature — cinq, et pas d'autres

Tous les modules n'ont pas la même forme, et confondre leurs formes est le
premier pas vers un module qui grossit. Chaque fiche déclare la sienne en tête.

| nature | possède un état ? | décide ? | forme concrète |
|---|---|---|---|
| **barème** | non — des constantes et des règles de lecture | non | des fonctions pures ; deux appels identiques rendent la même chose, toujours |
| **service** | non | non | des fonctions pures aussi, mais qui *calculent* au lieu de consulter (une route, une trajectoire) |
| **registre** | oui, et il en est l'écrivain unique | non | un état privé, des lectures, et des intentions qu'on lui remet |
| **acteur** | oui | oui — il tranche, et sa décision est traçable | un état privé, une fonction de battement, une trace |
| **sonde** | non | non | lit tout, n'écrit rien, ne peut être lue par personne |

Les conséquences sont dures et servent tous les jours :

- **Un barème et un service se testent sans monde et sans homme.** Aucun montage,
  aucune bataille : on appelle, on compare. C'est pour ça qu'on en veut le plus
  possible, et qu'on descend une règle d'un acteur vers un barème dès qu'elle
  cesse d'avoir besoin de savoir *qui* pose la question.
- **Un registre n'a pas d'avis.** S'il se met à choisir, il est devenu acteur et
  la fiche ment.
- **Un acteur ne se teste que par sa trace.** Il en écrit une à chaque décision,
  sinon on ne saura pas pourquoi il a fait ce qu'il a fait — c'est la faute qui a
  coûté le plus cher au moteur précédent.
- **Une sonde ne remonte pas dans le moteur.** Elle observe entre deux battements
  et ne s'y insère jamais, sinon elle mesure sa propre présence.

Une nature qu'on n'arrive pas à choisir est le signe d'un module qui en contient
deux.

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
