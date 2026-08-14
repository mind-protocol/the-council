# survival-stack — ce qu'un homme fait, en quatre couches et une composition

> Relu et renommé le 3e jour de la 4e lune, an 129, par Wenna la Nommeuse
> (affaire `affaire-migrer-la-bataille-vers-la-stack`, action ⚔️ 90320).
> **Ce fichier se contredisait d'une section à l'autre.** Les contradictions sont
> tranchées ici et la trace de chaque arbitrage est en bas, sous « Les mots, et
> les deux qu'on a écartés ». Rien dans les trois règles n'a bougé : elles
> étaient justes.

**Ce dossier n'est pas une refonte à partir de rien.** Les couches 2, 3 et 4
existaient déjà avant d'être écrites ici — sous une autre forme, dans la cascade
de `soldat()` de `bataille2d.js`, qui exécute des ordres, calcule des cibles et
poursuit un but. On ne construit pas à côté du vide : **on déménage**, morceau
par morceau, en mesurant à chaque cran. Le mot est important, il commande tout le
reste du fichier.

## Les quatre couches — et le cinquième fichier, qui n'est pas une couche

Chacune répond à une question qu'un homme se pose, dans l'ordre où il se la pose
— et l'ordre n'est pas négociable, parce qu'il est celui de l'urgence et non
celui de l'importance.

| # | fichier | la question, dans SA bouche | ce qu'elle produit |
|---|---|---|---|
| 1 | `1-corps.js` | *qu'a appris mon corps pour survivre ?* | un geste, sans qu'on l'ait voulu |
| 2 | `2-reflexion.js` | *comment me sortir de cette situation ?* | une issue, cherchée |
| 3 | `3-interpretation.js` | *comment faire ce qu'on m'a dit comme je veux ?* | une manière de tenir l'ordre |
| 4 | `4-envie.js` | *qu'est-ce que je veux, maintenant ?* | un désir, gratuit |
| — | `5-…` (à nommer, voir plus bas) | *rien : elle ne se pose pas de question* | **la composition des quatre sorties** |

**Quatre couches, cinq fichiers.** Le cinquième ne pense pas et n'a pas de
question à lui : il compose. Compter « cinq couches » est une faute qui se
propage — elle fait chercher une cinquième question, et il n'y en a pas.

Les quatre questions sont formulées à la première personne, et ce n'est pas un
ornement : aucune ne demande *ce qui serait optimal*, toutes demandent *ce que
moi je fais*. Une couche qui se met à calculer un optimum global s'est trompée
d'homme.

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
L'**emprise** de la couche 1 est donc une *fonction de l'alarme*, pas une règle
de priorité. C'est ce qui fait qu'un homme calme réfléchit, qu'un homme paniqué
ne fait que ce que son corps sait faire, et qu'entre les deux les deux se
mélangent.

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
  et ce n'est pas un lissage d'affichage : c'est une glande. Le banc de la
  couche 1 la sort toute seule : **3,0 s pour monter, 45,0 s pour retomber**,
  un rapport de quinze.

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
- **Aucune dépendance à `bataille2d.js`** — au sens du code : ces fichiers
  tournent dans node, seuls, sans faux navigateur. C'est la condition pour qu'on
  puisse les mesurer au lieu de les regarder.
  **Mais il existe une dépendance de fait, et il faut la nommer pour ne pas se
  mentir** : `3-interpretation.js` compte les clauses d'un ordre *dans l'ordre
  exact où la transmission les arrache* (`interdit`, `declencheur`, `marge`,
  `objet`), et cette liste est celle de `bataille2d.js`. Si elle change là-bas
  sans changer ici, la couche 3 se met à mesurer autre chose que ce qu'elle croit
  mesurer, **sans qu'aucun test ne casse**. Une dépendance qu'aucun `require` ne
  déclare est plus dangereuse qu'une dépendance déclarée, pas moins.
- **Les couches ne se parlent pas.** Elles ne se connaissent que par leurs
  sorties, que le cinquième fichier compose. Une couche qui en appelle une autre
  refait la cascade de `soldat()` avec plus d'étapes.

## Où l'on en est — compté sur le disque, non de mémoire

