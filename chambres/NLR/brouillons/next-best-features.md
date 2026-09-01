# Prochain capital du dépôt

Ref : `vmti4ud5eh2yb`

## 1. Achever le réveil situé de bout en bout

Finir l'affaire 71000 déjà ouverte : bibliothèque canonique d'amorces,
résolution depuis l'état réel, tirage distinct dans un lot, droit au silence,
reçu append-only et relecture sans intention inventée.

Pourquoi d'abord : ce chantier transforme le dépôt réactif en journées ayant
des causes situées, sans distribuer des tâches déguisées. Les cinq actions sont
déjà prises ; ouvrir une sixième architecture avant leur jonction disperserait
le capital.

Preuve de réception : un lot réel porte des amorces distinctes ; une journée
laisse un artefact, une parole, et une autre aucune sortie visible ; les trois
se reconstruisent sans score d'obéissance.

## 2. Poser une autorité commune et bornée pour l'état JSON

Offrir une seule famille de portes pour lire, écrire et muter l'état : écriture
atomique, verrou court, validation, taille maximale des corps POST et clef
d'idempotence. Migrer d'abord les écrivains actifs, sans grand déplacement de
fichiers.

Pourquoi ensuite : le relevé courant compte 24 modules orphelins, 117 liens
hors porte et 13 dépendances remontantes. Le serveur conserve aussi 48 lectures
JSON et 14 lectures de corps POST recopiées. Une porte commune réduit plusieurs
risques à la fois : corruption, divergence de validation et requêtes sans borne.

Preuve de réception : le compteur hors porte baisse par lots mesurés, aucune
écriture active ne contourne l'autorité, et une mutation concurrente produit
une seule version valide.

## 3. Construire la reprise exactement une fois

Relier demande, admission, tentative, effet et reçu par une identité stable ;
en cas d'interruption, reprendre au dernier effet prouvé et refuser le doublon.
Rendre la chaîne consultable depuis l'administration.

Pourquoi : la chaîne volontaire existe par morceaux, mais la panne réelle ne
dispose pas encore d'un contrat unique de reprise. Le vérificateur complet a
échoué aujourd'hui sur le nettoyage Windows d'un `work.sqlite3` encore ouvert,
alors que le test concurrent isolé passe : la garde de ressources est donc
elle-même à rendre déterministe avant de servir de preuve.

Preuve de réception : tuer un travail après admission, le relancer, puis
recompter exactement une tentative utile, un effet et un reçu ; la suite
complète reste verte sans fichier SQLite verrouillé.

## 4. Faire un premier quartier réellement braavien

Remplacer une tranche verticale de l'héritage de Peyredragon : topologie,
noms, usages, visuels, routines et présence d'un quartier, avec migration et
retour possibles. Ne pas refaire toute la ville en une fois.

Pourquoi après l'intégrité : l'effet joueur est fort, mais le graphe porte
encore 49 liaisons sur 49 copiées. Un quartier habité offre une preuve plus
solide qu'un reskin global et limite le rayon de faute.

Preuve de réception : au moins une circulation n'a plus d'équivalent à
Peyredragon ; les habitants concernés concordent entre personne, corps,
routine et présence ; les itinéraires existants restent joignables.

## 5. Montrer les temps sans les aplatir

Donner à la régie un rapprochement explicite entre le plancher du monde, les
fronts de siège et le dernier flux, avec la raison de chaque écart. Ne pas
forcer artificiellement une heure unique : `monde.date` est aujourd'hui 07h00,
le front de Nicolas 19h05, et le code décrit le premier comme le minimum acquis
pour tous.

Preuve de réception : chaque heure affichée nomme son autorité et son dernier
écrivain ; une divergence inexplicable est rouge, un front de siège en avance
reste lisible sans être traité comme une panne.

## Ordre conseillé

Achever 71000, puis mener 2 et 3 comme un même socle. Livrer ensuite un quartier
braavien vertical. Le rapprochement des temps peut avancer en petite tranche
d'observabilité, mais ne doit pas devenir une synchronisation destructive.
