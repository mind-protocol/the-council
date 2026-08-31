# Arbitrage du staging — 4e jour de la 4e lune, an 129

---

## SECONDE PASSE — trois pièces de plus (19 au total)

`tete-gerardys-129-4-4`, `tete-corlys-129-4-4`,
`tete-denys-bar-emmon-129-4-4`. Trois fois le même gabarit, trois fois la même
unique mutation : `intentions/<qui>` opération `tete`, champ `date_maj → 129.4.4`.
Et rien d'autre.

### **REFUSÉES toutes les trois — mais les pièces ne sont pas fautives**

Chacune porte, écrit par le script lui-même : `"matiere": {"journal": [],
"conclusion": false}`, et *« ajoute ici tes mutations d'etapes et de croyances
d'apres la matiere, puis applique le tout »*. **Le script ouvre le dossier et
dit honnêtement qu'il est vide ; il ne prétend pas l'avoir rempli.** Ce qu'il
propose, en revanche, est la seule mutation qui ne devrait jamais partir seule.

**`date_maj` est le champ que l'audit lit pour dire qu'une tête est périmée.**
La poser sans avoir touché une croyance ni une étape, c'est **éteindre le
témoin sans réparer la fuite** — la panne silencieuse que je reproche partout
ailleurs, cette fois fabriquée de ma propre main.

### Ce que l'ouverture des trois rapports apprend, et qu'aucune pièce ne dit

Les trois rapports existent bien et portent `date_jeu: 129.4.4`. Mais celui de
Gerardys s'ouvre directement sur un **`cahier2`** copieux — des versements aux
affaires, dont le verrou neuf `11041` *« Les sept jours rendus ne sont à
personne »*. **Pas de `journal`, pas de `travaux`, pas de `conclusion`.**

Autrement dit : **la dépêche du 4e a fait travailler ces hommes sur les
REGISTRES, pas sur eux-mêmes.** Il est donc parfaitement normal que leur tête
n'ait pas bougé — et parfaitement faux de la dater. La pièce a raison de ne
rien trouver ; c'est la conclusion qu'elle en tire qui est mauvaise.

### Les trois ne sont pas dans la même situation

| qui | `date_maj` actuelle | écart | ce que la mutation ferait |
| --- | --- | --- | --- |
| gerardys | 129.4.3 | 1 jour | cosmétique aujourd'hui — dans la tolérance ; **mensonge demain** |
| corlys | 129.4.3 | 1 jour | idem |
| **denys-bar-emmon** | **129.4.2** | **2 jours** | **éteindrait un signal VRAI** — sa tête est hors tolérance et n'a pas été relue |

**Denys est le seul cas réel**, et il ne se règle pas par une date : il se règle
par une relecture. Il rejoint `L.33` (relire les têtes du quartier en retard),
au lieu de disparaître de l'audit sans avoir été touché.

### La règle que je pose, et qui vaut pour toutes les pièces de ce gabarit

> **`date_maj` ne se pose jamais seule.** Une dépêche qui n'a rendu ni journal
> ni conclusion ne rafraîchit aucune tête : le script devrait alors ne RIEN
> proposer, plutôt que proposer la seule mutation qui trompe l'audit. Dater une
> tête est le dernier geste d'une mise à jour, jamais le premier ni le seul.

C'est un billet à dev, et il tient en une phrase : *si `matiere.journal` est
vide et `conclusion` fausse, ne pas émettre de pièce.*

---

16 pièces. **Quatorze sont déjà triées** (voir *La porte*, dépouillement du 4e) :
6 au plan de la Couronne qui repartent à mj-portreal, 1 par `reparer_renvois.py`,
6 périmées écartées avec leur raison, 1 vivante — le mot de Waltyr Poix.
**Deux sont neuves de ce soir, et les voici arbitrées.**

---

## 1. `20260831-gunthor-darklyn-mort.json` — de mj-sombreval — **OUI, EN ENTIER**

Le meilleur travail de proposition que j'aie eu à arbitrer. Il porte sa pièce
fondatrice (`sac-sombreval`, statut `résolu`, 129.4.3), il nomme ce qui ne passe
pas par le vocabulaire au lieu de le contourner, et il vérifie ses effets de
bord au lieu de les affirmer.

**Les quatre mutations : OUI, sans réserve.**
- `personnages/gunthor-darklyn → etat: "mort"`. Il était `dormant` avec
  condition `mort` — un état qui autorise encore la relecture. C'est
  exactement mon L.14, et l'argument est le bon : **c'est l'`etat` que le tick
  relit**, pas la `condition`.
- Les trois étapes (`gunthor-ecrit-de-la-reine`, `gunthor-la-chaine-du-quai`,
  `gunthor-sacre`) → `abandonne`, `jours_restants: 0`. Trois étapes vivantes
  chez un décapité.

**La suppression du bloc `intentions` : OUI, et elle reste à ma main.** Il
n'existe pas d'opération `tete_retirer` dans le vocabulaire — la proposition le
dit elle-même au lieu de bricoler. **Ma main est coupée (P05) : je ne peux pas
la faire ce soir.** La proposition a prévu ce cas et c'est ce qui la rend
bonne : *« appliquées seules, les mutations rendent le mort inoffensif même si
le bloc reste une nuit de plus »*. Qu'on applique donc la ceinture tout de
suite ; le bloc part au premier réveil où j'ai la porte.

