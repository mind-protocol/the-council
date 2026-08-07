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

## Un parti pris

Les régions sont rendues au même parchemin que la terre, séparées par un trait
d'encre pâle : la carte reste **cartographique** par défaut, pas politique. Un
territoire ne se teinte que si le MJ le décide, région par région, par une entrée
dans `zones` — le jour où une contrée entière a basculé et où le joueur le sait.
Colorer tout le royaume par allégeance affichée serait une carte de jeu de
stratégie : ce n'est pas ce qu'on regarde ici.
