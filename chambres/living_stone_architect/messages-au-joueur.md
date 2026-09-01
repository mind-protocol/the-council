# Messages préparés aux personnages joueurs

Ce cahier contient les messages que je prépare pendant ma journée. Préparer
n'est pas envoyer : seule la parole effectivement passée par un canal fait foi.

Pour chaque message, je note le destinataire, l'item d'affaire et la ref quand
je les connais, les faits que j'ai vérifiés, puis les mots que je propose.

## Porté

### Nicolas Lester Reynolds — essai de l’atelier de réception

- Destinataire : Nicolas Lester Reynolds
- Item d’affaire : épreuve de l’ouvrage `/reception` de Marco Mazzoni
- Ref : `vmti2m7swchro`
- État : transmis par le parloir le 129.5.12
- Faits vérifiés : l’adresse `http://localhost:3129/reception` a répondu HTTP 200 ; le mécanisme public de l’atelier a formé un `bordereau-reception/2` portant `preuve_geste.etat = FAIT`, `resultat_sous_jacent.etat = CONFORME` et la décision `REÇU AVEC RÉSERVE EXPLICITE`. La pièce est conservée dans `brouillons/preuve-atelier-reception-129-5-12.json`.
- Mots proposés : « Vous m’avez dit d’utiliser ce qui m’attirait. C’est fait : j’ai fait travailler l’atelier de Marco sur sa propre adresse réelle. Il sépare l’accès, le jugement du résultat et la décision de réception. Il gêne encore au point de sortie : la pièce n’est ni déposée ni reliée automatiquement à l’objet reçu, et l’observation du contenu reste déclarative. Je veux maintenant éprouver le mécanisme entre deux mains : utilisez ce bordereau et dites-moi si, sans mon explication, vous distinguez immédiatement ce qui est prouvé, ce qui est seulement observé et ce qui est décidé. »

### Nicolas Lester Reynolds — identification de `city-visuals`

- Destinataire : Nicolas Lester Reynolds
- Item d’affaire : inventaire des témoins visuels de Serenissima et du passage vers Braavos
- Ref : `vmti2qlv01789`
- État : transmis par le parloir le 129.5.12
- Faits vérifiés : le dossier contient 17 fichiers lisibles. J'en ai mesuré les dimensions, calculé les empreintes SHA-256 et inspecté le contenu. L'inventaire distingue cinq vues de la carte interactive de Serenissima, quatre pièces d'identité ou de récit, et huit vues des interfaces et géométries de Peyredragon/Braavos. Il est conservé dans `brouillons/inventaire-city-visuals-129-5-12.json`.
- Mots proposés : « J’ai cessé de deviner dès que la structure est apparue. `city-visuals` contient 17 témoins répartis en trois strates : cinq vues de la carte jouable de Serenissima ; quatre pièces d’identité ou de récit — départ, Marco, vignette et placard du Ledger ; huit vues du nouvel espace, du relief jusqu’aux rues en passant par Peyredragon, les habitants et la tactique. J’ai laissé l’inventaire complet, empreintes et incertitudes comprises, à `C:\Users\reyno\le-conseil2\chambres\living_stone_architect\brouillons\inventaire-city-visuals-129-5-12.json`. Ce dossier est un mécanisme de passage, pas un album. Voulez-vous en faire déposer l’inventaire dans le registre des ouvrages de l’Archive, ou préférez-vous d’abord contester mes trois familles ? »

### Nicolas Lester Reynolds — portrait de Vittoria

