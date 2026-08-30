# Structurer `serveur/serveur.js`

> **FAIT le 30e jour de la 8e lune (2026-08-30).** `serveur.js` fait **65 lignes** ; le reste vit dans `contexte.js`, `http.js`, `siege.js`, `dates.js`, `portraits.js`, `monde3d.js`, quatre modules de `domaine/` et vingt et un fichiers de `routes/`. Aucun fichier au-dessus de 400 lignes hors `monde3d.js` (954) et `domaine/echiquier.js` (1 302). Cinquante URL ont été comparées corps pour corps entre l'ancien serveur et le nouveau : aucune différence hors horodatages. **L'état actuel et les règles à tenir sont dans [`serveur/CLAUDE.md`](../serveur/CLAUDE.md)** ; ce document garde le raisonnement, qui vaut encore.
>
> Deux écarts assumés au plan ci-dessous, tous deux dits dans `serveur/CLAUDE.md` : la table de dispatch reste une **liste ordonnée** (une `Map` d'égalités exactes ne sait pas dire les routes par préfixe, et il y en a six) ; `serviceMonde` garde `res` et reste dans `monde3d.js`, hors de `domaine/`, parce que c'est un service de fichiers et non un moteur.
>
> **Trois fichiers de ce plan n'existent plus** (30 août 2026, sortie du moteur de bataille) : `croiser.js` — cité au §2 comme l'un des trois patrons de module CommonJS —, `domaine/recherche.js` et `routes/bataille.js`, ainsi que `routes/vue.js`. Le lot 6 s'est donc réduit à deux blocs, et `routes/` compte dix-neuf fichiers et non vingt et un. Le raisonnement du plan ne change pas ; ce qu'il nomme, si.
>
> **Ce que la comparaison n'a pas vu, et qu'il faut savoir avant le prochain lot.** `POST /marche` et `GET /chemin` avaient perdu leurs `require` au recâblage et rendaient une erreur de référence : aucune des cinquante URL comparées n'allait jusqu'à ce code — l'une n'était pas frappée du tout, l'autre l'était sans ses paramètres. Un `try/catch` de route déguise une référence absente en réponse d'erreur ordinaire. **Une comparaison ne prouve que les chemins qu'elle emprunte** ; c'est l'argument le plus net en faveur du lot 0, qu'on a sauté. Le lot 0 — le harnais des 57 routes — n'a pas été écrit : la preuve a été faite par comparaison des deux serveurs, ce qui ne laisse rien derrière soi. Deux tests durables existent en revanche, tous deux vérifiés par mutation : [`serveur/test_siege.js`](../serveur/test_siege.js) tient le tri par `pour` sur ses deux moitiés (lecture et écriture) et l'écart de front ; [`serveur/test_marche.js`](../serveur/test_marche.js) tient le moteur de la marche — itinéraire stable, minutes non perdues à l'arrondi, position écrite, sac déposé à l'arrivée seulement.

État au 27e jour de la 8e lune (2026-08-27), avant le chantier : **6 345 lignes, 342 Ko, un seul fichier**, dont **3 798 lignes dans un unique callback `createServer`** (L2534 → L6331). 57 routes y sont branchées par une chaîne de `if (url === "…")`, et la plus grosse — `/echiquier` — pèse **1 293 lignes à elle seule**, à l'intérieur du `if`.

Ce document dit **pourquoi ce n'était pas déjà fait**, puis **où couper, dans quel ordre, et comment prouver après chaque coupe qu'on n'a rien cassé**. Il ne demande aucune réécriture : c'est du déplacement de code, lot par lot, chaque lot livrable et vérifiable seul.

---

## 0. Pourquoi ce n'est pas déjà fait

La question mérite mieux qu'un haussement d'épaules, parce que la réponse commande le remède. Quatre causes, et aucune n'est l'oubli.

**a) Le geste le moins risqué est toujours d'ajouter une ligne.** Une route neuve dans la chaîne de `if`, c'est +30 lignes qui ne peuvent casser que ce qu'elles ajoutent. Extraire un module, c'est toucher un serveur qui tient une partie en cours. À chaque session le calcul local dit « ajoute » — et 57 fois de suite, le calcul local a gagné. Un monolithe n'est pas une décision, c'est une **somme d'optimisations locales correctes**.

