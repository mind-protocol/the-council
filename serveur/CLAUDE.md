# `serveur/` — comment ce dossier est fait, et ce qu'on y ajoute

Le serveur du jeu tenait dans un seul fichier de **6 345 lignes**, dont 3 798 dans un unique callback `createServer`. Il est découpé depuis le 30e jour de la 8e lune. Le plan, ses raisons et ses lots restent dans [`docs/serveur-structuration.md`](../docs/serveur-structuration.md) — ce fichier-ci ne dit que **l'état actuel et les règles à tenir**.

## La règle qui compte

> **Une route neuve ne s'écrit plus dans `serveur.js`.** Elle s'écrit dans un fichier de `routes/` — celui de sa famille s'il existe, un nouveau sinon —, et son module s'ajoute à la table `ROUTES`.

Sans elle, le fichier repousse en trois lunes et le découpage n'aura servi à rien : le geste le moins risqué est toujours d'ajouter une ligne là où l'on est déjà.

## Ce qu'il y a, et où

```
serveur.js        65 l.   ouvre le port, présente la requête aux routes, 404, EADDRINUSE
contexte.js      117 l.   RACINE, PORT, MAX_FIL, cheminEtat, cheminNotes, lireCroyance,
                          dateDe, resoudrePresence — les chemins de l'état
http.js           45 l.   envoyer, fichierStatique, inlinerFigure — le transport
siege.js         218 l.   roster, qui, regardeur, monPersonnage, audienceCourante,
                          volumesVisibles, ecartDe — LE SIÈGE ET LE BROUILLARD
dates.js          56 l.   jourAbsolu, vieillir, AGE_DIT, dateCourte, absolues
portraits.js      71 l.   teinteDuNom, portraitDefaut, portraitFrais, rafraichirPortraits
monde3d.js       954 l.   graphe piéton, bâti, repères, péremption, serviceMonde
domaine/
  echiquier.js  1302 l.   le moteur de plan : cahiers, chaînes, détecteurs, X/Z, missions
  activations.js 565 l.   activations, têtes, criticité, santé, charge, fil du MJ actif
  regie.js       521 l.   filPersonnage, recherche dans le flux, extrait, regie()
  marche.js      394 l.   la montre, la position, ce qu'on longe et perçoit, le sac
  recherche.js    51 l.   dossiersRecherche
routes/          21 fichiers, 24 à 244 l. — un par famille d'URL, en-tête disant lesquelles
```

## Deux contrats

**Une route** est une fonction de transport, et rien d'autre :

```js
module.exports = function traiter(req, res, url) {
  if (req.method === "GET" && url === "/carte") return envoyer(res, 200, /* … */);
  return false;                       // « je ne reconnais pas cette URL »
};
```

`false` est le SEUL signal de non-reconnaissance. Une route qui répond en différé — un POST qui attend son corps — ne rend rien du tout, et ce silence vaut « je m'en charge ». C'est ce qui permet à `serveur.js` de tomber sur son 404 sans se tromper.

**Un module de `domaine/`** ne connaît ni `req` ni `res` : il prend des valeurs, il rend un objet sérialisable. `domaine/echiquier.js` expose `composer(req, url)` et la route qui l'appelle tient en deux lignes. **Si un fichier de `domaine/` mentionne `res`, la coupe est ratée.**

## Ce qu'on ne casse pas

- **L'ORDRE DE `ROUTES` EST SÉMANTIQUE.** Plusieurs routes se reconnaissent par préfixe (`/salles` avant `/salles/`, `/monde/` après `/chemin`, `/modules/…` par expression régulière) et la première qui prend la requête la garde. C'est la seule différence assumée avec le plan du document, qui prévoyait une table `Map` d'égalités exactes : elle ne sait pas dire les préfixes. Déplacer une entrée de la liste, c'est changer le routage.
- **Les caches vivent avec la fonction qui les remplit** — `cachePresence` dans `contexte.js`, `_portraitsFrais` dans `portraits.js`, `_rues`/`_bati`/`_monde`/`_peremption` dans `monde3d.js`, `cacheCriticite`/`cachePlanModele`/`cacheFilMjActif` dans `domaine/activations.js`. Un cache partagé entre deux modules recrée le monolithe sous un autre nom.
- **Les commentaires partent avec leur code, intacts.** Ils portent des décisions payées en bugs : pourquoi `MAX_FIL` vaut 80, pourquoi un item sans `pour` n'est servi à personne, pourquoi on meurt sur `EADDRINUSE` au lieu de se rabattre sur un autre port.
- **Un seul port, le 3129.** On redémarre le serveur, on n'en ouvre pas un second. Un atelier passe `PORT=…` pour ne pas disputer le port de la partie en cours.

