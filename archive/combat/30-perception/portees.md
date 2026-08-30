# Portées

## Où l'on se trouve

Le système de combat est empilé en couches, et chacune ne connaît que celles du
dessous. Le [monde](../20-monde/) — couche 20 — tient la vérité : où sont les
corps, ce qui les sépare, ce qui les blesse. Le [combattant](../40-combattant/)
— couche 40 — tient un homme et ses décisions. **Entre les deux, il faut un
étage où le monde devient de l'information**, parce qu'un homme ne décide jamais
sur ce qui est, seulement sur ce qui lui est parvenu. C'est la couche 30, la
perception, et elle compte quatre modules.

`portees` est le premier des quatre, et le seul qui ne connaisse aucun homme.

## Le problème qu'il résout

Avant que quiconque puisse voir ou entendre quoi que ce soit, il faut répondre à
une question, et toujours la même : **jusqu'où ?**

Un homme est à quatre-vingts mètres, dans la brume du matin — le distingue-t-on ?
Et son enseigne, en reconnaît-on la couleur ? Un ordre est crié à quarante
mètres, derrière un mur, dans le vacarme d'une mêlée — passe-t-il ?

Ces questions n'ont rien de rhétorique : chacune se tranche par un nombre, et ce
nombre est réclamé un peu partout dans le moteur. **Le problème n'est pas de
savoir répondre — c'est de répondre au même endroit.** Une distance de perception
écrite à deux endroits est une distance qui divergera à la première retouche, et
personne ne verra passer la divergence : les deux valeurs sont plausibles, et
aucune n'est fausse au point de faire tomber quoi que ce soit.

## Ce qu'il tient

Trois familles de nombres, et pas une de plus.

**Des distances, en mètres**, par sens et par nature de ce qu'on observe. Voir
qu'il y a quelqu'un, reconnaître une couleur d'enseigne et reconnaître un visage
sont trois portées différentes, et la troisième est bien plus courte que la
première. De même pour l'oreille : un cri, un ordre articulé qu'on comprend, une
trompe, un rugissement.

**Des facteurs sans unité, entre 0 et 1**, qui rabotent ces distances selon les
conditions du moment : l'heure du jour, la brume, la pluie, la fumée, le vent et
son sens, le bruit de fond d'une mêlée. Un facteur de 0,4 ne veut pas dire qu'on
voit à moitié : il veut dire que la portée vaut quatre dixièmes de ce qu'elle
vaudrait par temps clair.

**Une fraction de confiance** : au-delà de quelle part de la portée une
observation devient douteuse. À la limite du champ, on voit *quelque chose*, et
c'est précisément là que naissent les rapports faux qui font perdre les
batailles.

À quoi s'ajoute la nature de ce qui interrompt : un mur coupe la vue et atténue
le son, une haie atténue les deux, un tertre coupe la vue et laisse passer le
son. Le module ne dessine pas les murs — il dit ce qu'un mur fait.

## Pourquoi ces nombres méritent un module

Pas par propreté. Un chiffre qui n'a qu'un lecteur reste chez son lecteur ; ici,
**les lecteurs sont plusieurs et ne se parlent pas**.

Prenons la portée d'un cri. Elle décide de ce qu'un homme entend, donc elle est
lue par [`ouie`](ouie.md). Elle décide du rayon dans lequel un ordre crié atteint
quelqu'un, donc elle est lue par
[`60-transmission/canal`](../60-transmission/canal.md). Elle décide de ce qu'un
chef peut espérer commander à la voix avant de devoir envoyer un homme, donc elle
est lue par [`50-unite/chef`](../50-unite/chef.md).

Trois modules, dans trois couches différentes, qui ne se connaissent pas et n'ont
aucune raison de se connaître. Sans point commun, chacun écrit quarante mètres
chez lui — et le jour où l'on décide que c'est trente-deux, deux des trois
gardent quarante.

## Pourquoi il ne sait pas qui regarde

C'est la coupe qui porte tout le reste, et elle mérite d'être comprise avant le
détail.

Le barème répond à *« jusqu'où porte un cri, ici, maintenant »*. Il ne répond
jamais à *« qu'est-ce que cet homme-là entend »*. On peut l'interroger sans avoir
un homme sous la main, et sans même qu'il y ait un homme.

Trois choses en découlent, et ce sont elles qui justifient la coupe :

**Il se teste sans monde et sans bataille.** On l'appelle avec des conditions, on
compare des nombres. Pas de terrain à monter, pas d'armée à peupler, pas de
battement à simuler. C'est la propriété la plus précieuse qu'un module puisse
avoir, et on la perd dès qu'on lui donne un observateur en argument.

**Il ne peut pas tricher par camp.** Il n'a pas l'argument qui le permettrait.
« Le barème ne dépend jamais du camp de l'observateur » n'est donc pas une
promesse qu'il faudrait surveiller : c'est une impossibilité de signature.