| fichier | écrit | chargé par `jeu.html` | conduit dans le jeu |
|---|---|---|---|
| `1-corps.js` | oui, 1 566 l. + banc | oui | **oui** — six gestes, voir plus bas |
| `2-reflexion.js` | **non** | — | — |
| `3-interpretation.js` | oui, 193 l. | oui | **oui** — `Interpretation.pas` et `deSoiMeme` |
| `4-envie.js` | oui, 229 l. | oui | partiellement — `Envie.temperament` |
| la composition | **non** | — | — |
| `scenario-3-contre-2.js` | oui — le banc de la couche 1, hors pile | — | — |

**Ce que la couche 1 conduit aujourd'hui, nommément** : `sidération`, `fuite`,
`recul`, `serrer`, `ruée`, et les **bras morts** (`ballants`, qui retire la
capacité de frapper sans dicter de conduite). `planté` ne prend rien — c'est
justement l'état où le corps n'a rien à dire, donc la tête garde la main, et
c'est ce qui maintient le déménagement progressif.

## Le déménagement est PROGRESSIF, et il ne se mérite pas

**On n'attend pas que les cinq fichiers soient écrits.** Ce fut la première
intention, et c'était une erreur : elle promettait de ne rien montrer dans le jeu
avant la fin de tout, donc de ne jamais rien vérifier là où ça compte. **On ne
valide pas une couche en la regardant calculer à côté.**

Les étapes, et **les deux premières sont derrière nous** :

1. ~~**Voir avant de conduire.**~~ *Faite.* La couche tournait pour chaque homme
   et s'affichait sous le doigt, à côté de ce que la tête décidait.
2. ~~**Conduire un état, puis deux.**~~ *Faite, et dépassée* — six gestes, pas
   deux.
3. **Élargir**, en mesurant à chaque cran ce que ça change au compte des morts et
   des fuyards. ← *nous sommes ici*
4. **Remplacer la cascade** morceau par morceau, quand les couches hautes
   arriveront — et non l'inverse.

### ⚠ IL N'Y A PLUS DE SEUIL D'EMPRISE, ET IL NE FAUT PAS EN REMETTRE

L'ancienne version de ce fichier finissait sur : *« le seuil d'emprise est le
bouton : le baisser donne plus de place au corps »*. **C'est faux depuis que
`pilote` et `emprise > 0,60` ont été retirés.** Ce bouton n'existe plus. Qui le
cherche ne le trouvera pas ; qui le remet réintroduit la faute qu'on a payée pour
supprimer — la couche décidait *à côté* de la cascade, les deux jugeaient de la
même chose, et l'on héritait du pire des deux sans plus savoir lequel produisait
quoi.

Ce que le seuil protégeait a été remplacé par deux mécaniques, et il faut les
nommer toutes les deux :

- **L'emballement du grégarisme** — une rétroaction positive — est borné par
  `c.social` : le niveau ambiant auquel on s'habitue, dont seul le DÉPASSEMENT
  passe. Une ligne uniformément tendue ne transmet plus rien ; un seul homme qui
  craque à l'instant transmet tout.
- **`emprise` n'a pas disparu : elle agit DANS l'élection**, par `SOUS_EMPRISE`.
  Fuir, se figer et se ruer demandent que le corps ait la main — ce sont les
  trois gestes dont le nom même est « le corps a pris la main ». Un homme calme
  ne part donc pas en courant, et **ce n'est plus un seuil posé dehors qui l'en
  empêche, c'est le modèle**.

**Il n'y a qu'une emprise, et c'est le point.** Le même nombre sort vers les
couches 2, 3 et 4 *et* borne les gestes de la couche 1 elle-même. Le défaut
principal de la première passe était exactement là : elle sortait vers les autres
et n'agissait jamais sur elle-même, si bien qu'un conscrit rompait à 0,0 s, sans
un stimulus, **avec `emprise` à 0,00** — un geste de corps élu pendant que le
corps ne tenait rien du volant. Après correction, il rompt à 5,7 s et le relevé
montre enfin un ARC : coup reçu à 1 s, dérobade, il tient, la glande monte de
−1,00 à −0,16, l'emprise atteint 0,78, **et alors** il s'en va.

