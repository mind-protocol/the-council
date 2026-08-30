# La propriété des données

**Chaque donnée a un écrivain unique.** Les autres la lisent, ou en demandent la
modification à son propriétaire. Aucun module ne modifie ce qu'il ne possède pas.

## Le tableau

| donnée | écrivain unique | lecteurs |
|---|---|---|
| position, vitesse, orientation | `20-monde/mouvement` | tous, sous réserve de perception |
| terrain, bâti, franchissabilité | `20-monde/terrain` | navigation, mouvement, perception |
| état d'un seuil | `20-monde/seuils` | mouvement, unité, commandement |
| emprise, poussée, qui touche qui | `20-monde/contact` | mouvement, densité, coup |
| vie, blessure, effet d'un coup | `20-monde/coup` | combattant, unité, observation |
| fait perçu | `30-perception/fait` | la mémoire du témoin, et elle seule |
| les cinq couches d'un homme | `40-combattant/<la couche>` | l'arbitre, l'observation |
| geste voulu | `40-combattant/geste` | `20-monde`, et personne d'autre |
| ordre reçu par un homme | `40-combattant/memoire` | ses couches, sa pensée |
| appartenance, chef courant | `50-unite/identite` | ses membres, le commandement |
| forme, cohésion, allure | `50-unite` | membres, commandement, observation |
| route d'un groupe | `20-monde/navigation` | le chef de ce groupe, et lui seul |
| croyance | `70-commandement/croyances` | la décision de CE commandant |
| ordre littéral | `70-commandement` ou `80-conduite` | transmission, destinataires |
| mission | `80-conduite/mission` | les commandants concernés |
| trace de décision | l'acteur qui a décidé | observation |

## Ce que « demander » veut dire

Un module qui a besoin d'un changement qu'il ne possède pas **produit une
intention** et la remet au propriétaire. Il n'a aucune garantie qu'elle
aboutisse, et c'est le sujet.

L'exemple qui gouverne tout le reste : **un combattant ne se déplace pas.** Il
produit une intention de geste — marcher dans cette direction, à cette allure,
pour cette raison — et la remet au monde. Le monde applique l'accélération, teste
le bâti, résout les collisions et décide de la position résultante. L'homme peut
vouloir et ne pas obtenir.

C'est ce qui rend une bousculade, une venelle trop étroite ou une masse trop
dense racontables sans une seule ligne de code qui les raconte.

## L'invariant qui rend le reste possible

**Une seule fonction au monde écrit une position.** Pas « en général » : une.
C'est la différence entre « la traversée de mur est rare » et « la traversée de
mur est impossible ».

L'ancien moteur avait ce point de passage unique pour la position, et il tenait.
Mais il avait aussi un **second écrivain de la vitesse**, dans une branche de
déroute, qui contournait le plafond d'accélération et le bonus de monture.
Personne ne le savait ; c'est de là que sortait un fantassin en fuite plus rapide
que la cavalerie du même moteur.

Un écrivain unique n'est vrai que s'il est **vérifié**.

## Le corollaire sur la forme des données

Un porteur de données sans forme déclarée n'a pas de propriétaire réel : n'importe
qui peut lui ajouter un champ.

Mesuré sur l'ancien moteur : un homme portait **174 champs distincts**, écrits
depuis **229 endroits**. Il n'existait aucun endroit unique disant ce qu'un homme
possède. Conséquence directe : une comparaison de champ portant sur un nom qui
n'existait pas est passée inaperçue, et une donnée censée changer restait figée
pour toute la bataille sans que le compte le montre.

**Chaque entité qui a une identité a une forme déclarée en un seul endroit.**