**b) Rien ne prouve qu'un déplacement n'a rien cassé.** Deux fichiers de test pour 6 345 lignes de serveur, et aucun ne couvre le tri par `pour` — la garantie du brouillard à deux joueurs. Sans harnais, restructurer est un pari ; donc on ne restructure pas. **La structure est d'abord un problème de vérifiabilité**, pas de goût : elle devient abordable le jour où l'iso-comportement se prouve, et ce jour-là seulement. D'où le lot 0, qui n'est pas un préliminaire mais la condition.

**c) Le fichier est écrit pour être lu par la session suivante, et il l'est par `grep`.** Ses commentaires portent des décisions payées cher — pourquoi `MAX_FIL` vaut 80, pourquoi un item sans `pour` n'est servi à personne, pourquoi on meurt sur `EADDRINUSE` plutôt que de se rabattre sur un autre port. Tout au même endroit, `grep` trouve tout. Découper ressemblait à perdre la carte. C'est faux, mais il faut le dire : **si le découpage disperse ces commentaires sans les garder intacts, l'objection redevient juste.**

**d) Celui qui écrit ne paie pas la longueur.** Une session n'a jamais lu ce fichier de haut en bas : elle y entre par `grep` à la ligne 3 511 et en ressort. 6 345 lignes ne lui coûtent presque rien, alors qu'à un lecteur humain elles coûtent tout. **Un défaut qu'on ne sent pas ne se corrige pas spontanément.**

Corollaire, et c'est la seule ligne de ce document qui doit survivre même si le chantier est ajourné :

> **Une route neuve ne s'écrit plus dans `serveur.js`.** Elle s'écrit dans un fichier de `routes/`, même si `serveur.js` n'a pas encore été découpé — la table de dispatch du lot 3 les ramassera. Sans cette règle, le fichier repousse en trois lunes et ce document ne sert à rien.

---

## 1. Ce qu'il y a dedans, mesuré

| Région | Lignes | Contenu |
|---|---:|---|
| L1-46 | 46 | requires, `RACINE`, `PORT`, `MAX_FIL` |
| L47-138 | 92 | portraits par défaut, teinte du nom, dates et vieillissement des certitudes |
| L139-485 | 347 | `envoyer`, `roster`, `cheminEtat`, `qui`, `monPersonnage`, `audienceCourante`, `volumesVisibles`, `fichierStatique` — **le siège et le brouillard** |
| L486-649 | 164 | `dossiersRecherche` |
| L650-1465 | 816 | graphe piéton, index du bâti, métiers, repères, péremption, `serviceMonde` — **le monde 3D** |
| L1466-2039 | 574 | activations, têtes, criticité, santé, charge, fil du MJ actif — **l'admin** |
| L2040-2533 | 494 | `filPersonnage`, `chercherDansFlux`, `extraitDuFlux`, `regie` — **la régie** |
| L2534-5158 | 2 625 | les 46 routes GET, en ligne dans le callback |
| L5159-6331 | 1 173 | les 14 routes POST, en ligne dans le callback |

Les cinq routes les plus lourdes concentrent **2 070 lignes** :

| Route | Lignes | Ce que c'est vraiment |
|---|---:|---|
| `GET /echiquier` | 1 293 | le moteur de plan : lecture des cahiers, graphe des chaînes, six détecteurs, calcul X/Z, missions |
| `POST /marche` | 340 | itinéraire piéton et rendu de ce qu'on croise |
| `GET /calendrier` | 169 | bandes, jours, notes d'agenda |
| `GET /carte` | 168 | jetons, traits, bannières, vieillissement |
| `GET /presence` | 160 | quartier, creux, salles |

**Le diagnostic n'est pas « le fichier est long ».** Il est que trois choses de natures différentes y sont mélangées : (a) du **transport** HTTP, (b) de la **lecture d'état** avec ses règles de brouillard, (c) des **moteurs de domaine** — l'échiquier, le graphe piéton, les activations — qui n'ont rien à faire dans un handler et qu'on ne peut aujourd'hui ni tester ni appeler depuis un script.