---

## Les mots, et les deux qu'on a écartés

Chaque ligne : le mot retenu, ce qu'il désigne exactement, et les deux candidats
écartés avec la raison. **On ne revient pas dessus dans un mois.**

### `emprise` — retenu

*De combien le corps tient le volant, entre 0 et 1, fonction de l'alarme et du
dressage.* — Écartés : **`panique`**, qui nomme une cause là où l'on mesure un
effet (un vétéran très effrayé garde la main ; sa panique est haute et son
emprise basse, les deux mots ne peuvent donc pas être le même) ; **`priorité`**,
qui dit un rang alors que c'est un continuum, et qui ferait relire toute la pile
comme une liste ordonnée — exactement le contresens que la couche 1 passe une
page à démonter.

### `SOUS_EMPRISE` — retenu, et le « seuil d'emprise » enterré

*La courte liste des gestes que le corps seul peut produire (`fuite`,
`sidération`, `ruée`), pondérés par l'emprise à l'intérieur de l'élection.* —
Écartés : **`seuil d'emprise`**, qui promet une comparaison et un bouton, dont ni
l'un ni l'autre n'existent plus, et qui a donc menti à ce fichier pendant toute
sa durée de vie ; **`garde-fou`**, qui était le nom de la première passe et
désignait `pilote` + `> 0,60` — deux pièces retirées le même jour ; le réemployer
ferait croire qu'on a gardé la chose sous un autre nom.

### `pilote` — **à renommer, et ce n'est pas ma main**

Le champ `h.l1.pilote` ne pilote plus rien : il est posé pour la bulle de survol,
et son propre commentaire le dit (`« pour la bulle de survol, plus pour la
conduite »`). **Un nom qui a survécu à sa fonction est pire qu'un nom absent** :
il fait chercher une conduite là où il n'y a qu'un affichage.

Le mot juste : **`corpsAgi`** — *vrai si la couche a pris ce battement-ci*. Un
fait de battement, pas un régime. — Écartés : **`pilote`**, qui dit une conduite
permanente, et qu'un lecteur pressé prendra pour le drapeau retiré ; **`actif`**,
car la couche est toujours active — ce qui varie n'est pas qu'elle vive, c'est
qu'elle ait AGI. (Même remarque pour `corpsPilote`, sa copie dans ce que la vue
dépose au MJ.)

`bataille2d.js` est l'office du **Fer** (Ygga Main-de-Pierre) : je pose le nom et
la raison, la main qui grave est la sienne.

### Le cinquième fichier — **je ne le nomme pas aujourd'hui, et je dis pourquoi**

Deux textes lui donnent deux métiers incompatibles :

- Ce README, règle de forme : *« une couche qui rendrait un objet obligerait
  l'arbitre à cesser d'être une somme »* — il **compose** des nombres, il ne
  tranche rien. Nom qui suivrait : `5-composition.js`.
- L'affaire, action ⚔️ 90311 : *« écrire l'arbitre : qui, du corps ou de la tête,
  tient la main sur un geste donné »* — il **désigne un vainqueur**. Nom qui
  suivrait : `5-la-main.js`.

**Ce n'est pas un désaccord de vocabulaire, ce sont deux modèles.** Une somme
mélange les quatre sorties et n'en préfère aucune ; une main choisit une couche
et jette les autres pour ce geste-là. Elles ne rendent pas la même bataille et ne
se testent pas de la même façon. Nommer avant qu'on ait tranché ferait tenir la
décision par le nom, et l'on découvrirait dans trois semaines qu'on a bâti la
mauvaise pièce parce qu'un fichier s'appelait comme ça.

**Écarté d'avance dans les deux cas : `arbitre`.** Un arbitre départage des
prétendants — le mot suppose déjà la réponse « on tranche », et il l'a supposée
en silence dans tout ce fichier. Écarté aussi : `orchestrateur`, jargon qui
dirige, alors qu'ici rien ne dirige.

Cette contradiction est portée à l'affaire comme **verrou 🔒 90330**. Elle se
tranche avant qu'on écrive une ligne du cinquième fichier, pas après.
