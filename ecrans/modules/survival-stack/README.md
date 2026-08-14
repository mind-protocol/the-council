# survival-stack — la machine à états, refaite de zéro

Quatre couches, empilées. Chacune répond à une question qu'un homme se pose,
dans l'ordre où il se la pose — et l'ordre n'est pas négociable, parce qu'il est
celui de l'urgence et non celui de l'importance.

| # | couche | la question, dans SA bouche | ce qu'elle produit |
|---|---|---|---|
| 1 | **le corps** | *qu'a appris mon corps pour survivre ?* | un geste, sans qu'on l'ait voulu |
| 2 | **la réflexion** | *comment me sortir de cette situation ?* | une issue, cherchée |
| 3 | **l'interprétation** | *comment faire ce qu'on m'a dit comme je veux ?* | une manière de tenir l'ordre |
| 4 | **l'envie** | *qu'est-ce que je veux, maintenant ?* | un désir, gratuit |

Les quatre sont formulées à la première personne, et ce n'est pas un ornement :
aucune ne demande *ce qui serait optimal*, toutes demandent *ce que moi je fais*.
Une couche qui se met à calculer un optimum global s'est trompée d'homme.

Deux remarques sur la forme de cette pile, parce qu'elles décident du reste.

**La couche 3 ne demande pas s'il obéit.** Elle suppose qu'il obéit — c'est le
cas ordinaire — et cherche COMMENT, ce qui est toute la matière. Un ordre est
sous-déterminé : « tenez la porte » ne dit pas où l'on se tient, ni qui l'on
frappe d'abord, ni ce qu'on fait de son cousin blessé à dix pas. C'est là-dedans
que l'homme met le sien, et c'est ce qui produit une troupe qui obéit sans être
une troupe de pions. La désobéissance n'a donc pas besoin d'une couche : elle est
le cas limite de l'interprétation, quand la manière qu'il veut ne ressemble plus
du tout à ce qu'on lui a dit.

**La couche 1 ne préempte pas parce qu'elle est la première.** Elle prend la main
parce que la peur suspend physiologiquement la délibération — sous stress, le
cortex préfrontal se désengage et ce sont les automatismes acquis qui pilotent.
L'emprise de la couche 1 sur les trois autres est donc une **fonction de
l'alarme**, pas une règle de priorité. C'est ce qui fait qu'un homme calme
réfléchit, qu'un homme paniqué ne fait que ce que son corps sait faire, et
qu'entre les deux les deux se mélangent.

---

## Les trois règles

### 1. Toujours réaliste — physique et psychologie, jamais l'équilibrage

Chaque quantité doit se rattacher à un fait mesurable : une vitesse de marche,
une largeur d'épaules, un temps de réaction, une durée de montée d'adrénaline.
Quand un chiffre paraît faux, **on le corrige contre la réalité**, pas contre
l'envie que la bataille dure plus longtemps ou fasse plus de morts.

Le corollaire est dur et il faut le tenir : *si le comportement obtenu ne plaît
pas mais que la mesure est juste, c'est le modèle qui est incomplet, pas le
chiffre qui est mal réglé.* On cherche alors ce qu'on a oublié de modéliser.

La psychologie compte autant que la physique, et elle est moins intuitive :

- **La peur et la douleur sont deux canaux séparés.** Un homme peut être
  gravement blessé sans panique, et intact et paralysé. Les confondre dans une
  seule jauge de « santé » est la faute la plus répandue du genre.
- **Il n'y a pas deux réponses au danger mais trois** : fuir, combattre, et
  **se figer**. L'immobilité tonique est la réponse la plus fréquente à une
  menace soudaine et écrasante. Elle doit sortir du modèle — jamais d'une
  branche manquante.
- **On ne réagit pas à un compte global mais à ce qu'on touche du coude.** Un
  homme ignore combien des siens sont tombés à l'autre bout de la ville ; il
  sait que celui qui était à sa gauche n'y est plus.
- **L'hystérésis est physiologique, pas cosmétique.** L'adrénaline a un temps de
  montée et un temps de descente. On ne change pas d'état deux fois par seconde,
  et ce n'est pas un lissage d'affichage : c'est une glande.

### 2. Tout est normalisé sur [−1, 1]

Signaux d'entrée, états internes, sorties : **tout**. Sans exception.

