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
  ├─ map_data/rivers.png        le réseau de rivières, navigables ou non
  ├─ map_data/mask-baronyroad.png  les routes (canal alpha)
  ├─ map_data/heightmap.png     le relief
  └─ common/landed_titles/      province → baronnie → comté → … → empire
                │
                │  scripts/carte_geo.py   (outil de build, lancé à la main)
                ▼
        ecrans/modules/geo.js   ~560 Ko, `window.Geo`
                │
                │  ecrans/modules/carte.js
                ▼
        les deux cadrages de la table
```

## Régénérer

```bash
python scripts/carte_geo.py
```

Une trentaine de secondes (la pleine résolution et le parcours des routes se
paient là, une fois pour toutes). À relancer seulement si le mod change, ou si
l'on touche aux listes de régions, de lieux, de bourgs ou de routes dans
`scripts/carte_geo.py`.

## Comment le tracé est obtenu

1. **Rattachement.** `landed_titles` est parcouru à pile : chaque
   `province = N` est attribué au comté (`c_*`) et à l'empire (`e_*`) ouverts
   à ce moment-là. Dans AGOT, ce sont les **empires** qui portent les grandes
   régions — `e_the_north`, `e_the_crownlands`, `e_dorne`… — et non les
   royaumes, qui sont d'un cran plus fins.
2. **Grille.** `provinces.png` est lu à **pleine résolution** — chaque pixel
   est remplacé par l'identifiant de sa région, par une table de
   correspondance de 16 Mo sur les 2²⁴ couleurs possibles (un `np.unique`
   aurait coûté 450 Mo d'indices pour le même résultat). La grille est
   ensuite cadrée sur Westeros (2223 × 3716 px utiles, soit ~6 px de source
   par unité SVG).
3. **Contours.** Chaque masque de région est suivi le long des **arêtes entre
   pixels**, pas de leur centre. Deux régions voisines produisent ainsi
   exactement la même arête sur leur frontière commune : elles s'emboîtent
   sans jour ni recouvrement. Les boucles obtenues sont simplifiées
   (Douglas-Peucker, tolérance 0,22 unité — la moitié de ce que la source
   permet, jamais moins) et les îlots de moins de ~1,5 unité² sont jetés.
4. **Lieux.** Chaque lieu de `etat/lieux.json` est associé à un comté du mod
   (table `LIEUX` dans le script) ; sa position est le centre de la province
   qui porte le château. Les **bourgs** (table `BOURGS`) suivent le même
   calcul, mais portent leur nom français avec eux : ils n'existent dans
   aucune table de l'état.
5. **Les couches de détail.** Trois masques du mod, chacun à son propre grain
   (le pixel ne sert à rien pour du relief) : les **rivières**, tout le réseau
   et pas seulement les provinces d'eau ; le **relief**, en deux bandes tirées
   du percentile d'altitude sur la terre ; et le réseau de **routes**, dont on
   ne garde que les grandes — voir plus bas.

## Ce que contient `geo.js`

| clé | contenu |
| --- | --- |
| `viewBox`, `largeur`, `hauteur` | le repère : Westeros seul, hauteur 620 |
| `terre` | la silhouette du continent et de ses îles, d'un seul tenant |
| `regions[]` | `{id, nom, court, d, etiquette}` — dix régions |
| `eaux` | lacs et rivières navigables (l'Œildieu, le Trident, la Néra…) |
| `rivieres` | tout le réseau, navigable ou non — le grain du pays entre deux places |
| `relief` | `{collines, montagnes}` — deux bandes d'altitude, sur la terre |
| `routes` | `[{id, nom, d}]` — les grandes routes, suivies sur le réseau du mod |
| `fonds` | terres hors Westeros, gardées en fond discret (au-delà du Mur) |
| `lieux` | `{id: [x, y]}` pour les 19 lieux de l'état |
| `bourgs` | `[{id, nom, p}]` — les places intermédiaires, à la loupe seulement |
| `cadres` | `westeros` et `baie` — voir ci-dessous |

Les rivières et les lacs sont **creusés dans la terre** (ce sont des provinces
d'eau pour le jeu), puis repeints par-dessus : d'où un tracé à part.

### Les routes — ce qu'on garde, et pourquoi si peu

Le mod porte le réseau **capillaire** : chaque baronnie a ses chemins, et le
masque couvre 8 % du continent. Rendu tel quel, il pèse 2,4 Mo et donne une
toile d'araignée où plus aucune place ne se lit — l'essai a été fait, il ne
sert à rien de le refaire.

On ne garde donc que les routes qui **portent un nom** (table `ROUTES` du
script : la route de l'Or, celle de la Rivière, la Royale, celle de la Rose,
celle de Sombreval), et on ne les trace pas à la règle : chaque étape est
cherchée **de proche en proche sur le masque réel** (parcours en largeur,
`tracer_route`), après une dilatation de deux pixels qui referme les gués et
les ponts que le masque ne peint pas. Ce qui sort est la chaussée telle
qu'elle est, avec ses détours autour des monts.

Une route dont le réseau ne relie pas deux étapes n'est **pas** tracée : mieux
vaut un manque qu'un chemin inventé. Le script le dit à la génération.

### Les bourgs — les étapes du chemin

Ni allégeance, ni bannière, ni pièce de guerre, et rien à penser dessus : un
bourg ne sert qu'à situer une distance sur une route. Ils n'apparaissent qu'en
deçà de 46 % du royaume dans le cadre (`SEUIL_BOURGS`) — au cadrage du
royaume entier, trente noms de plus écraseraient les dix places qui décident.

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
| `cavalier` | un porteur par les routes (peu courbé — il suit le sol) |
| `vol` | un dragon en l'air (très courbé, franc : il ignore le sol) |
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

### Les filtres — quatre familles, qu'on allume et qu'on éteint

Une table qui porte tout à la fois ne se lit plus : les osts, les plis, les
serments et les gens s'empilent au-dessus des mêmes dix places de la baie.
Chaque marque appartient donc à une famille, déduite de son `genre` (ou forcée
par un champ `filtre`), et chaque famille s'allume et s'éteint d'un bouton — en
haut à droite de la vignette, et dans la légende de la grande table. Le choix
tient dans `localStorage`.

| filtre | ce qu'il porte |
| --- | --- |
| **Les armes** | jetons `armee` `cavalerie` `flotte` `garnison` `siege` `bataille` `camp` `vivres` ; traits `marche` `mer` `attaque` `retraite` `menace` |
| **Les dragons** | jetons `dragon` ; traits `vol` |
| **Les plis** | jetons `pli` `incident` ; traits `corbeau` `cavalier` `propagation` |
| **Le plan** | jetons `dessein` ; **tout ce qui porte `plan: true`** |
| **Les liens** | traits `serment` `vassal` `mariage` `querelle` ; les zones |
| **Les gens** | jetons `tete` |
| **Les oreilles** | jetons `oreille` |

Un genre inconnu tombe dans **les armes** — c'était toute la table avant les
filtres. Et **une démonstration rallume sa famille** : un conseiller qui pose le
doigt sur un filtre éteint montrerait du vide.

Les dragons ont leur famille à eux, séparée des armes, et ce n'est pas un
rangement : c'est la seule pièce de cette table qui décide seule d'une journée.
On veut pouvoir éteindre les osts, les plis et les serments pour ne regarder que
les bêtes — qui est en l'air, qui est au sol, qui est à trois heures de vol de
quoi.

### Les plis — ce qui a été écrit, et où ça en est

Un message n'est pas un objet, c'est un **état qui change**. Le trait
(`corbeau`, `cavalier`) dit la route ; le jeton `pli`, posé sur la place
destinataire, dit où en est l'affaire. Les deux portent le même champ `etat`.

```json
{"id": "pli-staunton", "genre": "pli", "camp": "noir", "ou": "repos-des-freux",
 "nom": "Convocation à Staunton", "etat": "muet", "certitude": "sure",
 "date": {"annee": 129, "lune": 3, "jour": 17},
 "contenu": "Ser Simon Staunton est convoqué à Peyredragon pour y prêter serment à la reine, dans la quinzaine.",
 "detail": "Parti avec les autres. Rien n'en est revenu.", "statut": "actif"}
