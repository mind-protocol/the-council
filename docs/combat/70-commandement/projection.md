# Projection

## 1. Ce que c'est

Ce que donnerait chaque option, poussée grossièrement sur un horizon court, à
partir des **croyances** du chef — jamais du monde réel.

## 2. Ce qu'il possède

- **L'horizon** : une durée courte et déclarée, de l'ordre de ce qu'un chef peut
  se représenter — quelques minutes, quelques centaines de mètres. Au-delà, on ne
  projette pas, on écrit qu'on ne sait pas.
- **La grossièreté assumée** : on projette des **agrégats** — un corps, sa masse,
  son front, son allure moyenne —, jamais chaque homme. La projection n'est pas
  une simulation en réduction ; c'est une estimation d'aboutissement.
- **Les grandeurs projetées**, les mêmes pour toute option, sans quoi rien n'est
  comparable :
  - **la distance** à parcourir et le temps qu'elle coûte sur ce terrain ;
  - **l'exposition** en chemin — à quoi l'on s'offre, et pendant combien de temps ;
  - **la cohésion probable à l'arrivée** — on n'arrive pas dans l'état où l'on
    part, et c'est souvent ce qui décide ;
  - **le progrès vers l'objectif** courant ;
  - **le risque de rupture** — la probabilité crue que le corps casse en chemin
    ou au contact ;
  - **l'information gagnée** — ce qu'on apprendra en le faisant, qui peut être la
    seule raison de le faire.
- **Les inconnues qui rendent la projection fragile** : la liste explicite de ce
  qu'on a dû supposer, avec l'effet qu'aurait l'erreur. Une projection sans cette
  liste est un chiffre déguisé en certitude.
- **La sensibilité** : lesquelles de ces suppositions, si elles tombent,
  changeraient le classement des options.

## 3. Ce qu'il lit

- Du socle : horloge, mesures. Pas l'urne : une projection est déterministe.
- Du monde : le terrain et la navigation, pour les distances, les délais et les
  passages — la géométrie est publique, elle n'est pas du renseignement.
- De l'unité : les capacités génériques d'un corps de telle forme et de tel
  effectif — combien il perd de cohésion à courir, ce qu'il tient de front.
- De la transmission : l'ordre courant, et le délai qu'il faudrait pour en faire
  parvenir un nouveau.
- **Des croyances et de l'estimation du chef**, pour tout ce qui concerne
  l'adversaire et pour l'état de ses corps qu'il ne voit pas.
- Des options : ce qu'il y a à projeter.

Il ne lit **jamais** les positions, effectifs, ordres ou intentions réels du camp
adverse. Une projection contre un ennemi réel produit un chef devin, et les
grandeurs ci-dessus deviennent des prédictions justes — ce qui est exactement le
défaut à éviter.

## 4. Ce qu'il produit

- **Une projection par option**, portant les sept grandeurs, chacune en
  intervalle quand elle hérite d'un intervalle de croyance.
- **Les inconnues et leur poids.**
- **Le refus de projeter**, quand une option porte sur un objet trop mal connu :
  c'est une sortie légitime, et elle vaut information — elle ouvre la voie à
  « aller voir » plutôt qu'à un chiffre inventé.

## 5. Invariants

- **Une projection ne consulte que des croyances.** Une sonde extérieure vérifie
  qu'aucune grandeur projetée ne corrèle mieux avec l'état réel adverse qu'avec
  ce que le chef en croit.
- Toute grandeur héritée d'un intervalle reste un intervalle. Aucun resserrement
  gratuit.
- Même croyances, même options, même projection : aucun tirage.
- L'horizon est le même pour toutes les options d'un même examen. Comparer une
  option projetée sur deux minutes à une autre sur dix est la faute classique.
- Toute projection est conservée dans la trace de décision, y compris celles des
  options rejetées.

## 6. Ce qu'il ne fait pas

- **Il ne resimule pas la bataille.** Pas de mêlée jouée en accéléré, pas de
  pertes calculées homme par homme. Si l'on éprouve le besoin de descendre à
  l'homme, c'est que l'horizon est trop long.
- **Il ne choisit pas** et ne pondère pas les grandeurs entre elles : le poids
  relatif de la cohésion et du progrès appartient à la décision.
- **Il ne consulte pas l'avenir réel.** Aucun accès à ce qui va se passer.
- **Il ne cache pas ses suppositions.** Une projection dont les inconnues ne sont
  pas listées est refusée.
- **Il n'apprend pas.** Aucun ajustement de ses estimations à partir de ce qui
  s'est réellement produit : un chef qui se trompe systématiquement continue.
- **Il ne projette pas les autres camps comme s'ils décidaient.** L'adversaire y
  est une masse crue, avec sa fourchette, pas un agent qui choisit.

## 7. Ce que l'ancien moteur faisait mal ici

**Ce module n'existait pas, et rien n'a été mesuré à son sujet.** Aucun chef ne
projetait quoi que ce soit : **aucun chemin de code ne permettait qu'un ordre
naisse d'un renseignement**, et **les cinq endroits qui posaient un ordre le
recevaient tous de l'extérieur du moteur**. Il n'y avait donc ni horizon, ni
grandeur projetée, ni rejet motivé — rien à relever.

Le seul chiffre voisin est celui qui dit l'ampleur du vide : **zéro ordre adapté
sur quinze chefs**, pour **41 observations typées de cavalerie**, **94 de longues
hampes** et **478 communications entre chefs** sur une bataille.

Ce qu'on ne sait donc pas, et qu'il faudra mesurer pour de bon : le coût en temps
de calcul d'une projection par option et par examen, le nombre d'options qu'un
chef peut raisonnablement projeter, et la longueur d'horizon au-delà de laquelle
la projection cesse de discriminer. Aucune de ces trois grandeurs n'a de
précédent ici ; les poser au jugé est le risque principal de cette fiche.
