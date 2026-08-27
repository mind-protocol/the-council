# La forme d'une unité

## 1. Ce que c'est

Une formation est un **ensemble de contraintes** — orientation, largeur,
profondeur, voisinage, densité — et non une grille de positions. Chaque homme
reçoit une **région ou une relation**, jamais un point du monde.

## 2. Ce qu'elle possède

- la **forme demandée** : le genre (ligne, colonne, coin, carré, essaim, tas) et
  ses contraintes chiffrées — orientation, largeur voulue, profondeur voulue,
  écart entre voisins, densité tolérée ;
- l'**ancre** : ce à quoi la forme est accrochée — un point du terrain, le chef,
  un seuil, une autre unité ;
- l'**assignation** : pour chaque membre, ce qu'il doit tenir. Deux formes
  seulement, et pas une troisième : une **région** (« ce quart du front, à trois
  rangs »), ou une **relation** (« à l'épaule droite de cet homme », « derrière
  celui-là, à deux pas »).

## 3. Ce qu'elle lit

- `50-unite/identite` et `50-unite/chef` : qui est là, qui mène, où est l'ancre ;
- `40-combattant/identite` : le métier, qui décide du rang qu'un homme doit tenir
  (les piques devant, les arcs derrière) ;
- `20-monde/terrain` : ce que le sol permet — une ligne de trente hommes ne
  s'inscrit pas dans une venelle ;
- `30-perception` : ce que le chef voit du terrain devant lui.

## 4. Ce qu'elle produit

Pour chaque membre, une **contrainte à satisfaire**, remise à la mémoire de cet
homme comme un élément de son ordre. La couche 2 de l'homme en tire une issue
— se ranger, se serrer, contourner — et la couche 3 en tire une barre. Aucun
homme ne reçoit jamais une coordonnée à atteindre.

Elle produit aussi l'**écart de forme** : à quel point ce qui est tenu ressemble
à ce qui est demandé.

## 5. Invariants

- **Aucun point du monde n'est distribué à un homme.** Une sonde vérifie qu'aucune
  assignation ne contient de coordonnée. C'est l'invariant central de la fiche.
- Une contrainte est **satisfiable ou déclarée insatisfiable**. Une région qui
  tombe dans un mur est refusée à la source, pas laissée à un homme qui s'y
  écrasera.
- La forme est **relative à l'ancre** : bouger l'ancre bouge la forme sans
  réassigner personne.
- Une forme demandée à une unité incomplète reste la même forme, avec des trous.
  On ne rétrécit pas la largeur pour faire joli.
- L'écart de forme est mesurable de l'extérieur, sans instrumenter le moteur.

## 6. Ce qu'elle ne fait pas

- Elle **ne déplace personne**. Elle n'écrit aucune position, ne pousse aucun
  homme dans sa case, ne corrige aucun retard. Un homme qui ne tient pas sa
  région ne tient pas sa région ; c'est un fait, pas une erreur à réparer.
- Elle **ne trace aucune route** : aller quelque part est `20-monde/navigation`,
  et cette route appartient au chef.
- Elle ne **juge pas si le groupe tient** : la dispersion, l'isolement et la
  capacité collective sont la cohésion.
- Elle ne **choisit pas la formation** : quelle forme prendre est une décision de
  commandement, reçue d'en haut. Elle l'exécute en contraintes.
- Elle ne **règle pas l'allure** du guide.
- Elle ne réordonne pas les membres pour améliorer son propre écart.

## 7. Ce que l'ancien moteur faisait mal ici

**Non mesuré.** Aucun relevé du moteur précédent ne dit sous quelle forme un
homme recevait sa place — région, relation, ou coordonnée —, ni combien
d'assignations étaient insatisfiables.

Un fait mesuré ailleurs éclaire pourtant le sujet : parmi les **56 endroits** où
la pensée d'un homme était écrite, l'un des libellés les plus fréquents nommait
l'ordre de formation comme cause de son déplacement. Autrement dit, la formation
**déplaçait** des hommes — c'était une branche de code capable de mouvoir un
corps, et non une contrainte remise à une couche.

La distinction entre « je pousse l'homme à sa place » et « je dis à l'homme quelle
région il doit tenir » est toute la différence entre une grille et une troupe.
