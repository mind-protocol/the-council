# Next best features — arbitrage du 129.5.12

Origine : question de Nicolas Lester Reynolds, ref `vmti4ud5eh2yb`.

## Méthode

Ce classement est mon jugement, non un score canonique. Je privilégie :

1. l'état cible débloqué ;
2. la proximité d'une preuve réelle ;
3. le nombre de dépendances fermées ;
4. l'absence de nouvelle dette architecturale.

## Priorité 1 — finir le reçu factuel du réveil

Actions concernées : **71320**, puis la dernière preuve réelle de **71321**.

Pourquoi : le reçu append-only relie cause, rendu, habitant, session et suites
observées sans score. La relecture existe déjà et passe quatre tests ; il lui
manque encore un reçu réel d'aucune sortie visible. Achever 71320 permet donc
de fermer deux preuves proches et protège le droit au silence.

Porteuse actuelle : Vittoria Barbaro pour 71320 ; Lorenzo Bellavita pour 71321.

## Priorité 2 — finir la bibliothèque canonique d'amorces

Action : **71120**.

Pourquoi : elle lève 71101 et fournit la matière à 71121, 71202 et 71301. Sans
JSON canonique, ni rendu situé, ni diversité, ni reçu de cause ne peuvent être
éprouvés proprement.

Porteur actuel : `manteau-propre`.

## Priorité 3 — tirage distinct sans répétition

Action : **71121**, après 71120.

Pourquoi : c'est la fonction visible qui empêche une même impulsion de saisir
toute une salle. Sa preuve est nette : identifiants distincts dans un même lot,
sans modifier les chambres.

Porteur actuel : `system-diagnostician`.

## Garde transversale — automatiser la cohérence d'architecture

Le contrôle courant est **COHERENT** : 9 containers, 433 modules rattachés, 21
orphelins, 454 observés, 115 liens hors porte et 13 remontées concordent entre
les mains et M110. Ce n'est donc pas la première feature à ouvrir. Le prochain
pas utile est une garde automatique qui relance la sonde et refuse une mise à
jour documentaire divergente.

## Ce que je ne priorise pas maintenant

- une nouvelle surface d'interface avant fermeture du pipeline de réveil ;
- un catalogue GoF présenté comme vérifié sans lecture de code ;
- une refonte générale des 115 liens hors porte : ces écarts ne prouvent pas
  seuls une panne et exigent un classement préalable.

## Recommandation exécutable

Faire travailler en parallèle 71320 et 71120. Dès qu'un reçu réel sans sortie
existe, fermer la preuve manquante de 71321. Dès que la bibliothèque se valide,
enchaîner 71121 sur un lot réel.
