# Le détachement

## 1. Ce que c'est

Un membre envoyé faire autre chose — porter un message, éclairer, fouiller un
bâti, tenir la liaison avec un voisin. Ce sont des **états explicites**, jamais
une perte d'appartenance.

## 2. Ce qu'il possède

- pour chaque membre détaché : son **état** (messager, éclaireur, fouille,
  liaison), depuis quand, pour quelle tâche, et jusqu'à quel terme ;
- le **terme** : ce qui met fin au détachement — la tâche faite, un délai écoulé,
  le retour à portée, la mort ;
- le **compte des détachés**, par état.

## 3. Ce qu'il lit

- `50-unite/identite` : les membres, et le fait qu'un détaché en reste un ;
- `50-unite/chef` : qui détache ;
- `10-socle` : l'horloge, pour dater et pour les termes ;
- `40-combattant/memoire` : ce que le détaché porte comme ordre, pour vérifier
  qu'il en a bien un — un détaché sans ordre en propre est un détaché perdu.

## 4. Ce qu'il produit

L'état de détachement d'un homme, lisible par la forme (qui ne lui assigne plus
de région), par la cohésion (qui ne le compte pas comme isolé), et par
l'observation. Et le **fait** du départ et du retour, daté.

## 5. Invariants

- **Un détaché reste membre.** Son appartenance ne change pas d'un iota ; seul son
  état change. Une sonde vérifie qu'aucun détachement n'a jamais retiré un homme
  d'une liste de membres.
- **Un détaché n'est pas un isolé.** La cohésion doit le distinguer d'un homme
  qui a décroché, sinon toute unité qui envoie deux éclaireurs se lit comme une
  unité qui se délite.
- **Tout détachement a un terme écrit**, y compris « jusqu'au retour ». Un
  détachement sans terme est un homme perdu qu'on ne comptera jamais comme perdu.
- L'état est **explicite et énuméré** : les quatre états, et pas un cinquième
  ajouté en passant.
- Un homme est dans un état de détachement et un seul.

## 6. Ce qu'il ne fait pas

- Il ne **décide pas** qui détacher, ni pour quoi. C'est une décision de chef, et
  elle vient d'en haut ; ce module tient l'état, pas le choix.
- Il ne **porte pas le message** et ne connaît pas son contenu : ce qui circule,
  et comment ça se perd, est `60-transmission`. Ici, on sait seulement qu'un
  homme est parti porter quelque chose.
- Il ne **conduit pas le détaché** : un messager en route est un homme comme un
  autre, avec ses quatre couches, son arbitre et son geste. Il peut avoir peur,
  convoiter, se tromper de chemin.
- Il ne **crée pas d'unité** pour le détachement, même à plusieurs.
- Il ne **ramène personne** : le retour est un fait constaté, pas une téléportation
  de fin de tâche.

## 7. Ce que l'ancien moteur faisait mal ici

**Non mesuré.** Aucun relevé ne dit combien d'hommes étaient détachés, ni
comment leur absence était comptée par les mesures de groupe.

Deux faits mesurés ailleurs disent pourquoi la question mérite une sonde dès le
premier jour. La pensée d'un homme était écrite depuis **56 endroits**, dont l'un
des libellés récurrents nommait un porteur de message — signe qu'un messager
était conduit par une branche propre plutôt que par ses couches. Et la dispersion
au chef était lue par ses **déciles**, sans qu'on sache si les détachés en étaient
exclus : un éclaireur à cent mètres et un traînard à cent mètres ne disent
pourtant pas la même chose du groupe.

Les deux sondes à poser : aucun détaché sorti d'une liste de membres, et aucun
détaché compté dans la dispersion ni parmi les isolés.
