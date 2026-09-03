# Se relire — le format d'un monde sauvé

Doctrine : [`../../docs/etat-sauvegardes.md`](../../docs/etat-sauvegardes.md).
Ici, le champ par champ, mesuré sur le code.

## État : le moteur se relit

**C'était faux au moment d'écrire ce document** — il n'existait aucune porte de
sortie ni d'entrée, chaque container tenant son état dans des `Map` fermées
dans sa fabrique. Les portes sont posées depuis : `etat()` / `restaurer()` sur
🌍 `monde`, ❤️ `corps`, 🧠 `cognition`, et sur chaque pièce qui tient de la
matière (registre, chaleur, blessures, souffle, équipement, carquois,
représentation, couverture, la machine à états et les quatre brains).

`src/partie.js` porte `sauver()` / `charger()` — une seule définition, partagée
par l'écran (`src/main.js`, exposé en `window.partie`) et par les bancs
headless de `coding/`.

**Mesure du tour complet** (banc, après 30 s de divergence réelle) : positions
et têtes reviennent identiques à l'instantané, au caractère près. Un banc qui
mesurerait sur un monde figé sort en code 1 — une sauvegarde qui « marche »
sur un monde immobile ne prouve rien.

Ce qui suit reste la liste exacte de ce qui sort et rentre.

## Le corps — `corps.jsonl`, une ligne par homme nommé

Du registre (`monde/registre.js`), tout est déjà de la donnée plate :

`id`, `pos {x,y}`, `vel {x,y}`, `cap`, `posture`, `rayon`, `masse`, `gabarit`,
`livree`, `nom`, `panache`, et `vol {z, vz, vitesseAir, banque, pente,
phaseAile}` quand il y en a un.

De ❤️ (`corps/expose.js`), quatre chiffres et trois booléens :

| | |
|---|---|
| `coups` | les blessures encaissées (`blessures.coups`) |
| `souffle` | `{reserve, effortTick}` |
| `equipement` | `{arme, bouclier, arc}` |
| `fleches` | ce qui reste au carquois |
| `dragon` | l'entrée de `dragons` s'il en est un |

**`id` doit être stable à la relecture.** Le registre distribue un `prochainId`
croissant jamais réutilisé : il se sauve avec le monde, sinon un homme
ressuscité prend l'identité d'un mort et toutes les croyances qui le nomment
désignent quelqu'un d'autre.

## La tête — `tetes.jsonl`

C'est là qu'est le travail. De `cognition/representation.js` :

**La semence** — déjà acceptée par `attacher()` : `monId`, `chefId`, `maLivree`,
`suivis`, `amis`, `unite`, `nomsParId`.

**L'acquis** — ce qu'aucune porte ne reprend aujourd'hui :

| | |
|---|---|
| `individus` | id → `{pos, cap, ageS}` — où je crois que sont les gens |
| `tas` | étiquette → `{barycentre, etendue, effectif, poids, direction, ageS}` |
| `peur`, `picPeur`, `tauPeurS` | le moral, qui est une croyance |
| `mortsMiens`, `mortsAmisVus`, `mortsUniteVus`, `mortsConnus` | ce que j'ai vu tomber |
| `ordreRecu` | `{ordre, emetteur, ageS}` — le dernier ordre entendu |
| `posteVoulu` | où j'ai décidé de me tenir |
| `couverture` | l'état de `creerCouverture` — où j'ai regardé |

**Et le piège, qui coûterait cher : la feuille de la machine à états.**
`brains/machine.js` tient `feuille` — l'état courant du soldat. Sans elle, un
homme rechargé en pleine charge repart à l'état initial, c'est-à-dire à
*flâner*. **C'est le seul champ dont l'oubli est invisible au chargement et
catastrophique à la seconde d'après.** Le `journal`, `tempsParEtat` et
`bascules` de la même machine, eux, sont de l'introspection : ils ne se sauvent
pas.