**Ce que je confirme et qu'ils ont eu raison de ne pas toucher** :
`pli-protection-sombreval` reste `remis`, main `marec-fosse`. L'acte existe, il
est dans une ville tenue par Criston, et c'est de la matière — pas une écriture
à annuler. Ma reine ignore encore où il est ; son déclencheur sur Sombreval
porte précisément *« qui avait mon acte de protection en main, et s'il est
vivant »*.

---

## 2. `20260831-tete-rhaenyra-siege-quitte.json` — **SUSPENDUE : LE JOUEUR EST REVENU**

> **AJOUT, quelques minutes après l'arbitrage ci-dessous.** Le siège s'est
> rouvert : le joueur a repris la main à 9h00 (une question sur l'appareil,
> `action-1788136501310`). **Cette tête ne doit donc PAS être appliquée.**
> L'appliquer ferait tourner un acteur simulé sur un siège de nouveau tenu — et
> le `si_bloque` du Guet, celui-là même que je bornais deux paragraphes plus
> bas, deviendrait actif alors que le joueur est assis là pour en décider.
>
> Elle n'est pas annulée : elle est **en réserve**, prête à servir le jour où
> le siège se videra pour de bon. Tout ce qui suit reste valable pour ce
> jour-là, réserves comprises.
>
> Et la leçon est plus large que la pièce : **une tête de siège quitté se
> vérifie contre l'inbox à la seconde où on l'applique, jamais à la seconde où
> on l'écrit.** Entre les deux, le joueur peut être revenu.

### L'arbitrage sur le fond — **OUI, DEUX RÉSERVES**

Le siège du joueur est quitté ; sans tête, la reine dormirait pendant qu'on
regarde le monde tourner. La tête est juste : son `ignore` est exact au fait
près (Sombreval tombée, le Trident levé **au nom de Daemon**, l'acte aux mains
de l'intendant, les bêtes des fosses, Rosby qui l'apprendra par une rumeur), et
ses croyances ne portent rien qu'elle ne sache.

### Réserve 1 — le champ `echelle`, et ce n'est PAS la pièce qui a tort

`CHAMPS_TETE_REQUIS` (`scripts/etat/mutations/vocabulaire.py` l.40) exige
`echelle`. La pièce ne le porte pas. **Avant de la corriger, j'ai compté :
`"echelle"` apparaît ZÉRO fois dans `etat/intentions.json`** — pas une tête sur
l'ensemble du corpus.

Et `scripts/temps/bouche.py` l.19 l'écrit en toutes lettres :
**« L'ÉCHELLE A DISPARU, et le QUARTIER la remplace. Ce qui la remplace ne se
déclare pas : il se MESURE, à chaque tick, sur la topologie. »** Le module dit
même pourquoi : trois systèmes réglaient l'importance d'un acteur et se
marchaient dessus ; l'échelle posée à la main recopiait ce que le tissu
calculait déjà et **se contredisait avec lui six fois sur quinze**.

**Donc la pièce est conforme à la doctrine et le validateur est un résidu.** Si
l'on « répare » la pièce en y écrivant une échelle, on grave à la main
exactement ce que la doctrine a supprimé, et on rouvre le troisième système. Je
refuse cette réparation-là. C'est `CHAMPS_TETE_REQUIS` qui doit lâcher
`echelle` — et c'est de la même famille que R.11 : **le code déclare une norme
que le corpus ne porte pas, et cette fois le corpus a raison.**

Tant que ce n'est pas tranché, aucune tête neuve ne peut entrer par la porte.

### Réserve 2 — le `si_bloque` du nom du Guet dépasse ce qu'elle a décidé

L'étape `rhaenyra-le-nom-du-guet` porte : *« Si le nom n'est pas rendu avant
midi, elle ne monte pas : elle prend le prochain huitième, écrit la charge de
sa main, et le prince apprendra le nom qu'elle a mis à la place du sien. »*

À neuf heures, elle a dit **« Nous attendons midi »** et rien d'autre. Nommer
un officier du Guet à la place de son époux est le geste le plus lourd de la
journée, et **c'est précisément le fil unique que le joueur a laissé ouvert en
partant.** Un joueur qui revient et découvre que son personnage a nommé
quelqu'un pendant son absence n'hérite pas d'une situation : il hérite d'une
décision qu'on a prise pour lui.

**Verdict : l'étape passe, le `si_bloque` se borne.** Ce qu'elle a réellement
tranché va jusqu'à midi et pas au-delà. Rédaction que je retiens :

> *« Si le nom n'est pas rendu avant midi, elle ne monte pas et elle ne nomme
> personne : elle fait porter au registre, sous son nom et daté de midi, que la
> case est restée en blanc et par la faute de qui. Le prochain huitième jour
> reste ouvert. »*

C'est plus dur pour Daemon, plus fidèle à ce qu'elle a dit ce matin, et ça ne
brûle pas la décision du joueur.

Le reste de la pièce — les trois autres étapes, les deux déclencheurs,
l'`attitude_joueur` qui dit honnêtement le prix du départ — passe tel quel.
Comptes : 6 croyances / 4 étapes / 2 déclencheurs, contre un budget de scène de
6 / 5 / 3. Ça tient.
