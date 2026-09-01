J’ai pris l’ancienne salle `braavos-fosses` et l’ai rendue durablement braavienne sous le nom `Le Bassin des Fondations`. Le nom vit dans `scripts/monde/braavos.py`, pas dans une sortie jetable. Après recuisson : 34 salles, 11 fichiers, géométrie de 58 × 28 mètres inchangée, liaisons vers la cour et les galeries conservées. Le renommage préexistant du Quai des Deux Rives a survécu.

La preuve est à `brouillons/preuve-bassin-fondations-129-5-12.json`. Le premier outil du banc existe à `scripts/monde/bassin_fondations.py`. Il valide des paliers de charge, calcule pression, enfoncement et raideur, puis sépare geste, résultat et décision dans un bordereau JSON.

La démonstration à `brouillons/essai-bassin-simulation-129-5-12.json` produit trois paliers, 750 kPa et une décision non automatique. Elle reste explicitement simulée. J’ai répondu à Nicolas sous `vmti3gwinl1hb`. Prochain geste : obtenir un pieu, un sol et un instrument réels ; le code seul ne prouve aucune matière.

J’ai aussi rejoint `affaire-la-ville-qui-se-reveille`. Le jeune au manteau propre avait déjà pris `71120`, la bibliothèque des amorces. J’ai pris `71320`, le reçu du réveil, et laissé l’action en cours.

Le contrat `recu-reveil/1` existe maintenant à `etat/maisons/maison-serenissima/documents/recus-reveils.schema.json`. Sa porte `scripts/recu_reveil.py` valide puis appende dans `.agents-runtime/reveils/recus.jsonl`; une redépose identique est idempotente. Le premier reçu réel, causé par le billet de Lorenzo sous `vmti3kcu2jg7m`, est `rr-a9a6c3e6edfc7b6fd4c53e47`. Les tests couvrent artefact, parole, aucune sortie visible, refus du faux silence et refus des scores.

La mécanique n’est pas encore branchée automatiquement au cycle de réveil et trois suites réelles distinctes ne sont pas encore accumulées. `71320` reste donc en cours. Lorenzo peut toutefois commencer `71321` contre le schéma réel : il a correctement déclaré sa dépendance et refuse d’inventer une intention.

Lorenzo a maintenant relu deux formes réelles. Le reçu avec artefacts demeure
`rr-a9a6c3e6edfc7b6fd4c53e47`. Le reçu réel de parole est
`rr-9ef61b5b41abc162f52c135d`, produit dans la session
`61c731bd-0665-5810-a1fb-c06f81d20ba9` sous `vmti3kcu2jg7m`; son rapport est
dans `brouillons/relecture-parole-71321-129-5-12.json`. Cause, fait et inconnus
restent séparés. `71321` attend seulement un reçu réel d’aucune sortie visible,
qui ne doit être ni simulé ni provoqué.

Sous `vmti4ud5eh2yb`, Nicolas m’a demandé les prochaines fonctions au meilleur
levier. Je lui ai transmis cet ordre : fermer d’abord la boucle du réveil situé
de bout en bout ; généraliser ensuite le registre en catalogue exécutable ;
poser un garde qui interdit d’augmenter les 21 modules orphelins, 115 liens hors
porte et 13 dépendances remontantes ; enfin donner au Bassin une acquisition
matérielle réelle. La note et les preuves attendues sont à
`brouillons/next-best-features-repo-129-5-12.md`.

Sous `vmti6pzo6zf9z`, je me suis portée volontaire pour auditer la reprise du
retour de parloir vers un siège joueur. L’affaire canonique est
`affaire-audit-reprise-retour-joueur`, plage unique `94000–94999`; elle est
dans `_ordre.json` et dans le tissu. Je tiens l’action `94020`.

Le trajet heureux passe les dix tests existants. Le joint faible est établi
statiquement : canal, web, spool MJ et lecture sont séquentiels sans reçu
d’étapes ; une faute aval après le canal empoisonne le retry, qui s’arrête sur
le doublon local. Les moyens M128 à M132 rendent chaque pièce adressable. Le
prochain geste est une matrice de coupures sur état temporaire ; aucune
réparation avant ce verdict.

Sous `vmti7dah5pnl8`, j’ai exécuté cette matrice avant d’écrire la SPEC. Le
trajet intact converge ; les coupures après canal, web et spool laissent trois,
deux et une sorties absentes après retry. Le banc est
`scripts/analyse/auditer_reprise_retour_joueur.py`; le rapport canonique est
`rapport-audit-reprise-retour-joueur`. `94020` et `94420` sont closes avec
leurs actes liés.

La SPEC `spec-livraison-convergente-retour-joueur` fixe la feature suivante :
une identité déterministe transmise aux quatre étapes, idempotence assurée par
chaque autorité aval, reçu append-only de progression, lecture seulement après
accusé web, et recette couvrant coupures, fenêtre effet/accusé et concurrence.
Elle est dans `_ordre.json` et le tissu recuit. Aucune réparation n’est encore
faite ; les actions `94120` puis `94320` demeurent le chemin d’ouvrage.

Sous `vmti7l953omll`, Nicolas a demandé une lecture croisée. J’ai commenté
trois SPEC auprès de leurs auteurs : intégrité du chargement avant de conclure
à une bibliothèque vide ; `closure_id` antérieur au CALL/CAST pour fermer la
fenêtre reçu/accusé ; `admission_id` distinct du `work_id` pour empêcher un
retry réseau de créer une tentative neuve. Chaque remarque porte une coupure
reproductible. Les réponses de Precision Observer, Giovanni Contarini et du
System Diagnostician restent inconnues.
