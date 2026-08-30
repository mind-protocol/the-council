# Les tensions connues du découpage

Ce dossier n'est pas un découpage évident. Neuf frontières ont demandé un
arbitrage, et **rien ne garantit qu'il soit le bon**. Elles sont listées ici pour
qu'on les reconnaisse quand le code les fera craquer, au lieu de les redécouvrir
comme des surprises.

Une tension n'est pas un défaut à corriger tout de suite. C'est un endroit où,
si l'implémentation résiste, **la fiche a probablement tort et pas le code**.

## Dans le monde

**`terrain` et `bâti` se chevauchent sur le mur.** Arbitrage retenu : le bâti
*déclare* une emprise, le terrain l'*inscrit*, et une sonde compare les deux. Si
les deux se contredisent un jour, c'est qu'il fallait un seul module.

**`densité` ne possède aucune donnée.** Elle recalcule tout à partir du contact
et du mouvement. Un module sans donnée propre contredit la définition d'un
module ; il est gardé séparé parce que ses seuils sont un sujet en soi, mais
c'est un candidat à la fusion dans `contact`, ou au déplacement vers
l'observation.

## Entre le monde et la perception

**`fait` est rangé dans la perception et ne perçoit rien.** Un fait *rapporté* ou
*déduit* naît sans aucun sens. Sa **forme** appartient au socle ; ce qui reste en
perception, c'est comment un sens en produit un. Le découpage actuel mélange les
deux.

**`ouïe` frôle la transmission.** Un ordre crié est à la fois une émission sonore
et un message. La coupe retenue : le bruit reçu et le contenu compris
appartiennent à l'ouïe, l'acheminement à la transmission. La frontière est fine
et tiendra mal si personne ne l'applique.

## Chez le combattant

**`envie` et `réflexion` peuvent proposer le même geste.** La frontière tient au
seul objet désigné : « fuir vers un abri repéré » est une convoitise, « céder »
est une réflexion — mais un abri perçu fait basculer la même conduite d'une
couche à l'autre. Deux prétendants risquent donc de réclamer les jambes pour la
même raison, et l'arbitre ne saura pas que c'est la même.

## Dans l'unité

**`cohésion` lit les positions réelles**, alors que tout ce qui est au-dessus de
la perception vit sous brouillard. C'est assumé — la cohésion est une mesure du
monde, pas une croyance de chef — mais c'est la seule fiche de sa couche à y
échapper, et elle appartient peut-être à l'observation.

**`forme` et `allure` produisent des contraintes destinées à un homme**, donc à
une couche inférieure. La donnée descend, ce qui est licite. Mais **par quel
canal** — remise directe, ou passage par la transmission — n'est pas tranchable
depuis l'unité seule.

**`chef` et `détachement` se recouvrent sur le chef détaché.** Ni l'un ni l'autre
ne dit qui mène l'unité pendant que son chef porte un message. C'est un trou,
pas une tension : il faudra trancher.

## Dans la conduite

**`allocation` et `réserve` décrivent la même force sous deux titres.**
Arbitrage retenu : une réserve est *constituée*, avec un motif et des conditions
d'engagement écrites à froid ; le reste est du non-affecté. La distinction ne
tiendra que si quelqu'un l'applique.

**`objectif` et `mission` pourraient n'en faire qu'un.** Les conditions
d'abandon d'une mission dépendent de la valeur restante d'un but, donc la mission
lit l'objectif en permanence.

## Dans l'observation

**`rendu` ne fait presque que mettre en forme ce que `trace` possède.** Sa seule
matière propre est l'empreinte de ce qui est réellement servi au navigateur et
les états d'affichage. C'est la fiche la plus fragile du dossier.

## Ce qu'il faut en faire

Rien, pour l'instant. Mais quand l'implémentation d'un de ces modules demandera
de remonter une couche, d'ajouter un argument bizarre ou de dupliquer une donnée
— **relire cette page avant de contourner**. Neuf fois sur dix, la réponse est
que la frontière était mal placée, et il vaut mieux déplacer la fiche que tordre
le code autour d'elle.
