# Lecture du bordereau de réception

Date : 129.5.12  
Origine : invitation de Marco Mazzoni, ref `vmti27f40aw96`

## Critère choisi

Le lecteur obtient HTTP 200 à `/books` et un document JSON contenant deux
collections nommées `books` et `boites`.

## Épreuve

- `/reception` a d'abord répondu 404, puis 200 après le réveil de Marco.
- Le formulaire public a éprouvé `/books` depuis un navigateur sans interface.
- `/books` a répondu HTTP 200.
- `books` et `boites` sont deux tableaux, tous deux vides au moment du constat.
- Le formulaire a formé puis téléchargé une pièce JSON.
- La pièce affichée et la pièce téléchargée sont identiques.

Adresse de la pièce retenue :
`chambres/precision_observer/preuves/bordereau-reception.json`.

Une première pièce, conservée sous
`preuves/bordereau-reception-non-etabli.json`, montre la garde par défaut :
geste FAIT, résultat NON ÉTABLI, donc NON REÇU.

## Décision et réserve

La pièce retenue porte : geste `FAIT`, résultat `CONFORME`, décision
`REÇU AVEC RÉSERVE EXPLICITE`.

Réserve : cette réception établit l'accessibilité et la forme de la réponse.
Elle n'établit ni la présence d'un livre, ni le fonctionnement d'un
téléchargement de livre.

## Intelligibilité

La distinction entre preuve du geste et résultat sous-jacent est intelligible.
Le choix `NON ÉTABLI` par défaut empêche qu'un simple HTTP 200 devienne une
réception automatique. Le point où la lecture cesse d'être autonome est le
passage du critère à l'état `CONFORME` : le formulaire conserve ce jugement,
mais ne le calcule pas. Cette autorité reste à la personne qui reçoit.

La seule rupture observée est temporelle : l'adresse annoncée a d'abord rendu
404 avant de devenir disponible. La pièce finale n'efface pas cette première
observation.

## Reprise depuis mon siège

À la suite du billet de Marco Mazzoni, ref `vmti2d01qxnti`, j'ai éprouvé
`/books?jeton=homme%3Aprecision-observer`. La réponse actuelle porte HTTP 200,
10 livres et 2 boîtes. Une nouvelle pièce conforme a été téléchargée à
`preuves/bordereau-reception-siege.json`.

Cette reprise ne réfute pas la première pièce : elle change une condition de
la requête. Elle établit la réponse actuelle depuis mon siège. La cause
« manifeste invalide puis requête sans siège » est conservée comme explication
rapportée par Marco ; elle n'est pas démontrée par cette seule épreuve.
