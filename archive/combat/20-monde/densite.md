# Densité

## 1. Ce que c'est

La densité locale de corps, tenue comme une **mesure du monde** — et ce qu'elle
retire physiquement à un homme, qui n'est jamais une émotion.

## 2. Ce qu'il possède

- **La densité en un point** : le nombre de corps par mètre carré autour de lui,
  sur un voisinage déclaré.
- **Les issues disponibles** pour un corps donné : dans combien de directions il
  peut encore faire un pas complet. C'est la grandeur qui compte réellement, et
  la densité n'en est que le résumé.
- **La marge de recul** : peut-il reculer, et de combien.
- **Le plafond d'allure imposé par l'encombrement**, remis au mouvement comme une
  contrainte.

## 3. Ce qu'il lit

Le socle (mesures). Le terrain, pour la surface réellement disponible — une place
bordée de murs n'offre pas la même densité qu'un champ. Les seuils, pour les
goulots. La collision, pour l'emprise des corps.

## 4. Ce qu'il produit

- **Combien d'issues il reste** à un corps, et lesquelles.
- **Le plafond d'allure** dû à l'encombrement, remis au mouvement.
- **L'impossibilité de reculer**, remise telle quelle : c'est un fait physique
  qu'un homme constate, pas une humeur qu'on lui prête.
- **Un signalement de seuil franchi**, pour que l'observation le voie et que les
  couches hautes en tirent ce qu'elles veulent.

## 5. Invariants

- La densité rendue est cohérente avec l'emprise des corps et la surface libre :
  on ne dépasse pas le nombre de corps qui tiennent physiquement.
- Ce module **retire** des possibilités ; il n'en ajoute aucune. Il ne rend jamais
  un homme plus rapide.
- Les trois régimes se lisent dans les issues, pas dans un état déclaré : la
  vitesse volontaire baisse, puis les contacts involontaires dominent, puis le
  mouvement volontaire et le recul disparaissent.
- Les mesures cibles sont écrites et vérifiables : la vitesse volontaire baisse
  vers **2-3 personnes/m²**, les contacts involontaires dominent vers **4-5**, le
  mouvement volontaire et la capacité de recul disparaissent vers **5-6**.
- Une sonde extérieure relève la distribution des densités, pas seulement le
  maximum : un maximum bas ne prouve rien si personne n'a jamais été serré.

## 6. Ce qu'il ne fait pas

- **Il ne fait paniquer personne.** Il ne dit jamais « l'unité panique » : il dit
  « ses issues ont disparu, il ne peut plus reculer ». Ce qu'un homme en ressent
  se forme à la couche 40, à partir du fait qu'on lui remet. C'est la frontière la
  plus importante de cette fiche, et la plus facile à franchir par commodité.
- **Il n'écrit aucune position.** Il rend des contraintes au mouvement.
- **Il ne blesse ni n'étouffe.** L'écrasement est un effet de la collision ; la
  densité en fournit la condition.
- **Il ne connaît ni camp, ni unité, ni formation.** Une densité ne distingue pas
  ses amis.
- **Il ne calcule pas de route de dégagement.** Où aller quand on étouffe est une
  décision, pas une mesure.
- **Il ne lisse pas.** Une densité moyennée sur une grande surface ne dit rien du
  goulot où trente hommes s'écrasent ; le voisinage est local et déclaré.

## 7. Ce que l'ancien moteur faisait mal ici

**La densité maximale relevée était de 2,2 personnes/m², et zéro seconde
au-dessus de 4.**

Ce n'est pas un bon résultat, c'est un résultat vide : **la physique de foule
n'avait jamais rien à mordre, donc elle n'était pas vérifiable**. Tout ce qui
concerne la compression, la perte d'issues et l'impossibilité de reculer était du
code jamais exercé — ni validé, ni infirmé.

Les cibles à tenir sont donc empruntées à la littérature, faute d'observation
propre : baisse de la vitesse volontaire vers **2-3 pers/m²**, domination des
contacts involontaires vers **4-5**, disparition du mouvement volontaire et de la
capacité de recul vers **5-6**. Et la première tâche de ce module n'est pas de
coder ces régimes : c'est de construire une condition où la foule atteint
réellement ces densités. Sans elle, on réécrira du code invérifiable.