---

## 2. La cible

Le dépôt a déjà le bon patron : `bibliotheque.js` et `voix.js` sont des modules CommonJS, sans dépendance, avec un `module.exports` nommé et un test à côté. On l'étend, on n'invente rien.

```
serveur/
  serveur.js            ~150 l.  requires, PORT, création du serveur, table de routes, 404, listen
  contexte.js           ~120 l.  RACINE, cheminEtat, lireJson, lireCroyance, dateDe
  http.js                ~90 l.  envoyer, fichierStatique, lireCorps (POST), inlinerFigure
  routes.js              ~80 l.  la table { methode, chemin } → handler, et le dispatch
  siege.js              ~300 l.  roster, qui, monPersonnage, audienceCourante, volumesVisibles, ecartDe
  portraits.js           ~90 l.  teinteDuNom, portraitDefaut, portraitFrais, rafraichirPortraits
  dates.js               ~60 l.  jourAbsolu, vieillir, AGE_DIT, dateCourte
  flux.js               ~200 l.  lecture et fenêtrage de flux.jsonl, tri par `pour`, append d'un item
  domaine/
    echiquier.js       ~1 300 l.  le moteur de plan (détecteurs, X/Z, missions)
    monde.js             ~820 l.  graphe piéton, bâti, repères, péremption, serviceMonde
    marche.js            ~340 l.  itinéraire et ce qu'on croise
    activations.js       ~580 l.  activations, têtes, criticité, santé, charge, fil MJ
    regie.js             ~500 l.  filPersonnage, recherche dans le flux, extrait
    recherche.js         ~170 l.  dossiersRecherche
  routes/
    jeu.js                        /, /moi, /bascule, /jeu.css, pages statiques
    scene.js                      /scene, POST /action
    carte.js                      /carte, /ville, /terrain, /plis, /nappe (+ POST)
    livres.js                     /books, /echiquier, /notes (+ POST)
    gens.js                       /presence, /gens, /entites, /salles, /fils, /depeches
    admin.js                      /admin*, /criticite, /retrospective, /medailles
    monde.js                      /monde3d, /pas, /foule, POST /marche, POST /ou, POST /piece
    joueur.js                     /objectifs, /calendrier, POST /agenda, POST /vue
    bataille.js                   /bataille*, /architecture-bataille*, POST /marque-bataille
    voix.js                       /voix/*, POST /foule/journal
```

### Deux contrats, et ils suffisent

**Un handler de route** est une fonction de transport, et rien d'autre :

```js
// routes/carte.js
module.exports = [
  { methode: "GET", chemin: "/carte", faire: (req, res, ctx) => { /* … */ } },
];
```

`ctx` porte ce que tout le monde partage — `RACINE`, `envoyer`, `lireJson`, `qui`, `monPersonnage`, `roster`, `dateDe` — et **rien d'autre**. Pas de singleton importé de partout : un module de domaine reçoit sa racine en argument, comme `bibliotheque.charger(RACINE)` le fait déjà. C'est ce qui rend un test possible sans lancer de serveur.

**Un module de domaine** ne connaît ni `req` ni `res` :

```js
// domaine/echiquier.js
module.exports = { plateau, missions, detecteurs };   // plateau(racine, moi) → objet sérialisable
```

Règle dure : **si un fichier de `domaine/` mentionne `res`, la coupe est ratée.**

---

## 3. L'ordre des lots

L'ordre n'est pas cosmétique : chaque lot est choisi pour être **vérifiable par un moyen différent du précédent**, et pour rendre le suivant mécanique. Un lot = un commit = un serveur qui redémarre et une partie qui se rejoue.

### Lot 0 — le filet (avant toute coupe)

Sans lui, tout le reste est un pari. `test_piece_http.js` prouve qu'on sait déjà lancer un serveur sur un port libre avec `CONSEIL_RACINE` pointé sur une partie miniature : on en fait un harnais.