**La fatigue, l'attention et l'âge d'un homme ne descendent jamais ici.** Ce sont
des modificateurs, appliqués par [`vue`](vue.md) et [`ouie`](ouie.md) *par-dessus*
ce que le barème rend. Un guetteur perché voit plus loin non parce que le barème
le sait, mais parce que la vue tient compte de sa hauteur.

Cette absence d'observateur explique aussi le rang du module : il est le premier
de sa couche, et il ne lit aucun des trois autres.

## Ce qu'il n'est pas, en regard de ses trois voisins

La couche 30 tient en une chaîne courte, et il vaut la peine de la lire dans
l'ordre : `portees` dit ce qui est possible, [`vue`](vue.md) et [`ouie`](ouie.md)
disent ce qu'un homme donné en tire, [`fait`](fait.md) en fait quelque chose de
transmissible.

| | ce qu'il répond | connaît-il un homme ? |
|---|---|---|
| **`portees`** | jusqu'où ça porte, et ce que ça traverse | non |
| [`vue`](vue.md) | ce que **cet** homme voit, avec ses yeux et son orientation | oui |
| [`ouie`](ouie.md) | ce que **cet** homme entend, et ce qu'il en comprend | oui |
| [`fait`](fait.md) | ce que ça devient une fois qu'on peut le rapporter — un auteur, une date, un lieu, une confiance | oui |

D'où sa liste de refus, qui est le négatif exact de ce tableau. Il ne perçoit
rien. Il ne produit aucun fait, n'a ni auteur ni date ni témoin. Il ne connaît
pas le contenu de ce qu'on perçoit : il dit jusqu'où l'on distingue une enseigne,
jamais de quelle maison elle est. Il ne décide pas de la confiance d'un fait — il
en donne l'attendu, le fait porte le résultat. Et il ne masque rien de sa propre
autorité : la géométrie appartient au [`terrain`](../20-monde/terrain.md), il la
consomme.

## Pourquoi il est en couche 30 et non dans le socle

Un module fait de constantes, sans état et sans décision, ressemble à s'y
méprendre à du [socle](../10-socle/). Il n'y est pas, et la raison n'est pas de
goût : **il lit le monde**. La géométrie des masques vient du
[`terrain`](../20-monde/terrain.md) ; la fumée et le vacarme viennent des
[`dangers`](../20-monde/dangers.md).

Or [la règle de dépendance](../00-principes/01-regle-de-dependance.md) dit qu'un
module ne lit que des couches strictement inférieures à la sienne. Un module qui
lit la couche 20 ne peut pas vivre en couche 10, quelle que soit sa simplicité
apparente. La règle ne souffre pas d'exception au prétexte que le module est
petit — c'est exactement par là que les exceptions commencent.

Ce qu'il reste de socle dans sa nature se lit ailleurs : c'est un **barème** au
sens de [la taxonomie des modules](../00-principes/03-ce-qu-est-un-module.md#sa-nature--cinq-et-pas-dautres),
c'est-à-dire des constantes et des règles de lecture. Deux appels identiques
rendent la même chose, toujours. Il n'a ni mémoire, ni tirage, ni avis.

## Ce qui doit rester vrai

- **Un seul barème.** Aucun module ne porte sa propre constante de distance, même
  « pour aller vite ».
- **La géométrie est symétrique** : si A est masqué de B, B est masqué de A. Ce
  qui ne l'est pas — la hauteur, l'éclairage, le vent — est déclaré comme tel et
  se voit dans la réponse.
- **La portée décroît de façon monotone.** Aucune bande de distance où l'on
  verrait mieux plus loin.
- **Toute portée est un chiffre écrit**, pas une valeur enfouie dans une
  condition.
- Le barème ne dépend jamais du camp de l'observateur.

## Ce que l'ancien moteur payait ici

**Rien de mesuré.** Aucun relevé de la campagne ne porte sur les portées
elles-mêmes : ni sur leur dispersion entre modules, ni sur leur dégradation par
les conditions. Il faut le dire franchement, parce qu'une fiche qui invente un
défaut pour justifier son existence ne vaut pas mieux qu'un module qui invente un
besoin.

Ce que la campagne a montré, en revanche, c'est que le renseignement circulait
sans que personne en fasse rien. Extraire les portées dans un barème unique est
donc une mesure de propreté, pas une correction d'un défaut mesuré — et la
première sonde à écrire est celle qui compte les endroits du code où une distance
de perception est écrite en dur. **L'attendu est un.**

## Là où ça craquera

**Le jour où une portée dépendra vraiment de l'observateur.** Un guetteur en haut
d'une tour, un vieil homme qui voit mal : la coupe tient tant que ces cas restent
des modificateurs appliqués par-dessus. Si l'un d'eux exige de changer le barème
lui-même, c'est la frontière qui est mal placée, pas le cas qui est bizarre.

**Le cri d'un ordre**, qui est portée et message à la fois. La coupe retenue —
le bruit reçu et le contenu compris à l'ouïe, l'acheminement à la transmission —
est fine et ne tiendra que si quelqu'un l'applique. Elle figure dans
[les tensions connues](../00-principes/08-tensions-connues.md), et c'est là qu'il
faut retourner avant de la contourner.
