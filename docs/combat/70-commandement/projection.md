# Projection

## 1. Ce que c'est

Ce que donnerait chaque option, poussée grossièrement sur un horizon court, à
partir des **croyances** du chef — jamais du monde réel.

## 2. Ce qu'il possède

- **L'horizon** : une durée courte et déclarée — quelques minutes, quelques
  centaines de mètres. Au-delà, on écrit qu'on ne sait pas.
- **La grossièreté assumée** : on projette des **agrégats** — un corps, sa masse,
  son front, son allure —, jamais chaque homme. C'est une estimation, pas une
  simulation en réduction.
- **Les grandeurs projetées**, les mêmes pour toute option, sans quoi rien n'est
  comparable :
  - **la distance** et le temps qu'elle coûte sur ce terrain ;
  - **l'exposition** en chemin — à quoi l'on s'offre, et combien de temps ;
  - **le progrès vers l'objectif** courant ;
  - **la cohésion probable à l'arrivée** — on n'arrive pas dans l'état où l'on
    part, et c'est souvent ce qui décide ;
  - **le risque de rupture**, la probabilité crue que le corps casse ;
  - **l'information gagnée**, qui peut être la seule raison de le faire.
- **Les inconnues qui rendent la projection fragile** : ce qu'on a dû supposer,
  l'effet qu'aurait l'erreur, et lesquelles de ces suppositions changeraient le
  classement. Sans cette liste, c'est un chiffre déguisé en certitude.

## 3. Ce qu'il lit

Du socle : horloge, mesures — pas l'urne, une projection est déterministe. Du
monde : le terrain et la navigation, pour les distances, les délais et les
passages ; la géométrie est publique, ce n'est pas du renseignement. De l'unité :
les capacités génériques d'un corps de telle forme et de tel effectif. De la
transmission : l'ordre courant et le délai pour en faire parvenir un nouveau. Des
options : ce qu'il y a à projeter. **Des croyances et de l'estimation du chef**,
pour l'adversaire et pour ses corps qu'il ne voit pas.

Il ne lit **jamais** les positions, effectifs, ordres ou intentions réels du camp
adverse. Une projection contre un ennemi réel produit un chef devin : les
grandeurs ci-dessus deviennent des prédictions justes.

## 4. Ce qu'il produit

- **Une projection par option**, portant les sept grandeurs, chacune en
  intervalle quand elle hérite d'un intervalle de croyance.
- **Le refus de projeter** quand l'objet est trop mal connu.

## 5. Invariants

- **Une projection ne consulte que des croyances** : une sonde vérifie qu'aucune
  grandeur ne corrèle mieux avec l'état réel adverse qu'avec la carte du chef.
- Toute grandeur héritée d'un intervalle reste un intervalle, et l'horizon est le
  même pour toutes les options d'un examen : comparer une option projetée sur deux
  minutes à une autre sur dix est la faute classique.
- Toute projection est conservée dans la trace, y compris celle des rejetées.

## 6. Ce qu'il ne fait pas

- **Il ne resimule pas la bataille** : ni mêlée en accéléré, ni pertes homme par
  homme. Le besoin d'y descendre dit que l'horizon est trop long.
- **Il ne choisit pas** et ne pondère pas les grandeurs entre elles : le poids
  relatif de la cohésion et du progrès appartient à la décision. L'adversaire y
  reste une masse crue, jamais un agent qui choisit.
- **Il ne consulte pas l'avenir réel**, et une projection dont les inconnues ne
  sont pas listées est refusée.

## 7. Ce que l'ancien moteur faisait mal ici

**Ce module n'existait pas, et rien n'a été mesuré à son sujet.** Aucun chef ne
projetait quoi que ce soit : **aucun chemin de code ne permettait qu'un ordre
naisse d'un renseignement**, et **les cinq endroits qui posaient un ordre le
recevaient tous de l'extérieur du moteur**. Rien à relever.

Le seul chiffre voisin dit l'ampleur du vide : **zéro ordre adapté sur quinze
chefs**, pour **41 observations typées de cavalerie**, **94 de longues hampes** et
**478 communications entre chefs** sur une bataille.

Ce qu'il faudra mesurer : le coût en calcul d'une projection par option et par
examen, le nombre d'options qu'un chef peut projeter, et l'horizon au-delà duquel
elle cesse de discriminer. Les poser au jugé est le risque de cette fiche.
