# Terrain

## 1. Ce que c'est

L'autorité unique sur ce que le sol autorise : franchissable, infranchissable, ou
inconnu — et rien d'autre.

## 2. Ce qu'il possède

- **La géométrie du sol** : la surface de bataille, ses limites, ce qui la borne.
- **L'empreinte au sol du bâti et de l'eau**. Un mur, une haie, une berge, un
  fossé : c'est ici qu'ils sont des obstacles, et nulle part ailleurs. Le module
  du bâti décrit les bâtiments comme objets ; il ne décide pas de leur emprise
  physique — il la déclare, et le terrain l'inscrit.
- **Le troisième état.** Une case du monde vaut *franchissable*,
  *infranchissable*, ou **on ne sait pas** — parce que le relevé n'a jamais
  couvert cet endroit. Ce troisième état n'est pas une commodité de mise au
  point : c'est la seule façon de distinguer « il n'y a pas d'obstacle » de « on
  n'a rien construit ici ». Confondre les deux, c'est laisser une armée traverser
  une région qui n'existe pas.
- **Le coût de traversée** d'un pas franchissable : une pente, une boue, un
  éboulis coûtent des secondes sans interdire.

## 3. Ce qu'il lit

Du socle seulement : les mesures (mètres, pas, secondes), l'identité stable des
entités de décor, et de quoi signaler.

Il ne lit aucun autre module du monde. Il est le premier de sa couche, et l'ordre
intra-couche part de lui.

## 4. Ce qu'il produit

- **Est-ce franchissable, ici ?** — répondu avec l'état, jamais rabattu sur un
  booléen. Un appelant qui reçoit *inconnu* doit choisir explicitement quoi en
  faire ; le terrain ne choisit pas pour lui.
- **Que coûte ce pas ?** — en temps, pas en distance.
- **Le premier obstacle rencontré** le long d'un segment, et où.
- **La normale de l'obstacle** en un point, pour que le mouvement sache glisser
  au lieu de s'arrêter net.

## 5. Invariants

- Une seule autorité répond sur la franchissabilité. Aucun autre module ne tient
  sa propre carte des murs, même partielle, même « pour aller vite ».
- La réponse en un point ne dépend pas de qui demande, ni de son camp, ni de son
  état. Le terrain ne sait pas qui marche dessus.
- Le relevé est stable : la même question au même point rend la même réponse tant
  que rien n'a détruit ni construit.
- Toute surface où un corps peut se trouver est couverte par le relevé. Une sonde
  extérieure vérifie qu'aucun corps vivant ne se tient sur une case *inconnue*.

## 6. Ce qu'il ne fait pas

- **Il ne connaît aucun corps.** Ni homme, ni cheval, ni foule. Un corps n'est pas
  un obstacle de terrain : il est traité par la collision. Faire du terrain
  l'arbitre des corps est le premier pas vers le fichier de onze mille lignes.
- **Il ne calcule pas de route.** Répondre « franchissable » n'est pas répondre
  « par où ». La navigation lui pose des questions ; elle n'habite pas ici.
- **Il ne déplace rien.** Il n'écrit aucune position, aucune vitesse.
- **Il ne connaît pas la densité.** Un endroit encombré reste franchissable pour
  lui ; ce que la foule retire est mesuré ailleurs.
- **Il n'a pas d'opinion sur la visibilité.** Un mur bloque le pas et le regard,
  mais la portée du regard est une question de perception : le terrain rend la
  géométrie, la couche 30 en tire ce qu'elle veut.
- **Il ne se répare pas tout seul.** Une zone jamais relevée reste *inconnue* et
  se voit ; elle ne se devine pas en franchissable.

## 7. Ce que l'ancien moteur faisait mal ici

Rien, et c'est le résultat le plus surprenant de la campagne de mesure. Sur
**23 900 relevés**, **zéro téléport** et **zéro homme vivant dans le bâti** :
la géométrie était unifiée, contrairement à ce qu'on croyait. On soupçonnait deux
cartes divergentes ; il n'y en avait qu'une, et elle tenait.

La conséquence pour la reconstruction est une contrainte, pas un soulagement : ce
point de passage unique existait *par chance de conception*, sans sonde pour le
garder. Il doit être tenu explicitement cette fois — sinon la prochaine mesure ne
rendra pas le même zéro.
