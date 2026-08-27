# Mouvement

## 1. Ce que c'est

**Le seul écrivain de position et de vitesse au monde.** Il reçoit des intentions
de déplacement, les confronte au sol, et décide de ce qui arrive réellement.

## 2. Ce qu'il possède

- **La position** de chaque corps, son **orientation**, sa **vitesse** — et rien
  d'autre au monde ne les écrit.
- **Le plafond d'allure** de chaque corps : ce qu'il peut donner au mieux, selon
  sa nature (à pied, monté), son fardeau, sa fatigue et ses blessures.
- **Le plafond d'accélération et de virage** : on ne passe pas de l'arrêt à la
  course en un pas, et une colonne au galop ne tourne pas à angle droit.
- **L'état de marche** : arrêté, au pas, à l'allure, à la course, en fuite.

## 3. Ce qu'il lit

Le socle (mesures, horloge, formes). Le terrain, pour la franchissabilité, le
coût du pas et la normale d'un obstacle. Les seuils, pour la conduite d'un
franchissement. La navigation, pour la route du groupe.

Il ne lit ni la perception ni le combattant : il reçoit des intentions, il ne va
pas les chercher.

## 4. Ce qu'il produit

- **Le résultat d'une intention** : la position et la vitesse effectives après le
  pas, et le motif quand le voulu n'a pas été obtenu — mur, seuil fermé, corps en
  travers, plafond d'accélération.
- **Le glissement le long d'un mur.** Un corps qui vise à travers un obstacle ne
  s'arrête pas net : il est projeté sur la surface et continue de ce qu'il peut.
- **Un signalement** de franchissement, de blocage durable, d'arrivée au but.

## 5. Invariants

- **Un seul point de passage écrit une position. Un seul point de passage écrit
  une vitesse.** Les deux, séparément, et tous deux vérifiés — l'un sans l'autre
  ne prouve rien.
- Aucun corps ne se retrouve dans l'infranchissable, à aucun pas intermédiaire.
- Le déplacement d'un pas ne dépasse jamais la vitesse fois la durée du pas. Une
  sonde extérieure mesure les sauts entre deux relevés ; l'attendu est zéro.
- Aucune vitesse ne dépasse le plafond de l'état courant, **y compris en fuite**.
  Une comparaison n'est valable qu'à état comparable : on compare une fuite à une
  fuite, une marche à une marche.
- L'accélération est plafonnée dans tous les états, sans exception de branche.
- À graine tenue, la même intention sur le même sol rend la même position.

## 6. Ce qu'il ne fait pas

- **Il ne décide pas où aller.** Il n'a ni objectif, ni ennemi, ni peur. Une
  intention lui arrive de la couche 40 ; il en fait ce que le monde permet.
- **Il ne calcule pas de route.** Il consomme celle du groupe et ne la
  reconstruit pas quand elle l'ennuie.
- **Il ne résout pas les corps entre eux.** L'évitement, la poussée et le contact
  sont de la collision. Le mouvement traite le sol ; la collision traite les
  voisins.
- **Il n'a pas d'exception de déroute.** Une fuite est un état de marche, avec
  ses plafonds, dans le même code. Une branche spéciale pour la panique est
  exactement la faute mesurée ci-dessous.
- **Il ne blesse ni ne tue.** Un homme qui heurte un mur à la course n'est pas son
  affaire.
- **Il ne connaît pas la formation.** Tenir un front est une contrainte d'unité,
  qui arrive sous forme d'intention par homme.

## 7. Ce que l'ancien moteur faisait mal ici

**La position avait un point de passage unique, et il tenait** : zéro téléport sur
23 900 relevés.

Mais **la vitesse avait un second écrivain caché dans une branche de déroute**,
sans plafond d'accélération ni bonus de monture. Résultat mesuré : **un fantassin
en fuite atteignait 3,6 m/s contre 3,18 pour la meilleure cavalerie**.

Deux enseignements, et ils gouvernent la fiche entière. Le premier : deux
grandeurs, deux écrivains à vérifier — tenir la position ne dit rien de la
vitesse. Le second : la faute vivait dans une **branche d'exception**, celle
qu'on écrit un soir pour que la panique ait l'air urgente. C'est pourquoi il n'y
a pas, ici, de code de déroute séparé.
