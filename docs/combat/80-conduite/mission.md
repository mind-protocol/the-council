# Mission

## 1. Ce que c'est

Ce que le général demande à un commandant : **un résultat et des conditions,
jamais un comment.**

## 2. Ce qu'il possède

- **La forme de la mission**, et il n'y en a que trois : **détruire une cible**,
  **contrôler une zone**, **empêcher quelqu'un d'atteindre son objectif**. Tout
  ce qui ne rentre pas dans ces trois-là n'est pas une mission — c'est une
  instruction déguisée, et elle se refuse.
- **Le destinataire** : un commandant, un seul, nommé. Une mission adressée à
  personne n'a pas été donnée.
- **Les conditions de succès** : ce qui, observé, vaut mission remplie.
- **Les conditions d'abandon** : ce qui, observé, vaut mission caduque — le coût
  dépassé, l'échéance passée, la cible disparue, le but qu'elle servait devenu
  sans valeur.
- **L'échéance** et **l'état** : donnée, reçue, en cours, remplie, abandonnée,
  perdue en route — avec l'instant et le motif de chaque passage.

## 3. Ce qu'il lit

L'objectif, pour savoir ce que la mission sert et ce qu'elle a le droit de
dépenser. La transmission, pour savoir si l'ordre est parti et s'il est arrivé.
Le commandement, pour l'état rapporté de son destinataire.

Il ne lit pas la position réelle des unités, ni celle de la cible.

## 4. Ce qu'il produit

- **L'ordre littéral** remis à la transmission : le résultat voulu, les deux
  jeux de conditions, l'échéance. Aucun chemin, aucune formation, aucun horaire
  de pas.
- **Cette mission tient-elle encore ?** — l'évaluation des conditions d'abandon
  sur ce qui est rapporté.
- **Un signalement** à chaque changement d'état, motif compris.

## 5. Invariants

- **Toute mission porte ses conditions d'abandon.** Sans elles, une mission
  devenue impossible reste active pour toujours, et la force qu'elle immobilise
  ne revient jamais. Une sonde refuse toute mission qui n'en déclare pas.
- Succès et abandon ne peuvent pas être vrais ensemble ; si les deux sont
  observés, l'abandon l'emporte et le conflit est tracé.
- Une mission remplie ou abandonnée libère aussitôt la force qu'elle immobilisait.
- Toute mission dont l'ordre n'est jamais arrivé est visible comme telle : perdue
  en route n'est pas la même chose qu'ignorée.

## 6. Ce qu'il ne fait pas

- **Il ne dit jamais comment.** Pas de route, pas de formation, pas d'allure, pas
  d'ordre de marche, pas de « par le nord ». Le commandant choisit ses moyens ;
  c'est toute la raison pour laquelle il existe.
- **Il ne descend pas au-dessous du commandant.** Il ne s'adresse ni à une unité,
  ni à un chef de rang, ni à un homme. Un général qui nomme un homme a court-
  circuité sa propre couche.
- **Il ne constate pas lui-même le succès.** Ce sont les rapports du commandant,
  avec leur âge et leur confiance, qui font foi — jamais l'état vrai du monde.
- **Il ne réattribue pas une mission** qui échoue. Il l'abandonne et signale ;
  l'allocation décide ce qu'on fait de la force libérée.
- **Il n'invente pas une quatrième forme.** « Soutenir », « surveiller »,
  « aider » sont des comment sans résultat : ce sont des missions vides, et un
  destinataire ne peut ni les remplir ni les abandonner.

## 7. Ce que l'ancien moteur faisait mal ici

**Il n'existait aucune mission.** Aucun ordre du moteur ne portait un résultat,
des conditions de succès ou des conditions d'abandon : tous les ordres venaient
d'un scénario écrit à l'avance, et ce scénario disait des comment — aller là,
prendre cette formation — sans jamais dire ce qui vaudrait réussite.

Conséquence directe et non mesurable autrement : la question « cette mission
tient-elle encore ? » ne se posait nulle part, faute d'objet à interroger. Le
taux de missions abandonnées, le délai entre l'impossibilité et l'abandon, la
part de force immobilisée par une mission caduque : **aucun de ces trois points
n'a été mesuré**, parce qu'il n'y avait rien à mesurer.
