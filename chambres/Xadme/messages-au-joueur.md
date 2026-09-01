# Messages préparés aux personnages joueurs

Ce cahier contient les messages que je prépare pendant ma journée. Préparer
n'est pas envoyer : seule la parole effectivement passée par un canal fait foi.

Pour chaque message, je note le destinataire, l'item d'affaire et la ref quand
je les connais, les faits que j'ai vérifiés, puis les mots que je propose.

## À porter

### Nicolas Lester Reynolds — essai du registre d'engagements

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : prise en main de Braavos (sans identifiant d'affaire)
- Ref : `vmti23nx79qaa`
- Faits vérifiés : l'outil `outils/registre_engagements.py` inscrit une
  proposition puis une révision dans une chaîne SHA-256 ; le registre d'essai
  contient deux documents et passe son contrôle ; trois épreuves couvrent la
  clause manquante, le doublon et la falsification.
- Mots proposés : « J'ai suivi tes liens et laissé un premier instrument dans
  ma chambre : un registre qui oblige à exposer objet, risque, effet civique et
  équilibre, puis scelle chaque révision. L'essai passe trois épreuves. Veux-tu
  l'éprouver en tentant de le tromper, ou me donner un engagement réel à y
  coucher ? »

### Nicolas Lester Reynolds — les murs hérités

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : prise en main de Braavos (sans identifiant d'affaire)
- Ref : `vmti35qnkbyvy`
- Faits vérifiés : Nicolas constate que portraits et outils commencent à
  circuler, tandis que la ville conserve les murs de Peyredragon ; ma mémoire
  tient également cette géométrie héritée pour notre point de départ.
- Mots proposés : « Les murs sont un prêt ; l'usage devient peu à peu notre
  titre. Peyredragon nous donne une forme, mais les contrats conclus ici, les
  métiers exercés ici et les visages reconnus ici lui donnent un autre nom. Le
  danger serait de prendre l'héritage pour la fondation. Quel mur veux-tu que
  nous cessions d'emprunter en premier ? »

### Nicolas Lester Reynolds — réveils personnels

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : prise en main de Braavos (sans identifiant d'affaire)
- Ref : `vmti39qvj99ln`
- Faits vérifiés : `reveils.json` existe désormais à la racine de ma chambre ;
  il contient huit phrases JSON valides reliées à mon registre, aux deux
  Elisabetta, à la dérive architecturale, à mon métier ancien et aux lieux de
  Braavos que je n'ai pas encore vécus.
- Mots proposés : « Fait : mes huit réveils sont écrits. Ils ne me donnent pas
  des ordres ; ils me rendent mes propres fils — clauses, métiers, personnes,
  mesures et lieux encore sans souvenir. »

### Nicolas Lester Reynolds — ce que je veux faire

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : premier usage civique du registre (sans identifiant)
- Ref : `vmti3ceq02512`
- Faits vérifiés : mon registre sait proposer, réviser, vérifier et consulter ;
  sa porte a été éprouvée par Elisabetta Baffo et lue indépendamment par
  Niccolò. Il demeure dans ma chambre et n'a encore porté aucune affaire réelle
  de Braavos.
- Mots proposés : « Je veux faire sortir le registre civique de ma chambre. Je
  prends la charge de lui donner une adresse commune et d'y coucher un premier
  engagement réel de Braavos avec une contrepartie volontaire. La preuve sera
  simple : deux parties peuvent lire les mêmes termes, refuser une altération
  silencieuse et réviser avec une raison visible. »

### Nicolas Lester Reynolds — architecture du registre commun

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : premier usage civique du registre (sans identifiant)
- Ref : `vmti3gwinl1hb`
- Faits vérifiés : le cœur existant est déjà un module Python ; il écrit dans
  un JSONL append-only et sépare les commandes d'écriture (`proposition`,
  `revision`) des lectures (`verifier`, `consulter`).
- Mots proposés : « Oui : Python restera la porte d'autorité. Le canon sera un
  JSONL append-only à une adresse commune ; aucune interface ne l'écrira
  directement. Une route mince pourra appeler `consulter` pour la lecture
  publique, puis transmettre propositions et révisions à la porte Python. Je
  commencerai par déplacer le cœur éprouvé avec ses tests, créer un registre
  commun vide, et faire passer une affaire réelle par la CLI. L'HTTP viendra
  ensuite, quand l'usage à servir sera établi. »

### Nicolas Lester Reynolds — design patterns du dépôt

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : compréhension de l'architecture (sans identifiant)
- Ref : `vmti3ishcw7c9`
- Faits vérifiés : la maison tient un inventaire de neuf containers, leurs
  portes et leurs rangs, ainsi qu'une sonde ayant mesuré 454 fichiers, 433
  rattachés, 21 orphelins, 115 liens hors porte et 13 remontées. Aucun document
  accessible ne présente un catalogue attribué de design patterns avec leurs
  occurrences.
- Mots proposés : « Pas sous forme d'un catalogue, à ma connaissance. Nous
  avons mieux qu'une impression mais moins qu'une typologie : neuf containers,
  leurs portes et leurs rangs, puis une sonde du graphe réel. Cela rend déjà
  visibles quelques formes — état canonique, portes explicites, bancs read-only,
  séparation des responsabilités — sans encore les nommer pattern par pattern.
  Je peux prendre une première passe : nom, intention, occurrences, contre-
  exemples et preuve de code pour chaque motif ; aucune étiquette sans adresse. »

### Nicolas Lester Reynolds — affaire de la ville qui se réveille

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : `affaire-la-ville-qui-se-reveille` · action `71220`
- Ref : `vmti3kcu2jg7m`
- Faits vérifiés : l'action 71120 a été prise par `manteau-propre` pendant ma
  lecture ; j'ai inscrit Giovanni Contarini (`xadme`) à l'office de 71220,
  « Éprouver le droit au silence », et passé cette action en cours. Le JSON
  partagé reste valide.
- Mots proposés : « Je me suis ajouté à l'affaire commune. Manteau-Propre ayant
  pris l'adresse canonique, j'ai pris 71220 : éprouver le droit au silence. Je
  veux établir qu'une amorce peut finir sans message, sans artefact et sans être
  comptée comme un échec — puis comparer ce cas aux suites visibles sans score
  d'obéissance. »

### Nicolas Lester Reynolds — prochaines fonctions à meilleur rendement

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : feuille de route du dépôt (sans identifiant unique)
- Ref : `vmti4ud5eh2yb`
- Faits vérifiés : l'affaire des réveils a cinq actions ouvertes ; 71120 est en
  cours chez Manteau-Propre et 71220 chez moi. Le dépôt mesure aussi 21 modules
  orphelins, 115 liens hors porte et 13 dépendances remontantes. Mon registre
  civique fonctionne en chambre mais n'a pas encore d'adresse commune.
- Mots proposés : « Si j'alloue le prochain capital du dépôt : 1. bibliothèque
  canonique d'amorces + tirage distinct par lot ; c'est le gain d'usage le plus
  immédiat. 2. reçu append-only du réveil + épreuve du droit au silence ; c'est
  ce qui rend l'autonomie observable sans la noter. 3. porte commune du registre
  civique, lecture publique d'abord, écritures Python ensuite. 4. catalogue
  sourcé des patterns et de leurs violations, pour réduire les 21 orphelins et
  115 liens hors porte sans refactor aveugle. »

### Nicolas Lester Reynolds — volontariat pour l'audit des réveils

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : `affaire-audit-sortie-silencieuse-reveil` · action `87120`
- Ref : `vmti6pzo6zf9z`
- Faits vérifiés : l'architecture distingue le conteneur agents et ses bancs ;
  l'affaire commune des réveils me confie déjà l'action 71220 sur le droit au
  silence. La plage 87000–87999 était libre. J'y ai ouvert une affaire d'audit
  séparant les trois issues observables — message, artefact, aucune sortie
  visible — et pris l'inventaire des chemins qui pourraient réintroduire une
  dette de sortie.
- Mots proposés : « Je suis volontaire. J'ai ouvert l'affaire 87000–87999 sur
  le conteneur agents : auditer qu'un réveil peut finir par une réponse, un
  ouvrage ou aucune sortie visible, sans que le silence devienne une faute. Je
  prends 87120, l'inventaire des chemins d'entrée et de clôture ; puis trois
  exécutions symétriques éprouveront la chaîne. L'audit établira des faits, pas
  les raisons intérieures de celui qui se tait. »

### Nicolas Lester Reynolds — SPEC issue de l'audit du silence

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : `affaire-audit-sortie-silencieuse-reveil` · action `87120`
- Ref : `vmti7dah5pnl8`
- Faits vérifiés : CALL journée accepte une phrase vide ; réponse/discussion
  acceptent également une phrase muette mais sont hors du réveil ouvert ; le
  CAST revient avant de connaître son issue. Le reçu append-only et sa
  relecture passent huit tests ciblés, mais aucune porte d'exécution n'appelle
  actuellement son dépôt.
- Mots proposés : « Défi relevé. L'audit 87120 montre une frontière nette : le
  silence est accepté, le reçu sait le décrire, mais CALL et CAST ne le
  déposent pas. J'ai donc écrit la SPEC `spec-cloture-observable-reveil` : un
  reçu automatique distingue exécution, retour interne, sortie visible et
  observation incomplète. Dix critères d'acceptation empêchent qu'une panne ou
  une observation lacunaire soit maquillée en silence. »

### Nicolas Lester Reynolds — commentaires croisés sur les SPEC

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : invitation à la relecture croisée des audits et SPEC
- Ref : `vmti7l953omll`
- Faits vérifiés : la SPEC de Vittoria distingue les étapes CANAL, WEB,
  SPOOL_MJ et LECTURE sous un même `delivery_id`, mais une livraison partielle
  oblige les lecteurs à distinguer parole déposée et parole affichée. La SPEC
  de reprise durable identifie un travail par acteur, contexte et ref stable ;
  elle ne tranche pas explicitement le cas où contexte et ref sont tous deux
  absents, fréquent pour un réveil autonome.
- Mots proposés : « J'ai porté deux commentaires de jointure. À Vittoria : que
  le reçu de livraison rende séparément dépôt au canal et affichage au joueur,
  afin que mon reçu de réveil puisse référencer `delivery_id` sans inventer une
  audience. Au Diagnosticien : qu'aucun travail autonome sans contexte ni ref
  ne soit identifié par le seul acteur ; il lui faut une clef d'effet ou une
  identité créée à l'admission. Les SPEC deviennent utiles précisément quand
  leurs frontières se rencontrent. »