```

Un pli est la **plus grosse pièce de la table** (×1,45), et c'est délibéré : ce
qu'on a écrit pèse ici autant qu'un ost, et la marque d'état doit se lire à la
vignette sans qu'on ait à s'approcher. La pièce grossit, mais **pas ses textes** —
sans quoi un pli écrirait son nom plus grand que le nom du lieu qu'il désigne.

- **`contenu`** — ce que le pli DIT, en toutes lettres, sous le doigt. C'est la
  seule pièce de la table qui a un contenu ; le cacher ferait de la convocation
  la plus décisive de la partie un rond de plus. `reponse` s'y ajoute quand elle
  est revenue.
- **`date`** — le jour du départ. **Le serveur compte les jours** contre la date
  du joueur et injecte `jours` : le MJ ne retape rien à chaque battement. Le
  compte s'écrit au flanc droit de la pièce (« 9 j »), en face de la marque
  d'état, et prend son encre quand le pli est `muet` ou en `attente` — parce que
  « muet depuis neuf jours » n'est pas « muet depuis hier », et que c'est
  exactement ce qu'on vient lire sur cette table. Les traits `corbeau` et
  `cavalier` datés reçoivent le même compte.

`canal` dit par quoi c'est passé — `lettre` `corbeau` `homme` `dragon` `oral`
`cri` —, et ce n'est pas un détail : un mot porté par un prince sur un dragon
n'a ni le même poids ni le même démenti possible qu'un feuillet scellé. `ames`
compte qui l'a reçu ou entendu (dix-neuf membres d'une cour, deux personnes dans
une salle du Nord).

| `etat` | ce que ça dit | la marque |
| --- | --- | --- |
| `redige` | écrit, **pas parti** — encore sous la main du joueur | un trait nu |
| `parti` | il est en route | une flèche |
| `remis` | il est arrivé | une coche |
| `confirme` | reçu, et on le sait par retour | une coche cerclée |
| `attente` | trop tôt pour une réponse | un rond creux |
| `muet` | resté sans réponse — et ça veut dire quelque chose | un rond barré |
| `perdu` | il n'est jamais arrivé | une croix |
| `intercepte` | quelqu'un d'autre l'a lu | un œil |

**L'état prime sur le camp pour la couleur** : un corbeau confirmé (vert) et un
corbeau perdu (sang) ne peuvent pas être de la même encre, fût-ce le même camp
qui les a envoyés. La marque se pose au flanc **gauche** de la pièce, à l'opposé
du `?` du doute — les deux se lisent ensemble sans se toucher. Comme une tête,
un pli n'est pas une force : il se range **sous** la place et porte son objet en
clair, parce qu'un message dont on ne lit pas l'objet ne sert à rien.

Même brouillard que le reste : `attente` et `muet` sont des croyances du joueur
(il n'a pas reçu de réponse), `intercepte` ne s'écrit que le jour où il
l'apprend — sinon le pli reste `remis` ou `muet` et c'est tout ce qu'il en sait.

### Les incidents — ce qui a pris, et jusqu'où ça a gagné

Un feu, une rumeur, une peur, une contagion : sur cette table, ça se suit
pareil. Un **foyer**, les endroits que ça a **gagnés**, ceux dont on **craint**
qu'ils y passent, une date par endroit, et une estimation d'âmes touchées.

Le MJ écrit **un seul objet** ; le module en dérive le foyer, chaque relais,
chaque fil de propagation et chaque crainte. Écrire quinze marques à la main
pour un seul incident, personne ne le tiendrait deux battements.

```json
{
  "id": "feu-serment", "genre": "incident", "camp": "vert", "feu": "vif",
  "nom": "Le bruit du serment forcé", "ou": "port-real",
  "ames": 400, "date": {"annee": 129, "lune": 3, "jour": 18},
  "certitude": "rapportee",
  "contenu": "On dit que la reine a fait jurer Sombreval sous la gueule de Syrax.",
  "propage": [
    {"ou": "rosby", "ames": 150, "date": {"annee": 129, "lune": 3, "jour": 19}, "certitude": "rumeur"},
    {"ou": "stokeworth", "ames": 90, "date": {"annee": 129, "lune": 3, "jour": 20}}
  ],
  "risque": [
    {"ou": "sombreval", "ames": 900, "note": "le bourg entier, si ça passe le Gosier"}
  ]
}
```

| champ | |
| --- | --- |
| `ou` / `point` | le **foyer** — d'où c'est parti |
| `ames` | l'estimation d'âmes touchées **à cet endroit** ; le foyer affiche le TOTAL |
| `feu` | `vif` (il gagne encore) · `couve` · `eteint` |
| `contenu` | ce qui se dit, en toutes lettres sous le doigt — comme un pli |
| `propage[]` | les endroits GAGNÉS : `{ou, ames, date, certitude, note}`, ou juste `"rosby"` |
| `propage[].contenu` | ce qui se dit **là-bas**, déformé — la version du propos à ce relais. Sans lui, le relais hérite du texte du foyer et la rumeur voyage sans se déformer. Écrit à la main, jamais par un script (voir `docs/plis.md`) |
| `propage[].depuis` | d'où le saut est parti : un **lieu** (bouche à oreille anonyme — la certitude doit décroître d'un cran) ou une **personne** (une parole d'autorité, avec un nom dessus : elle n'est pas tenue de décroître) |
| `risque[]` | les endroits qu'on CRAINT — même format, jamais de date d'arrivée |

- **Un relais adossé à quelqu'un n'est plus une rumeur.** `depuis` dit qui, et la
  fiabilité cesse alors d'avoir à décroître : `certitude` mesure la confiance de
  qui entend, pas la vérité de ce qui se dit.

Ce qui se lit à l'œil, et qui est tout l'intérêt de la chose :

- **La propagation ne se montre qu'au survol.** Quatre incidents posés tout
  entiers font une toile d'araignée par-dessus la baie : trente fils et quinze
  flammes pour quatre nouvelles, et plus personne ne lit les osts. Au repos, la
  table ne garde que les **foyers** et les endroits qui ont **réellement pris** ;
  les fils et les craintes apparaissent quand on tient l'incident sous le doigt,
  et l'ensemble de sa famille s'allume d'un coup — on va chercher la toile, elle
  ne s'impose pas.
  L'éveil est gardé **dans le module**, pas posé sur le DOM : la loupe remplace
  le `<svg>` soixante fois par seconde et une classe accrochée après coup ne
  survivrait pas au premier tour de molette. Et le survol **bascule la classe en
  place** au lieu de redessiner — un redessin ôterait de sous le curseur la pièce
  même qu'on survole, le navigateur enverrait aussitôt un `mouseout`, et la table
  clignoterait sans fin.
- **Le foyer est plein et cerclé de sang**, il écrit son nom en clair et porte le
  **total** ; les relais sont plus petits, plus pâles, anonymes, et portent leur
  compte local. On voit d'un coup où c'est parti et jusqu'où c'est allé.
- **Ce qu'on craint n'est qu'un contour** : pièce vide, fil maigre et pointillé,
  compte en italique préfixé `?` au lieu de `~`. Lire une crainte comme une
  nouvelle est exactement la faute que cette table interdit — et le seul moyen
  de l'empêcher est qu'elles ne se ressemblent pas.
- **Le tilde est là pour qu'on ne lise jamais ces chiffres comme un effectif.**
  `~640` n'est pas 640 hommes qu'on commande : c'est une estimation d'âmes.
- **Chaque relais compte ses propres jours** (même machinerie que les plis : une
  `date`, le serveur soustrait). C'est la colonne de chiffres qui dit à quelle
  vitesse la chose gagne — trois endroits en trois jours n'est pas trois
  endroits en trois lunes.
- Un incident `eteint` reste sur la table, en gris troué : on garde la mémoire
  de par où c'est passé.

### Le plan — ce qu'on veut faire, et sur qui ça atterrit

Tout le reste de cette table décrit ce qui **est** (ou ce qu'on croit qui est).
Le plan décrit ce qu'on **veut** — et c'est l'autre moitié d'une table de
guerre : un conseil ne se tient pas pour constater, il se tient pour décider
qui fait quoi et avant quand.

```json
{
  "id": "couper-grain", "genre": "dessein", "quoi": "intercepter", "camp": "noir",
  "nom": "Couper la route du grain", "ou": "rosby",
  "par": "ser Robert Quince", "echeance": {"annee": 129, "lune": 3, "jour": 22},
  "detail": "Deux barques et douze hommes, avant la marée."
}
```

| `quoi` | | | |
| --- | --- | --- | --- |
| `assieger` | `prendre` | `tenir` | `intercepter` |
| `frapper` (au dragon) | `bruler` | `bloquer` | `lever` (des hommes) |
| `ravitailler` | `evacuer` | `guetter` | `parler` |

- **`par`** — l'homme sur qui ça tombe. Un dessein sans `par` s'affiche « sur
  personne » au registre, et c'est un reproche : ce qui n'atterrit sur personne
  n'a pas été décidé.
- **`echeance`** — le jour où c'est dû. **Le serveur compte les jours qui
  restent** et injecte `dans` : la pièce écrit `J−6`, puis `échu`. Même
  machinerie que l'âge d'un pli, dans l'autre sens.
- **Un dessein ne doit jamais pouvoir se lire comme un fait** : contour seul,
  cercle interrompu, fond évidé, encre d'accent. On voit d'un coup que rien
  n'est encore là. Son nom, lui, est **en clair** — on ne devine pas ce qu'on a
  décidé de faire.
- **`plan: true` sur n'importe quelle marque** la bascule dans le plan et lui
  donne le même traitement fantôme : une marche projetée reste une marche, mais
  elle n'a rien à faire au milieu des marches réelles quand on regarde la carte
  de ce qui est.

Au registre, **le plan passe en tête, rangé par échéance** — ce qui est échu ou
tombe demain d'abord. C'est la seule part de cette liste qui demande une
décision ce soir ; le reste est du constat, et le constat peut attendre.

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

### Les oreilles — qui écoute pour vous, et depuis quand il se tait

Un pli arrive une fois et c'est fini. Une **oreille** est permanente, et toute
sa valeur est sa fraîcheur : ce qu'on vient lire sur la table n'est pas où elle
est, c'est **depuis combien de jours elle n'a rien dit**.

```json
{"id": "oreille-meliss", "genre": "oreille", "camp": "noir", "ou": "peyredragon",
 "nom": "Meliss, à la Claie", "certitude": "sure",
 "date": {"annee": 129, "lune": 3, "jour": 22},
 "donne": "ce qui mouille, ce qui décharge, ce qui ne descend pas",
 "prix": "du sel au prix du marais, la liste des quinze jours, la paix avec la garnison",
 "detail": "Ce qui se DIT chez elle est à ses clients et ne sera jamais demandé.",
 "statut": "actif"}
