# Le chef d'une unité

## 1. Ce que c'est

Qui mène ce groupe en ce moment, et qui prend la suite quand il tombe. Sans
tirage : le successeur **découle** des hommes présents.

## 2. Ce qu'il possède

- le **chef courant** : un membre de l'unité, ou personne ;
- la **date et la cause** de la dernière succession : mort, blessure hors de
  service, détachement, absence prolongée ;
- l'**ordre de succession** : la suite ordonnée des prétendants, dérivée et non
  tirée.

## 3. Ce qu'il lit

- `50-unite/identite` : la liste des membres ;
- `40-combattant/identite` : le métier, la trempe, le rang de chacun — ce qui
  ordonne les prétendants ;
- `20-monde` : l'état vital d'un homme, pour savoir qu'il n'est plus en état de
  mener ;
- `10-socle` : l'horloge, pour dater la succession.

## 4. Ce qu'il produit

Le nom du chef courant, et **le fait de la succession** quand elle a lieu : le
chef est tombé, voici son successeur, à cette date, pour cette cause. Ce fait est
rendu ; l'unité ne sait pas qui l'écoute. C'est à la perception et à la
transmission de décider qui l'apprend, quand, et déformé comment.

## 5. Invariants

- **Aucun tirage.** Le successeur est déterminé par les hommes présents et leur
  ordre dérivé. À état identique, même successeur.
- **Le calcul est sans effet de bord.** Interroger « qui mène ? » ne doit
  jamais, en aucune circonstance, changer qui mène. Une sonde interroge deux fois
  de suite au même battement et exige la même réponse et un état inchangé.
- La succession n'a lieu qu'**une fois** par cause, à un instant daté et unique
  dans le battement.
- Un chef est toujours membre de son unité. Une unité peut n'avoir personne, et
  c'est un état légitime — pas un trou à combler d'office.
- Le chef courant ici est la **vérité** ; ce qu'un homme en sait est dans sa
  mémoire, et les deux peuvent différer longtemps.

## 6. Ce qu'il ne fait pas

- Il ne **prévient personne**. Aucun membre n'apprend la succession du fait
  qu'elle a eu lieu ; il faut l'avoir vue ou se l'être fait dire.
- Il ne **transmet aucun ordre** au successeur : le nouveau chef n'hérite pas de
  ce que l'ancien avait en tête.
- Il ne **promeut pas** d'un autre groupe : le successeur sort des membres de
  cette unité, jamais d'ailleurs. S'il n'y a personne, il n'y a personne.
- Il ne juge pas de la compétence d'un chef ni ne le remplace pour mauvaise
  conduite.
- Il ne bouge pas, ne trace pas de route, ne fixe pas d'ancre.

## 7. Ce que l'ancien moteur faisait mal ici

La fonction qui élisait le successeur d'un chef avait un **effet de bord** :
**elle réaffectait le chef courant au moment où on l'interrogeait**. Poser la
question changeait la réponse du monde.

Le prix mesuré : appeler cette fonction plus tôt dans un battement faisait
observer une succession **un cran trop tôt**. Un simple déplacement de code — le
genre d'opération que l'étalon doit rendre à l'identique — changeait donc l'issue,
et l'on ne pouvait plus distinguer un bug d'une réorganisation.

C'est le contre-exemple canonique du principe de propriété : une lecture qui
écrit. La règle qui en sort tient en une phrase — **interroger n'est jamais
décider** — et elle se vérifie par une sonde qui pose la même question deux fois.