## Prouver qu'un déplacement n'a rien cassé

C'est du déplacement de code : la preuve est l'**iso-comportement**, pas la relecture. Deux serveurs, l'ancien et le nouveau, sur deux ports, et l'on compare les réponses route par route :

```bash
git show HEAD:serveur/serveur.js > serveur/_ancien.js
```

Puis on lance les deux (`PORT=3199 node serveur/serveur.js`, `PORT=3198 node serveur/_ancien.js`) et l'on `diff` chaque URL. **Comparer les corps privés de leurs chiffres** (`tr -d '0-9'`) : `/admin/*` et `/criticite` portent des horodatages qui bougent d'une requête à l'autre — un écart qui ne tient qu'aux chiffres n'est pas une régression, un écart de structure en est toujours une.

### Une comparaison ne prouve QUE les chemins qu'elle emprunte

C'est la leçon du chantier, et elle a coûté deux routes. Le découpage a été validé sur cinquante URL comparées à l'ancien serveur : `POST /marche` n'en faisait pas partie, et `GET /chemin` n'y était frappé que sans paramètres. Les deux avaient **perdu leurs `require`** au recâblage — `_resteMarche`, `batiAutour`, `LIEU3D_DEFAUT`, `graphePieton` — et rendaient depuis `{"erreur":"_resteMarche is not defined"}`. Rien ne l'avait dit : un `try/catch` de route transforme une référence absente en réponse d'erreur ordinaire, et une URL frappée sans ses paramètres sort avant d'atteindre le code cassé.

Donc, après tout déplacement : **frapper chaque route avec des paramètres qui vont jusqu'au bout du handler**, POST compris, et se méfier d'une comparaison qui passe. Le détecteur d'identifiants orphelins vaut mieux que rien, mais il bruite sur les déstructurations imbriquées — c'est l'exécution qui tranche.

### Les tests

Quatre tests montent une partie miniature dans un dossier temporaire (`CONSEIL_RACINE`) et exercent le serveur entier. À lancer après toute coupe :

```bash
node serveur/test_siege.js && node serveur/test_marche.js && node serveur/test_piece_http.js && node serveur/test_bibliotheque.js
```

**`test_marche.js` tient le moteur de la marche** : le même couple de points rend le même itinéraire deux fois, la polyligne part du point cliqué et n'est jamais plus courte que la ligne droite, quatre tronçons à 0,3 minute paient **une** minute et gardent le reste (sans ce report, un kilomètre coûterait zéro), la position et le bandeau sont écrits, et le sac ne tombe dans l'inbox qu'à l'arrivée — le guetteur du MJ ne se réveille pas par tronçon. Il monte le monde 3D en **jonction** (1,2 Go : on ne le copie pas) et se déclare sans objet si le bâti n'a pas été engendré. Attention en le retouchant : les jonctions se défont par `rmdirSync` nu, jamais par un effacement récursif qui suivrait le lien et viderait `monde/`.

**`test_siege.js` tient le brouillard** : trois sièges, un flux de dix items dont six portent une audience, et l'on vérifie que chacun reçoit **exactement** le sien — la liste, dans l'ordre, pas « au moins » ni « pas trop ». Il couvre les deux moitiés, parce qu'elles se ferment l'une l'autre : la lecture (`GET /scene`, dont le verrou par en bas — passé la ligne du dernier arrivé, un item sans `pour` ne part chez personne) et l'écriture (`POST /action`, qui estampe la parole du joueur de l'audience de sa scène). Il a été **vérifié par mutation** : désarmer le verrou de lecture le fait tomber sur « la reine ne reçoit pas exactement sa scène », retirer l'estampille d'écriture sur « une question hors fiction a fuité ». Un test de brouillard qui n'a jamais été vu échouer ne prouve rien.

## Ce qui reste à faire

- **`serviceMonde` garde `res`** et vit dans `monde3d.js`, hors de `domaine/` pour cette raison : c'est un service de fichiers (treize sorties, dont du gzip et de l'octet-stream), pas un moteur. Le sortir demande de le convertir en descripteur de réponse, ce qui n'est pas un déplacement.
- **48 `JSON.parse(fs.readFileSync(…))` recopiés** attendent toujours un `lireJson(relatif, defaut)` unique dans `contexte.js` ; **la lecture de corps POST est recopiée 14 fois**, sans limite de taille.