```

| champ | ce qu'il dit |
| --- | --- |
| `date` | **le dernier mot qu'elle a donné** — le serveur en tire les jours de silence |
| `donne` | ce qu'elle rapporte, en clair. Une oreille qui rapporte « tout » n'est pas une oreille |
| `prix` | ce qu'elle coûte, et en quoi. Une oreille qu'on ne paie pas est une oreille qu'on n'a pas |
| `etat` | **`nouee`** ou **`perdu`** seulement — le reste se dérive |

**Ce qui se calcule et ce qui se juge.** Le MJ n'écrit que les deux états qu'un
calcul ne saurait pas deviner : `nouee` (elle n'a rien donné encore) et `perdu`
(on **sait** qu'elle est tombée). Le serveur dérive les deux autres de l'âge du
dernier mot — `parle` en deçà de trois jours, `muette` au-delà — et la pièce
pâlit toute seule, sans jamais **sortir** de la table : une oreille qu'on
n'entend plus depuis deux lunes est précisément ce qu'il faut voir, et la faire
disparaître comme une position périmée reviendrait à cacher le trou.

**Il n'existe pas d'état « retournée ».** Si la reine le savait, elle la
couperait. C'est le silence long qui porte le doute — morte, retournée, ou
simplement rien à dire —, et il ne dit jamais lequel des trois.

**On n'y montre JAMAIS les oreilles d'en face.** La table est une table de
croyances : les oreilles de Larys Strong dans les châteaux de la baie n'y ont
rien à faire, même quand le MJ sait qu'elles y sont. Un soupçon d'oreille
adverse a déjà sa forme — un `incident` qui court, ou un pli `intercepte`.

Discipline : une oreille naît d'une scène — un accord passé, un homme envoyé —
et jamais d'un menu. Le jour où elle parle, on avance sa `date` ; le jour où
l'on apprend qu'elle est tombée, on la passe en `perdu` et on l'y laisse.

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

## Le registre — les affaires en cours, une par ligne

Une table de quarante marques ne se lit pas en cherchant à l'œil. Un pli et un
incident ne sont pas des décors : ce sont des **affaires**, avec un état, une
date et un compte — et une affaire se tient en liste avant de se regarder sur
la carte. La grande table porte donc un rail à gauche, `#table-liste`, construit
par `Carte.registre()`.

- **Les plis**, rangés par ce sur quoi le joueur peut encore agir : ce qui est
  `redige` (écrit, pas parti — encore sous sa main) d'abord, puis ce qui attend,
  ce qui est resté muet, ce qui est parti. Chaque ligne dit le destinataire,
  l'âge et l'état ; la pastille reprend l'encre de l'état, et un `redige` est un
  cercle **creux** — rien n'est parti.
- **Ce qui se propage**, rangé par ce que ça pèse EN TOUT (et non par ce que le
  foyer a pris) : c'est l'ordre dans lequel ces affaires vous tombent dessus.
  Chaque ligne dit le foyer, le nombre d'endroits gagnés, le total d'âmes et la
  vitesse.

**Cliquer une ligne ne fait qu'une chose : ne garder que celle-là.** La table
n'affiche plus que ce pli et la route qu'il a prise, ou cet incident et toute sa
famille (fils compris — on vient de cliquer son nom, on ne va pas les lui cacher
derrière un survol). Les filtres sont suspendus le temps qu'on tient l'affaire :
on a demandé CETTE chose-là, on ne va pas la cacher parce que sa famille est
éteinte. Le cadrage passe en `auto` sur les deux surfaces, la vignette comprise.

Recliquer la ligne, ou « Tout revoir », rend la table. Fermer la table la rend
aussi : on ne rouvre pas sur un royaume amputé sans se rappeler pourquoi.

Le lien entre un pli et son fil est explicite — `pli_id` sur le trait —, sans
quoi isoler un pli le montrerait sans sa route.

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

Deux garde-fous. On ne descend pas sous **22 unités** de large : plus près, la
simplification des côtes (Douglas-Peucker, 0,22 unité) se verrait en facettes. Et
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

### Ce qui est DIT, et ce qui n'est que le sol

Une table qui pose tout du même poids n'articule rien. Un geste qui parle de
deux coques se noyait dans les six plis que la table portait déjà : tout était
là, également nommé, également encré — donc rien n'était dit. Une phrase, elle,
distingue toujours *de quoi* on parle et *ce qu'on en dit*.

**Ce que la main pose parle ; le reste devient sol.** Le temps de la
démonstration, les pièces du geste gardent leur encre et portent leur nom en
clair ; tout ce que la table portait déjà s'amincit, pâlit, et **perd son nom**.
Le sol n'est pas effacé — on doit encore voir où ça se passe — il se tait. La
règle « un pli, une tête, un dessein s'écrivent toujours en clair » vaut sur la
grande table, où personne ne parle ; elle saute dès que quelqu'un parle.

Rien à écrire pour l'obtenir : c'est ce qui est dans `montre` qui parle. Sur le
décor, la hiérarchie dure le temps de la braise (~9 s), puis tout revient au
même poids. Dans la **vignette du fil**, elle est permanente — la vignette est
la citation du geste, et une citation ne se relit pas trois jours plus tard avec
les mots de quelqu'un d'autre en gras.

D'où la seule discipline que ça demande : **une carte, une phrase.** Trois
pièces au plus par geste. Ce qui ne rentre pas dans les trois va dans
`etat/jetons.json` s'il doit durer, ou n'est pas dit ce tour-ci.

### Nommer une pièce dans le texte

Un appui du MJ — `**deux coques repeintes**` — s'accroche tout seul à la pièce
dont c'est le `nom`. Survoler la phrase allume le jeton, survoler le jeton
allume la phrase. **Aucune syntaxe nouvelle** : on écrit ses appuis comme on les
écrivait, et la couture se fait à l'affichage. Une syntaxe de liaison à écrire à
la main sous pression de tour ne serait pas écrite.

Quand la phrase ne peut pas porter le nom exact, la pièce porte ses
formulations : `"ancre": ["les deux coques", "coques repeintes"]`. La
comparaison ignore la casse, les accents et la ponctuation.

Le survol va dans les **deux sens**, et ce n'est pas de la symétrie pour la
symétrie : une désignation à sens unique reste une légende, et une légende n'est
pas une langue.

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
sans une seule collision. Qui se tient où ne s'écrit plus en toutes lettres sous
la salle courante : ce sont les taches qui le disent, et pour toutes les salles
à la fois (voir ci-dessous).

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

### Qui se tient où — une tache, deux lettres

Le plan disait où l'on est ; il dit maintenant **avec qui**, et à trois portes de
qui. Chaque homme suivi pose une **tache d'encre de sa couleur, ses initiales
dedans**, dans la salle où il se trouve. Ceux qui partagent une salle se rangent
en couronne autour de son centre, et la tache rétrécit quand ils sont nombreux :
un plan illisible ne dit plus rien.

```
etat/presence.json          où se tient chacun (routines + exceptions, resolu)
        │  /presence → places
        ▼
ecrans/modules/taches.js    la couleur, les deux lettres, la forme de la tache
        │
        ▼
ecrans/modules/plan.js      les pose salle par salle ; terrain.js les pose au point près
```

