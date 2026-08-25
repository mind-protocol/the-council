# Les écarts — ce que le code tient, ce que le dossier prescrit

Le [README](README.md) dit que ce dossier est « l'autorité pour les effectifs,
les noms et les humeurs », et que `ecrans/modules/bataille2d.js` « cite ce
dossier comme autorité ». [`ancrages.md`](ancrages.md) va plus loin : *« l'ordre
de bataille est à deux endroits […] les deux doivent s'accorder »*.

**Ils ne s'accordent pas.** Ce qui suit est la confrontation ligne à ligne, du
plus grave au plus anodin. Chaque écart est soit un bug du moteur, soit une
doctrine périmée du dossier — la colonne « verdict » tranche.

> **Ce n'est pas de la dérive récente.** `git log 745c8eb..HEAD` sur le module
> ne touche aucune de ces données : les six commits depuis la dernière écriture
> du dossier n'ont pas déplacé un effectif ni un nom. Les écarts ci-dessous sont
> d'origine — le dossier ne s'est jamais accordé au code sur ces points-là.

---

## Ce qui S'ACCORDE, et qu'il faut dire d'abord

Tout ce que le dossier appelle « les effectifs et les humeurs » est **juste**.
Les cinq corps, leurs chiffres, leurs portes, leurs trois comportements, le
total de la garnison, l'escorte du roi, son recul : rien à redresser.

| | Dossier | Code (`l. 983-1009`) |
|---|---|---|
| cole | 500, la Gadoue, — | 500, porte par défaut, `humeur: null` ✅ |
| vantre | 350, la porte de Fer, — | 350, `"La porte de Fer"`, `null` ✅ |
| cranche | 250, la porte du Roi, `ferme` | 250, `"La porte du Roi"`, `"ferme"` ✅ |
| gueux (Rous Cantel) | 400, la Vieille Porte, `sourd` | 400, `"La Vieille Porte"`, `"sourd"` ✅ |
| bleusailles (Petit Wend) | 200, la Gadoue, `versatile` | 200, défaut, `"versatile"` ✅ |
| garnison | 200 + 100×3 + 300 = 800 | `garnison(200/100)` l. 1737, `garnison(300)` l. 1774 ✅ |
| escorte du roi | 40 | `ROI_ESCORTE = 40` l. 535 ✅ |
| recul du roi | « trois cents pas en arrière du fer » | `ROI_RECUL = 230` m ÷ 0,75 = 307 pas ✅ |
| Cole au premier rang | « il est au PREMIER rang » | `rangTete: 0` ✅ |
| porte du four | « repassée à `false` » | `PORTE_OUVERTE_ESSAI = false` l. 318 ✅ |

Les écarts ne portent donc **pas** sur ce que le dossier revendique tenir. Ils
portent sur les **trois étages de noms en dessous** — les meneurs, l'arbitrage,
les habitants — et sur une doctrine que le code a changée sans le dire.

---

## 1. Mag la Gaffe n'est pas dans la bataille

**Verdict : bug du moteur.** C'est le seul écart qui coûte l'argument central
du dossier.

