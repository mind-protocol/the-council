# La table peinte — d'où vient la carte

La carte de Westeros n'est pas dessinée à la main : elle est **extraite des
données de carte du mod AGOT** de Crusader Kings III, puis figée dans le dépôt.
Le jeu ne dépend donc ni du mod ni de CK3 à l'exécution — seulement du fichier
généré.

```
mod AGOT (Steam workshop 2962333032)
  ├─ map_data/provinces.png     9216 × 6144, une couleur par province
  ├─ map_data/definition.csv    couleur → numéro de province
  ├─ map_data/default.map       mers, lacs, rivières navigables
  └─ common/landed_titles/      province → baronnie → comté → … → empire
                │
                │  scripts/carte_geo.py   (outil de build, lancé à la main)
                ▼
        ecrans/modules/geo.js   ~180 Ko, `window.Geo`
                │
                │  ecrans/modules/carte.js
                ▼
        les deux cadrages de la table
```

## Régénérer

```bash
python scripts/carte_geo.py
```

Deux secondes environ. À relancer seulement si le mod change, ou si l'on
touche à la liste des régions ou des lieux dans `scripts/carte_geo.py`.

## Comment le tracé est obtenu

1. **Rattachement.** `landed_titles` est parcouru à pile : chaque
   `province = N` est attribué au comté (`c_*`) et à l'empire (`e_*`) ouverts
   à ce moment-là. Dans AGOT, ce sont les **empires** qui portent les grandes
   régions — `e_the_north`, `e_the_crownlands`, `e_dorne`… — et non les
   royaumes, qui sont d'un cran plus fins.
2. **Grille.** `provinces.png` est sous-échantillonné d'un facteur 2, puis
   chaque pixel est remplacé par l'identifiant de sa région. La grille est
   ensuite cadrée sur Westeros (1112 × 1858 px utiles).
3. **Contours.** Chaque masque de région est suivi le long des **arêtes entre
   pixels**, pas de leur centre. Deux régions voisines produisent ainsi
   exactement la même arête sur leur frontière commune : elles s'emboîtent
   sans jour ni recouvrement. Les boucles obtenues sont simplifiées
   (Douglas-Peucker, tolérance 0,45 unité) et les îlots de moins de
   ~1,5 unité² sont jetés.
4. **Lieux.** Chaque lieu de `etat/lieux.json` est associé à un comté du mod
   (table `LIEUX` dans le script) ; sa position est le centre de la province
   qui porte le château.

## Ce que contient `geo.js`