Les brains gardent chacun une bricole à verser au même endroit : `dernier` pour
le soldat, `accumSaillance` pour le commandant.

## Ce qui ne se sauve pas, et pourquoi

- **`contacts`** — les corps vus au contact, oubliés en 4 s. C'est du présent,
  pas de la mémoire. Il se reconstitue à la première perception.
- **`tempsRestant` / `tempsMasse`** — l'échelonnage des cadences de perception,
  tiré au sort pour que tout le monde ne perçoive pas à la même frame. Se
  retire au chargement : personne ne s'apercevra qu'il a regardé un
  quarantième de seconde plus tôt.
- **navgrid, index spatial, chemins, forces, bulles** — rebâtis en une frame.
- **le masque du terrain** — cuit et immuable : on garde son nom.

## La décimation — par le rôle

La carte du regard est le poste le plus lourd d'une sauvegarde, et elle ne sert
pas la même chose selon qui la porte. Le **commandant** RATISSE : sa carte
longue est son outil de travail, elle sort entière. L'homme du **rang** s'en
sert pour ne pas re-scruter l'angle qu'il vient de faire — cette mémoire-là se
refait toute seule en quelques secondes de regard, on n'en garde que les
**30 dernières secondes**. Ce qu'on perd est borné et se répare tout seul : un
homme rechargé re-balaye un angle, une fois.

La décision se prend dans `cognition.etat()`, sur le `role` que chaque brain
déclare dans son propre `etat()` — pas besoin d'`introspect()`, qui construit
des structures de debug, pour sauvegarder.

**Mesure** (`node coding/banc-sauvegarde.mjs`, 60 corps, assaut de rue) :

| temps sim | pleine | décimée | gain |
|---|---|---|---|
| 30 s | 183,6 Ko | 183,6 Ko | 0 % |
| 120 s | 217,5 Ko | 195,1 Ko | 10 % |
| 300 s | 297,8 Ko | 214,2 Ko | 28 % |
| 600 s | 329,9 Ko | 220,2 Ko | 33 % |

**Le gain n'est pas le point : c'est que la décimée se STABILISE.** La pleine
grimpe sans fin (1 323 → 3 790 cases, elle suit la péremption à 600 s) ; la
décimée plafonne autour de 1 300 cases et 220 Ko, quelle que soit la durée de
la bataille. Une partie de trois heures ne coûte pas plus qu'une de dix
minutes.

**Ce qui reste ouvert** : 3 759 octets par corps, soit ~14 Mo à 4 000 hommes.
La décimation a borné la croissance dans le TEMPS, pas le coût par tête. C'est
la ligne nommé / compté qui doit s'en charger, et le banc est là pour la
mesurer.

## Les deux gestes — la forme des portes

Un container, une porte — c'est déjà la doctrine du dépôt. Donc sur chaque
`expose.js` :

```js
etat()        // rend de la donnée plate, sérialisable, sans référence vivante
restaurer(d)  // reprend cette donnée — même forme, exactement
```

Trois règles pour que ça ne pourrisse pas :

1. **`etat()` ne rend jamais un objet interne**, seulement une copie. Un
   `Map.values()` livré tel quel fait écrire dans le monde par la sauvegarde.
2. **`restaurer()` est le seul chemin d'entrée**, et il remplace : jamais de
   fusion avec ce qui est déjà là. Charger, c'est composer un monde neuf — la
   décision est déjà actée pour les scénarios, elle vaut ici.
3. **Ce qui n'a pas de champ dans `etat()` n'existe pas au chargement.** Un
   champ ajouté au moteur et pas à la porte est un bug muet — c'est
   exactement la classe de `feuille`.

## L'ordre du chargement

Il n'est pas libre : 🌍 le monde et les corps d'abord (les têtes désignent des
`id`), puis ❤️ ce que les corps ont subi, puis 🧠 les têtes, et enfin 📯 les
unités qui nomment leurs chefs. Une tête restaurée avant son corps croit en
quelqu'un qui n'existe pas encore.