[`narratif.md`](narratif.md) donne **huit** habitants avec une adresse. Le
premier de sa table, en gras, est *« **Mag la Gaffe**, tenancière — sous l'arche
de la porte de la Gadoue — elle est à l'intérieur du premier contact. Elle ne
peut pas ne pas voir. *(déjà dans l'état)* »*.

[`ancrages.md`](ancrages.md) en fait la mesure qui vaut le dossier entier :
**47 m, 62 pas de la porte qu'on enfonce**, et *« les deux premières lignes sont
le cadeau de la géométrie ».* Le [README](README.md) en fait la troisième et
*« vraie »* raison d'avoir choisi cet exercice : *« il y a un siège dedans ».*

**`bataille2d.js` ne contient ni « Gaffe », ni « Mag », ni « Marlo », ni
« Vasse », ni « Bourbe ».** Zéro occurrence. Des quatre personnes que le README
place sur le pas de leur porte, une seule existe dans le sac : Waltyr Poix.

Le code a bien huit `fig("ville", …)` (l. 1832-1847), mais la huitième est
**« la Veuve », receleuse rue des Sœurs** (l. 1846) — un nom qui n'apparaît dans
aucun fichier du dossier. Elle occupe la place de Mag la Gaffe.

> `ancrages.md` coche pourtant *« 5 — Les huit habitants en positions fixes ✅
> ils sortent aux annales, nommés et situés »*. Ils sortent, ils sont huit, et
> ce ne sont pas les mêmes huit.

---

## 2. L'arbitrage n'existe pas — c'est-à-dire le sujet

**Verdict : bug du moteur**, ou plus exactement : une doctrine écrite et jamais
posée.

Le [README](README.md) dit le sujet en une phrase : *« ce n'est pas “personne ne
commande”. C'est “tout est commandé, tout est écrit, et le compte est faux.” »*
[`chaines.md`](chaines.md) en fait la troisième chaîne, *« le neuf »*, et
tranche : *« c'est le défaut le plus grave des trois et c'est le seul qui
survive à la nuit. Les deux autres coûtent des hommes ; celui-là coûte l'année
suivante. »*

Ce qu'il faudrait pour ça : dix-neuf clercs, des tablettes de cire, un homme
mort quand un clerc le dit.

| Cherché dans `bataille2d.js` | Occurrences |
|---|---|
| `clerc` | 2 — toutes deux dans des listes de métiers de la couche de peur |
| `arbitre` | 1 — au sens figuré (« l'arbitre qui tient ses jambes ») |
| `craie` | 0 |
| `tablette` | 0 |

**Rien n'est déclaré mort dans ce module ; on y meurt.** Trois conséquences en
cascade, toutes écrites dans le dossier et aucune produite :

- **Waltyr Poix** ([bleus.md](bleus.md)) : *« déclaré mort dans les quarante
  premières secondes […] il ne meurt pas : il est mis de côté, vivant, et
  regarde prendre son poste pendant une heure. […] C'est une bouche à faire
  parler, et elle est dans la partie dès le lendemain. »* Le code le **nomme**
  (l. 1753) et rien d'autre. Sans mise à l'écart, il se bat et il meurt — la
  bouche du lendemain n'existe pas.
- **Cranche** ([rouges.md](rouges.md)) : *« il refuse de retirer ses hommes
  déclarés morts […] la seule partie du compte d'Orwyle qui soit fausse par
  vertu. »* Pas d'arbitrage, pas de retrait, pas de refus. La phrase survit dans
  le champ `dit` du corps (l. 994) et nulle part ailleurs.
- **Orwyle** ([autorite.md](autorite.md)) : *« c'est lui qui tient les
  arbitres. »* C'est le seul des six de l'autorité dont le dossier dise qu'il
  produit quelque chose dans le sac — et il n'y est pas.

---

## 3. Les vingt-quatre meneurs : douze écrits, zéro posés

**Verdict : les deux.** Doctrine périmée dans le dossier, dette dans le code.

Le [README](README.md) pose quatre étages de lisibilité et en fait *« la règle
qui commande tout le dossier »* :

| Étage | README | Réellement |
|---|---|---|
| l'autorité | 6 nommés | **2** dans le sac (Aegon, Cole) |
| les commandants | 5 rouges + 4 bleus | **5 rouges**, 0 bleus commandant des hommes |
| les meneurs | **24 nommés** | **0** |
| le reste | ~2 400 | ✅ |

Et le dossier ne tient pas son propre compte : [`rouges.md`](rouges.md) titre
« Les douze meneurs rouges » puis en nomme **six** ; [`bleus.md`](bleus.md)
titre « Les douze meneurs bleus » et en nomme **six**. Douze noms écrits,
vingt-quatre annoncés.

Dans le code, les capitaines d'aile sont **anonymes** : `h.capitaine = true`
(l. 1714) sans nom, sur *« le premier homme de l'aile qui n'est pas déjà chef
d'escouade »*. Les seuls porteurs de nom du sac entier sont les cinq têtes de
corps, le roi, et Waltyr Poix — **sept**. C'est cohérent avec le `chef-tombe ×3`
que rapporte [`ancrages.md`](ancrages.md), et ça veut dire que l'étage 3 de la
règle des noms, celui qui devait rendre les morts lisibles, n'a jamais été bâti.

---

## 4. Ser Luthor Largent n'existe pas

**Verdict : bug du moteur.** Zéro occurrence de « Largent » dans
`bataille2d.js`.

[`bleus.md`](bleus.md) en fait le Commandant du Guet, chef de l'ensemble des
huit cents, *« sept pieds de haut, la créature d'Otto »*, avec sa peur écrite
(*« il craint de demander des renforts »*) et son rôle dans le sac (*« il tient
l'anneau du Donjon et il ne le resserre jamais à temps »*). Le README le range
même parmi **ce qui est canon et ne doit pas bouger**.

Le dossier se contredit d'ailleurs à côté : bleus.md donne l'anneau à Largent
dans sa fiche, et à **Coutre** dans la fiche de Coutre (*« c'est lui qui décide
si l'anneau des trois cents se resserre »*). Le code a tranché pour Coutre
(`DELIBERE_TENIR`, l. 565) sans que personne l'écrive.

**Conséquence de deuxième ordre** : les quatre cents hommes des trois portes à
cent et de l'anneau n'ont **aucun chef attaché** dans le code. Gaunt et Coutre y
sont des `fig("garde", …)` — des noms peints sur le plan à côté du Donjon
(l. 1822-1828), pas des commandants de troupe. La chaîne de commandement bleue
prescrite par le dossier (Largent → Coutre / Poix / Gaunt) n'est bâtie que sur
un maillon : Poix, et sans grade.

---

## 5. La porte de la Gadoue est à 10 % — et le dossier l'ignore

**Verdict : doctrine périmée du dossier.** Le code a raison, le dossier n'a pas
suivi.

`bataille2d.js` l. 297 :

```js
const USURE = { "La porte de la Gadoue": 0.10 };
```

Neuf cents points au lieu de neuf mille. Le commentaire du module en tire lui-
même la portée : *« deux minutes de sept haches deviennent DOUZE SECONDES. Ce
n'est pas un détail d'ambiance : c'est l'exercice entier qui se déplace, parce
que la première porte tombe avant que quiconque ait eu le temps d'y penser. »*
Le module émet même un fait pour ça, `porte-abimee` (l. 1567).

**Aucun fichier de `docs/bataille/` ne contient le mot « usure », ni le fait
`porte-abimee`.** L'horloge de [`chaines.md`](chaines.md) — contact à 0h08,
porte qui cède à 0h38 — décrit une porte à neuf mille points ; le relevé de
faits de [`ancrages.md`](ancrages.md) (402 faits, 14 août) ne liste pas
`porte-abimee`, donc il a été pris avant.

La justification narrative de l'usure est pourtant belle et elle est **dans le
code** : la Gadoue est la porte du port, elle travaille tous les jours,
*« personne ne l'a referrée depuis des années, et c'est écrit dans les demandes
de réfection que le sergent Waltyr Poix envoie au Donjon et que personne ne
lit »* — ce qui raccorde exactement aux trois demandes de renfort de bleus.md.
C'est du dossier qui vit dans le moteur.

---

## 6. `humeur` est un label mort ; la vraie donnée est ailleurs

**Verdict : dette du code**, invisible pour le dossier — mais elle décide de
l'extraction.

Le dossier dit « les humeurs » et coche *« 2 — Trois comportements : ferme,
sourd, versatile ✅ »*. C'est vrai à l'écran. Ce n'est plus vrai dans le champ
`humeur`.

`humeur` est écrit sur chaque escouade (l. 1637), chaque homme (l. 1657) et
chaque tête (l. 1679) — soit sur ~2 500 objets. Il n'est **relu nulle part**,
sauf pour émettre la ligne d'ouverture `corps-ferme` / `corps-sourd` /
`corps-versatile` (l. 1695-1699). Le module le dit lui-même en trois endroits :
*« champ dissous dans la couche 1 et absent des hommes depuis »* (l. 6545),
*« les trois planchers d'`humeur` sont déposés »* (l. 574).

Le comportement réel vient de **`ECOLE_CORPS`** (l. 1302-1308) :

```js
cranche:     { dressage:  0.70, vecu:  0.60, sourd: 0    },  // « ferme »
gueux:       { dressage: -0.30, vecu: -0.20, sourd: 0.85 },  // « sourd »
bleusailles: { dressage: -0.60, vecu: -0.70, sourd: 0    },  // « versatile »
cole:        { dressage:  0.30, vecu:  0.20, sourd: 0    },
vantre:      { dressage:  0.10, vecu:  0.00, sourd: 0    },
```

…et de **`BRULE`** (l. 6550) : `{ gueux: 0.75, cranche: 0, bleusailles: 0.10 }`.

**Ces deux tableaux sont de l'ordre de bataille**, au même titre que les
effectifs : ils disent ce qu'un corps vaut. Ils vivent à **320 et 5 570 lignes**
de `CORPS`, et le dossier ne les mentionne pas. Une extraction qui emporterait
`CORPS` en laissant `ECOLE_CORPS` et `BRULE` sur place produirait un fichier de
données qui **ne décide plus de rien** — le piège principal de ce chantier.

---

## 7. Les outils de Vantre ne servent à rien

**Verdict : bug du moteur.** [`rouges.md`](rouges.md) : *« son corps est le seul
qui ait des outils — masses, coins, cordages, pris au chantier. **Contre le
verrou, ses hommes valent double.** »*

`const HACHE = 11` (l. 319) est plat : onze points de porte par homme au contact
et par seconde, pour tout le monde. Aucune lecture du corps dans la machine du
verrou. Les outils n'existent que dans la phrase `dit` du corps (l. 990).

C'est un écart bon marché à combler et il change une horloge : Vantre est le
corps qui *« arrive en flanc, donc en retard »*, et son intérêt entier est
d'arriver tard mais de valoir double.

---

## 8. La consigne de Petit Wend dit 265 pas, pas 200

**Verdict : bug du moteur, à une ligne.**

`bataille2d.js` l. 1007, avec son commentaire l. 1006 :

```js
// Celle-ci dit littéralement « gardez-vous à deux cents pas de Cole ».
consigne: { verbe: "suivre", objet: { corps: "cole" }, marge: 200, … }
```

Mais `marge` se consomme **en mètres** (l. 3524 : `c[0] + nx * marge`) et se
rend **en pas** (l. 3529 et 4331 : `enPas(marge)`, avec `PAS_M = 0.75`,
l. 748). `enPas(200)` vaut **265**. La consigne d'avant-nuit place donc les
bleusailles à 265 pas de Cole et l'écrit ainsi dans les annales, là où le
dossier et le commentaire de la ligne au-dessus disent deux cents.

Pour dire deux cents pas, il faut écrire `marge: 150`.

*(Même unité pour les deux marges de la doctrine d'ailes, l. 4217 et 4238 :
`marge: 60` se dit « à 80 pas », `marge: 90` se dit « à 120 pas ». Le
commentaire l. 4234 dit d'ailleurs « cent vingt pas » — celui-là est juste.)*

---

## 9. La checklist de `ancrages.md` est en retard d'un cran

**Verdict : doctrine périmée.** [`ancrages.md`](ancrages.md), *« ce que ça
demande au four »* :

| | Dit | Réellement |
|---|---|---|
| 4b | **Gaunt qui ouvre** — une fin qui ne passe pas par le verrou | ⬜ | **✅ fait** — `DELIBERE_OUVRIR` (l. 566), `anneauOuvert` (l. 1115), et toute la branche l. 4009-4065, y compris *« celle qu'on ouvre est celle où ils sont »* |
| 7 | **`ville-avertie`** | ⬜ | ⬜ confirmé — zéro occurrence |

Le nœud n° 7 est bien le seul qui manque, mais ce n'est plus « le seul » : 4b
est passé sans que la case soit cochée.

---

## 10. Les petits comptes qui ne tombent pas juste

**Verdict : anodin, mais ce sont des chiffres écrits en toutes lettres.**

- **`bataille2d.js` l. 939** : *« la garnison est passée à sept cent quatre —
  deux cents à la Gadoue, cent à chacune des trois autres, trois cents à
  l'anneau ».* 200 + 300 + 300 = **800**, pas 704. La décomposition est juste,
  le total est faux. *(804 avec les quatre messagers de porte, l. 1758-1768 —
  jamais 704.)*
- **`ancrages.md`** : *« les 2 546 corps sont le compte juste : 1 700 rouges +
  800 bleus + les quarante de la Garde Royale ».* 1 700 + 800 + 40 = **2 540**.
  Les six manquants sont les cinq têtes de corps et le roi, qui ne sont dans
  aucun effectif — ce qui est vrai, intéressant, et non écrit.
- **`bataille2d.js` l. 975 et 1013** : *« les six corps »*, deux fois, pour un
  `CORPS` qui en contient **cinq**. `ancrages.md` a raison (*« cinq au lieu de
  six »*) ; le commentaire est resté. Même chose l. 1491 (*« l'humeur des six
  corps »*).
- **`bataille2d.js` l. 1675** : *« elle se tient au rang que son caractère lui
  donne : **Cole au troisième**, dans sa propre masse ».* `rangTete: 0` — Cole
  est au premier, et [rouges.md](rouges.md) insiste que c'est *« tout le
  personnage »*. Le commentaire décrit la version d'avant.
- **`README.md`** annonce la garnison comme *« câblée à part dans
  `bataille2d.js` »* : c'est exact, et c'est précisément ce que ce chantier
  propose de défaire.

---

# La frontière donnée / mécanique

La section « L'ORDRE DE BATAILLE » va de la **l. 920** au séparateur suivant,
**l. 3963** — **3 044 lignes**. Le titre trompe : elle contient l'ordre de
bataille *et* toute la machine du soldat.

## Ce qui est une DONNÉE — extractible

| Bornes | Quoi | Lignes |
|---|---|---|
| **983-1009** | `CORPS` — les cinq corps : nom, effectif, porte, humeur, forme, recul, côté, rang de tête, `dit`, la consigne de Petit Wend | 27 |
| **1302-1309** | `ECOLE_CORPS` + `ECOLE_GARDE` — ce qu'un corps vaut réellement (voir écart n° 6) | 8 |
| **1822-1847** | les douze `fig()` — quatre figures du Donjon, huit habitants : nom, rôle, place, phrase | 26 |
| **255-259** | `SACS` — la distribution d'armes par camp | 5 |
| **534-539** | `ROI_RECUL`, `ROI_ESCORTE`, `ROI_PRESSE`, `ROI_VERSE` | 4 |
| **565-566** | `DELIBERE_TENIR`, `DELIBERE_OUVRIR` — les deux horloges du Donjon | 2 |
| **282**, **297**, **318-319** | `VERROU_PV`, `USURE`, `PORTE_OUVERTE_ESSAI`, `HACHE` | 4 |
| **6550** | `BRULE` — par corps (voir écart n° 6) | 1 |
| | **littéral extractible** | **~77** |

Plus les commentaires qui **justifient ces chiffres** et qui doivent partir avec
eux, parce qu'ils sont du dossier tombé dans le code : `266-296` (pourquoi neuf
mille points, pourquoi l'usure), `971-982` (la forme est l'argument),
`1002-1006` (la consigne d'avant-nuit), `1299-1301`, `1786-1791` (pourquoi des
figures), `6532-6549` (pourquoi on brûle). **~85 lignes de plus.**

> **L'extraction retirerait donc de l'ordre de 160 lignes sur 3 044 — 5 % de la
> section, 2,3 % du fichier** — et il faudrait en rendre une quinzaine au
> chargeur. **Gain net : ~145 lignes.** C'est le vrai chiffre, et il corrige la
> prémisse : cette section n'est pas « des données recopiées à la main », c'est
> de la mécanique avec 5 % de données dedans. L'extraction vaut pour **la source
> unique**, pas pour le dégraissage.

## Ce qui est une MÉCANIQUE — à ne pas toucher

| Bornes | Quoi | Pourquoi ça reste |
|---|---|---|
| 960-974 | `ECHELLE`, `combien()`, `garnison()` | deux fonctions et un plancher ; la règle « toute masse se divise, la géométrie jamais » est du code |
| 1024-1040 | `verrous`, `porteDuCorps`, `ailesDe`, `axeDe` | la structure de commandement se calcule sur l'effectif plein |
| **1042-1084** | `poserCorps()` | **le piège principal** : les quatre formes (`nuee`, `paquets`, colonne, ligne) sont de la géométrie qui LIT les données. Le `forme:` du corps part, la fonction reste |
| 1086-1116 | `figures`, `roi`, `arret`, `messagers`, `conseil`, `anneauOuvert` | des variables d'état, pas des valeurs |
| 1117-1330 | la trempe, l'œil, le souffle, le fond, le cercle social | 213 lignes de physique de l'homme — aucune donnée d'ordre de bataille, sauf `ECOLE_CORPS` incrusté au milieu |
| **1464-1884** | `dresser()` | **la zone mixte, et la seule vraiment délicate.** 420 lignes de mise en place où la donnée est *incrustée dans les expressions* : `garnison(premiere ? 200 : 100)` l. 1737, le nom de Poix en ternaire l. 1753-1754, `garnison(300)` l. 1774, `fig("ville", dans(20, 12), …)` l. 1832+. Extraire ces valeurs demande d'ouvrir les expressions, pas de couper des lignes |
| 1886-2017 | le voisinage, le chemin | grille et A\* |
| 2018-2660 | la machine du soldat, la chasse, le seuil d'entame, le collage, le recul, l'adresse | 640 lignes de comportement |
| 3520-3530 | la consommation de `marge` | c'est ici que se voit l'écart n° 8 |
| 3766-3963 | qui a le droit de cogner, la machine du verrou | le front, les sept haches, la cession |

**La règle de coupe, en une phrase :** *ce qui a une unité (des hommes, des
mètres, une probabilité, un nom) sort ; ce qui a une boucle reste.* Les deux
seuls endroits où elle est difficile à tenir sont `poserCorps()` — qui ressemble
à de la donnée et n'en est pas — et `dresser()`, où la donnée est en ternaires
au milieu de boucles.

## Ce qui doit sortir AVEC, et qui n'est pas dans la section

Trois valeurs d'ordre de bataille vivent loin du bloc et seraient oubliées :

- `ECOLE_CORPS` / `ECOLE_GARDE`, **l. 1302-1309** — 320 lignes plus bas ;
- `BRULE`, **l. 6550** — 5 570 lignes plus bas ;
- `USURE`, **l. 297** — 690 lignes plus haut, et c'est celle qui déplace le plus
  la nuit.

Un fichier de données qui ne les emporte pas serait un fichier décoratif.

---

## Le fichier candidat

[`ordre-de-bataille.json`](ordre-de-bataille.json) — les valeurs **du code**
(pour qu'un branchement ne change aucune cuisson), avec une clef `ecart` partout
où le dossier prescrit autre chose. Il n'est branché par personne.