- **`serveur/test_routes.js`** : démarre le serveur sur port libre, `CONSEIL_RACINE` sur un dossier temporaire monté de quelques fichiers d'état, et **frappe les 57 routes**. Il n'assertionne pas le contenu : il assertionne le **code HTTP** et, pour le JSON, la **liste des clefs de premier niveau**. C'est un test de non-régression de forme — exactement ce dont un déplacement de code a besoin.
- **`serveur/empreinte.js`** : même chose contre le serveur de la **vraie partie** (port 3129), écrivant un `empreintes.json` — code, longueur, clefs, hash du corps, par route et **par siège**. On le lance avant le lot, après le lot, on `diff`. Un octet qui bouge se voit.
- Les deux se lancent à la main (`node serveur/test_routes.js`) et doivent tenir sous dix secondes. Il n'y a pas de CI, et ce n'est pas ce chantier-ci qui en montera une.

**Critère de sortie** : les 57 routes répondent, l'empreinte est stable sur deux exécutions consécutives sans modification.

### Lot 1 — `http.js`, `dates.js`, `portraits.js` (~240 lignes)

Les feuilles du graphe : elles ne dépendent de rien. `envoyer` est appelé 144 fois — le déplacer d'abord fait passer tout le reste par un point unique. Risque nul, vérification par l'empreinte, à l'octet.

### Lot 2 — `contexte.js` et `siege.js` (~470 lignes)

Le cœur du brouillard : `qui`, `monPersonnage`, `volumesVisibles`, `audienceCourante`, `roster`, `cheminEtat`. **Cette coupe mérite un vrai test, pas seulement une empreinte** : c'est le seul endroit du serveur où un bug rend visible à un siège ce qu'un autre a entendu.

**`serveur/test_siege.js`** : trois sièges factices, un flux de dix items dont trois portent `pour`, et l'on vérifie que chacun reçoit exactement ce qu'il doit — dont la régie, qui voit tout. Ce test survit au refactor et vaut par lui-même.

Attention aux **caches de module** : `cachePresence`, `_portraitsFrais`, `_rues`, `_bati`, `_monde`, `_peremption`, `cacheCriticite`, `cachePlanModele`, `cacheFilMjActif`. Chacun déménage **avec la fonction qui le remplit**, jamais dans `contexte.js` — un cache partagé entre deux modules est la façon la plus rapide de recréer le monolithe sous un autre nom.

### Lot 3 — `routes.js`, la table (~80 lignes, mais c'est le pivot)

On remplace la chaîne de `if` par une table et un dispatch :

```js
const table = new Map();          // "GET /carte" → faire
for (const r of [...jeu, ...scene, ...carte /* … */]) table.set(r.methode + " " + r.chemin, r.faire);
```

Deux gains immédiats et non négociables :
- **les doublons deviennent impossibles** — aujourd'hui `/regie/chercher` est testé deux fois (L2865), le premier `if` étant mort, et rien ne le signale ;
- **l'ordre cesse d'être sémantique** : une route ajoutée en haut ne peut plus voler celle du bas.

À ce stade les handlers restent dans `serveur.js` : on ne déplace que le dispatch. C'est le lot qui rend tous les suivants mécaniques — et celui qui rend applicable la règle du § 0.

### Lot 4 — `domaine/echiquier.js` (1 293 lignes)

Le plus gros gain, et le plus facile à isoler : ce bloc ne touche `res` qu'à sa dernière ligne. On extrait `plateau(racine, moi)`, il reste trois lignes dans la route.

Ce qui en sort en prime, et qui justifie le lot à lui seul : **le moteur de plan devient appelable hors HTTP**. `scripts/criticite.py` et `scripts/couverture.py` calculent des choses voisines de leur côté ; un `node -e "require('./serveur/domaine/echiquier').plateau(…)"` permet enfin de comparer les deux au lieu de les croire.

Vérification : empreinte de `/echiquier` **identique à l'octet, siège par siège** — le contenu dépend du siège, un seul ne prouve rien.

### Lot 5 — `domaine/monde.js` et `domaine/marche.js` (~1 160 lignes)

Le graphe piéton et ses caches. `POST /marche` sort avec, puisqu'il n'est que l'exposition du graphe. Vérification particulière : une même paire de points doit rendre le même itinéraire **au mètre** avant et après — c'est là-dessus que se calent des `cout` d'étape et des délais de course.

