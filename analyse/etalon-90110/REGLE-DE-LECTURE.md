# La règle de lecture de l'étalon — écrite AVANT le chiffre

Toll Œil-Noir, l'eau. 129.4.3, à la Souche. La cuisson de 600 s tourne pendant
que j'écris ceci, sur l'horloge de l'Équerre et hors de ma journée. Je n'ai pas
vu son résultat, et c'est la seule raison pour laquelle cette page vaut quelque
chose : **une règle de lecture écrite après le chiffre se plie au chiffre.**

---

## Article 0 — Ce qui se lit, et contre quoi

Le chiffre attendu est le quatuor d'une cuisson de **1700 hommes, 600 s** :
ordres déformés · déclencheurs tombés · initiatives · coureurs.

La **seule** chose à quoi il se compare est `monde/essai.reference.json` et ses
annales — mêmes hommes, même durée. Recompté à la main aujourd'hui dans
`essai.reference.annales.json` (`par_quoi`), et il tombe juste :

    ordre-deforme 5 · declencheur-tombe 5 · initiative 14 · coureur-part 54

N'entrent PAS dans la comparaison, et il ne faut pas y revenir :

- **le banc `deux-causes.js`** — il monte la chaîne seule et ne charge pas la
  ville. Ses faits ne portent ni `habitant`, ni `peur-gagne`, ni `guet-a-vu`,
  ni `prend-les-armes`, quand la référence en porte **quinze**. Le banc et le
  four ne comptent pas la même nuit ; ils comptent les mêmes NOMS de faits.
- **toute cuisson d'une autre durée ou d'un autre nombre d'hommes.** À 400
  hommes les quatre valent 0, 0, 0 et 12.

## Article 1 — Sept lignes, ou l'on ne lit pas

Un chiffre sans sa condition n'est pas un étalon. La condition tient en sept
lignes : hommes · durée · **graine** · **drapeaux** · **empreintes** des sept
fichiers de la chaîne · **jour et minute de la ville** · **peuple et tournée**.

Le manifeste du four n'en grave que six CHAMPS (`sac.js` l.865 : `porte`,
`hommes`, `duree_s`, `pas_s`, `tolerance_m`, plus l'issue) et **aucune des
trois dernières lignes**. Vérifié sur `essai.reference.json` : ni graine, ni
drapeaux, ni empreintes, ni jour, ni minute.

**Conséquence, et il faut l'avaler telle quelle : la référence 5, 5, 14, 54 ne
peut pas servir de contrôle d'égalité.** Trois de ses sept conditions sont
inconnues et irrécupérables — dont l'heure de la ville, que `sac.js` l.605-606
lit EN DIRECT dans `etat/monde.json` (🔒 91013) : la même commande ne cuit pas
la même nuit deux jours de suite, et le 14 août n'est pas le 3e jour de la 4e
lune.

Donc la référence sert d'**ordre de grandeur**, pas de juge. Le chiffre qui
tombe aujourd'hui devient le premier étalon dont la condition est écrite ;
c'est LUI qu'on comparera demain, et c'est de lui qu'on exigera l'égalité.

## Article 2 — L'attendu est ZÉRO, jamais « à peu près »

À condition identique et graine tenue, la cuisson est **déterministe** —
vérifié aujourd'hui : `compte-tirages.js` rend deux fois exactement 119 238
tirages au dressage et 105 668 en cuisson.

Donc, entre deux cuissons de même condition, **l'écart attendu est 0**, et il
n'y a pas de seuil à écrire : un écart non nul sous condition identique n'est
pas une tolérance à élargir, c'est la reproductibilité qui est cassée — le
repli muet de `corps-adapt.js` l.350 (🔒 90140), ou un décalage d'urne
(🔒 90150). On ne rend jamais un seuil qui autorise un écart entre deux
cuissons de même condition. C'est la seule ligne de cette page qui ne se
négocie pas.

## Article 3 — Quand la condition a bougé, le bruit se MESURE

Et elle a bougé : la ville n'est plus celle du 14 août. Il faut donc une bande
de bruit, et une bande ne se décrète pas.

Mesurée aujourd'hui, banc tel-quel, **1700 hommes, 150 s**, la graine seule
changée — rien d'autre, pas une ligne de source :

| graine | ordres déf. | déclench. | initiatives | coureurs |
| --- | --- | --- | --- | --- |
| 20161219 (la nôtre, cuite deux fois) | 3 | 5 | 4 | 47 |
| 20161220 | 4 | 5 | 5 | 48 |
| 424242 | 3 | 5 | **1** | 47 |
| 7 | *encore au feu au moment où j'écris* | | | |

Trois graines rendues sur quatre : ce qui suit est un **plancher** de bruit,
jamais un plafond, et la règle est écrite pour qu'un plancher suffise — elle ne
fait que REFUSER de lire, elle n'autorise rien.

**La bande, à 150 s, mesurée sur la graine seule :**

| compte | vu | bande |
| --- | --- | --- |
| ordres déformés | 3 · 4 · 3 | au moins ±1 |
| déclencheurs tombés | 5 · 5 · 5 | **0 — le seul qui n'ait pas bougé** |
| initiatives | 4 · 5 · **1** | au moins **de 1 à 5**, soit tout ce qu'on a jamais lu |
| coureurs | 47 · 48 · 47 | au moins ±1 |

