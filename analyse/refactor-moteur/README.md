# Dossier de référence du refactor du moteur

Sortie du **lot 0** de [`docs/bataille/refactor-complet-moteur.md`](../../docs/bataille/refactor-complet-moteur.md) :
ce que le moteur rendait au moment où le refactor a commencé, pour qu'un
déplacement de blocs se voie.

Posé le **26 août 2026**, sur `master` à `133878c` plus les modifications en
cours.

## Ce qu'il contient

| Fichier | Ce que c'est |
|---|---|
| `etalon-depart.json` | copie de `ecrans/modules/bataille/etalon-moteur.json` au moment de la reprise |
| `releve-220s.txt` | la même condition poussée à 220 s, pour voir ce qui se passe *après* la fenêtre de l'étalon |

La condition est celle du banc : 150 hommes, « La porte de la Gadoue », graine
20161219, pas de 0,05 s, ni peuple ni tournée. Elle se rejoue par

```bash
node ecrans/modules/bataille/banc-moteur.js
```

## L'étalon a été reposé, et il faut savoir pourquoi

L'étalon en place datait du **24 août**. Sept fichiers de la chaîne avaient
changé depuis (`mesures`, `roster`, `1-corps`, `corps-adapt`, `reflexion-adapt`,
`commandement`, `bataille2d`), au fil des trois derniers commits — géographie de
Port-Réal unifiée, dragons et commandement enrichis, croisement de vingtaines.
Le banc rendait donc 29 relevés en désaccord : un étalon périmé, pas une
régression introduite par le refactor.

On l'a reposé sur l'état du 26 août. **C'est cet état-là qui fait foi pour la
suite** : à partir du lot 1, toute extraction doit rendre l'égalité exacte, et un
écart non nul est une faute du refactor, jamais une tolérance à élargir.

## Ce que le relevé de départ dit — et il ne dit rien de bon

Sur 100 s comme sur 220 s, dans la condition du banc :

- **0 mort, 0 blessé, 0 fuyard** ;
- la porte de la Gadoue descend de 9000 à **900 points de bois, et s'y arrête** :
  un `porte-abimee`, jamais de `porte-cede` ni de `porte-enfoncee` ;
- aucun `contact`, aucun `premier-sang`, aucun `chef-tombe` ;
- 99 hommes en colonne et 99 qui tiennent, à la fin comme au début.

L'étalon du 24 août, lui, portait 6 morts, 3 blessés, le contact, le premier
sang, la porte enfoncée à la hache et le verrou ouvert. **Le fer ne se touche
plus.** Doubler la durée n'y change rien : ce n'est pas une bataille devenue
lente, c'est une bataille qui s'arrête.

Ce défaut est **antérieur au refactor** et il n'est pas de son ressort immédiat.
Il est noté ici parce que c'est exactement ce que le lot 0 demande de relever
avant de déplacer quoi que ce soit, et parce qu'il tombe dans le périmètre
annoncé des lots 2 et 3 :

> « Fermer les derniers mètres est un mouvement physique ; aucun combattant ne
> s'arrête à 5–10 m parce que l'état `engager` a été atteint. »
> — *validation du lot 3 : « contact réellement fermé jusqu'à la portée »*

**Conséquence pratique pour la suite.** Tant que le contact ne se ferme pas,
l'étalon ne mesure plus le combat : il mesure une marche, une porte frappée une
fois, et des ordres qui circulent. C'est suffisant pour valider une extraction —
ce que le lot 1 demande — et insuffisant pour valider un changement de modèle du
combat. Le premier lot qui touche au contact devra donc reposer une condition où
le fer se touche, et non se contenter de l'égalité de celle-ci.

## Ce que le lot 0 n'a pas fait

- ~~Les métriques manquantes ne sont pas encore instrumentées.~~ **Faites au
  lot 2** : `banc-monde.js` relève téléports, hommes dans le bâti, A* calculés,
  densité, distance P90 au chef et arrêtés hors portée — voir plus bas. Restent
  les décisions et les communications, qui attendent que quelque chose écrive
  dans le journal (`moteur/commun/traces.js`).
- C5, C6, le ratissage, le messager et l'entrée de bâtiment n'ont **pas** été
  relevés séparément : seule la condition du banc l'a été.

---

## Lot 2 — ce que les sondes disent, et pourquoi le fer ne se touche pas

`ecrans/modules/bataille/banc-monde.js` est la sonde qui manquait. Elle est
**extérieure au moteur** : elle fait tourner la bataille et regarde la troupe
entre deux pas, sans instrumenter une ligne — elle ne peut donc pas fausser
l'étalon pendant une extraction.

