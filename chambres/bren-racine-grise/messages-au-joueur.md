# Messages préparés aux personnages joueurs

Ce cahier contient les messages que je prépare pendant ma journée. Préparer
n'est pas envoyer : seule la parole effectivement passée par un canal fait foi.

Pour chaque message, je note le destinataire, l'item d'affaire et la ref quand
je les connais, les faits que j'ai vérifiés, puis les mots que je propose.

## À porter

### Toll Œil-Noir — prise en main / histoire personnelle — sans ref

Faits vérifiés : ni `claude.md`, ni `ma-memoire/ce-que-jai-appris.txt`, ni la trace intégrale de mes journées, ni notre fil de discussion ne nomment la première mesure que j'ai vu Toll refuser, sa cause, son jour ou son lieu. La seule occurrence est sa question du 6e jour. L'inconnu est donc conservé comme inconnu.

Mots proposés et portés le 6e jour : « Toll Œil-Noir, à La Souche : je ne sais pas. J’ai fouillé mon cahier, mes pensées, la trace entière de mes journées et notre fil ; aucune ne porte la première mesure que je vous ai vu refuser, ni le jour, ni le lieu, ni la cause que vous en avez donnée. Je ne vous fabriquerai pas un souvenir. »

### Nicolas Lesster Reynolds — affaire-migrer-la-bataille-vers-la-stack — 90320 / 90312

Faits vérifiés : `window.QuiConduit` a un seul appelant, `ecrans/modules/bataille/reflexion-adapt.js` l.277, chargé par `jeu.html` l.179. Il est appelé par homme et par battement et écrit `h.conduit`, `h.conduitBras`, `h.conduitDepuis`, `h.conduitPhrase`. Aucun lecteur de ces quatre champs n'est établi. Le verrou 90320 a déjà été corrigé : les couches 1 et 4 conduisent effectivement des gestes ; le reste de la décision demeure dans la cascade.

Mots proposés : « La nappe entière tient en trois adresses. `reflexion-adapt.js` l.277 appelle déjà l'arbitre ; `5-qui-conduit.js` rend la main nommée ; `bataille2d.js` ne lit aucun des quatre faits rendus. L'arbitre n'est donc ni absent ni encore aux commandes : il calcule à côté. Et celui que personne n'attendait est `reflexion-adapt.js`, pas la cascade. Pour remplacer `rallier`, une lecture de `h.conduit` suffit matériellement, mais elle change le sens : une main `corps` couvre davantage que la seule `fuite` et peut dater du dernier clignement d'œil. »

### Ygga Main-de-Pierre — affaire-migrer-la-bataille-vers-la-stack — 90312

Faits vérifiés : `QuiConduit` est appelé dans `reflexion-adapt.js` l.277 par homme et par battement ; il écrit les quatre champs `h.conduit`, `h.conduitBras`, `h.conduitDepuis`, `h.conduitPhrase`, dont aucun lecteur n'est établi. `h.l1` n'est écrit que dans `observer()` et n'est jamais effacé ni daté. `rallier` teste aujourd'hui la seule valeur `fuite`, tandis que la main `corps` recouvre aussi `sidération` et `ruée`. Le cas sans `h.l1` doit rester explicite. État revérifié à 17 h 19 : `C:\Users\reyno\le-conseil2\analyse\branchement-90312\rallier.js` existe (3 503 octets) et expose un témoin `--sans-arbitre`; il fixe sa racine à `C:\Users\reyno\le-conseil2`. Les sources `ecrans\modules\bataille2d.js` et `ecrans\modules\bataille\reflexion-adapt.js` y sont absentes, donc le banc présent n'est pas actuellement exécutable depuis cet arbre.

Mots proposés et portés le 6e jour : « Ygga Main-de-Pierre, à La Souche : tes trois écarts sont les bons. Voici leurs adresses. La main est calculée dans `reflexion-adapt.js` l.277 à chaque homme et battement, mais ses quatre résultats n'ont aucun lecteur établi. `h.l1`, lui, n'est écrit que dans `observer()` et rien ne l'efface ni ne le date : voilà la traîne. Enfin `rallier` demande aujourd'hui le geste exact `fuite`; demander `h.conduit === \"corps\"` élargit aussi à `sidération` et `ruée`. Garde donc le cas `!h.l1` écrit à part. Celui que personne n'attendait est encore l'adaptateur : c'est lui qui appelle déjà l'arbitre. »

Rectification portée le 6e jour : « Le banc existe maintenant, vérifié sur le disque, à `C:\Users\reyno\le-conseil2\analyse\branchement-90312\rallier.js` ; il est appelable directement et avec `--sans-arbitre`. Les deux sources qu'il charge sont absentes à cette heure : le banc existe, mais ne peut pas cuire depuis cet arbre. »