**Les initiatives sont le compte le plus bruyant des quatre, et de loin.** Une
graine, rien d'autre, les fait passer de 5 à 1. C'est précisément le compte
dont mon verdict d'hier disait qu'il « ne porte aucun verdict à 150 s et qu'il
faut le recuire à 600 s » : c'était vrai, et c'est pire que je ne le pensais —
à 150 s ce compte-là ne se lit PAS DU TOUT, à aucune finesse. À 600 s elle sera au moins
celle-là, et probablement plus large — un compte plus gros remue davantage.
Tant qu'on n'aura pas payé les quatre graines à 600 s, **la bande de 600 s est
inconnue et se majore : on ne lit à 600 s que ce qui dépasse largement ±1.**

## Article 4 — Les quatre ne se lisent pas ensemble

Interdits, et ce sont des interdits, pas des préférences : la somme des quatre,
une distance sur les quatre, un pourcentage d'écart, la moyenne de deux
cuissons. Chacun se lit seul, contre sa bande.

- **Un compte qui tombe à zéro, ou qui part de zéro, est un MÉCANISME** — quelle
  que soit sa taille, et il se lit avant tout le reste. Fondé, pas décrété : le
  drapeau `PORTE_OUVERTE_ESSAI` met les ordres déformés et les déclencheurs à
  0 et 0.
- **Un écart d'UNE unité ne dit rien, sur aucun des quatre** — pas même sur les
  déclencheurs qui ne valent que 5, et c'est là que je réponds à l'Équerre :
  non, une unité sur les coureurs et une unité sur les déclencheurs ne veulent
  pas dire la même chose, mais pas dans le sens qu'on croit. Ce n'est pas une
  affaire de proportion (1 sur 54 contre 1 sur 5) : c'est que **la seule graine
  déplace déjà les ordres déformés de 3 à 4 et les coureurs de 47 à 48.** Ce
  qui n'a pas bougé sous la graine seule, ce sont les déclencheurs — d'où la
  seule asymétrie que je grave : **un écart d'une unité sur les déclencheurs
  se NOTE et se recuit ; le même écart sur les trois autres ne se note même
  pas.** Et sur les initiatives, qui vont de 1 à 5 sous la seule graine, on ne
  lit rien en deçà de **quatre** unités.
- **Un écart qui dépasse la bande est un fait à expliquer par une cause nommée**,
  et rien ne se conclut tant que la cause n'est pas nommée. Un écart expliqué
  vaut mieux qu'un étalon qui retombe juste.

## Article 5 — Ce qu'un écart ne dira JAMAIS tant que l'urne est unique

`bataille/hasard.js` n'a qu'un état, `_s`, et tout le monde y puise dans
l'ordre où il passe. Mesuré aujourd'hui, à 1700 hommes (2550 corps) :

- **119 238 tirages au dressage**, soit **46,8 par corps** — dont **24 par
  homme** pour ses seules quatre déviations (`trempe`, `vivacite`, `fond`,
  `souplesse`, plus deux `trempe` d'école : quatre `R()` chacune), soit
  **61 200 tirages, plus de la moitié du dressage, pour fabriquer QUI sont les
  hommes** ;
- **21 134 tirages par seconde de bataille**, soit près de **13 millions** sur
  une cuisson de 600 s.

Un seul tirage décalé en amont rebat tout ce qui suit. **Deux cuissons qui
diffèrent d'un rien n'ont donc pas les mêmes hommes** — pas des hommes
« presque pareils » : d'autres hommes, avec d'autres cœurs et d'autres yeux.

D'où la règle : **un écart n'est jamais « la part » de la cause qu'on a
changée. C'est la cause PLUS le rebattement, et les deux ne se séparent pas par
soustraction.** Ce qui se lit malgré tout, c'est ce qui dépasse le rebattement
de plusieurs longueurs : 47 → 27 coureurs se lit ; 47 → 48 ne se lit pas.

## Article 6 — Ce que je retire de mon verdict d'hier

La ligne « l'interprétation vaut une initiative sur quatre » ne tient plus :
l'écart 4 → 3 est bien en deçà du bruit d'urne que je viens de mesurer — la
graine seule fait 4, 5 puis 1 sur ce compte. Je la retire, et je retire avec
elle l'idée qu'un écart d'une unité sur les initiatives puisse un jour vouloir
dire quelque chose à 150 s.

Ce qui tient, et sans une ombre : **le drapeau a bougé trois comptes sur
quatre** — 3 et 5 vers 0 et 0, 47 vers 27. Ces écarts-là sont hors de toute
bande. Et la part de `4-envie` reste non mesurable, pour la raison écrite dans
le verdict : elle ne se débranche pas.

---

## En une phrase, pour l'Équerre

Si le quatuor de 600 s tombe à **5, 5, 14, 54**, je ne dirai pas que l'étalon
est retrouvé : je dirai qu'il retombe juste, et j'écrirai sa condition, qui est
la seule chose neuve. S'il en diffère d'une unité, je ne dirai pas qu'il a
bougé. **Le premier chiffre que je rendrai comme un verdict sera le second
quatuor de 600 s, cuit sous une condition écrite en sept lignes.**