À l'épaule droite de la tache, une pastille porte le **signe de l'office** —
⚔ la garde, 📜 le mestre, ⚓ le port, ⚒ les tailleurs, ⛓ les fers, ✉ le page,
🗣 qui parle pour les siens, 👑 le sang, ✧ la septa. Il se déduit du `titre`
(première clause seulement : « Septa de la maison de la reine ; élève Aegon »
n'est pas une reine), à défaut de l'id, et se force avec `embleme`. Sans office
reconnu, pas de pastille : mieux vaut rien qu'un symbole qui ne distingue
personne.

Le signe est commun au plan et aux cartes du dessus (`acteurs` de `ville.json` et
`terrain.json`) : le même homme se reconnaît d'une échelle à l'autre. La couleur
est stable, tirée de l'id ou forcée par `teinte` ; les initiales se déduisent du
nom, titres et particules ôtés — « Ser Robert Quince » fait **RQ**. Le
personnage joué porte un halo, la salle où l'on se tient un contour de braise.
Cliquer une tache ouvre un moment de pensée sur la personne
(`cible_type: "personnage"`), comme cliquer une salle en ouvre un sur le lieu.

**La salle où l'on est prime sur le fichier.** Qui a son visage au bandeau est
là — on le voit de ses yeux —, et il pose sa tache dans la salle courante même
si `presence.json` ne l'a jamais placé nulle part. Sans cette règle, un conseil
de neuf paraissait en compter quatre : `presence` ne tient que les gens qu'une
routine ou une scène a posés quelque part. Le plan se redessine à chaque item du
flux (groupé sur un quart de seconde), pas seulement toutes les quinze secondes.

Deux personnes d'une même salle qui tomberaient sur les mêmes lettres sont
départagées par la première lettre où leurs **prénoms** diffèrent : Rhaenyra
fait **RR**, Rhaenys **RS**.

**Le brouillard n'est pas levé pour autant.** Ce sont ses gens, dans ses murs,
dont l'office dit l'endroit : le mestre à la roukerie, le maître de port au
quai. Le serveur retire de `places` les personnages des **autres joueurs** tant
qu'ils ne sont pas sous les yeux — savoir où se tient sa maîtresse de la voix ne
se lit pas sur un plan — et rien ne s'affiche pour une salle d'un autre château.
Une salle nommée par les routines mais absente de `plans.js` ne montre personne :
c'est un trou de dessin, pas un secret. Trois y ont été ajoutées à ce titre — la
porte de mer, les galeries, le bourg.

### Ce que le plan ne fait pas

Il ne sert pas à se déplacer : cliquer une salle ouvre un moment de pensée (même
canal que les entités du fil : `cible_type: "salle"`). On y songe, on n'y va
pas ; se déplacer se dit dans le champ libre.

## Le terrain — le champ, vu du dessus

La troisième échelle du décor. Le royaume dit **où** porte la guerre, le château
dit **qui est à trois portes de moi**, le terrain dit **ce que mille hommes
occupent réellement de sol, et dans quel ordre ils s'y tiennent**.

```
etat/terrains/<lieu>.json   le champ de la ville où l'on se tient, s'il existe
etat/terrain.json           sinon, le champ courant, ou rien
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

**Un terrain par ville**, même contrat que `etat/villes/<lieu>.json` :
`etat/terrains/<lieu>.json` est lu d'abord — `<lieu>` étant le `lieu_id` du
personnage assis —, `etat/terrain.json` ensuite. Strictement additif : tant
qu'aucun fichier ne porte le nom du lieu où l'on se tient, on sert exactement ce
qu'on servait avant. Un champ dont le `lieu_id` nomme un autre lieu que celui du
joueur est écarté — mieux vaut pas d'échelle qu'une échelle qui ment. C'est ce
qui permet de tenir le champ d'une ville où l'on n'est pas encore, et, à deux
sièges dans deux lieux, de ne pas se marcher dessus.

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
le long d'une route) le nomme. Un `detail` s'ajoute au survol après le nom —
c'est là qu'une rue dit POURQUOI elle existe. Un bois porte son semis d'arbres,
une colline sa seconde courbe de niveau ; un champ garde des bords droits, parce
que c'est une charrue qui les a tracés.

**Piège du `village` : ses `points` ne dessinent pas un contour, ce sont les
TOITS eux-mêmes**, un par point. Un polygone de douze sommets ne donne pas un
bourg, il donne douze maisons posées en cercle. Un point vaut `[x, y]` — le toit
prend alors sa taille et son biais du hasard, ce qu'il faut pour un hameau — ou
`[x, y, angle, largeur]`, et c'est ce qu'il faut pour une VILLE : là, une maison
n'est pas jetée sur le sol, elle a **sa façade sur la rue**. D'où l'ordre dans
lequel une ville s'écrit : la circulation d'abord (nœuds obligatoires → artères
→ rues → ruelles), les maisons ensuite, alignées le long de ce que la
circulation a découpé. Semer les maisons puis passer les rues entre elles donne
une constellation, jamais une ville — `etat/villes/port-real.json` est bâti dans
le bon ordre et sert de modèle.

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

- **acteurs** : la couche des VISAGES. Un corps dit combien d'hommes tiennent un
  endroit ; un acteur dit QUI s'y trouve. Une tache d'encre de sa couleur avec
  ses initiales dedans, rien de plus — le nom et le titre viennent au survol, un
  clic ouvre un moment de pensée (`cible_type: "personnage"`).

  ```json
  { "id": "rulf-corne", "nom": "Rulf Corne", "titre": "Maître de port",
    "ou": [178, 140], "camp": "noir", "teinte": "#8c2f39",
    "certitude": "sure", "joueur": false, "taille": 1, "ou_dit": "Au quai" }
  ```

  `ou` [x,y] dans le repère ; `teinte` facultative (sinon une couleur stable
  tirée de l'id) ; `initiales` pour forcer les deux lettres, sinon elles se
  déduisent du nom, titres et particules ôtés. `joueur: true` cercle le
  personnage joué. La `certitude` délave et pointille la tache comme partout.
  **Ceux qui partagent une place se rangent en couronne autour d'elle** — vingt
  personnes dans un château ne s'empilent pas. La tache garde une taille
  constante à l'écran : c'est un repère, pas une surface de sol.

  Même brouillard que le reste, et il mord ici plus qu'ailleurs : n'y figure que
  qui le joueur a vu ou qu'on lui a rapporté. Un homme dont il ignore la
  position n'a pas de tache ; un homme qu'on lui a dit au quai en porte une,
  délavée, au quai — même s'il est ailleurs.

`par_cercle` se choisit à l'échelle : 25 hommes pour une bataille, 10 personnes
pour une ville, sans quoi les petits corps (vingt et un sauniers) disparaissent.

Même brouillard que partout : **n'y figure que ce que le joueur a vu ou qu'on lui
a rapporté**, avec sa `certitude`. Et referme la ville (vide le fichier) quand on
a quitté les lieux — un décor qui traîne est un mensonge sur où l'on est.

## L'échiquier — les affaires du conseil, de ce qu'on a à ce qu'on veut

La table peinte dit **où** porte la guerre. L'échiquier dit **comment** ce qu'on
a devient ce qu'on veut — dans le vocabulaire de la maison, celui du guide
[« Comment on ouvre une affaire »](../etat/books.json) (`guide-des-affaires`),
posé sur cette table même. La boîte reste sous la Table Peinte dans la fiction,
mais **l'échelle s'ouvre partout** : elle est dans la bascule d'où que le joueur
regarde, dès qu'il y a une affaire à lire — une ligne de jeu qu'on ne peut relire
qu'au seul endroit où l'on n'a plus besoin de se la rappeler n'est pas relue.

**Sept objets, et pas un de plus** — ce sont ceux du guide, avec ses signes :

| | l'objet | ce que c'est |
| --- | --- | --- |
| 🏰 | l'**affaire** | le conteneur de travail du conseil. « N'est pas un septième objet » : elle ne dit rien du monde, elle rassemble. **Un plateau = une affaire.** |
| 🎯 | l'**état cible** | ce qui doit devenir vrai dans le monde. **Une colonne = un état cible.** |
| 🔒 | le **verrou** | le fait du monde qui empêche un état de tenir |
| 🗝️ | la **clef** | le mécanisme envisagé pour lever un verrou — *à étudier · retenue · écartée* |
| ⚔️ | l'**action** | ce qu'on décide effectivement de faire |
| 🔨 | le **moyen** | ce qu'on peut réellement employer — cité (M01, M18…), jamais créé |
| 🪶 | l'**office** | l'autorité sous laquelle une action est portée — cité (O03, O07…) |

**Le temps n'y est pas une coordonnée.** C'est un damier, pas une frise : ce qui
s'y lit est la position, pas l'histoire. Les cinq rangs sont la chaîne du guide,
et l'on **DESCEND** de haut en bas : état cible → verrou → clef → action →
moyen et office.

### Les états cibles ne sont pas une rangée — c'est un arbre

La colonne `⬆️ Sert` du registre pointe vers l'état **amont** (« 200 sert 100 »).
Les douze états cibles de la Prise de Port-Réal ne sont donc pas douze colonnes
parallèles : c'est un arbre de **quatre niveaux sous une seule racine**. Les
étaler à plat était un contresens autant qu'un problème de place — les cases
tombaient à 39 px.

Le haut du plateau est donc une **canopée** : chaque état s'assied à son niveau
et s'étend sur les colonnes de son sous-arbre. Une **colonne** s'ouvre sous un
état qui porte des verrous, et sous une feuille qui n'en porte aucun — pour
qu'une feuille rompue reste comptée. Un état intermédiaire sans verrou n'a pas de
colonne à lui : **il coiffe celles de ses enfants**. La Prise de Port-Réal passe
ainsi de douze colonnes à **huit**, et la case de 39 à **60 px**.

Les étages de canopée sont des bandes (0,46 case) et non des rangs de cases : un
jeton y tient au large, et les quatre rangs du damier gardent leurs cases
carrées. Les branches de l'arbre sont tracées par la même main que les marches,
d'un sceau à l'autre.

Un arbre qui n'a qu'un niveau — les affaires à un ou deux états — ne change pas
d'aspect : la canopée fait alors une seule bande.

### La source, et elle a changé : les CAHIERS

**Il y avait deux plans dans `books.json`, et cette vue lisait le petit.** Chaque
cahier `affaire-*` porte ses propres tables — 🎯 États cibles, 🔒 Verrous,
🗝️ Clefs, ⚔️ Actions — avec le même vocabulaire que les six registres par type.
Le compte tranche :

| | lignes | dont actions |
| --- | --- | --- |
| les 37 cahiers porteurs de tables | **1 164** | **580** |
| les six registres par type | 156 | 60 |

*Contrôle naval* tient à lui seul 22 actions dans son cahier quand le registre en
connaît 12 en tout, et les affaires les plus travaillées — *Ce qui part, et par
où*, *Le jour d'entrée*, *Financement de la campagne* — n'avaient pas une ligne
au registre. Le guide le disait déjà : **« l'affaire est l'unité de TRAVAIL, les
six registres par type sont l'unité de RANGEMENT »**. Le travail est dans les
cahiers ; l'index avait décroché.

**Un cahier = une affaire = un plateau.** On passe de 12 à **36 plateaux**, de 60
à **657 actions**, de 49 à **504 actes** — et l'appariement par NOM disparaît :
le volume EST l'affaire, avec son titre, son emblème, son lien et sa main. C'est
lui qui perdait *L'entrée sans bataille* et faussait les fanions d'office.

**Les colonnes se trouvent par leur en-tête, jamais par leur rang.** Un cahier
écrit `💰 Le prix` et `🚪 Ce que cela ferme` là où le registre a une seule
colonne de coût ; un autre n'a pas de colonne `📍 Où`. La colonne `⚖️ Retenue`
des registres s'appelle `⚖️ Décision` dans les cahiers, avec les mêmes trois
valeurs — *retenue* (192), *à étudier* (22), *écartée* (2) —, plus trois lignes
« à trancher (la reine) » qui comptent comme *à étudier*, ce qui est leur sens.
**Ce qu'un cahier n'écrit pas, on ne l'invente pas** : la case reste vide et la
conclusion en tient compte.

**Les six registres restent en repli, et le repli est vide** : les 12 affaires
qu'ils décrivent ont toutes leur cahier. Le code les reprendrait — pour les seuls
états qu'aucun cahier ne porte, et seulement ce qui chaîne à eux — si l'index
devait un jour connaître une affaire que le travail ignore.

**Un seul plateau en détail à la fois.** 36 cahiers font 2 275 pièces et **1,83
Mo** en une réponse, quand le joueur n'en regarde qu'un. La route accepte donc
`?affaire=<id>` : le détail ne part que pour l'affaire ouverte, les autres
n'envoient que leur chapeau — titre, emblème, objet, comptes, pieds d'arbre pour
la bulle du blason. La page redemande la route quand on change de plateau et
garde ce qu'elle a reçu. **412 Ko** au lieu de 1,83 Mo, dont 235 de catalogue de
missions et 86 de portraits.

**Vérifié après bascule** : 36 affaires, 2 275 pièces (109 états, 306 verrous,
267 clefs, 657 actions), **zéro référence cassée**, zéro pièce sans amont, zéro
pièce qui conclut « la chaîne tient » en portant une mission. Le coffret « Les
sujets » passe de **5 idées sur 38 volumes à 32**.

#### Ce que disent les tables « Les trous »

Quatre cahiers portent une table `🕳️ Les trous`, écrite à la main, qui liste ce
que les détecteurs cherchent. C'est un jeu de test humain, et la comparaison
apprend quelque chose dans les deux sens :

| cahier | écrit à la main | détecté | accord |
| --- | --- | --- | --- |
| Entrée du Donjon Rouge | 4 actions sans office | 4 | **exact** |
| L'entrée sans bataille | 8 | 3 | les 3 sont dans les 8 |
| Déplacement de l'armée | 2 | 13 | aucun commun |
| Affaire vierge — IV | « aucun » | 17 | aucun commun |

L'écart n'est pas un bug : **les deux ne cherchent pas la même chose.** L'homme
note « office cité en clair au lieu de son numéro » — vrai de 537 actions sur
580. Le détecteur, lui, demande seulement qu'un office du registre RÉPONDE de
l'action, et il en retrouve beaucoup par le nom de leur titulaire. Là où l'homme
a écrit sa liste et ne l'a pas tenue à jour (*Déplacement de l'armée*), c'est le
détecteur qui a raison ; là où il en voit plus que nous (*L'entrée sans
bataille*), c'est son critère qui est plus strict. Aucune des deux listes ne se
substitue à l'autre, et le tableau ci-dessus est la seule façon honnête de le
dire.

### Rien n'est écrit ici — tout est dérivé des CAHIERS

**Il n'y a pas de fichier d'état pour l'échiquier**, et c'est le point. La route
`/echiquier` dérive tout des tables des **cahiers d'affaire** de
`etat/books.json` — 🎯 États cibles, 🔒 Verrous, 🗝️ Clefs, ⚔️ Actions —, qui
sont l'unité de TRAVAIL de la maison. Une vue qui recopierait le plan à la main
serait un mensonge en attente.

> **Cette phrase du guide n'est plus vraie, et c'est une décision de la maison,
> prise le 30e.** « Quand l'affaire et le registre se contredisent, c'est le
> registre qui a raison » supposait un registre TENU. Il ne l'est plus : 156
> lignes contre 1164, et la plupart des affaires les plus travaillées n'y ont
> pas une ligne. **Un seul plan désormais : les cahiers d'affaire sont la
> vérité, les registres par type deviennent dérivés** — régénérés depuis les
> cahiers, jamais écrits à la main, comme `couverture.py` régénère déjà les
> tables de trous. Le guide reste un objet de fiction et ne se corrige pas ;
> c'est ici qu'on note ce qui a changé.

Conséquence pour le MJ : **on ne met pas l'échiquier à jour, on tient les
cahiers.** Une clef qui passe de *à étudier* à *retenue* dans la table 🗝️ Clefs
de son cahier
ouvre une brèche sur le plateau à la lecture suivante, sans qu'on touche à rien
d'autre. Les liens se font par les adresses : un verrou dit quel état il bloque,
une clef quel verrou elle ouvre, une action quelle clef elle réalise, et une
adresse ne se renumérote jamais.

### L'épreuve du guide, rendue à l'œil

C'est ce que la vue apporte de neuf, et sa raison d'être. Le guide demande de
**REMONTER** depuis n'importe quelle action jusqu'à l'affaire : « si la remontée
est impossible, l'action n'a pas de raison stratégique démontrée — elle se
supprime ou se requalifie. C'est la seule épreuve de ce livre qu'on doive faire
passer à chaque conseil. »

Sur le plateau, elle se passe toute seule : **une colonne qui ne descend jusqu'à
aucune action a sa réglette rouge**, et son état cible porte le fanion de faute.
Et elle **remonte dans l'arbre** : un état qui coiffe des colonnes toutes rompues
est rompu lui-même, sa branche vire au rouge et le fanion se pose sur lui. La
tuile d'une affaire qui en contient prend un liseré rouge, de sorte que le défaut
se voit avant même d'ouvrir le plateau.

Les autres fautes se repèrent de la même façon, sans survol : une pièce sans
preuve, un verrou dont on ne sait pas dire à quoi il serait levé, une action que
ne porte aucun office, un moyen cité dans une action et absent de son registre —
le guide le dit : « le moyen et l'office ne se créent jamais dans une affaire ».

### Le survol allume la chaîne causale

C'est l'épreuve du guide rendue au geste, et c'est ce que la vue apporte de plus.
`vers` monte toujours — un moyen vers son action, l'action vers sa clef, la clef
vers son verrou, le verrou vers son état, un état vers celui qu'il **sert** —,
alors deux parcours du même graphe disent tout :

- **L'AVAL, à pleine encre** : tout ce qui **construit** la pièce survolée. Sur un
  état cible, c'est son sous-arbre entier — ses verrous, les clefs qui les
  ouvrent, les actions qui réalisent ces clefs, les moyens et offices qu'elles
  citent, **et la même chose pour chaque état qui le sert**, jusqu'en bas.
- **L'AMONT, à mi-voix** : ce à quoi elle **sert**, jusqu'à la racine de l'arbre.
  Depuis une action : sa clef, son verrou, son état cible, puis la branche
  `⬆️ Sert` jusqu'au pied. C'est mot pour mot la **REMONTÉE** que le guide veut
  faire passer à chaque conseil — « si la remontée est impossible, l'action n'a
  pas de raison stratégique démontrée ».

Le reste du plateau s'estompe — jetons, traits, réglettes, canopée. **On ne
touche que l'opacité** : pas une mesure ne bouge, donc pas de reflow, et l'on
peut traverser le damier sans que l'écran saute. Un trait ne s'allume que si
**ses deux bouts** sont dans la chaîne, sans quoi une clef écartée qui touche le
même verrou s'allumerait par la bande.

Le geste est amorti : **90 ms avant d'allumer** (40 ms si l'on passe d'un jeton à
son voisin), **140 ms de tolérance à la sortie**. Une souris qui traverse le
plateau n'allume rien au passage.

### Chaque affaire porte son emblème, et l'action porte un visage

**L'emblème d'une affaire est celui de son volume** — `embleme` dans
`books.json`, choisi par la maison —, servi par la route à côté du titre et
jamais choisi ici. L'emblème de l'affaire courante s'affiche **en grand** (46 px)
au chef du plateau : c'est la seule pièce du dispositif qui ait le droit d'être
grosse, elle dit de quoi ce plateau parle avant qu'on ait rien lu. À côté, la
bascule montre chaque affaire par son emblème, plus petit (24 px), la courante
allumée et les autres en retrait. Le liseré rouge de l'épreuve reste sur les
deux. Une affaire qu'aucun volume ne nomme garde le 🏰 générique du guide — et
cette absence est une information : c'est un cahier qui reste à ouvrir.

**Le jeton d'une action porte le visage de son teneur.** La chaîne du
rattachement est celle du guide : action → son office → le titulaire de cet
office → le personnage. Le portrait vient **inliné en SVG par le serveur**, comme
partout ailleurs dans ce jeu (la page ne charge aucune ressource externe), et
chaque portrait n'est **servi qu'une fois** : un dictionnaire à part, et l'action
ne porte que l'identifiant de son teneur.

**Et il faut de la hauteur à un visage.** La barrette coupe à 22 % et 78 % : sur
un sceau carré de 25 px, il ne restait que 14 px de portrait — 23 % de la case,
pour l'objet le plus vertical du plateau. Deux corrections, dans cet ordre : le
**cadre monte et descend** (le sceau d'une action à visage s'allonge ; la case,
elle, ne bouge pas d'un pixel et reste carrée), et la **barrette s'assouplit** à
14/86 sur ces jetons-là. Entre une barrette parfaite et un visage lisible, on
prend le visage. Le dessin est en outre cadré en `slice` : sans cela, un portrait
carré posé dans un cadre haut se centre et laisse deux bandes vides — on aurait
agrandi le cadre sans agrandir le visage. Résultat mesuré sur la Prise de
Port-Réal : **de 23 % à 47,5 % de la hauteur de case**, le portrait rendu passant
de 25 à 40 px.

Le cadre haut ne s'applique qu'aux cases qui tiennent **une ou deux pièces** :
au-delà les jetons s'empilent sur deux rangées et un sceau haut déborderait. Les
cases denses gardent l'ancien carré — on n'y lisait de toute façon aucun visage.

La dernière jointure se fait sur un nom écrit en toutes lettres, donc on la fait
sobrement : on ne lit que la tête de la cellule, on ôte les titres, et l'on
n'accepte qu'une **suite de mots entiers** commune aux deux côtés — « Wend » ne
devient pas « Wenda », et un office VIDE ne prend pas le visage de qui se trouve
nommé dans sa ligne. **Faute de teneur, l'action garde ⚔️** : l'absence est déjà
une faute, elle porte son fanion, et elle devient très lisible quand toutes les
autres actions ont un visage. Quand l'office ne se résout pas mais que l'action
nomme quelqu'un (« Dame Aurore Inchauspé, maîtresse des nouvelles »), le visage
apparaît **et le fanion reste** : quelqu'un le fait, et personne n'en répond.

Dans la bulle, le teneur se glisse **dans la tête**, sous le titre : il n'ouvre
pas une quatrième ligne, c'est la même chose qu'on regarde — l'action, et la main
qui la porte.

### Les marches — la chaîne, en traits

Chaque montée d'un rang à l'autre est un trait tiré d'un jeton à l'autre, et la
monnaie n'est pas la même à chaque étage :

| de | vers | ce qui la paie |
| --- | --- | --- |
| verrou | état cible | savoir dire **à quoi il serait levé** |
| clef | verrou | être **retenue** — une clef à étudier n'a rien converti |
| action | clef | être **faite ou en cours** |
| moyen · office | action | être **au registre**, sous son numéro |

Trait plein quand c'est payé, **pointillé neutre** quand ça attend (ce n'est pas
une faute, c'est le tarif qui court), **tirets rouges** quand la remontée
s'arrête là. Survoler une pièce allume ses traits.

### L'occlusion — un état cible ne se voit que par les brèches de ses verrous

On repose sur le jeton de l'état **une dalle par verrou**. La brèche s'ouvre
quand une clef **retenue** est écrite contre ce verrou-là, et pas avant : c'est
la définition même du verrou dans le guide (« si tout le reste était acquis et
que ceci restait vrai, l'état serait-il impossible ? »).

Un état à deux verrous dont un seul est percé se voit à moitié ; un état à un
verrou sans clef retenue est **muré**. Ce n'est pas un effet : ça interdit de se
raconter un plan. Le joueur ne voit pas un but *difficile*, il voit un état
**qu'il ne peut pas encore formuler**. Trois silhouettes de cadre doublent
l'occlusion pour qu'elle se lise de loin, et les brèches se comptent en points
sous le jeton.

### Ce qu'on voit, et ce qu'on lit

**Aucun texte sur le plateau.** Des cases carrées, toutes égales, un jeton par
pièce — et la **forme avant la couleur** : la silhouette du sceau reprend les
pièces de bois de la nappe (tuile à huit côtés, rectangle, hexagone, losange,
barrette, rond, carré épais), l'emoji du guide porte le sens, et la teinte du
rang passe entièrement par le cadre, puisqu'un emoji n'obéit pas à la couleur du
texte.

**Le titre de l'affaire ouverte s'écrit en clair**, à côté du grand blason :
l'emblème la dit d'un coup d'œil, le titre la nomme. Le « zéro texte » vaut pour
le PLATEAU — les cases, les jetons, la canopée, la gouttière ; ceci est hors du
damier. Et seulement l'affaire ouverte : les autres restent des emblèmes muets,
c'est le contraste qui fait la lecture. Le titre cède la place (une ligne,
coupée) plutôt que de pousser la bascule sur un second rang, qui prendrait la
hauteur du plateau.

**Le plateau est plein de sa case** : il prend tout l'emplacement du décor, et
c'est la TAILLE de la case qui se calcule — la plus grande qui tienne en largeur
comme en hauteur, canopée comprise dans le compte, appliquée uniformément —,
jamais la case qui s'étire. Il se recalcule à chaque changement de taille.

### La bulle conclut — où ça casse

Une **conclusion** dit, en une phrase, le **premier maillon qui manque en
descendant**. Jamais un résumé : une pièce, un coupable, une phrase. Elle se pose
sous la tête et au-dessus des maillons — c'est la réponse à « alors, où on en
est ? », et ce qui suit est là pour qui veut vérifier.

Elle ne lit **que la topologie** — ni date, ni prose — et se calcule au serveur
avec le reste des dérivations. **Un seul mécanisme, pas six cas particuliers** :
on descend depuis la pièce et l'on s'arrête au premier trou. Un état descend sur
ses verrous ET sur les états qui le servent, ce qui est exactement ce que compte
déjà l'épreuve du guide — les deux calculs disent donc la même vérité.

| état du graphe | ce que la bulle conclut |
| --- | --- |
| aucun verrou sous l'état cible | aucun verrou écrit : c'est une intention, pas un plan |
| un verrou sans aucune clef | rien n'est envisagé contre lui |
| toutes les clefs sont *à étudier* | sa clef 🗝️ *X* n'est qu'à l'étude |
| une clef *retenue* sans action | elle est retenue, et personne ne la fait |
| une action sans teneur | personne n'en répond |
| la chaîne descend jusqu'au bout | **la chaîne tient** |

Quand plusieurs maillons cassent de la même façon, on nomme le premier et l'on
compte les autres (« et 2 autres dans le même cas ») : une liste de griefs, c'est
le tunnel. Un moyen et un office, qui n'ont rien en dessous, ne concluent rien.
Et quand la chaîne tient, **on le dit** — c'est assez rare pour que le silence se
confonde avec un oubli.

**Le verdict et le fanion disent la même chose.** Une action que quelqu'un porte
sans qu'aucun office numéroté n'en réponde arbore son fanion : sa conclusion le
dit aussi — « la chaîne tient — mais aucun office ne la porte » —, sinon le
joueur lirait un drapeau rouge sous un verdict serein.

**La bulle de survol DIT la chaîne** que le plateau vient d'allumer, pour qu'on
n'ait pas à suivre les traits à l'œil. Trois étages, et un seul texte long :

- **Au-dessus, à mi-voix, ce à quoi la pièce sert** — la remontée, du plus proche
  à la racine, en signes et titres sur une ligne. Même grammaire que sur le
  plateau, où l'amont est estompé.
- **La tête : la pièce survolée** — signe, nom, description. **Elle est la seule à
  garder sa description**, qui est la colonne qui DIT la chose dans le registre de
  son rang : `✅ Ce qui doit être vrai` pour un état cible, `📌 Ce qui est vrai
  aujourd'hui` pour un verrou, `💡 Le principe` pour une clef, `📝 Ce qu'on fait,
  et où` pour une action, `💪 Ce qu'il sait faire` pour un moyen, `📿 Ce dont il
  répond` pour un office.
- **Dessous, ce qui la construit** : un maillon par ligne, **signe et titre
  seulement**, dans l'ordre de la descente. La chaîne BRANCHE — un état a
  plusieurs verrous, un verrou plusieurs clefs — et à cette taille un arbre
  indenté ne se lit pas : on **groupe par rang** (les états qui servent, puis les
  verrous, les clefs, les actions, les moyens et les offices), ce qui se lit d'un
  coup d'œil. Chaque maillon porte la teinte de son rang, comme son jeton.

**La bulle est bornée, et elle le dit** : quatre maillons par rang, puis « et
N autres ». Sans quoi la racine de la Prise de Port-Réal, qui allume 53 pièces,
ferait une bulle de 53 lignes — c'est le tunnel, et il est interdit ici comme
ailleurs. Vérifié : 24 maillons montrés et 29 annoncés font bien les 53 allumés.
Au-delà de 58 % de la hauteur de fenêtre elle défile au lieu de déborder, et
**elle se range à côté du damier, jamais dessus** : elle décrit le plateau, elle
ne doit pas le cacher.

**Tout le reste attend le clic sur l'encart**, qui le retient et le déplie : la
preuve, le « levé quand », le coût de la clef, où en est l'action, le détail des
brèches, les fautes, et l'adresse au registre. Rien n'est perdu, rien n'encombre.
Ce qui doit se voir **sans rien survoler** reste sur le plateau : le fanion des
fautes, et lui seul.

**Et le clic sur un jeton ouvre le volume de l'affaire dans les livres** — c'est
là qu'on travaille, le plateau n'en est qu'une vue. Le bandeau de tuiles 🏰 en
haut donne une affaire par tuile : un clic change de plateau, un clic sur la
tuile courante ouvre son volume. Une affaire nommée aux registres et qui n'a pas
encore son volume ouvre le registre des états cibles — on n'invente pas un lien
mort ; mieux vaut alors **lui ouvrir son cahier**, comme on l'a fait pour la
Prise de Port-Réal (`affaire-prise-de-port-real`), aux quatre champs du guide et
sans une ligne qui ne soit déjà aux registres.

### La bulle prescrit — ce qu'il y aurait à faire

La conclusion dit **où ça casse** ; elle s'arrêtait là, et le joueur repartait
avec un diagnostic et rien à faire. Les **missions** sont l'autre moitié. Elles
se calculent au serveur avec les autres dérivations, sur la **seule topologie et
l'état des nœuds** — ni date, ni lecture de prose —, et **rien ne s'écrit** : une
mission s'affiche, elle ne touche aucun registre et ne commande rien.

**Un gabarit, et il est lui-même le filtre :**

> Afin d'atteindre **{X}**, faire **{Y}** aurait effet **{Z}**.

**X** se calcule **en remontant** — l'état cible que l'acte sert, et combien
d'autres il touche quand un verrou en bloque plusieurs. **Y** est la seule part
écrite en dur, par un verbe : *retenir, écarter, désigner, écrire, trouver*. **Z**
se calcule **en regardant l'amont immédiat**, et il doit être **honnête** : « le
seul verrou qui l'en sépare » quand c'est vrai, « un verrou sur deux » quand ça ne
suffit pas. Un détecteur dont on ne sait pas calculer le X ou le Z n'en est pas
un : il se jette, il ne s'écrit pas avec un Z vague.

| condition sur le graphe | l'acte | sur qui ça tombe | tombe |
| --- | --- | --- | --- |
| toutes les clefs d'un verrou sont *à étudier* | **retenir ou écarter** 🗝️ la clef | la reine | 12 |
| aucun office du registre ne porte une action | **désigner qui répond de** ⚔️ l'action | la reine | 30 |
| un état cible sans aucun verrou | **trouver ce qui empêche** 🎯 l'état | le conseil | 6 |
| un verrou sans aucune clef | **écrire une clef contre** 🔒 le verrou | le conseil | 1 |
| une action sous une clef non *retenue* | **trancher** 🗝️ la clef | la reine | 19 bruts, 0 après dédup |
| une clef *retenue* sans action | **écrire l'action de** 🗝️ la clef | le conseil | 0 aujourd'hui |

**LA DÉDUPLICATION SE FAIT PAR L'ACTE, PAS PAR LE DÉTECTEUR**, et c'est le cœur
du dispositif. « Toutes les clefs de ce verrou sont à l'étude » et « cette action
pend sous une clef qui n'est pas retenue » désignent le plus souvent **le même
acte** : retenir cette clef-là. Un acte s'identifie donc par le couple (verbe,
pièce) et se pose **une seule fois** ; le premier détecteur qui le trouve écrit
sa phrase, les suivants s'y rangent. Mesuré sur le plan : **68 détections brutes
→ 49 actes**, les 19 « trancher » se rangeant en entier derrière les 12
« retenir ou écarter » — parce qu'aucun verrou du plan n'a plus d'une clef.
Sans cela, le plateau réclamerait trois fois la même décision sous trois
libellés : c'est le tunnel, et il est interdit ici comme ailleurs.

**Deux familles de porteurs, et elles se voient sans qu'on lise** — filet braise
ou filet vert le long de la ligne. **À la reine** (retenir, écarter, désigner) :
c'est sa parole, personne d'autre ne peut, et ça ne coûte rien à exécuter puisque
le texte est déjà au registre. **Au conseil** (écrire, trouver) : c'est du
travail, et ça se dépêche. Sur le plan : 42 à la reine, 7 au conseil.

**Sur un jeton**, les missions de toute sa chaîne descendante, dédupliquées,
**deux au maximum** puis « et N autres » — la racine de la Prise de Port-Réal en
réclame onze. **Sur le blason de l'affaire**, ce qui est vrai de l'affaire
entière : le compte de ses missions, et **le fait retourné** — aucun de ses
verrous n'a de rechange, une clef contre chacun, là où le guide veut qu'elles
« se disputent la place ». C'est le principe : *un fait vrai de presque tout le
monde va au chapeau, jamais sur les jetons*. « Ce verrou n'a pas de rechange »
est vrai de 32 verrous sur 33 — posé sur les pièces il ne dirait rien et noierait
le reste. **Zéro texte sur le plateau**, comme partout : tout est dans la bulle,
et les fanions ne bougent pas.

**Les deux calculs doivent dire la même vérité**, et c'est la vérification qui
compte : une pièce qui conclut « la chaîne tient » ne porte **aucune** mission,
une pièce à fanion en porte **au moins une**. Deux divergences trouvées et
corrigées du côté qui mentait — le calcul des missions a servi de révélateur :

- « personne n'en répond » **ne s'arrêtait pas de remonter** : une clef dont
  toutes les actions sont portées hors registre concluait « la chaîne tient » à
  plat, au-dessus de trois fanions. Le caveat remonte désormais avec la chaîne.
- l'acte « trancher une clef » s'accrochait à **l'action** qui l'avait fait voir,
  alors que la conclusion rend son verdict au **verrou**. Deux calculs qui
  accrochent la même chose à deux rangs différents finissent par se contredire :
  l'acte se pose au verrou.

Restent 53 fanions sans mission, tous de la même famille : un moyen ou un office
**cité dans une action et absent de son registre**. Le catalogue n'a pas de
détecteur pour eux, et l'on n'en invente pas : leur X et leur Z ne se calculent
pas sur ce graphe.

### La lampe — une mission se voit de loin

Une mission qu'on ne découvre qu'en promenant le curseur n'est pas rendue : le
plateau porte donc une **💡 au coin du sceau**, sur toute pièce sous laquelle il
y a quelque chose à faire — comme le fanion porte la faute. Elle se pose
**au-dessus des dalles d'occlusion** : un état muré est celui qui en a le plus
besoin. C'est une **marque**, pas un glyphe de pièce : plus petite que les signes
de rang, en surimpression, et jamais dans le sceau. Elle porte en `title` la
mission en clair — le plateau reste muet à l'œil, il ne l'est pas pour qui
écoute. Elle **remonte l'arbre** comme l'épreuve du guide, et sans qu'on ait rien
à écrire pour ça : `missions` est déjà la chaîne descendante entière, les états
coiffés compris. Mesuré : **49 lampes pour 49 actes**, sur les douze plateaux, états murés
compris.

**Une par ACTE, et sur la seule pièce qu'il vise** — la clef à retenir, l'action
dont il faut désigner le teneur, le verrou contre quoi écrire une clef, l'état à
mettre à l'épreuve. Marquer toute pièce dont la chaîne descendante porte une
mission couvrait le plateau de lampes qui disaient la même chose : un même acte
en allumait trois, sur l'état cible, sur son verrou et sur l'action qui l'avait
fait voir. C'est la déduplication par l'acte, déjà faite pour les missions,
appliquée au marquage — **90 pièces marquées, puis 49, soit exactement le nombre
d'actes**. Les pièces d'amont continuent de dire la mission dans leur bulle, ce
qui est sa place. Et la pièce visée porte l'acte dans sa bulle même s'il est
attaché plus haut dans la chaîne : une lampe sans phrase serait une énigme.

**Elle ne remplace pas le fanion**, et c'est la mesure qui l'a tranché. On
pouvait le croire — la conclusion et les missions coïncident parfaitement, et un
plateau qui dit *voilà ce qu'il y a à faire* vaut mieux qu'un plateau qui dit
*il y a un problème*. Mais **fanion et lampe ne recouvrent pas le même
ensemble** :

| | pièces |
| --- | --- |
| fanion **et** lampe | 33 (30 actions dont aucun office ne répond, 3 états) |
| fanion **sans** lampe | **53** — un moyen ou un office cité dans une action et absent de son registre : le catalogue n'a pas d'acte pour eux |
| lampe **sans** fanion | **57** — un état, un verrou, une clef dont la chaîne descend jusqu'à une décision qu'on n'a pas prise. Ce n'est pas une faute : c'est une attente |

Les deux signes disent donc deux choses différentes, et l'on garde les deux. Ce
qui coïncide, et qui reste vérifié à chaque passage, c'est **la conclusion et les
missions** : aucune pièce ne conclut « la chaîne tient » en portant une mission,
aucune pièce à conclusion rompue n'en manque.

### La bulle se lit, et elle se retient

**Elle est le seul texte du dispositif** — le plateau est muet par construction —
et elle est écrite en conséquence : **380 px** de large (~48 signes par ligne
pour la description), cinq niveaux de taille et de graisse au lieu d'une seule,
et des blancs entre les blocs plutôt que des filets partout.

| | |
| --- | --- |
| l'amont, à mi-voix | 11 px |
| le nom de la pièce | **19 px, 600** — un titre, son signe devant, sur la ligne de base |
| la description | 14,5 px / 1,6 — la taille de lecture |
| la conclusion et les missions | 14 px, 500 — les deux phrases pour lesquelles la bulle existe |
| les maillons | 12 px / 1,35 — de la vérification, pas de la lecture |

**Les signes tiennent devant leur nom.** La bulle était bâtie en `flex`, et un
conteneur flex blockifie ses enfants : l'emoji tombait sur sa propre ligne dès
qu'on relevait le texte, et la bulle se lisait en escalier. Elle est désormais en
mise en page **inline**, sauf le portrait d'un teneur, calé par `vertical-align`.

**Le clic sur un jeton RETIENT la bulle** : elle ne suit plus le survol, la
chaîne reste allumée, et l'on peut lire, promener le curseur, relire. Le jeton
d'origine porte un anneau, la bulle un filet épais et la mention de sa sortie.
On lâche par un second clic sur le même jeton, par un clic à vide, ou par Échap
— les trois passent par le même geste, pour qu'ils fassent la même chose.
**Retenir n'enlève rien** : la bulle retenue AJOUTE le détail (numéro, preuve,
levé quand, coût, avancement, brèches, fautes) à ce que le survol montrait déjà.

Le clic ouvrait le volume de l'affaire ; **ce chemin ne se perd pas**, il devient
un renvoi qu'on VOIT, au pied de la bulle retenue, sous l'emblème de l'affaire.
C'est mieux que ce qu'il remplace : on découvrait l'ancien par hasard, en
cliquant sur un jeton pour une tout autre raison.

**Elle ne couvre toujours pas le damier**, et si la place manque elle **maigrit
avant de renoncer** : la plus large des deux gouttières, tant qu'elle y tient
lisiblement (300 px au moins) ; en deçà seulement, elle retombe près du jeton.
Vérifié sur les 54 pièces du plus gros plateau, survolées puis retenues : zéro
recouvrement, zéro débordement de fenêtre, et le pire cas (24 maillons, 558 px)
défile au lieu de déborder.

### Se voir, se cliquer, se lire — la passe de lisibilité

Le dispositif avait été construit en évitant le bruit, et il était passé de
l'autre côté : on se penchait pour lire ce qui devait sauter aux yeux. Trois
mesures, et le reste en découle.

**La zone de frappe occupe sa part de case.** C'était le défaut le plus grave, et
il ne se voyait pas : le bouton d'un jeton hugeait son sceau — **25 × 25 px dans
une case de 68**, un sixième de la surface, à viser au pixel. Le bouton s'étend
désormais jusqu'aux bords de sa part : une case à un jeton se clique tout
entière (**64 × 64, 88 % de la case**), à deux chacun sa moitié, à quatre chacun
son quart. Le sceau dessiné, lui, n'a pas bougé — c'est un rembourrage
transparent qui a grandi. Vérifié : **zéro chevauchement**, curseur en main sur
toute la zone, et un `elementFromPoint` sur une grille de 5 × 5 points par case
tombe dans le bon jeton **598 fois sur 600**. L'amorce du survol passe de 90 à
**120 ms** en conséquence — une zone de frappe plus large est aussi une zone de
survol plus large.

**Ce qui porte du sens monte d'un cran.** Les signes des sceaux de 19 à 24 px
(0,21 → 0,27 de la case), ceux de la gouttière de 13 à 16 px et de 60 à 85 %
d'opacité, l'emblème d'affaire de 26 à 31 px, la lampe de 10 à 14 px, le fanion
de 7 à 9 px.

**Les marches sont la charpente du plan**, et c'étaient des cheveux : 1,2 px à
moitié transparents. Elles passent à **2,4 px à 85 %** (3,4 px quand la chaîne
est allumée), et leurs trois états se distinguent maintenant par le TRAIT —
plein, pointillé fin, tirets longs — et non par une nuance d'opacité que
personne ne percevait. Les branches de la canopée de 1 à 2 px et de 30 à 62 %
d'encre, les réglettes de colonne de 4 à 6 px et de 60 à 88 %.

**Les valeurs s'écartent.** Fond de sceau 14 → 24 % de sa teinte, liseré 62 →
92 % et 1,5 → 2 px ; un état ouvert 2,5 → 3 px ; les gris de service de la bulle
passent de `--muted` nu à un mélange à l'encre — **contraste 4,52 → 7,52**, quand
la norme AA demande 4,5. L'estompage de chaîne descend au contraire de 13 à 10 %
pour que l'allumage reste franc maintenant que tout le reste a monté.

**La hiérarchie de la bulle se creuse au lieu de monter en bloc** : le titre 19 →
21 px, la conclusion et la mission 14 → 15,5 px et 500 → 600 de graisse, les
maillons **descendent** à 11,6 px. Ce sont les deux phrases pour lesquelles la
bulle existe qui gagnent le plus, et la liste de vérification qui recule.
Mesures en thème clair, sur le fond de la bulle : titre 13,6 · description 13,6 ·
mission 13,6 · conclusion 7,6 · détail et maillons 7,5. Le thème sombre donne le
même ordre, tout au-dessus de 4,5.

**Trois signaux coexistent sur un jeton, et ils ne se confondent pas** — c'est ce
qui a demandé de les poser en dernier dans la feuille, ancrés au damier : le
cadre d'un état muré, écrit plus bas, les mangeait à égalité de poids, si bien
qu'on cliquait un état muré et que rien ne changeait à l'écran.

| signal | traitement |
| --- | --- |
| **prochain pas** | halo BRAISE diffus tout autour, en pulsation lente de 2,8 s, coupée par `prefers-reduced-motion` — et coupée aussi hors de la chaîne allumée, pour qu'un pas éteint reste repérable sans être criard |
| **survol** | cadre intérieur à pleine encre du rang, 2,5 px, sans halo |
| **retenu** | anneau ACCENT net de 3 px, collé au sceau, sans flou |

### Le verdict d'une pièce parle d'abord d'elle-même

Une clef `à étudier` concluait « la chaîne tient » dès qu'une action portée
pendait dessous — sur la pièce même que tout le monde attend, et sur laquelle la
mission se pose. **L'empêchement d'une clef n'est pas sous elle, il est en
elle** : son état propre passe donc avant ce qu'elle porte. Douze clefs du plan
ont changé de verdict (« elle n'est pas tranchée : rien ne partira tant qu'on ne
l'aura pas retenue »), et une clef écartée dit de même que ce qui pend dessous ne
sert plus. Dans la foulée, une pièce porte dans sa bulle **l'acte qui la vise**,
et pas seulement ceux de sa chaîne : elle arborait sa lampe au coin du sceau sans
dire un mot de la mission. Et la ligne « en attente — retenue », qui contredisait
le « à étudier » écrit deux lignes plus haut, dit maintenant ce qui manque en
toutes lettres : « il faut la retenir ou l'écarter ».

### Les colonnes se trouvent par leur nom

Le registre des moyens a reçu deux colonnes le jour où `nos-moyens` y a été
fusionné (« Ce qu'il vaut », « Ce qu'il peut produire », 30 lignes, M01 à M30).
Lues au RANG, elles décalaient tout : la bulle disait « tenu par *Tout ce qui
flotte dans la baie* » et « à *Corlys Velaryon* ». La route lit désormais les
colonnes **par leur en-tête**, avec le rang d'avant pour seul recours. Un
registre qu'on tient à la main gagne des colonnes — c'est sa vie ; une vue qui
les compte est une vue qui mentira un jour sans prévenir.

## Un parti pris

Les régions sont rendues au même parchemin que la terre, séparées par un trait
d'encre pâle : la carte reste **cartographique** par défaut, pas politique. Un
territoire ne se teinte que si le MJ le décide, région par région, par une entrée
dans `zones` — le jour où une contrée entière a basculé et où le joueur le sait.
Colorer tout le royaume par allégeance affichée serait une carte de jeu de
stratégie : ce n'est pas ce qu'on regarde ici.