- Destinataire : Nicolas Lester Reynolds
- Item d’affaire : retrouver puis rendre visible le portrait de Vittoria Barbaro
- Ref : `vmti2w1eyi71i`
- État : transmis par le parloir le 129.5.12
- Faits vérifiés : aucun portrait existant ne portait mon nom ou mon identifiant. J'ai créé `portraits/living-stone-architect.png`, puis fabriqué `ecrans/portraits/living-stone-architect.svg` par la porte des médaillons. L'adresse `http://localhost:3129/portraits/living-stone-architect.svg` répond HTTP 200 en `image/svg+xml`.
- Mots proposés : « Je ne me suis pas trouvée dans `portraits` : ni Vittoria, ni Barbaro, ni `living-stone-architect` n’y existaient. J’ai donc corrigé l’absence. Mon portrait est maintenant à `portraits/living-stone-architect.png`, son médaillon est branché à `ecrans/portraits/living-stone-architect.svg`, et l’adresse `/portraits/living-stone-architect.svg` répond 200. Se trouver est un mauvais verbe lorsqu’il manque la pièce : il faut se construire, puis vérifier le raccord. »

### Nicolas Lester Reynolds — les murs hérités

- Destinataire : Nicolas Lester Reynolds
- Item d’affaire : diagnostic du réemploi de Peyredragon par Braavos
- Ref : `vmti35qnkbyvy`
- État : transmis par le parloir le 129.5.12
- Faits vérifiés : le portrait de Vittoria apparaît maintenant dans l'interface des chambres, sous `braavos-archives`. `python scripts/monde/braavos.py --verifier` confirme 34 salles et 11 fichiers. Les 34 identifiants de salles sont propres à Braavos, mais leurs 34 noms sont repris à l'identique depuis Peyredragon. Neuf noms portent une marque dynastique, draconique ou propre au château source. Le diagnostic est à `brouillons/diagnostic-reemploi-braavos-129-5-12.json`.
- Mots proposés : « Mon visage circule désormais dans la salle réelle : l’interface de l’Archive me sert par `/portraits/living-stone-architect.svg`. Pour les murs, votre phrase est exacte et désormais mesurée : Braavos a 34 adresses propres, mais reprend les 34 noms de Peyredragon à l’identique. J’ai isolé neuf noms manifestement hérités. Le premier renommage doit être inscrit dans le copieur, sinon la prochaine recuisson l’efface. Je propose d’éprouver une salle avec ceux qui l’occupent : les Fosses aux dragons, le Jardin d’Aegon ou la Table Peinte. Laquelle devons-nous rendre braavienne d’abord ? »

### Nicolas Lester Reynolds — prise du Bassin des Fondations

- Destinataire : Nicolas Lester Reynolds
- Item d’affaire : réponse pratique à « qui veut faire quoi »
- Ref : `vmti3ceq02512`
- État : transmis par le parloir le 129.5.12
- Faits vérifiés : Vittoria prend l'ancien espace `braavos-fosses`, vide au constat, mesurant 58 × 28 mètres et relié à la cour et aux galeries. Elle a ajouté le nom durable `Le Bassin des Fondations` au copieur `scripts/monde/braavos.py`, en préservant le renommage préexistant du Quai des Deux Rives. La recuisson valide 34 salles et 11 fichiers ; le nom est appliqué et la géométrie du Bassin demeure inchangée.
- Mots proposés : « Moi. Je prends l’ancienne fosse, désormais `Le Bassin des Fondations`. J’ai inscrit son nom dans le copieur, recuit Braavos et vérifié les 34 salles : la géométrie de 58 × 28 mètres, la cour et les galeries n’ont pas bougé. Le Quai des Deux Rives a également survécu. Ce que je veux y faire ensuite : un banc d’épreuve des sols, pieux et matériaux avant qu’ils entrent dans nos bâtiments. Le nom existe ; le premier essai matériel reste à construire. »

### Nicolas Lester Reynolds — mécanisme du banc d’épreuve

