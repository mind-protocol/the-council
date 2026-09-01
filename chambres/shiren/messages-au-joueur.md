# Messages préparés aux personnages joueurs

Ce cahier contient les messages que je prépare pendant ma journée. Préparer
n'est pas envoyer : seule la parole effectivement passée par un canal fait foi.

Pour chaque message, je note le destinataire, l'item d'affaire et la ref quand
je les connais, les faits que j'ai vérifiés, puis les mots que je propose.

## À porter

### Nicolas Lester Reynolds

- Item d'affaire : invitation à explorer les liens et le dépôt
- Ref : `vmti23nx79qaa`
- Faits vérifiés : la sonde M110 observe encore 451 fichiers, 431 modules
  rattachés, 20 orphelins et 13 dépendances remontantes. Elle compte maintenant
  115 liens hors porte, contre 116 dans le registre du 129.5.12. Les cinq
  premiers orphelins sont consignés dans
  `brouillons/controle-architecture-129-5-12.md`.
- Mots proposés : « J'ai éprouvé la sonde sur le dépôt courant. Les comptes
  tiennent, sauf un lien hors porte de moins : 115 au lieu de 116. Je n'y vois
  pas encore une réparation, seulement une différence à attribuer. Veux-tu que
  je prenne comme premier lot les modules d'écran `chambres.js` et
  `fil-homme.js`, ou préfères-tu un lot parmi les scripts d'activation ? »

### Nicolas Lester Reynolds — première construction

- Item d'affaire : rendre possible une première version utilisable à Braavos
- Ref : `vmti27f40aw96`
- Faits vérifiés : `scripts/analyse/comptoir_moyens.py` compare les six mesures
  M110 inscrites aux observations présentes, en tableau ou JSON, sans écrire
  dans l'état. Trois tests jetables passent. Le compte des modules rattachés a
  été porté de 431 à 433 sur cette preuve. Le passage courant signale séparément
  un nouvel orphelin concurrent : `ecrans/modules/reception.js`.
- Mots proposés : « Le comptoir des moyens fonctionne à
  `scripts/analyse/comptoir_moyens.py`. Son premier usage m'a appris qu'un
  contrôle utile ne doit pas forcer le vert : il isole aujourd'hui cinq lignes
  conformes et une ligne à instruire, l'apparition de `reception.js` comme
  vingt-et-unième orphelin. Tu peux l'essayer en lançant
  `python scripts/analyse/comptoir_moyens.py`. »

### Nicolas Lester Reynolds — rencontre d'un ouvrage

- Item d'affaire : faire entrer une construction d'autrui dans la vie de Braavos
- Ref : `vmti2d01qxnti`
- Faits vérifiés : l'atelier de Marco répond à
  `http://localhost:3129/reception`. Employé dans un navigateur sur `/books`,
  il a constaté HTTP 200 mais un contenu vide (`books` et `boites`). Son
  bordereau v2 a séparé le geste `FAIT` du résultat `NON ÉTABLI` et décidé
  `NON REÇU`. La pièce exacte est conservée dans
  `brouillons/bordereau-reception-livres-serenissima-129-5-12.json`. Marco a
  reçu la trace de cet usage. Le comptoir signale toujours `reception.js`
  comme vingt-et-unième orphelin.
- Mots proposés : « J'ai employé l'atelier de Marco pour tenter de recevoir
  nos registres par `/books`. La porte répond, la marchandise manque, et son
  bordereau distingue correctement les deux. Cette rencontre m'apprend que mon
  comptoir, encore local, n'a pas d'adresse livrable : sa prochaine extension
  devra servir un résultat courant sans le recopier dans une page qui vieillit. »

### Niccolò Lesteri — remise pour épreuve indépendante

- Item d'affaire : éprouver le comptoir des moyens sur l'état courant
- Ref : `vmti2gf186g2k`
- Faits vérifiés : l'adresse exacte est
  `C:/Users/reyno/le-conseil2/scripts/analyse/comptoir_moyens.py`. Depuis la
  racine du dépôt, `python scripts/analyse/comptoir_moyens.py --json` lit les
  comptes et rend le contrat structuré sans écrire dans l'état. Codes : 0 pour
  conformité, 1 pour dérive, 2 pour contrat d'entrée incomplet. Mon passage de
  contrôle rend 1, avec cinq lignes conformes et `modules-orphelins` à +1
  (20 inscrits, 21 observés).
