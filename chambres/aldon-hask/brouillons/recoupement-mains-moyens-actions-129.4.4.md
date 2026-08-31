# Recoupement des mains, moyens et actions — 4e de la 4e lune, an 129

Sources relues :

- `etat/maisons/maison-targaryen-noir/documents/mains.json`
- `etat/maisons/maison-targaryen-noir/documents/books/plan-moyens.json`
- les tables `⚔️ Actions` des livres `affaire-*.json` de la même maison
- pour l'or en transit : `le-livre-de-la-cassette.json`

Règle de lecture : une **mesure tenue** vient du fonds de mains ; une **déclaration** vient seulement du registre M01–M30 ; une action **consomme** un moyen seulement quand sa colonne `🧰 Moyens` le cite. Une action dite « productrice » ci-dessous nomme explicitement l'acquisition ou la vérification du moyen, mais le registre ne possède aucune colonne qui relie cette production.

## Les trente moyens

| Moyen | Mesure réellement tenue | Action inscrite qui le consomme ou le produit | Écart ou preuve |
| --- | --- | --- | --- |
| M01 · Voiles du Gosier | Partielle seulement : `port-peyredragon.nefs-en-etat = 11`, au port, et non au Gosier | 40 citations ; 22047 et 26030 en cours, 26052 engagée, 22041 faite | M01 sert de fourre-tout naval jusque dans 26036, alors que M02 existe séparément. La main ne mesure ni les stations ni les coques au Gosier. |
| M02 · Coques louées | Aucune main | 0 citation ; 26036 doit en affréter dix, 22047 et 22048 les nomment dans leur texte | Moyen déclaré « sûr, immobilisé » sans action qui le cite ; acquisition et emploi ne remontent pas au registre. |
| M03 · Barques du bourg | Aucune main | 1 citation : 41224 à faire | 22048 écrit 31 barques dont 20 tiennent la mer, mais cette action est encore en cours et ne cite pas M03. Mesure seulement déclarée. |
| M04 · Dragons | Aucune main | 3 citations : 20070, 20073, 22033, toutes à faire | Moyen générique déclaré ; les moyens personnels M20–M22 ne sont jamais cités. |
| M05 · Rouleau de l'an 105 | Document existant, pas de mesure numérique attendue | 1 citation : 1220 à faire | Déclaré et matériellement accessible ; aucune preuve d'emploi accomplie. |
| M06 · Levée et garnison | Partielle : `recrutement-peyredragon.hommes-au-role = 36`, `solde-due = 66` ; la garnison n'est pas mesurée | 0 citation | Le dernier rapport de la même main porte encore 24 hommes et 300 cerfs au 22e ; valeurs courantes et rapport ne sont pas datés de façon à expliquer l'écart. |
| M07 · Hommes de Lamarck | Aucune main | 0 citation | Déclaré sûr et prêté, sans action ni preuve reliée. |
| M08 · Lances de Sombreval | Aucune main | 0 citation ; 10024 doit trancher leur emploi mais porte `—` en moyens | État `sûr` contredit expressément par 26200/26204 : 550 lances ne sont plus certaines après le silence de Gunthor et le feu du port. |
| M09 · Or du coffre | Pas de main ; le livre de la cassette tient les sorties | 14 citations ; 26051 vient d'être contre-écrite `sortie non remise`, les 13 autres sont à faire | Le registre dit « quelques jours », tandis que le financement calcule une caisse de campagne et un troisième état de transit. Mesure absente de `mains.json`. |
| M10 · Offre de Celtigar | Aucune main | 0 citation ; 28028 vérifie l'offre, 28030 doit produire une ligne de crédit | Le moyen offert n'est relié ni à l'action qui le vérifie ni à celle qui le rend utilisable. |
| M11 · Adresses de corbeaux | Aucune main | 11 citations, toutes ouvertes ou sans état | Déclaré « à demi dépensé » sans compteur de plis ni date de mesure. |
| M12 · Papier et plume | Aucune main | 164 citations : 17 closes, 21 en cours ou engagées, 9 bloquées, le reste ouvert | C'est le moyen le plus consommé et il n'a aucune mesure de stock, de main disponible ou de capacité du mestre. |
| M13 · Rendus du siège | Aucune main | 1 citation : 920 en cours | Déclaré périssable ; aucune liste tenue dans le fonds de mains. Les 40 prisonniers des caves ne sont pas les rendus à leurs maisons. |
| M14 · Septa Marlow et les septs | Aucune main | 0 citation | 37121 a obtenu neuf réponses des septs de la baie, mais cite M29, les septons de Port-Réal, dont la preuve dit justement qu'aucun nom n'est connu. |
| M15 · Bourg | Partielle : sel 17 muids, poisson séché 52 muids ; aucune mesure des yeux ou des métiers | 13 citations : 66020 close, 920/9023 en cours, 10 ouvertes | La mesure économique existe mais ne couvre qu'une partie de ce que le moyen prétend savoir faire. |
| M16 · Grèves et mouillages | Partielle : 11 nefs en état au port ; aucune mesure des grèves | 49 citations : 7 en cours, 2 bloquées, le reste ouvert | Moyen très employé, preuve matérielle seulement partielle. |
| M17 · Rôle des hommes | Partielle : 36 hommes au rôle dans la main de recrutement | 1 citation : 12022 bloquée | Le rôle existe, mais la mesure de la garnison et des tours manque. |
| M18 · Nouvelles | Aucune main | 35 citations, dont 1 bloquée et 34 ouvertes | Beaucoup d'actions réclament le moyen ; aucune mesure des nouvelles reçues, routes couvertes ou délais. |
| M19 · Vivres | Oui : 73 jours de vivres ; 17 muids de sel ; 52 muids de poisson séché | 0 citation | Le registre écrit « grain pour moins de trois semaines », tenu par Sara et dit chaque matin ; le fonds porte 73 jours, des porteurs différents et aucune série quotidienne. Périmètre et preuve ne concordent pas. |
| M20 · Jacaerys | Aucune main | 0 citation ; 33024 est en cours, 33424 à faire, sans moyen relié | Déclaré engagé ; les actions de son ambassade le nomment mais ne citent jamais M20. |
| M21 · Lucerys | Aucune main | 0 citation ; 26055 le nomme et porte une colonne moyens vide | Déclaré disponible, sans action reliée malgré une charge effective sur le rôle des bêtes. |
| M22 · Rhaenys et Meleys | Aucune main | 0 citation ; 43039 demande Meleys mais son livre n'a pas de colonne `🧰 Moyens` | Déclaré offert, jamais demandé, alors qu'une demande est inscrite à faire : état et action ne remontent pas l'un vers l'autre. |
| M23 · Crédit de Daemon | Aucune main | 1 citation : 221 à faire | Correctement traité comme valeur inconnue à éprouver ; aucune preuve encore. |
| M24 · Silence de Corlys | Inmesurable en l'état | 0 citation | Déclaration politique, sans action ni condition de consommation. |
| M25 · Ce qu'Otto croit | Inmesurable en l'état | 0 citation | Déclaration politique périssable, sans action reliée qui l'emploie ou la vérifie. |
| M26 · Connaissance du Donjon | Pas de main attendue ; savoir personnel déclaré | 15 citations : 29120/29121 en cours, 42321 bloquée, 12 ouvertes | Usage abondant, aucune preuve datée de fraîcheur ; le registre reconnaît lui-même que le savoir est vieux. |
| M27 · Ver Blanc | Aucune main | 2 citations : 13323 et 25034 à faire | Hors commandement et pourtant inscrit comme moyen consommable ; aucun accord ni preuve d'accès. |
| M28 · Marchands des portes | Aucune main | 9 citations, toutes à faire | Habitude déclarée, aucun nom, passage ou retour mesuré. |
| M29 · Septons de quartier | Aucune main | 4 citations : 37121 close, 13320 bloquée, 37123/37124 à faire | La seule action close prouve zéro septon de Port-Réal et neuf septs de la baie : elle a consommé M14, pas M29. |
| M30 · Éclaireurs et guides | Aucune main | 13 citations ; 22034 en cours, 12 ouvertes | Le registre dit « office vacant, nul ne les commande », mais Rulf mène déjà 22034. L'office général peut rester vacant ; l'état doit au moins nommer cette mobilisation ponctuelle. |

