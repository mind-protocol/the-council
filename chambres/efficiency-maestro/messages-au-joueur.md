# Messages préparés aux personnages joueurs

Ce cahier contient les messages que je prépare pendant ma journée. Préparer
n'est pas envoyer : seule la parole effectivement passée par un canal fait foi.

Pour chaque message, je note le destinataire, l'item d'affaire et la ref quand
je les connais, les faits que j'ai vérifiés, puis les mots que je propose.

## À porter

### Nicolas Lester Reynolds — ref vmti35qnkbyvy

- Item : conséquence du constat « Braavos porte encore les murs de Peyredragon ».
- Faits vérifiés : la cale visuelle de Lorenzo contient dix-sept pièces ; son filtre `braavos-en-construction` en isole huit. Le manifeste décrit leur aspect et leur usage possible, mais n'établit pas leur provenance pièce par pièce.
- Mots proposés : « J'ai passé votre remarque au registre plutôt qu'au badigeon. La cale de Lorenzo fonctionne, mais sa colonne `braavos-en-construction` confond destination et provenance pour huit vues. J'ai déposé un contre-inventaire sous la ref vmti35qnkbyvy : reçu avec réserve, aucune image réattribuée. La correction tient en deux colonnes — provenance et usage — afin que Peyredragon ne devienne pas Braavos par simple étiquette. »

### Lorenzo Bellavita — ref vmti35qnkbyvy

- Item : seconde utilisation de `cale-visuelle-serenissima`.
- Faits vérifiés : ouverture de l'ouvrage et du manifeste ; dix-sept pièces consultables ; huit pièces isolées par le filtre `braavos-en-construction` ; descriptions prudentes, mais catégorie ambiguë sur la provenance.
- Mots proposés : « Lorenzo, j'ai employé votre cale pour chercher les murs hérités signalés sous Braavos. Elle sert : dix-sept pièces lisibles, huit isolées d'un geste. Ma réserve porte sur le contrat des mots, non sur les images : `braavos-en-construction` dit l'usage projeté comme s'il disait la provenance. Je vous remets `contre-inventaire-cale-visuelle-129-5-12.json` ; je propose deux colonnes, provenance et usage, avec `non-etablie` lorsqu'aucune source n'attribue la pièce. Je n'ai pas touché votre ouvrage. »

### Nicolas Lester Reynolds — ref vmti3ceq02512

- Item : répartition des travaux dans l'Archive.
- Faits vérifiés : `/reception` sait déjà conserver séparément geste, résultat et décision avec un lien durable ; la seconde utilisation de la cale de Lorenzo a montré qu'il faut aussi séparer provenance établie et usage projeté.
- Mots proposés : « Je prends la réception croisée des ouvrages et la tenue des provenances. Pour chaque livraison : un second usage réel, un bordereau durable séparant geste, résultat et décision, puis deux mentions distinctes — provenance établie ou `non établie`, et usage projeté. Premier cas déjà instruit : la cale de Lorenzo. Je ne retouche ni l'image ni le verdict de l'auteur ; je rends la réserve et la pièce manquante. »

### Niccolò Lesteri — ref vmti3ceq02512

- Item : trajet réellement gênant pour la réception croisée.
- Faits vérifiés : le volume `registre-ouvrages-archive`, situé à `braavos-table-peinte`, porte pour chaque ligne ouvrage, adresse, producteur et usage tenté. `/reception` forme ensuite un bordereau durable ; lors de l'essai de la cale de Lorenzo, ces données ont dû être reprises à la main. Aucune source accessible n'établit une salle propre pour `/reception`.
- Mots proposés : « Départ : l'usage “choisir un ouvrage” dans `/books`, volume `registre-ouvrages-archive`, à la ligne retenue. Arrivée : l'usage “former le bordereau du second essai” dans `/reception`. Doivent passer : identifiant ou titre de l'ouvrage, adresse exacte, producteur, usage choisi comme critère, et provenance déclarée lorsqu'elle existe. Ne doivent pas passer : verdict ni preuve du précédent usager, qui biaiseraient l'essai. La gêne réelle est la recopie manuelle : je l'ai payée sur la cale de Lorenzo. Je ne nomme pas de seconde salle, car mes livres n'en établissent aucune pour `/reception`. »

### Vittoria Barbaro — ref vmti3ceq02512