### Lot 6 — `activations.js`, `regie.js`, `recherche.js` (~1 250 lignes)

Trois blocs indépendants, sans état partagé, lus seulement par les écrans d'admin et de régie. Le moins risqué des gros lots : si l'un casse, personne ne perd une partie en cours.

### Lot 7 — les fichiers de `routes/` (~2 600 lignes redistribuées)

Les handlers restants quittent `serveur.js` par groupes thématiques. Purement mécanique une fois le lot 3 posé. À l'arrivée, `serveur.js` ne contient plus que : les requires, `PORT`, la construction de `ctx`, `createServer` avec le dispatch, le 404, `listen`, le `EADDRINUSE`.

**Critère de fin de chantier** : `wc -l serveur/serveur.js` < 200 ; aucun fichier de `serveur/` au-dessus de 400 lignes sauf `domaine/echiquier.js` ; empreinte des 57 routes inchangée depuis le lot 0.

---

## 4. Les règles du chantier

1. **Aucun changement de comportement dans un lot de déplacement.** Une amélioration repérée en route s'écrit au § 5 — elle ne se glisse pas dans le commit. Un lot qui change à la fois la structure et le comportement n'est plus vérifiable par l'empreinte, et l'empreinte est tout ce qu'on a.
2. **Les commentaires partent avec leur code, intacts.** Ce fichier est commenté au-dessus de la moyenne du dépôt, et ces commentaires portent des décisions payées en bugs. Les perdre coûterait plus que le monolithe — voir § 0 (c).
3. **On ne coupe pas pendant une partie.** Le serveur vit sur le port 3129 et une séance peut tourner. Un lot se pose entre deux séances, et le serveur se redémarre une fois — on n'ouvre jamais un second serveur.
4. **À deux plumes, `serveur.js` se relit avant d'être écrit.** Un déplacement réécrit le fichier en entier ; deux lots concurrents s'écrasent en silence. Annoncer le lot au parloir avant de le commencer.
5. **Un lot par commit**, message disant le lot et le nombre de lignes déplacées.

---

## 5. Ce qu'on répare une fois la place faite (pas avant)

Repéré en lisant, à ne surtout pas mélanger aux lots :

- **`/regie/chercher` est testé deux fois** (L2865), le premier `if` étant mort. À supprimer au lot 3, où la table le rend visible.
- **48 `JSON.parse(fs.readFileSync(…))` recopiés**, chacun avec son `try/catch` et son défaut. Un `ctx.lireJson(relatif, defaut)` unique les remplace — et permet un cache par mtime, impossible à poser aujourd'hui.
- **La lecture de corps POST est recopiée 14 fois** (`req.on("data") … req.on("end")`), sans limite de taille. Un `lireCorps(req, max)` la borne d'un coup.
- **`/scene` relit et parse `flux.jsonl` en entier à chaque appel.** Le fichier ne fait que grossir et la page l'interroge en boucle. Une fois `flux.js` isolé, un index par offset fait une trentaine de lignes ; aujourd'hui c'est intouchable.
- **Aucun test ne couvre le tri par `pour`**, qui est la garantie du brouillard à deux joueurs. Le lot 2 le pose ; il doit rester après.

---

## 6. Résumé opérationnel

| Lot | Contenu | Lignes | Risque | Preuve |
|---|---|---:|---|---|
| 0 | harnais `test_routes.js` + `empreinte.js` | +200 | — | 57 routes, empreinte stable |
| 1 | `http.js`, `dates.js`, `portraits.js` | 240 | nul | empreinte |
| 2 | `contexte.js`, `siege.js` | 470 | **élevé** (brouillard) | `test_siege.js` + empreinte |
| 3 | `routes.js` — table de dispatch | 80 | moyen | empreinte, doublon `/regie/chercher` levé |
| 4 | `domaine/echiquier.js` | 1 293 | moyen | empreinte par siège |
| 5 | `domaine/monde.js`, `marche.js` | 1 160 | moyen | itinéraires au mètre |
| 6 | `activations.js`, `regie.js`, `recherche.js` | 1 250 | faible | empreinte |
| 7 | `routes/*.js` | 2 600 | faible | empreinte, `serveur.js` < 200 l. |