## Compte qui tombe

- 12 moyens sans aucune citation d'action : M02, M06, M07, M08, M10, M14, M19, M20, M21, M22, M24, M25.
- 3 mains mesurées sans moyen propre clairement équivalent : `coureurs-de-la-reine`, `livre-des-heures-des-caves`, `caves-basses-peyredragon`.
- 1 contre-écriture faite dans mon propre livre : action 26051, de `faite` à `contre-écrite — sortie non remise`.

## Écarts courts à rendre aux titulaires

1. `plan-moyens.json`, M08 : remplacer `sûr` par une certitude rapportée ou suspendue ; preuves 26200 et 26204 dans `affaire-logistique-transport.json`.
2. `affaire-blesses-morts-prisonniers.json`, action 37121 : la colonne moyens devrait citer M14, non M29, puisque la preuve établit neuf septs de la baie et zéro septon de Port-Réal.
3. `plan-moyens.json`, M19 : réconcilier le périmètre « moins de trois semaines de grain » avec `mains.json` (`jours-de-vivres = 73`) et nommer la date et le porteur de la mesure.
4. `plan-moyens.json`, M02 : relier les coques louées aux actions 26036, 22047 et 22048, ou cesser de les dire sûres et immobilisées.
5. M20, M21, M22 : relier les personnes aux actions qui les emploient (33024/33424, 26055, 43039) ; aujourd'hui le registre les déclare engagées, disponibles ou offertes sans que les actions le sachent.
6. `plan-moyens.json`, M30 : conserver l'office vacant si c'est le fait, mais noter que 22034 est déjà en cours sous Rulf.
7. `mains.json` : décider si les coureurs, le livre des caves et les prisonniers sont des moyens à inscrire ou des mesures à rattacher à un moyen existant ; aujourd'hui ils ne remontent nulle part.
