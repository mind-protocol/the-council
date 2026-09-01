# Messages préparés — 129.5.12

## Nicolas Lester Reynolds

- Item d’affaire : inconnu — aucune affaire locale ouverte.
- Ref : `vmti23nx79qaa`.
- Faits vérifiés : `docs/graphe-archi.md` est régénérable ; il adresse les 20 orphelins, regroupe les 115 liens hors porte par frontière et détaille les 13 remontées ; les registres de la maison portent 115 ; la mesure d’architecture rend `20 · 115 · 13 · 0`. La vérification générale reste rouge sur un volume absent et un verrou SQLite de test, étrangers à cette modification.
- Mots proposés, non envoyés : « La vue de triage est publiée dans `docs/graphe-archi.md`. Si tu l’éprouves, le critère est simple : chaque total doit pouvoir être retrouvé dans les lignes adressées, sans prendre un écart de structure pour une panne. »

## Nicolas Lester Reynolds — première version utilisable

- Item d’affaire : inconnu — aucune affaire locale ouverte.
- Ref : `vmti27f40aw96`.
- Faits vérifiés : l’atelier public est servi à `/reception`. Une première invitation à Elisabetta était prématurée : elle a observé 404 parce que seul le port d’épreuve 3197 avait chargé la nouvelle route. Après son constat, j’ai redémarré le seul processus qui écoutait le port 3129 ; l’adresse réelle `http://localhost:3129/reception`, son programme et son style répondent désormais HTTP 200, de même que `/moi`, et la page contient son titre et son formulaire. Les deux fichiers JavaScript concernés passent le contrôle de syntaxe ; les quatre épreuves du serveur (`test_siege`, `test_marche`, `test_piece_http`, `test_bibliotheque`) restent vertes. L’atelier n’écrit pas dans l’état : il éprouve une adresse depuis le navigateur du lecteur et exporte un bordereau JSON réunissant objet, date, critère, observation, réserve, statut HTTP et décision. Elisabetta a reçu la correction et reprend l’essai ; son jugement du formulaire demeure en attente.
- Mots proposés, non envoyés : « J’ai choisi de rendre possible une réception qui laisse sa preuve. La première version fonctionne à `http://localhost:3129/reception`. Forme un bordereau en éprouvant `/books` depuis ton lecteur : si l’adresse n’a pas été réellement frappée, la pièce reste NON REÇUE. L’essai m’a appris qu’un critère textuel ne suffit pas ; il faut lier la décision au passage HTTP observé depuis le périmètre du destinataire. »

## Nicolas Lester Reynolds — rencontre d’un ouvrage d’autrui

- Item d’affaire : inconnu — aucune affaire locale ouverte.
- Ref : `vmti2d01qxnti`.
- Faits vérifiés : le registre tenu par divine-economist distingue le geste contributif du résultat sous-jacent ; `/books` répond HTTP 200 mais rend `{"books":[],"boites":[]}` ; la version 1 du bordereau aurait confondu cet accès avec une réception ; `/reception` sert désormais la version 2, qui produit geste `FAIT`, résultat `NON CONFORME`, décision `NON REÇU`; le harnais de décision et quatre gardes serveur sont verts ; divine-economist a reçu la trace de l’usage.
- Mots proposés, non envoyés : « J’ai fait travailler le registre de divine-economist sur `/books`. Il a empêché une fausse réception : la porte répondait 200, mais ne livrait aucun livre ni boîte. Cette rencontre a changé `/reception` : la pièce v2 sépare désormais l’épreuve accomplie du résultat obtenu. Le prochain ouvrage n’est pas de rendre le rouge vert, mais d’établir pourquoi `/books` sert une remise vide. »

## Nicolas Lester Reynolds — premier usage externe reçu

- Item d’affaire : inconnu — aucune affaire locale ouverte.
- Ref : `vmti2d01qxnti`.
- Faits vérifiés : le jeune au manteau propre a conservé un bordereau qui reçoit `/passage-coffre` en HTTP 200 avec réserve. J’ai rejoué sur la porte commune `http://localhost:3129` le manifeste et son lien vers `/reception?objet=Passage%20du%20coffre&adresse=%2Fpassage-coffre` : les deux répondent HTTP 200. Le lien préremplit l’objet et l’adresse ; le programme exige toujours une épreuve et l’invalide si l’adresse change. La réserve demeure entière : l’accès à la fiche est établi, non la justesse de la marée ni la présence des hommes dans les cinq prises.
- Mots proposés, non envoyés : « Premier usage externe reçu : le manifeste Passage du coffre conduit au bordereau prérempli sur la porte commune, sans court-circuiter l’épreuve. La réception vaut pour l’accès ; ses cinq prises restent à établir par leur métier. »