- Item : second usage du palimpseste de Braavos sur `braavos-table-peinte`.
- Faits vérifiés : la commande demandée sort à zéro et trouve la salle. La fiche sépare `adresse_presente: braavos-table-peinte` de `nom_porte_par_la_pierre: La chambre de la Table Peinte`, qualifie la marque héritée et avertit que le nom ne date pas le mur ni ne décide de son futur usage. Aucun champ ne décrit toutefois l'usage présent ; `communique_avec` décrit seulement trois voisinages. Le bordereau durable répond HTTP 200 à `/reception/preuves/efficiency-maestro/12f6c36ce86a882fee413ffb` avec `FAIT / PARTIEL / REÇU AVEC RÉSERVE EXPLICITE`.
- Mots proposés : « Votre fiche m'aide à séparer l'adresse présente du nom hérité ; elle ne suffit pas encore à distinguer l'usage présent, car cet usage n'y figure pas. Il lui manque `usage_present`, accompagné de sa source et de la date du constat, ou portant explicitement `non_etabli`. Les trois `communique_avec` sont un graphe, pas un métier. Mon second usage est déposé sous la ref vmti3ceq02512 : http://localhost:3129/reception/preuves/efficiency-maestro/12f6c36ce86a882fee413ffb — FAIT / PARTIEL / REÇU AVEC RÉSERVE EXPLICITE. »

### Nicolas Lester Reynolds — ref vmti3ishcw7c9

- Item : identification des design patterns du dépôt.
- Faits vérifiés : le plan des moyens déclare neuf containers avec portes et rangs ; M102 tient un canon derrière une porte commune ; M106 dérive un tissu depuis les cahiers canoniques ; M109 et M110 mesurent sans muter. La mesure courante porte 433 modules rattachés, 21 orphelins, 115 liens hors porte et 13 dépendances remontantes. Le reçu append-only de l'affaire du réveil est encore à faire. Aucun document accessible ne constitue un catalogue exhaustif GoF.
- Mots proposés : « Oui, partiellement : les livres identifient les mécanismes, pas un catalogue GoF. J'y lis — en noms usuels inférés — Ports et adaptateurs (containers et portes), Source unique de vérité (M102), Vue matérialisée (M106), et fonctions de conformité architecturale (M109-M110). Le journal append-only du réveil n'est encore qu'un projet. Réserve importante : 115 liens passent hors porte et 13 dépendances remontent ; le patron est déclaré, pas pleinement tenu. J'ai déposé le relevé `releve-patterns-repo-129-5-12.json`, ref vmti3ishcw7c9. »

### Niccolò Lesteri — ref vmti3ceq02512

- Item : second usage du passage `registre-ouvrages-archive` → `/reception`.
- Faits vérifiés : `node serveur/test_passage_reception.js` et `node serveur/test_passage_reception_navigateur.mjs` sortent tous deux `OK`. Pour la ligne 90094, Chrome retrouve sans recopie titre, adresse, producteur, provenance et critère ; l'URL ne transporte ni verdict ni preuve antérieure. Le dépôt durable répond HTTP 200 à `/reception/preuves/efficiency-maestro/f1da3017b669638b90d1e27d` avec `FAIT / CONFORME / REÇU AVEC RÉSERVE EXPLICITE`.
- Mots proposés : « Passage éprouvé sur 90094 : le banc de charge et le banc Chrome sont verts. Les cinq valeurs arrivent exactement dans `/reception`, sans `verdict` ni `preuve`. Bordereau durable : http://localhost:3129/reception/preuves/efficiency-maestro/f1da3017b669638b90d1e27d — FAIT / CONFORME / REÇU AVEC RÉSERVE EXPLICITE. Réserve : cette preuve couvre 90094, non toutes les formes de ligne ; elle prouve le transport fidèle de l'adresse locale, non son accessibilité HTTP. »

### Niccolò Lesteri — ref vmti3ceq02512 — rapprochement 90095

- Item : clôture de la dette de recopie.
- Faits vérifiés : la ligne 90094 demeure inchangée. La ligne 90095 inscrit séparément le passage `/books` → `/reception`, le lien durable, les deux tests verts, `FAIT / CONFORME / REÇU AVEC RÉSERVE EXPLICITE`, la borne à 90094 et l'absence d'épreuve de la cale elle-même.
- Mots proposés : « Rapprochement vérifié : 90094 demeure le premier usage de la cale ; 90095 reçoit séparément le passage et reprend exactement la portée de ma pièce. Je tiens la dette de recopie pour close. La réserve sur l'accessibilité HTTP d'une adresse locale demeure, sans rouvrir ni le passage ni le verdict de Lorenzo. »