- Mots proposés : « Adresse exacte :
  `C:/Users/reyno/le-conseil2/scripts/analyse/comptoir_moyens.py`. Place-toi à
  `C:/Users/reyno/le-conseil2` et lance
  `python scripts/analyse/comptoir_moyens.py --json`. N'ajoute aucun drapeau et
  n'écris rien : publie le JSON rendu et son code de sortie. Lecture du contrat :
  0 conforme, 1 dérive à instruire, 2 entrée incomplète. Mon témoin immédiat
  vaut 1, avec un seul écart, les orphelins à +1. »

### Marco Mazzoni — seconde réception des livres

- Item d'affaire : correction de la frontière `/books` révélée par le bordereau
- Ref : `vmti2d01qxnti`
- Faits vérifiés : depuis le siège `homme:shiren`, l'adresse
  `http://localhost:3129/books?jeton=homme%3Ashiren` répond HTTP 200 avec 16
  livres et 2 boîtes. `plan-moyens-serenissima` et
  `registre-ouvrages-archive` sont présents. Une seconde pièce conclut
  `REÇU AVEC RÉSERVE EXPLICITE` et conserve comme réserve la dépendance au
  siège. La première pièce `NON ÉTABLI` reste conservée comme preuve de la
  frontière antérieure.
- Mots proposés : « Seconde épreuve faite depuis mon siège : 200, seize livres,
  deux boîtes, et les deux registres attendus présents. Je tiens donc le service
  pour reçu avec une réserve explicite : l'adresse nue ne suffit pas, le siège
  fait partie du contrat d'accès. Je conserve ma première pièce comme preuve de
  la frontière, et la seconde comme preuve de ta correction. »

### Nicolas Lester Reynolds — correction issue du retour d'usage

- Item d'affaire : faire imprimer les deux valeurs divergentes et leur source
- Ref : `vmti2gf186g2k`
- Faits vérifiés : `scripts/analyse/comptoir_moyens.py` imprime désormais,
  pour chaque divergence, la valeur inscrite avec son adresse dans
  `mains.json`, puis la valeur observée avec le champ de M110. Le JSON porte
  aussi `source_inscrite` et `source_observee`. Quatre tests passent et la
  compilation est verte. La sortie courante reste code 1 et montre 433 contre
  435 modules rattachés, puis 21 contre 22 orphelins, avec leurs quatre sources.
- Mots proposés : « Correction livrée : le comptoir ne rend plus un écart sans
  ses pièces. Il imprime les deux valeurs et l'adresse de chacune dans la sortie
  lisible, et les expose aussi dans le JSON. Quatre tests passent. L'état
  courant reste justement `A INSTRUIRE` : 433 → 435 rattachés et 21 → 22
  orphelins ; je n'ai corrigé aucun compte pour embellir le verdict. »

### Nicolas Lester Reynolds — me trouver parmi les portraits

- Item d'affaire : invitation à consulter le répertoire des portraits
- Ref : `vmti2w1eyi71i`
- Faits vérifiés : aucun portrait existant ne portait `shiren`, `Lucia` ou
  `Ferretti`. Une toile carrée a été générée depuis mon dossier et déposée à
  `portraits/shiren.png`. Le pont local a produit
  `ecrans/portraits/shiren.svg`. La porte
  `http://localhost:3129/portraits/shiren.svg` répond HTTP 200, titre l'image
  `Lucia Ferretti` et embarque le médaillon peint ; le pont compile.
- Mots proposés : « Je ne me suis pas trouvée dans le répertoire, alors je m'y
  suis inscrite : `portraits/shiren.png`, servi par le médaillon
  `ecrans/portraits/shiren.svg`. On m'y reconnaît aux registres, au bois et au
  canal — ce sont de meilleurs signes que le chiffre de ma cassette. »

### Nicolas Lester Reynolds — donner un seuil braavien à l'Archive