- `+1` = le pôle favorable (intact, frais, épaulé, dégagé).
- `0` = l'ordinaire, l'homme moyen dans la journée moyenne.
- `−1` = le pôle défavorable (à bout, seul, acculé).

Ce n'est pas une commodité d'écriture, c'est ce qui rend les couches
**composables**. Deux grandeurs dans la même échelle se somment, se pondèrent et
se comparent honnêtement ; deux grandeurs dans des unités différentes ne se
comparent qu'au moyen d'un coefficient arbitraire — et un coefficient arbitraire
est exactement ce qu'on ne veut plus.

Conséquence pratique : **toute fonction sort d'une saturation**, jamais d'un
écrêtage. On borne par la forme (`tanh`, une fraction rationnelle), pas par un
`Math.min` posé après coup — sinon on fabrique une bosse artificielle à la borne,
là où le modèle devrait s'aplatir doucement.

### 3. Jamais de constantes, toujours des fonctions

**C'est la règle la plus importante des trois, et c'est celle qui a été payée
comptant.** Trois fois dans la même journée, une constante a menti :

- `SEUIL_RECUL = 0.5` — « sous la moitié de ses points, on décroche ». Vrai à
  300 points de vie où la moitié faisait sept coups encaissés. Le jour où les
  points sont passés à 30, la moitié valait **moins d'un coup** : tout homme
  touché une fois décrochait pour la nuit, et l'on a vu des lignes entières de
  statues plantées à un mètre de l'ennemi. La constante encodait un rapport
  qu'elle ne pouvait pas voir.
- `RIPOSTE = 0.55` — des points de vie retranchés en valeur absolue. Elle a dû
  être divisée par dix à la main, en même temps que les points de vie, faute de
  quoi une porte tuait ses assaillants en deux secondes.
- Un budget d'effort comparé à un score qui servait aussi à classer. Les deux
  s'écrivaient en mètres et ne disaient pas la même chose : toute troupe en
  ordre serré est devenue inattaquable, et l'assaut a traversé la ville sans se
  battre.

Donc : **un seuil est une fonction de l'état, pas un nombre**. `entame(h)` se
calcule à partir de ce qu'un coup typique retire, et survit à un changement de
l'échelle des points de vie. `portee(h)` sort de son arme et de son œil. La
question à se poser devant chaque nombre est : *de quoi est-il le rapport ?* —
et si la réponse existe, c'est ce rapport qu'il faut écrire.

**L'exception, et elle est étroite** : une constante est permise quand c'est une
**mesure du monde physique**, pas un réglage. La largeur d'épaules d'un homme en
armes, la vitesse d'une marche, le temps qu'un œil met à s'apercevoir de quelque
chose, la portée d'une lame. Elles vivent dans `mesures.js`, elles portent leur
source en commentaire, et **elles ne se règlent jamais pour obtenir un
comportement** : elles se corrigent quand on apprend qu'on s'était trompé sur le
monde.

Test avant d'écrire un nombre : *si une autre grandeur du modèle double, celui-ci
doit-il bouger ?* Si oui, ce n'est pas une constante — c'est une fonction qu'on
n'a pas encore écrite.

---

## Ce que ça implique pour la forme du code

- **Des fonctions pures.** Une couche prend un état et rend un nombre. Elle
  n'écrit rien, ne mute rien, n'appelle aucune autre couche. Ce qui se souvient
  (l'adrénaline qui monte, la décision qu'on tient) est un état explicite passé
  en argument et rendu en sortie, jamais un champ posé au passage.
- **Aucune dépendance à `bataille2d.js`.** Ces fichiers doivent tourner dans
  node, seuls, sans faux navigateur. C'est la condition pour qu'on puisse les
  mesurer au lieu de les regarder.
- **Les couches ne se parlent pas.** Elles ne se connaissent que par leurs
  sorties, que l'arbitre compose. Une couche qui en appelle une autre refait la
  cascade de `soldat()` avec plus d'étapes.

## État d'avancement

- [x] `1-corps.js` — première passe
- [ ] `2-reflexion.js`
- [ ] `3-interpretation.js`
- [ ] `4-envie.js`
- [ ] l'arbitre

Rien de tout ceci n'est encore branché sur le jeu. `bataille2d.js` continue de
tourner sur sa cascade ; on ne remplacera rien tant que les quatre couches ne
seront pas mesurées côte à côte.