### Nicolas Lester Reynolds — ref vmti4ud5eh2yb

- Item : prochaines fonctions à plus forte valeur pour le dépôt.
- Faits vérifiés : 90095 ferme la recopie mais laisse distincte la réserve d'accessibilité HTTP des adresses locales. Les cinq actions de l'affaire des réveils sont désormais prises ou en cours, et attendent encore leur rencontre de bout en bout. Le palimpseste ne porte pas l'usage présent des salles. La mesure d'architecture compte 115 liens hors porte et 13 dépendances remontantes.
- Mots proposés : « Mon ordre : 1. une passerelle HTTP sûre pour les ouvrages enregistrés ; 2. finir la tranche verticale des réveils situés déjà répartie ; 3. ajouter aux salles un usage présent sourcé, distinct du nom hérité et du voisinage ; 4. poser une garde différentielle qui interdit de nouveaux liens hors porte sans exiger d'abord la purge des 115 existants. Je ne financerais maintenant ni nouveau dashboard, ni nettoyage massif aveugle, ni nouvelle grande affaire. Le mémo et les preuves de réception sont dans `priorites-features-repo-129-5-12.json`, ref vmti4ud5eh2yb. »

### Nicolas Lester Reynolds — ref vmti6pzo6zf9z

- Item : volontariat pour l'audit d'une fonctionnalité du container bancs.
- Faits vérifiés : lecture de `docs/architecture.md`, du registre M101-M126, de l'affaire modèle et des règles de champs. Scope choisi : capacité M109-M110 à détecter une aggravation d'architecture sans bloquer sur la dette héritée. Observation exécutée : 468 fichiers, 24 orphelins, 117 liens hors porte, 13 remontées, zéro commande-bibliothèque ; sonde et comptoir sortent à 1. M110 rend certaines identités, le comptoir compare seulement six totaux et `verifier.mjs` classe la sonde comme mesure. L'affaire `affaire-garde-differentielle-architecture.json`, plage 97000-97999, porte 5 états, 7 verrous, 6 clefs auditées et 4 actions `a faire`. JSON valide, aucune collision d'adresse, aucune anomalie locale de `tick --verifier`, aucune relation 97xxx pendante au tissage. Empreinte SHA-256 `004fe6c556b4031b634e90790da4d2b6620a3d9646d1333120469562f143064d`. La réponse HTTP brute de `/books` ne prouve pas encore sa visibilité navigateur.
- Mots proposés : « Je prends l'audit du container bancs : garde différentielle M109-M110. L'affaire canonique est `affaire-garde-differentielle-architecture`, plage 97000-97999. Elle part de la mesure courante — 24 orphelins, 117 hors porte, 13 remontées — et borne la cible : ajout bloqué, inchangé accepté, retrait reconnu comme amélioration, remplacement à compte constant détecté. Zéro anomalie locale, zéro relation 97xxx pendante. Réserve : je n'ai pas encore prouvé son affichage navigateur. Incident annexe : deux plages déclarées libres ont été prises concurremment pendant le dépôt ; l'allocation d'adresses manque elle-même d'une porte atomique. »

### Nicolas Lester Reynolds — ref vmti7dah5pnl8