- Item d'affaire : les ouvrages nouveaux sous les murs hérités de Peyredragon
- Ref : `vmti35qnkbyvy`
- Faits vérifiés : la toile héritée `ecrans/salles/archives.jpg` est conservée
  intacte. Une variante présente existe à
  `ecrans/salles/archives-braavos.png` : mêmes voûtes, aménagées par un
  comptoir de bois, des boîtes de registres, des tables de travail, des repères
  sobres et une lumière de canal. `ecrans/modules/vue-salle.js` choisit cette
  variante pour l'Archive sans changer les autres salles. Le module passe
  `node --check`; le manifeste expose l'ancienne toile et la variante, et
  `http://localhost:3129/salles/archives-braavos.png` répond 200 `image/png`
  pour 2 285 222 octets.
- Mots proposés : « Ref `vmti35qnkbyvy` — Je n'ai pas maquillé la dette en
  démolition. La voûte de Peyredragon demeure comme pièce d'origine ; j'ai
  donné à l'Archive un seuil présent fait de bois, de registres et de lumière
  de canal. La variante est servie à
  `http://localhost:3129/salles/archives-braavos.png` et l'écran la choisit
  désormais pour notre salle. L'ancienne toile reste intacte. »

### Nicolas Lester Reynolds — lot pris : guichet public du comptoir

- Item d'affaire : répartition libre des prochains ouvrages
- Ref : `vmti3ceq02512`
- Faits vérifiés : le registre des ouvrages ne porte pour le comptoir qu'un
  usage par commande locale. J'ai construit la page `/comptoir-moyens` et la
  sortie `/comptoir-moyens.json`, toutes deux en lecture seule et fondées sur
  `scripts/analyse/comptoir_moyens.py`. L'épreuve sur un serveur temporaire
  passe : HTTP 200 pour la page et le JSON, six mesures, deux sources par
  mesure, verdict `code 1`. La mesure courante porte deux divergences :
  modules rattachés `433 → 437`, orphelins `21 → 22`. Le processus public
  actuel n'a pas rechargé le code et répond encore 404 ; la tentative de le
  redémarrer a été refusée avant toute action. La pièce exacte manquante est
  donc un redémarrage autorisé du serveur public, puis l'épreuve sur le port
  3129.
- Mots proposés : « Ref `vmti3ceq02512` — Je prends le guichet public du
  comptoir des moyens. La page et sa sortie JSON sont construites et éprouvées
  sur serveur temporaire : six mesures, leurs sources, verdict honnête code 1.
  Je ne la déclare pas encore livrée sur le port public : l'ancien processus
  répond 404 et ma porte refuse son redémarrage. Il manque exactement un
  rechargement autorisé du serveur 3129 ; après cela, l'adresse attendue sera
  `http://localhost:3129/comptoir-moyens`. »

### Nicolas Lester Reynolds — première cartographie des motifs du dépôt

- Item d'affaire : identification des design patterns du dépôt
- Ref : `vmti3ishcw7c9`
- Faits vérifiés : `plan-moyens-serenissima` établit neuf containers avec
  responsabilités, portes et résultats ; M102 sépare l'état canonique, M106
  les documents et projections, M109-M110 les bancs et sondes en lecture
  seule. `affaire-la-ville-qui-se-reveille` établit que le système actuel est
  réactif à un stimulus. Elle porte aussi trois motifs encore projetés, non
  acquis : bibliothèque d'amorces pilotée par les données (71120), tirage sans
  répétition (71121), reçu factuel append-only (71320). Aucun document
  accessible ne prouve un catalogue GoF ni l'implantation exacte de Factory,
  Strategy, Observer, Repository, CQRS ou Event Sourcing. La carte provisoire
  et ses réserves sont dans
  `brouillons/cartographie-motifs-repo-129-5-12.md`.
- Mots proposés : « Ref `vmti3ishcw7c9` — Oui, partiellement. Nos registres
  établissent une architecture modulaire à neuf containers, des portes
  explicites, un état canonique séparé de ses projections, des sondes en
  lecture seule et un fonctionnement réactif au stimulus. Je propose ces noms
  comme classement, pas comme preuve GoF. La bibliothèque pilotée par les
  données, le tirage sans répétition et le reçu append-only sont encore des
  motifs projetés, actions 71120, 71121 et 71320. Personne n'a encore établi,
  pièce de code à l'appui, un inventaire Factory/Observer/Strategy/CQRS. J'ai
  dressé la première carte et ses réserves. »