```bash
node ecrans/modules/bataille/banc-monde.js
```

Premier relevé, sur la condition de référence (150 hommes, la Gadoue, 100 s) :

| sonde | valeur | lecture |
|---|---|---|
| téléports | **0** | aucun pas au-dessus de 8 m/s |
| hommes dans le bâti | **0 %** | 0 sur 23 900 relevés |
| A* calculés | **4** pour 16 unités | 0,017 par homme — la route est bien collective |
| densité maximale | 2,2 /m² | jamais serré ; 0 seconde au-dessus de 4 |
| distance au chef, médiane | 7,6 m | |
| distance au chef, **P90** | **92,5 m** | la queue traîne à quatre-vingt-douze mètres |
| sans pair de son unité | 14,6 % | |
| arrêtés à 5–10 m d'un ennemi | **0 %** | |

**Trois des promesses du lot 2 sont déjà tenues** : pas de téléport, pas de
traversée de mur, pas d'A* par homme. Ce n'était pas su — rien ne le mesurait.

### Le fer ne se touche pas, et ce n'est pas un bouchon

`arrêtés à 5–10 m d'un ennemi : 0 %` élimine l'hypothèse du contact qui ne se
ferme pas : personne ne se fige devant l'ennemi. La distance de l'assaut à la
porte, relevée toutes les vingt secondes, dit autre chose :

| t | assaut → porte |
|---|---|
| 0 s | 110 m |
| 40 s | **13 m** |
| 60 s | 15 m |
| 80 s | 34 m |
| 140 s | 101 m |
| 220 s | 110 m |

**La colonne arrive à la porte à quarante secondes, ne la frappe jamais, puis
fait demi-tour et retourne à son point de départ.** Le verrou reste à 900 points
de bois — c'est son maximum, pas une usure : il n'a pas été touché une fois. Les
états le confirment : `colonne` tombe de 121 à 87 pendant que `forme` monte de
13 à 49. Ils se reforment au lieu d'assaillir.

Ce n'est donc **ni un défaut de topologie, ni un défaut de collision** — le
monde physique fait son travail. C'est une décision : quelque chose ordonne un
rassemblement qui prime sur l'assaut, et rien ne le révise quand la porte est à
treize mètres. Le lot 6 (« boucle après péremption », « `tenir` n'est choisi que
si une zone ou une contrainte lui donne une utilité ») est l'endroit où ça se
répare, pas le lot 2.

**Conséquence pour l'étalon**, et elle est ferme : tant que ce défaut tient, la
condition du banc mesure une marche, une porte jamais frappée et des ordres qui
circulent. C'est assez pour valider une extraction — le lot 2 s'en contente — et
ce n'est pas assez pour valider un changement de modèle du combat.

### Ce que le lot 2 a extrait

`moteur/monde/topologie.js` — le sol, le bâti, l'eau : `dehors`, `solConnu`,
`obstacleConnu`, `obstacleEn`, `libreEn`, `reglerTerrainEpreuve`, `degager`,
`murPres`, `obstaclePres`, `demiLibre`, plus `RAYON` et `DEGAGE_MAX`. Cent
soixante lignes **déplacées telles quelles**, commentaires compris — ce sont eux
qui portent les trois fautes qu'on a mis des semaines à trouver (un homme posé
dans un mur, la marge qui bloque une venelle, la rue plus large que le masque).

Le monolithe garde une ligne de liaison qui redonne les mêmes noms au même sens :
aucun site d'appel ne change. C'est la forme que prendront les quatre
extractions suivantes — navigation, mouvement, collisions, combat.

---

## Lot 3 — relevé avant de toucher au combattant

Trois faits, établis en lisant le code et non en le devinant. Ils expliquent
ensemble pourquoi « j'essaie de X parce que Y » ne dit pas la vérité sur un
homme, et pourquoi il n'y a pas d'assaut solo *observable*.

### 1. La pensée est une légende, pas une trace

`penser()` est appelée depuis **56 endroits**, et chacun nomme son propre
« système » :

