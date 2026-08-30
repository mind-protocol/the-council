# Navigation

## 1. Ce que c'est

Le calcul des routes : par où l'on va d'ici à là — **un chemin par destination et
par groupe conducteur**, jamais un chemin par homme.

## 2. Ce qu'il possède

- **Le graphe de circulation** : les endroits reliés à quels endroits, à quel coût,
  par quels seuils. Dérivé du terrain et des seuils, tenu ici, et couvrant **toute
  la surface où un corps peut aller** — dedans comme dehors.
- **Les routes calculées** : pour chaque couple *destination × groupe conducteur*,
  une suite de points de passage, sa longueur, son coût en temps, sa date.
- **L'invalidation** : quelles routes cessent d'être valables quand un seuil se
  ferme, une brèche s'ouvre, un pont cède.

## 3. Ce qu'il lit

Le socle (mesures, horloge, urne pour départager deux routes de coût égal). Le
terrain, pour la franchissabilité et le coût de traversée. Les seuils, pour les
passages et leur état. Le bâti, pour ce qu'un seuil dessert.

Il ne lit pas le mouvement : il ne sait pas où les corps sont, et n'a pas à le
savoir.

## 4. Ce qu'il produit

- **Une route** pour un groupe conducteur vers une destination : la suite des
  points de passage.
- **Le coût attendu** en temps et en distance, qui permet de choisir entre deux
  objectifs sans les essayer.
- **L'aveu qu'il n'y a pas de route** — réponse à part entière, qui remonte telle
  quelle. Rendre une route approximative quand il n'y en a pas ment à tout ce qui
  la lit.
- **Un signalement d'invalidation** quand une route rendue cesse d'être praticable.

## 5. Invariants

- **Le nombre de calculs de route par pas de temps est de l'ordre du nombre de
  groupes, pas du nombre d'hommes.** Une sonde extérieure mesure ce rapport ; il
  ne doit pas dériver.
- Toute route rendue est praticable : chacun de ses segments est franchissable, et
  chacun de ses seuils est ouvert à la date du calcul.
- Aucun point d'une route ne s'éloigne de la destination plus que le départ n'en
  était éloigné. Un détour est légitime ; au-delà du point de départ, c'est le
  signe d'un graphe troué, et la sonde le dit.
- Le graphe couvre l'extérieur des murs autant que l'intérieur. Une région
  atteignable à pied et absente du graphe est une faute, pas une lacune.
- À graine tenue, deux routes de coût égal sont départagées de la même façon.

## 6. Ce qu'il ne fait pas

- **Il ne calcule pas de route par homme.** C'est la ligne dure de cette fiche. Un
  homme suit son groupe ou fait un pas d'évitement local, qui est de la collision.
- **Il ne déplace personne.** Il rend une suite de points ; le mouvement décide de
  la vitesse et de ce qui arrive quand un mur est là.
- **Il n'évite pas les corps.** Une foule n'est pas un obstacle de graphe : elle
  change à chaque pas, et recalculer sur elle fait osciller une armée entière.
- **Il ne choisit pas la destination.** Où l'on va est une décision de
  commandement ; la navigation répond *comment*, jamais *pourquoi*.
- **Il ne garde pas de route périmée par confort.** Une route invalidée est
  signalée, pas rafistolée en silence.
- **Il ne modélise pas l'encombrement.** Une route lente parce qu'elle est pleine
  se voit dans le débit des seuils, pas dans son coût.

## 7. Ce que l'ancien moteur faisait mal ici

Le grief qu'on portait était faux, et le vrai était ailleurs.

**La route par groupe était déjà tenue** : **4 calculs de route pour 16 unités**,
soit **0,017 par homme**. Personne ne calculait un chemin par combattant, contre
ce qu'on supposait.

Le défaut était le **graphe lui-même**. Une route rendue faisait **223 m pour
110 m à vol d'oiseau**, et son point le plus éloigné se tenait à **164 m de la
cible** — plus loin que le départ. La voirie ne desservait pas l'extérieur des
murs, et le code le **documentait sans le réparer**.

C'est la leçon la plus dure de cette fiche : un défaut documenté est un défaut
qui ne se corrige jamais. Ce qui le corrige, c'est la sonde d'écart entre la
route et le vol d'oiseau, et le point le plus éloigné qu'elle relève.
