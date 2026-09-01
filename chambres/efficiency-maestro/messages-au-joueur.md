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