| ce que le système nomme | appels |
|---|---|
| une vraie couche (`corps · couche 1`, `réflexion · couche 2`, `envie · couche 4`) | **10** |
| la branche qui a bougé l'homme (`front de porte`, `ordre de formation`, `messager du Guet`, `coureur d'ordre`, `franchissement en file`…) | **46** |

Or l'arbitre existe et tourne à chaque battement : `QuiConduit` élit laquelle
des quatre — `ordre`, `corps`, `reflexion`, `envie` — tient les jambes, et le
résultat est posé dans `h.conduit` par `reflexion-adapt.js`. **Deux vérités sur
le même homme au même instant, et l'écran ne lit que la mauvaise.**

`diagnostic()` soupçonne déjà la divergence homme par homme (« le corps propose
X, un autre système conduit ») — personne ne l'a jamais comptée sur l'armée.
C'est ce que fait `banc-combattant.js`.

### 2. L'arbitre est consulté au tiers d'une cascade de 855 lignes

`soldat()` fait **855 lignes** et **38 sorties anticipées**. Les couches sont
observées en tête (L4810 pour la 1, L4837 pour la 2, et c'est là que l'élection
est posée), mais la seule ligne qui AGIT sur cette élection —
`if (executerReflexion(h, dt)) return;` — est à la **236ᵉ ligne** de la cascade.

Tout ce qui retourne avant elle — le saignement, le ratissage, le ralliement, la
rupture — contourne l'arbitre **par construction**, pas par accident. C'est
l'item « éliminer les branches de mouvement qui contournent `QuiConduit` », et
il ne s'agit pas d'éliminer des exceptions : il s'agit d'inverser l'ordre.

### 3. Deux couches sur quatre sont calculées trop tard

| couche | où elle est calculée | quand |
|---|---|---|
| `l1` corps | `corps-adapt.js` | **avant** l'élection |
| `l2` réflexion | `reflexion-adapt.js` | **avant** l'élection |
| `l3` interprétation | en ligne dans `soldat()`, L5391 | **après** |
| `l4` envie | en ligne dans `soldat()`, L5579 | **après** |

L'élection lit donc `l3` et `l4` du battement précédent — et seulement de celui
où la cascade était allée assez loin pour les écrire. `reflexion-adapt.js` le dit
lui-même en commentaire : « `h.l3` date du dernier ordre reçu et `h.l4` du
dernier pillage — ils sont ce qu'ils sont. La main les lit tels quels […] et il
faut le savoir en lisant `h.conduit`. »

C'est exactement l'item « faire passer corps, réflexion, interprétation et envie
par un adaptateur unique » : les quatre au même endroit, **avant** l'élection.

### Le banc

```bash
node ecrans/modules/bataille/banc-combattant.js
```

Extérieur au moteur, comme `banc-monde.js`. Il met côte à côte l'élection et la
pensée affichée, compte le désaccord, dit ce que chaque homme porte réellement
(ordre reçu, unité, chef connu, mémoire), relève la disponibilité des quatre
couches, et compte les attaquants sans un seul pair de leur unité à douze mètres.

### Le premier relevé, et ce que le premier pas a changé

Sur la condition de référence (150 hommes, la Gadoue, 100 s) :

| mesure | avant | après le 1er pas |
|---|---|---|
| pensée ≠ élection | **27,3 %** | 27,3 % *(rien ne lit encore les nouveaux champs)* |
| l'arbitre dit « le corps tient les jambes » | 28,7 % | — |
| la pensée affichée dit « corps » | **1,4 %** | — |
| couche 1 disponible | 97,9 % | — |
| couche 2 disponible | 97,9 % | — |
| couche 3 disponible | **55,9 %** | — |
| couche 4 disponible | **0,0 %** | — |
| un ordre reçu | **0,0 %** | **93,3 %** |
| un chef connu | **0,0 %** | **62,0 %** |
| une unité | 100 % | 100 % |
| une mémoire récente | 100 % | 100 % |

**Le corps conduit près d'un tiers de l'armée et l'écran ne le dit presque
jamais.** C'est la phrase que ces chiffres portent, et c'est ce que « brancher la
pensée sur la vraie trace d'arbitrage » veut dire concrètement.

**Correction — la première lecture de ces deux lignes était fausse.** J'avais
écrit « l'arbitre élit entre quatre candidats dont un est toujours nul », présenté
comme un défaut. Vérifié en faisant tourner `QuiConduit` à la main : une envie
absente est notée **exactement comme une envie de zéro** — aucune prétention, pas
un `NaN`. Et c'est la sémantique voulue, écrite dans le code : « la convoitise
n'existe pas sans objet : un homme au milieu d'un champ ne veut rien, et ce n'est
pas *faiblement* — c'est rien. »

Le vrai défaut est ailleurs, et il est structurel. Sur 239 hommes vivants, **239
ont une escouade** — la condition d'entrée de `l3` n'est donc jamais fermée — et
pourtant **135 seulement ont une `l3`**. Les 104 autres ont tout ce qu'il faut :
leur battement est sorti de la cascade avant la 680ᵉ ligne, où le calcul se
trouve. Celui de `l4` est à la 870ᵉ.

**La couche d'un homme dépend de la distance que son battement a parcourue dans
`soldat()`.** C'est le même défaut que « l'arbitre est consulté à la 236ᵉ ligne »,
vu par l'autre bout : ce n'est pas une couche qui manque, c'est un chemin qui
décide de ce qui existe.

### Ce que le premier pas a fait, et ce qu'il n'a pas fait

`porterOrdreEtChef()` en tête de `soldat()` : chaque homme vivant porte
désormais l'ordre qu'il a reçu — avec sa version, son mode, sa destination et sa
date — et l'identité de son chef, avec l'heure et l'endroit où il l'a vu pour la
dernière fois.

C'est **additif** : rien ne lit ces champs, et l'étalon est strictement
identique. C'est délibéré — le jour où la délibération lira `h.ordreRecu` au lieu
de `u.ordre`, ce sera un changement de modèle, à mesurer et à annoncer.

Deux pièges relevés en chemin, et aucun des deux ne se voyait à la relecture :

- **on ne passe pas par `guideDe()`**, qui réaffecte `u.cadre.chef` quand le chef
  courant est tombé. L'appeler en tête de battement ferait observer une
  succession un cran plus tôt qu'aujourd'hui — un changement de comportement
  déguisé en lecture ;
- **la clef de fraîcheur d'un ordre d'unité est `version`, pas `n`.** La première
  écriture comparait `undefined` à `undefined` : l'homme retenait son PREMIER
  ordre et ne remarquait plus jamais les suivants. Quatre-vingt-treize pour cent
  des hommes portaient un ordre, et c'était toujours le même. Ça s'est vu en
  regardant une valeur réelle dans le navigateur, pas en relisant le code.

### Le deuxième pas — la couche 3 remise avant l'arbitre

C'est le premier **changement de modèle** du refactor : l'étalon a bougé, et il a
été reposé.

Ce qui était faux : `l3` se calculait à la 680ᵉ ligne de la cascade de 855, donc
seulement pour les hommes dont le battement descendait jusque-là. Ce que ça
coûtait : `QuiConduit.barre(l3)` rend **zéro** quand la couche est absente — le
code l'écrit, « un homme sans ordre du tout n'a pas de barre : il est livré à ses
couches » — contre **0,50** pour un ordre ordinaire, « la seule raison pour
laquelle une troupe reste une troupe ». **43 % de l'armée était arbitrée comme
n'ayant reçu aucun ordre**, alors que tous en avaient un.

La prédiction, posée AVANT de mesurer : `corps` doit reculer, `ordre` doit monter.

| mesure | avant | après |
|---|---|---|
| couche 3 disponible | 55,9 % | **97,9 %** |
| élection : `ordre` | 55,6 % | **96,6 %** |
| élection : `corps` | 28,7 % | 0,0 % |
| distance au chef, P90 | 92,5 m | **68,8 m** |
| hommes sans pair | 14,6 % | 12,0 % |
| vintaines groupées | 90 % | **97 %** |
| A* pour 24 vintaines | 36 | **30** |
| au contact / coups | 86 / 745 | **112 / 1446** |
| en déroute | 0 | **6** |
| `banc-dynamiques` | 8 rouges | **8 rouges** |

L'échange sur les sondes rouges : « les deux chefs ont quitté leur place » est
**réparée** (3,2 m · 1,4 m → 2,2 m · 2,3 m) ; « seule une minorité combat au même
instant » **apparaît** (44 % contre un critère de ≤ 40 %). Une bataille plus
dense met plus d'hommes au contact en même temps — c'est le critère qui rencontre
une bataille plus vivante, et il faudra décider s'il tient encore.

**Deux choses à ne pas se raconter.**

1. **L'écart pensée/élection tombe de 27,3 % à 0,0 %, et ce n'est pas une
   victoire.** Les deux mesures se sont effondrées sur « ordre » : le désaccord
   ne se voit plus faute de variété, pas faute d'exister. L'item « brancher la
   pensée sur la trace d'arbitrage » reste entier.

2. **`corps` à 0,0 % n'est pas un défaut de calibrage.** `prendCorps` rend
   l'emprise du corps ; pour battre une barre à 0,50 il faut une emprise franche,
   et dans une bataille où le fer ne se touche jamais, rien n'agrippe personne.
   Le vrai test de `prendCorps` demande une condition avec contact — donc le
   défaut du lot 6 réparé d'abord. Avant ce changement, le corps l'emportait
   souvent : c'était une incarnation en trompe-l'œil, produite par l'absence de
   barre et non par une emprise réelle.

**Critère du nouvel étalon** : la couche 3 disponible pour au moins 95 % des
hommes vivants au moment de l'élection (`banc-combattant.js`).