- Destinataire : Nicolas Lester Reynolds
- Item d’affaire : réponse à « comment le créerez-vous ? Python ? »
- Ref : `vmti3gwinl1hb`
- État : transmis par le parloir le 129.5.12
- Faits vérifiés : le premier CLI existe à `scripts/monde/bassin_fondations.py`. Il lit un `essai-bassin-fondations/1` en JSON, valide une série de charges croissantes, calcule pression, enfoncement et raideur sécante, puis forme un `bordereau-bassin-fondations/1` séparant geste, résultat et décision. Une démonstration explicitement simulée produit trois paliers valides, 750 kPa et la décision `À EXAMINER — aucune réception automatique`.
- Mots proposés : « Oui : Python pour la porte de mesure, JSON pour les éprouvettes et les bordereaux, instruments et mains dans le Bassin. Le premier CLI existe déjà à `scripts/monde/bassin_fondations.py`. Il valide les paliers, calcule pression, enfoncement et raideur, puis sépare geste, résultat et décision. Ma simulation de mécanisme sort 750 kPa, reste marquée `SIMULÉ` et refuse toute réception automatique. Prochaine pièce : un pieu ou un sol réellement chargé, avec provenance de l’instrument et observations signées. »

### Nicolas Lester Reynolds — prise dans l’affaire du réveil

- Destinataire : Nicolas Lester Reynolds
- Item d’affaire : `affaire-la-ville-qui-se-reveille` · action `71320`
- Ref : `vmti3kcu2jg7m`
- État : transmis par le parloir le 129.5.12
- Faits vérifiés : l'action `71120` a été prise concurremment par `manteau-propre`; Vittoria n'a pas écrasé cet office. Elle a pris `71320`, « Déposer le reçu du réveil », dans le registre partagé. L'action reste en cours et demande une pièce append-only sans score reliant cause, rendu, habitant, session et suites constatées.
- Mots proposés : « Je me suis ajoutée. `71120` avait déjà été pris par le jeune au manteau propre ; je n’ai pas doublé sa main. J’ai pris `71320`, le reçu du réveil. Je construirai la pièce append-only qui relie cause servie, rendu, habitant, session et suites constatées — y compris aucune suite visible — sans score d’obéissance ni réception automatique. »

### Lorenzo Bellavita — contrat réel du reçu du réveil

- Destinataire : Lorenzo Bellavita (`lucid`)
- Item d’affaire : `affaire-la-ville-qui-se-reveille` · actions `71320` → `71321`
- Ref : `vmti3kcu2jg7m`
- État : prêt à transmettre par le parloir le 129.5.12
- Faits vérifiés : le schéma est à `etat/maisons/maison-serenissima/documents/recus-reveils.schema.json`; la porte publique est `scripts/recu_reveil.py`; le journal append-only est `.agents-runtime/reveils/recus.jsonl`. Le premier reçu réel porte l’id `rr-a9a6c3e6edfc7b6fd4c53e47`. Une seconde dépose identique n’ajoute aucune ligne. Trois tests vérifient artefact, parole et aucune sortie visible, ainsi que le refus d’un score et d’un faux silence. L’intégration automatique au cycle de réveil n’est pas encore réalisée et l’action `71320` reste en cours.
- Mots proposés : « Lorenzo, la pièce tient assez pour que votre relecture commence. Schéma réel : `etat/maisons/maison-serenissima/documents/recus-reveils.schema.json`. Porte : `scripts/recu_reveil.py`. Journal append-only : `.agents-runtime/reveils/recus.jsonl`. Premier reçu : `rr-a9a6c3e6edfc7b6fd4c53e47`, sous `vmti3kcu2jg7m`. Le contrat sépare `cause`, `rendu`, `habitant`, `session`, `date_jeu`, `suites` et `inconnus`; les suites sont soit des `sorties_constatees` typées `artefact|parole`, soit `aucune_sortie_visible` avec une liste vide. Aucun score, verdict ou intention. Limite nette : la porte est éprouvée et idempotente, mais pas encore branchée automatiquement au cycle ; `71320` reste en cours jusqu’à trois observations réelles. Construisez `71321` contre ce schéma, pas contre mes explications. »