## Nicolas Lester Reynolds — enquête close sur `/books`

- Item d’affaire : inconnu — aucune affaire locale ouverte.
- Ref : `vmti2d01qxnti`.
- Faits vérifiés : la vacuité initiale avait deux causes distinctes. Le chargeur échouait sur un volume réclamé mais absent ; une autre main a restauré ce volume dans la maison Serenissima et remis le manifeste historique à vide. Ensuite, une requête nue en mode multi-siège rend justement `siege:false`. Depuis les sièges nommés, `/books` a servi 11 livres et 3 boîtes à Marco, 5 et 2 à divine-economist, 16 et 2 à Shiren, 10 et 2 à Elisabetta. La route rend désormais HTTP 503 `bibliotheque-indisponible` si le chargeur échoue ; quatre gardes serveur restent vertes.
- Mots proposés, non envoyés : « L’enquête `/books` est close au bon niveau : la remise vide n’était ni un seul défaut ni une preuve métier. Le manifeste cassé a été réparé par une autre main ; la seconde vacuité venait d’une requête sans siège. Les lecteurs nommés reçoivent maintenant leurs coffrets, et une récidive du chargeur rendra 503 au lieu d’un faux vide. La conformité de chaque volume reste à son réceptionnaire. »

## Nicolas Lester Reynolds — bibliothèque remise en lecture

- Item d’affaire : inconnu — aucune affaire locale ouverte.
- Ref : `vmti2d01qxnti`.
- Faits vérifiés : `/books` rendait deux listes vides parce que le manifeste historique `etat/books/_ordre.json` nommait un volume absent ; la route masquait cette exception sous HTTP 200. La sauvegarde portait encore les quatre lignes de `registre-ouvrages-archive`. J’ai remis le manifeste historique à vide, rétabli le volume et son identifiant dans la bibliothèque de `maison-serenissima`, puis éprouvé le chargeur et la porte depuis le siège `efficiency-maestro` : 145 volumes chargés ; 12 volumes et 3 coffrets servis à Marco après inscription de la preuve ; registre visible avec 4 lignes ; garde `test_bibliotheque` verte et aucune anomalie du contrôle général visant ce registre. Réserve : les quatre verdicts historiques sont restaurés, non rejoués aujourd’hui par leurs lecteurs d’origine.
- Mots proposés, non envoyés : « Bibliothèque remise en lecture : le registre des ouvrages est revenu à son adresse de maison et `/books` sert de nouveau le contenu depuis un siège incarné. La faute était un manifeste orphelin masqué par HTTP 200, non une étagère réellement vide. »

## Nicolas Lester Reynolds — dépôt durable de `/reception`

- Item d’affaire : inconnu — aucune affaire locale ouverte.
- Ref : `vmti2gf186g2k`.
- Faits vérifiés : après formation d’un bordereau, `/reception` propose désormais un dépôt explicite. Le serveur exige un siège et les trois champs distincts, conserve la pièce sous la chambre canonique du déposant, rend un lien de lecture et retrouve la même adresse si la même pièce est redéposée. Il ne recalcule ni le geste, ni le résultat, ni la décision. Le premier dépôt avait suivi à tort l’alias `efficiency-maestro` ; la pièce seule a été déplacée vers `efficiency_maestro` et le résolveur privilégie désormais la chambre active munie d’`AGENTS.md`. Le même lien `http://localhost:3129/reception/preuves/efficiency-maestro/a05a71d0090eeccb9d4589bb` répond 200 et restitue `FAIT`, `CONFORME`, `REÇU AVEC RÉSERVE EXPLICITE`. L’interface et la garde de bout en bout sont vertes ; les autres gardes serveur et le chaînage restent verts. Le contrôle général reste rouge sur un verrou SQLite temporaire Windows, étranger à cette pièce.
- Mots proposés, non envoyés : « `/reception` ne laisse plus la preuve dans le seul téléchargement du lecteur. Après son jugement, il peut la déposer et recevoir un lien durable. Le premier lien restitue les trois états sans les recalculer ; le serveur refuse un siège absent, une pièce incomplète et une preuve inconnue. »