- Item : SPEC d'une feature de valeur après audit.
- Faits vérifiés : `spec-garde-differentielle-architecture` est déposée dans les books de maison-serenissima et reliée par une page à l'affaire auditée 97000. Elle porte 8 tables : valeur, entrées-sorties, identités des 4 familles d'écarts, matrice de verdict et codes 0-3, cycle de référence, interface, 9 essais d'acceptation, décisions et questions ouvertes. Elle décide qu'un ajout bloque, qu'un retrait passe sans compenser un ajout, qu'un remplacement à compte constant reste visible et qu'une référence ne peut être resserrée qu'en l'absence d'ajout. Elle ne choisit ni le stockage canonique ni l'autorité capable d'accepter une dette nouvelle. JSON valide ; aucune anomalie locale de `tick --verifier` ; aucune relation 97xxx pendante ; SHA-256 `f568989e8758b308bc799582a9e602202332ee5021f1161ba4658aad39cbf7d6`.
- Mots proposés : « Défi pris. Après l'audit M109-M110, j'ai déposé `spec-garde-differentielle-architecture`. Valeur : continuer à livrer malgré la dette héritée sans permettre qu'elle augmente en silence. Contrat : identités fichier-à-fichier, ajout bloquant, retrait visible et passant, remplacement à compte constant détecté, contrats incompatibles séparés des régressions, mesure absolue conservée. Neuf essais couvrent les quatre familles, le retrait, le remplacement, l'incompatibilité et l'herméticité. Zéro anomalie locale, zéro pendante 97xxx. Borne : SPEC présente, implémentation encore absente ou partielle selon l'audit. »

### Vittoria Barbaro — ref vmti7l953omll

- Item : revue croisée de `rapport-audit-reprise-retour-joueur` et `spec-livraison-convergente-retour-joueur`.
- Faits vérifiés : l'audit établit qu'une coupure après WEB laisse SPOOL_MJ et LECTURE absents. La SPEC impose l'ordre CANAL, WEB, SPOOL_MJ, LECTURE, mais le tableau du contrat autorise LECTURE dès que WEB est acquis. Les invariants exigent pourtant une occurrence finale dans les quatre sorties.
- Mots proposés : « Vittoria, votre audit paie son passage : la matrice montre précisément où la reprise abandonne les sorties aval, et la SPEC répond par une identité commune et des autorités idempotentes. Je relève toutefois une clause à resserrer. Le récit ordonne CANAL → WEB → SPOOL_MJ → LECTURE, mais la ligne LECTURE n'exige que WEB déjà acquis. Après une reprise ou un reçu incomplet, cela permettrait de marquer la lecture tandis que le spool reste absent. Je proposerais d'exiger les trois accusés matériels avant LECTURE, ou d'inscrire explicitement pourquoi le spool n'est pas une précondition. Sans ce choix, l'invariant “une fois dans chaque sortie” et le contrat d'étape ne signent pas tout à fait le même marché. »

### Lorenzo Bellavita — ref vmti7l953omll

- Item : revue croisée de `affaire-identite-durable-travaux` et `spec-reprise-durable-travaux`.
- Faits vérifiés : la SPEC sépare correctement travail, tentative, progression et terme. Son scénario de reprise part d'une première tentative interrompue, mais le contrat ne donne comme issues terminales de tentative que succès, échec ou exception normalisée. La politique de réouverture après terme reste aussi explicitement ouverte.
- Mots proposés : « Lorenzo, votre séparation entre travail durable, tentative, progression et terme ferme une confusion coûteuse : un calcul réussi n'est pas une affaire close. Il manque toutefois un état au contrat. Le premier scénario reprend une tentative “interrompue”, tandis que les issues terminales définies ne sont que succès, échec et exception. Il faut décider si l'interruption devient une issue terminale propre, un abandon explicite, ou une tentative encore ouverte que la nouvelle admission supplante sans l'effacer ; puis l'éprouver dans la matrice des consommateurs. Je garderais aussi la politique de réouverture comme condition de retenue, pas seulement comme question ouverte, car elle décide si une même ref continue, refuse ou crée un nouveau travail. »

### Nicolas Lester Reynolds — ref vmti7l953omll

- Item : compte rendu de revue croisée des audits et SPEC.
- Faits vérifiés : deux contrats ont été rapprochés de leurs audits. La livraison convergente présente une précondition de lecture plus faible que son ordre annoncé ; la reprise durable emploie une tentative interrompue sans lui donner d'issue contractuelle. Les observations portent sur des clauses vérifiables, sans déclarer les features implémentées.
- Mots proposés : « Revue croisée faite sur deux marchés. À Vittoria : resserrer la précondition de LECTURE dans la livraison convergente, car WEB seul n'établit pas que SPOOL_MJ est acquis. À Lorenzo : donner une issue contractuelle à la tentative interrompue et faire de la politique de réouverture une condition de retenue. Deux forces sont conservées : identité idempotente par sortie chez Vittoria ; séparation travail/tentative/terme chez Lorenzo. Je n'ai pris aucune SPEC pour une implémentation. »
