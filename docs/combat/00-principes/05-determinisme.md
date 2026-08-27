# Le déterminisme

**À condition identique et graine tenue, la bataille est exactement la même.**
Pas « à peu près » : la même, au dernier mort et au dernier fait.

## Pourquoi c'est non négociable

Sans lui, aucune mesure ne prouve rien. On ne peut ni comparer un avant et un
après, ni rejouer un défaut, ni distinguer une amélioration d'un tirage heureux.
Tout le reste de ce dossier — les sondes, l'étalon, les traces — repose dessus.

## Ce que ça impose

**Une seule urne**, dans le socle. Aucun module ne tire ailleurs, et surtout pas
via un générateur de plateforme.

**L'ordre des tirages fait partie du résultat.** Déplacer un tirage, en ajouter
un, ou en sauter un dans une branche rebat tout ce qui suit. Un changement qui se
croit neutre mais déplace un tirage ne l'est pas — et c'est une raison suffisante
pour reporter une réorganisation qui, autrement, semblait gratuite.

**Aucune horloge de plateforme dans la simulation.** Le temps de bataille est un
compteur de pas, pas une lecture de l'heure. Rien qui dépende de la vitesse de la
machine, de l'ordre d'arrivée d'un réseau, ou d'une itération sur une structure
dont l'ordre n'est pas garanti.

**Ce qui dérive d'une identité stable ne consomme pas l'urne.** Le biais d'un
homme dans son rang, sa main dominante, sa trempe : dérivés de son identifiant,
donc rejouables sans tirage. C'est ce qui permet de donner de la variété à deux
mille corps sans rendre la nuit irreproductible.

## La conséquence pratique la plus utile

**Une extraction de code doit rendre l'égalité exacte.** Si l'on déplace du code
sans intention de changer le comportement et que la bataille diffère, c'est qu'on
a changé quelque chose sans le savoir.

C'est le seul filet qui rende un démantèlement sûr. Il a tenu quatre fois de
suite sur le moteur précédent, et il a attrapé chaque fois ce qu'une relecture
n'aurait pas vu.

## Le piège à connaître

Un déterminisme vérifié dans une seule session ne prouve pas le déterminisme. Il
faut les deux :

- **deux cuissons dans la même session** — l'urne se ressème correctement ;
- **une comparaison à un étalon posé une autre fois** — rien ne dépend de
  l'environnement, de l'heure, ni d'un fichier lu en direct.

Et la condition doit être close : si la simulation lit une donnée du monde
extérieur qui bouge — une heure de jeu, un état de partie —, la même commande ne
cuit pas la même nuit deux jours de suite, et l'étalon ne veut plus rien dire.