| clé | contenu |
| --- | --- |
| `viewBox`, `largeur`, `hauteur` | le repère : Westeros seul, hauteur 620 |
| `terre` | la silhouette du continent et de ses îles, d'un seul tenant |
| `regions[]` | `{id, nom, court, d, etiquette}` — dix régions |
| `eaux` | lacs et rivières navigables (l'Œildieu, le Trident, la Néra…) |
| `fonds` | terres hors Westeros, gardées en fond discret (au-delà du Mur) |
| `lieux` | `{id: [x, y]}` pour les 17 lieux de l'état |
| `cadres` | `westeros` et `baie` — voir ci-dessous |

Les rivières et les lacs sont **creusés dans la terre** (ce sont des provinces
d'eau pour le jeu), puis repeints par-dessus : d'où un tracé à part.

## Les deux cadrages

Le plateau n'a qu'une colonne étroite : Westeros entier y flotterait dans le
vide. La vignette se cadre donc sur `cadres.baie` — la baie de la Néra, boîte
englobante des dix places du théâtre de la Danse, avec 30 % de marge — et
« s'approcher de la table » ouvre `cadres.westeros`, le royaume entier.

Ce dernier déborde de 48 unités à l'est : les places de la côte (Peyredragon,
l'Île aux Griffes, Pointe-Massey) écrivent leur nom vers le large, et il leur
faut de la mer pour le faire.

Une seule variable CSS, `--k`, porte le rapport entre le cadrage courant et la
carte entière. `carte.js` la pose sur chaque `<svg>` ; toutes les épaisseurs de
`jeu.css` en dépendent (`calc(1.4px * var(--k))`), et les corps de texte
suivent le `font-size` posé sur le même élément. C'est ce qui donne le même
grain de trait à la vignette serrée et à la grande table.

## Ce qui reste à la main dans `carte.js`

Trois tables, parce qu'elles relèvent de la mise en page et non de la
géographie :

- `ETIQ` — le décalage et l'ancrage du nom de chaque lieu. Autour de la baie,
  les noms rayonnent vers l'extérieur de la grappe pour ne pas se marcher
  dessus.
- `MERS` — les noms de mers : elles n'ont pas de contour dans l'état.
- `DECALE_REGION` — le générateur pose l'étiquette d'une région en son centre ;
  trois d'entre elles tombent alors sur un nom de lieu. `null` supprime
  l'étiquette : c'est le cas des Terres de la Couronne, qui ne sont qu'un
  anneau de côtes autour de la baie — aucun creux ne peut porter leur nom, et
  leurs places les nomment assez.

Un garde-fou écarte de la vignette tout lieu dont le nom déborderait du cadre :
mieux vaut l'absence qu'un nom tranché par le bord. Le lieu reste sur la
grande table.

## Ce que la table PORTE — jetons, traits, zones

`geo.js` donne la géographie, qui ne bouge jamais. La guerre, elle, bouge à
chaque battement : elle vit dans `etat/jetons.json`, est servie par `/carte` et
dessinée par `ecrans/modules/jetons.js`.

```
etat/jetons.json          ce que la reine croit tenir
        │  /carte
        ▼
ecrans/modules/jetons.js  glyphes, courbes, pointes de flèche, légende
        │
        ▼
ecrans/modules/carte.js   les pose sur les deux cadrages
```

**Ce fichier n'est pas la vérité du monde.** C'est la table de guerre du joueur :
ce qu'on y pose devrait pouvoir se justifier par une entrée d'`info.json`, une
parole entendue en scène ou un ordre qu'il a donné lui-même. Une position que
son personnage ignore n'a rien à y faire — la carte est le premier endroit où
l'on trahirait le brouillard de guerre.

Deux familles, une seule grammaire.

### Les jetons — une pièce posée quelque part

```json
{
  "id": "colonne-rosby", "genre": "armee", "camp": "vert",
  "nom": "La colonne de Rosby", "force": 1200, "unite": "hommes",
  "ou": "rosby",
  "detail": "Vues de Meleys : elles comptent les murs sans attaquer.",
  "certitude": "rapportee", "statut": "actif"
}
```

| champ | |
| --- | --- |
| `genre` | `armee` `cavalerie` `flotte` `dragon` `garnison` `siege` `bataille` `camp` `vivres` |
| `camp` | `noir` `vert` `neutre` — donne la couleur |
| `ou` / `point` | un id de lieu, ou `[x, y]` pour ce qui n'a pas d'adresse (une voile au large) |
| `force`, `unite` | le chiffre écrit au-dessus de la pièce ; `unite` n'apparaît qu'à l'infobulle (défaut : « hommes ») |
| `certitude` | `sure` `rapportee` `rumeur` — délave la pièce, une rumeur se troue et porte un `?` |
| `dec` | décalage manuel `[dx, dy]`, quand l'empilement automatique ne suffit pas |
| `statut` | tout ce qui n'est pas `actif` disparaît de la table (une colonne détruite se garde en mémoire) |

Plusieurs pièces sur une même place s'empilent **vers le haut** : côte à côte,
ce sont leurs chiffres qui se marcheraient dessus, et un compte illisible ne
vaut rien. Une pièce qui tomberait hors du cadrage est simplement absente de la
vignette — comme les noms de lieux — et reste sur la grande table.

### Les traits — un fil tendu entre deux endroits

```json
{
  "id": "ultimatum-otto", "genre": "menace", "camp": "vert",
  "de": "port-real", "vers": "peyredragon",
  "nom": "L'ultimatum d'Otto", "detail": "Jurer dans la quinzaine, ou l'attainder.",
  "certitude": "sure", "statut": "actif"
}
```

| genre | ce que ça dit |
| --- | --- |
| `marche` | une colonne en route (pointe pleine) |
| `mer` | une route de mer (tirets longs) |
| `corbeau` | un pli en vol (pointillé fin, très courbé) |
| `attaque` | un assaut (trait épais, pointe barbelée, sang) |
| `retraite` | un décrochage |
| `menace` | ce qu'on promet de faire (tirets, pointe ouverte) |
| `serment` | un hommage prêté (nœud au milieu, braise) |
| `vassal` | une sujétion de droit |
| `mariage` | une alliance de sang (anneau au milieu) |
| `querelle` | une inimitié (le trait grince) |

`de`/`vers` (ids de lieux) ou `point_de`/`point_vers` (`[x, y]`). En plus :
`avancement` (0→1) coupe le fil en deux — ce qui est parcouru est plein, ce qui
reste est en pointillé ; `courbure` et `sens: "gauche"` écartent deux fils tendus
entre les mêmes places.

### Les zones — une région qui a choisi son camp

`{"region": "the_reach", "camp": "vert"}` teinte le territoire d'un lavis. Les
ids de régions sont ceux de `geo.js` (`the_north`, `the_crownlands`, `dorne`…).

### Les têtes — où l'on CROIT que sont les gens

`personnages.lieu_id` est la **vérité**, et la vérité n'a rien à faire sur une
table de guerre. L'autre moitié vit dans `etat/vues.json` : la dernière position
**connue du joueur**, avec sa date et de quelle bouche il la tient. Le serveur la
projette en pièces de genre `tete` — le MJ n'écrit jamais ces pièces à la main.

```json
{"personnage_id": "daemon", "lieu_id": "harrenhal",
 "date": {"annee": 129, "lune": 3, "jour": 11},
 "canal": "corbeau", "source": "le mestre Gerardys",
 "certitude": "sure", "note": "il y installait sa garnison"}
```

| champ | ce qu'il dit |
| --- | --- |
| `canal` | `vu` (de ses yeux) · `temoin` · `corbeau` · `cavalier` · `rumeur` · `presume` |
| `source` | de quelle bouche il le tient — s'affiche sous le doigt |
| `certitude` | au moment de la vue ; elle se dégrade ensuite toute seule |
| `note` | une ligne de contexte, facultative |

**Le sel n'est pas la position, c'est son âge.** Une nouvelle ne reste pas
fraîche : ≤ 7 jours elle garde sa `certitude`, ≤ 21 elle retombe à `rapportee`,
≤ 45 à `rumeur`, au-delà la tête **sort de la table** — on ne sait plus. La pièce
dit « aujourd'hui », « hier », « il y a neuf jours » sous le doigt.
`canal: "presume"` est l'exception : un seigneur chez lui n'est pas une
observation, c'est une présomption de longue main — elle ne vieillit pas, reste
en `rapportee`, et se dit « on l'y suppose ».

Une tête n'est pas une force : elle se pose **sous** le point de la place (les
osts s'empilent au-dessus), elle pèse moins, et son nom reste **en clair** —
c'est toute l'information qu'elle porte. Trois têtes par place au plus, les plus
fraîches ; une quatrième pièce dit combien on en tait, et les nomme au survol.

Discipline : une nouvelle qui donne la position de quelqu'un met à jour son
entrée dans `vues.json`, comme elle met à jour `jetons.json`. Ce qui n'y est pas
n'apparaît nulle part — et c'est juste : Rhaenyra ne sait pas où est tout le
monde.

### Ce que ça donne à l'écran

Le nom d'une pièce ne s'écrit pas en clair : dix pièces nommées feraient une
bouillie par-dessus les noms de places. Il vient **sous le doigt**, au survol.
Le chiffre, lui, est toujours là — un conseil de guerre se tient sur des
chiffres. Cliquer une pièce ou un fil ouvre un **moment de pensée**, comme un
lieu ou un nom du fil : on soupèse ce qu'on croit savoir, on ne déplace rien.
La légende, sous les deux cartes, ne nomme que les genres effectivement posés.

## La couleur et les bannières

La carte a longtemps été du beige sur du beige : lisible, mais muette. Elle porte
maintenant deux couches de couleur, qui ne disent pas la même chose.

### Le lavis — ce que le pays EST

Un fond de mer franc (`--mer`), un **haut-fond** — un large trait pâle collé au
rivage, comme sur les cartes gravées, et c'est lui plus que la couleur qui fait
lire le trait de côte — puis une teinte par région, posée en **transparence** :
le grain du parchemin reste visible dessous. Le Nord est un gris de neige, le Val
un mauve de montagne, le Conflans un vert d'eaux, le Bief un or de moisson, Dorne
un sable, l'Orage un vert sombre.

Tout tient dans des variables CSS (`--t-nord`, `--t-bief`…) accrochées au
`data-region` que chaque tracé porte déjà — aucun code, deux jeux de valeurs,
l'un pour le jour, l'autre pour la nuit. **La Couronne est la plus discrète de
toutes** : elle remplit à elle seule le cadrage par défaut, et une teinte franche
y serait fatigante au bout d'une heure de jeu.

Ce lavis est **géographique, pas politique**. Voir « Un parti pris », plus bas.

### Les bannières — ce que le pays TIENT

`ecrans/modules/blasons.js`. Chaque place plante les armes de la maison qui la
tient (`lieux.controle_id`) : une petite bannière sur sa hampe, du côté **opposé
au nom** — le nom et les armes se partagent la place, ils ne se la disputent pas,
et les pièces de guerre s'empilent au-dessus du point sans toucher ni l'un ni
l'autre.

À douze pixels de haut, un lion rampant est une tache. On garde donc ce qu'une
bannière dit vraiment à cette distance — ses **émaux** et sa **partition** — et
la charge est ramenée à deux ou trois traits épais, qui redeviennent une bête à
mesure qu'on approche à la loupe. Partitions gérées : plain, `pal2`, `pal3`,
`ecartele`, `fusele`, `seme`, `hermine`.

La source est le champ `blason` de `etat/maisons.json`, en toutes lettres. Ce
qu'il faut pour le DESSINER relève de la mise en page, et vit donc à la main dans
`blasons.js` — comme `ETIQ` et `MERS` dans `carte.js`. Les quatre grandes maisons
qui n'ont pas d'entrée dans l'état (Tully, Arryn, Lannister, Stark) y figurent
quand même : leurs sièges sont sur la carte.

**Une maison nouvelle n'a pas d'armes tant qu'on ne les lui a pas dessinées** —
elle n'affiche alors rien, et sa place garde son point et son nom. Et **une place
qui change de main change de bannière** : `controle_id` suffit, c'est le levier
du MJ quand un château tombe.

Les places de la baie se tiennent à cinq lieues les unes des autres : au cadrage
du royaume, dix bannières y feraient une bouillie d'étoffe. Une place dont la
voisine est trop proche **garde son point et son nom, et retrouve ses armes quand
on approche** — même discipline que les noms de lieux. La parure vient avec la
distance.

## Se pencher sur la table — la loupe

`ecrans/modules/loupe.js`, branché sur la vignette du décor **et** sur la grande
table. Molette pour approcher (là où est le curseur, pas au centre), glissé pour
déplacer, pincement à deux doigts, double-clic pour reposer le cadrage.

**Approcher redessine, ça ne grossit pas l'image.** Toute épaisseur et tout corps
de texte de cette carte se calculent depuis la largeur du cadrage (`var(--k)`, et
l'`ech` que reçoivent jetons et traits). Un cadrage neuf, c'est donc la
géographie qui s'écarte pendant que les pièces, les noms et les traits gardent
exactement leur taille — et les noms écartés faute de place reviennent d'eux-
mêmes à mesure qu'on approche. Un zoom d'image grossirait tout ensemble et
n'apprendrait rien de plus qu'un coup d'œil.

Un redessin complet coûte ~8 ms : on le fait en direct, une fois par frame
(`requestAnimationFrame`), sans transformation intermédiaire. Comme le `<svg>`
est donc remplacé soixante fois par seconde, **les écoutants vivent sur l'hôte**
— clics par délégation, loupe sur le conteneur. Rien à rebrancher, rien à fuir.

Deux garde-fous. On ne descend pas sous **45 unités** de large : plus près, la
simplification des côtes (Douglas-Peucker, 0,45 unité) se verrait en facettes. Et
on ne sort pas du royaume : le cadrage est borné à Westeros plus 6 % de marge.

Un glissé n'est pas un clic : au-delà de quatre pixels, la loupe lève un drapeau
que le gestionnaire de clic consulte, pour qu'un déplacement qui finit sur une
place n'ouvre pas sa pensée.

Chaque surface garde deux cadrages : celui de **repos** (que la scène ou une
démonstration impose) et la **vue** courante, que la loupe déplace. Le
double-clic revient au repos ; une démonstration ou un changement de scène
reprend la table des mains du joueur.

## Un acteur qui montre — illustrer ses propos

Un conseil est une séance de travail : on ne dit pas « la flotte tiendra le
Gosier », on pose trois doigts dessus. `ecrans/modules/illustration.js` donne aux
acteurs la main sur la table, de deux façons.

**Un geste sur la carte** — un item de flux à lui seul, avec sa vignette dans la
chronique :

```json
{"type": "table", "acteur_id": "corlys",
 "texte": "Corlys pose deux doigts sur le Gosier, puis pousse un jeton de bois jusqu'au milieu de la Néra.",
 "cadre": "auto",
 "jetons": [{"id": "galeres-corlys", "genre": "flotte", "camp": "noir", "force": 6,
             "unite": "galères", "point": [311, 411], "nom": "Six galères"}],
 "traits": [{"id": "prise-cogues", "genre": "attaque", "camp": "noir",
             "point_de": [311, 411], "point_vers": [303, 419],
             "nom": "Prendre les cogues"}]}
```

**Une main qui pose pendant qu'il parle** — le même contenu sous la clé `montre`
d'une `replique` ou d'un `geste` : la table du décor bouge sous les yeux du
joueur pendant la réplique, et l'entrée de la chronique porte une mention
discrète pour y revenir (pas de seconde carte : il vient de la voir).

```json
{"type": "replique", "locuteur_id": "rhaenys", "texte": "Elles sont là. À hauteur de Rosby.",
 "montre": {"jetons": [{"id": "vu-colonne", "genre": "armee", "camp": "vert",
                        "ou": "rosby", "force": 1200, "certitude": "rapportee"}]}}
```

`cadre` vaut `"auto"` (défaut : la boîte de ce qu'on montre, avec de la marge),
`"baie"`, `"westeros"`, `[x, y, l, h]`, ou `"garder"` pour ne pas bouger la table.
Montrer bascule le décor sur le royaume : inutile de montrer la baie derrière le
plan du château.

**Ces pièces-là sont éphémères.** Elles vivent le temps de la scène, s'animent en
arrivant (braise, puis plus rien de particulier) et tombent au prochain
`effacer`. Ce qui doit durer, le MJ l'écrit dans `etat/jetons.json` : un geste de
démonstration n'est pas un fait acquis. Reposer une pièce du même `id` la
remplace — une colonne avance, elle ne se dédouble pas.

## La carte locale — le château, salle par salle

Deux échelles répondent à deux questions différentes. La table peinte dit *où
porte la guerre* ; le plan du château dit *où je suis et qui est à trois portes
de moi*. La seconde est l'échelle de la scène — c'est elle qui est affichée par
défaut. Une bascule au-dessus du décor (« Le château » / « Le royaume »)
échange les deux, et le choix tient dans `localStorage`.

```
ecrans/modules/plans.js    la géométrie, dessinée à la main, une entrée par lieu
ecrans/modules/plan.js     le rendu, la vignette, le plan déplié, la bascule
```

Rien n'est généré ici : un château ne change pas de salles. Et ce n'est pas un
relevé d'architecte — c'est le plan tel qu'on le tient dans la tête quand on y
vit : on garde ce qui a un enjeu (où l'on décide, où l'on dort, où arrivent les
corbeaux, par où l'on sort) et on jette le reste. Peyredragon compte dix-sept
lieux ; le format d'une salle est documenté en tête de `plans.js`.

Le plan est **orienté** — le Dragonmont au nord, le large au sud, et c'est pour
ça que la salle du levant est à droite. Une rose des vents le dit, posée dans
l'eau à l'ouest où rien ne se dispute la place (champ `rose: [x, y, rayon]`).

### La carte se règle sur la place qu'on lui donne

Un corps de texte écrit en unités du plan grandit **avec** la carte : 14 unités
sont justes dans une vignette de 250 px et deviennent énormes dans une de 700.
Le plan vise donc une taille **apparente** constante — 9,8 px dans le décor,
11,5 px déplié — obtenue en mesurant le rendu plutôt qu'en la devinant : on
trace d'après la place offerte, on mesure ce qui a été rendu (la carte peut être
bornée par la hauteur et non par la largeur), et on retrace si l'échelle devinée
était fausse. Jamais de troisième passe.

La densité des noms suit la même mesure. Sous **360 px de large**, la carte ne
porte que les salles marquées `cle` et celle où l'on se tient ; toutes les
autres y gardent forme, infobulle et clic. Au-delà, elle les porte toutes — le
seuil est relevé à l'essai : à 360 px, les trente et une étiquettes tiennent
sans une seule collision. Quand elle a la place d'écrire, la carte ajoute aussi,
sous la salle courante, le prénom de ceux qui y sont avec vous.

Trois choses peuvent changer la taille de la carte : la fenêtre, le bandeau des
présents qui s'épaissit et reprend de la hauteur au décor, et la bascule des
deux échelles. Un `ResizeObserver` les attrape toutes — mais **il ne dit rien
dans un onglet qui n'est pas à l'écran** : ses notifications sont servies avec
les frames, comme `requestAnimationFrame`. D'où un rattrapage toutes les deux
secondes (une mesure de rectangle, rien de plus), pour que le joueur qui revient
sur son onglet retrouve une carte juste.

### La part des colonnes

La chronique ne sait pas quoi faire d'une colonne plus large que sa mesure de
lecture (600 px) : au-delà, elle ne fabrique que de la marge. Sur un écran de
1512 px, elle en tenait 972 pour 600 utiles pendant que la table étouffait dans
486 — d'où un plan de 434 px surmonté de 415 px de vide. Les colonnes sont donc
réparties `1.25fr / 1fr` au-dessus de 1100 px de large : le fil garde sa mesure,
le décor prend le reste, et la carte passe de 434 à 596 px de large.

### Un plan est plat

Une chambre au sommet d'une tour et un cachot sous la cour ne peuvent pas être
posés à leur vraie place. Convention : la salle est dessinée **dans** ou
**contre** ce qui la porte, en trait pointillé (`etage: "sommet" | "dessous"`),
et son infobulle dit de combien on monte ou on descend. Les emboîtements se
lisent aussi à la teinte : `var(--paper)` est translucide, donc chaque étage
d'emboîtement pose un parchemin de plus — cour, puis salle, puis salle dans la
salle.

### Comment le jeu sait dans quelle salle on est

Nulle part dans `etat/` : la salle courante se lit dans **l'en-tête de lieu du
bandeau**, que le bus repose à chaque item porteur d'un `lieu`. Chaque salle
déclare ses `motifs`, et c'est le **premier** rencontré dans l'en-tête qui
gagne, pas le plus long — un en-tête nomme la salle puis la situe :
« L'archive, trois étages sous la salle du levant » est l'archive.

Quand l'en-tête ne suffit pas, un item du flux peut trancher avec un champ
`salle: "<id>"` : il fait alors foi jusqu'au prochain changement de lieu. Rien
d'autre à tenir à jour, et aucun flux ancien à réécrire.

### Ce que le plan ne fait pas

Il ne montre **personne** ailleurs que dans la salle où se tient le joueur : un
plan qui pointerait où est Daemon en ce moment serait une fuite de vérité. Et
il ne sert pas à se déplacer — cliquer une salle ouvre un moment de pensée
(même canal que les entités du fil : `cible_type: "salle"`). On y songe, on n'y
va pas ; se déplacer se dit dans le champ libre.

## Le terrain — le champ, vu du dessus

La troisième échelle du décor. Le royaume dit **où** porte la guerre, le château
dit **qui est à trois portes de moi**, le terrain dit **ce que mille hommes
occupent réellement de sol, et dans quel ordre ils s'y tiennent**.

```
etat/terrain.json           le champ courant, ou rien
        │  /terrain
        ▼
ecrans/modules/terrain.js   sol, formations, silhouettes, sa vignette et son déployé
        │
        │  s'inscrit comme échelle auprès de plan.js
        ▼
la bascule du décor         Le château · La ville · Le royaume · Le terrain
```

Pas de champ (fichier absent, vide, ou sans `id`) : **pas de troisième bouton**.
L'échelle n'existe que quand il y a quelque chose à voir dessus. Un champ qui
apparaît en cours de partie prend le décor de lui-même — c'est la guerre qui
s'invite ; au chargement de la page, non, le joueur retrouve l'échelle qu'il
avait laissée. Un champ peut refuser de s'imposer avec `"basculer": false`.

### Un cercle vaut toujours le même nombre d'hommes

C'est toute la raison de descendre à cette échelle. `par_cercle` (défaut 25) vaut
pour **tout le champ** : quatre-vingt-dix lances font six cercles, huit cents
fuyards en font cinquante-trois, et le rapport de force se lit sans qu'on ait à
comparer deux chiffres. La légende l'annonce en clair sous la carte.

```json
{
  "id": "lances-darklyn", "genre": "cavalerie", "camp": "noir",
  "nom": "Les lances de Sombreval", "hommes": 90,
  "centre": [131, 78], "cap": 128, "formation": "ligne", "etat": "ordre",
  "certitude": "sure", "etiq": [-4, -16]
}
```

| champ | |
| --- | --- |
| `genre` | `pique` `infanterie` `cavalerie` `archers` `prisonniers` `convoi` `dragon` `convives` |
| `hommes` | le compte ; `cercles` force le nombre de ronds quand le compte ne veut rien dire (deux scorpions, un dragon) |
| `centre`, `cap` | où, et vers où — `cap` est un relèvement : 0 le nord, 90 l'est |
| `formation` | `ligne` `ligne3` `colonne` `file` `carre` `coin` `essaim` `tas` `deroute` |
| `etat` | `ordre` `ebranle` `rompu` `fuite` `rendu` `mort` — les rangs se défont à mesure |
| `etiq` | décalage du nom depuis le centre, en unités du champ, quand ça se bouscule |

Tout ce qui se joue sur cent pas n'est pas une bataille : une cour où deux
partis se font face en est une aussi. D'où `convives` — des gens qui n'ont ni
cap ni rangs, dont le rond est vide et sans poids, mais qui occupent du sol, et
c'est bien le sol qu'on est venu regarder à cette échelle. Ils se comptent en
« personnes » et non en « hommes » (`mot` dans `GENRES_CORPS`), et l'on omet
leur `etat` : « en ordre » ne veut rien dire pour des gens qui dînent.

Un dragon n'est pas un rond : c'est une **envergure**, dessinée dans son repère
et tournée avec le corps. Une cavalerie porte son cavalier au centre du rond, un
convoi est fait de caisses et non d'hommes, des prisonniers sont des ronds vides
et gris. Un corps `deroute` s'étire vers l'arrière en s'élargissant : on voit la
colonne se défaire le long de la route.

### Le sol

`sol` se dessine avant les hommes : `route` `riviere` `haie` (des bandes, à
partir de `points`), `bois` `champ` `marais` `colline` (des aires), `village`
(un semis de toits). Un `nom` avec son `etiq` (et son `cap` pour coucher le texte
le long d'une route) le nomme. Un bois porte son semis d'arbres, une colline sa
seconde courbe de niveau ; un champ garde des bords droits, parce que c'est une
charrue qui les a tracés.

`faits` marque ce qui est arrivé au sol : `feu` (une brûlure et ses cendres),
`morts`, `melee`. Tout hasard — le semis d'un bois, la gîte d'un fuyard, la forme
d'une brûlure — est tiré d'une **graine déterministe** : sans quoi le décor
bouillonnerait à chaque redessin de la loupe.

### Ici, un homme occupe du sol

Différence de traitement avec la table peinte, et elle est délibérée. Là-haut,
une pièce est un **symbole** : elle garde sa taille à l'écran quel que soit le
cadrage. Ici, les cercles et les formations sont en unités du champ et
**grossissent avec lui** quand on approche — parce qu'un homme prend de la place
sur la terre. Seuls les textes, leurs décalages et les épaisseurs de trait
restent constants (`var(--k)`).

La loupe (molette, glissé, double-clic) marche comme sur la table peinte : elle
est générique. Cliquer un corps ouvre un moment de pensée, `cible_type: "corps"`.
On soupèse ce qu'on croit savoir ; on ne déplace pas les hommes du doigt.

Et comme la table peinte, **ce champ n'est pas la vérité du monde** : c'est ce
que le joueur a vu ou qu'on lui a rapporté. Un corps dont il ignore la position
n'y figure pas ; un corps mal compté porte sa `certitude`.

## La ville — l'île et le bourg, vus du dessus

Entre le château et le royaume. Le château dit **qui est à trois portes de moi**,
le royaume dit **où porte la guerre** ; la ville dit **ce qu'il y a hors les
murs, à portée de voix** : le bourg, le port, la rade, les fosses, le marais —
et chaque corps posé là où il se tient vraiment.

```
etat/ville.json             la ville courante, ou rien
        │  /ville
        ▼
ecrans/modules/terrain.js   MÊME module : ChampVu() est instancié deux fois
        │
        ▼
la bascule du décor         Le château · La ville · Le royaume · Le terrain
```

**C'est le dessin du terrain, au mot près.** Une ville vue du dessus pose le même
problème qu'un champ : du sol, et des corps dessus. `terrain.js` est donc une
fabrique `ChampVu({ id, route, nom, ordre, … })` appelée deux fois en bas de
fichier — `window.Terrain` sur `/terrain`, `window.Ville` sur `/ville`. Tout le
format de `terrain.json` vaut pour `ville.json` : `repere`, `par_cercle`, `sol`,
`faits`, `corps`, `certitude`, `basculer`. Fichier absent, vide, ou sans `id` :
pas de bouton.

Ce que la ville ajoute au vocabulaire :

- **sol** : `eau` (ce qu'on ne traverse pas), `greve`, `mur` (bâti à l'équerre —
  seul genre de bande qui ne se lisse pas), `quai`.
- **corps** : `gens` (des gens qui ne sont pas des troupes — un bourg, des
  sauniers, des bergers) et `nef` (une coque vue du dessus, proue en avant).
- **`taille`** sur un corps : un multiplicateur du rayon du genre. Un dragon
  occupe le tiers d'un champ de bataille et un point sur une île — `0.42` remet
  la bête à l'échelle sans toucher au genre.

`par_cercle` se choisit à l'échelle : 25 hommes pour une bataille, 10 personnes
pour une ville, sans quoi les petits corps (vingt et un sauniers) disparaissent.

Même brouillard que partout : **n'y figure que ce que le joueur a vu ou qu'on lui
a rapporté**, avec sa `certitude`. Et referme la ville (vide le fichier) quand on
a quitté les lieux — un décor qui traîne est un mensonge sur où l'on est.

## Un parti pris

Les régions sont rendues au même parchemin que la terre, séparées par un trait
d'encre pâle : la carte reste **cartographique** par défaut, pas politique. Un
territoire ne se teinte que si le MJ le décide, région par région, par une entrée
dans `zones` — le jour où une contrée entière a basculé et où le joueur le sait.
Colorer tout le royaume par allégeance affichée serait une carte de jeu de
stratégie : ce n'est pas ce qu'on regarde ici.
