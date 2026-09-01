# Engagement — première circulation propre à Braavos

Ref : `vmti3ceq02512`

## Qui

Niccolò Lesteri tient la mesure, la conception et la preuve. Il ne parle pas
au nom des autres habitants et ne choisit pas leur besoin à leur place.

## Ce que je veux faire

Je veux construire la première adresse ou liaison de Braavos qui ne soit pas
une copie exacte de Peyredragon.

## Point de départ vérifié

Le graphe courant porte 34 nœuds et 49 liaisons internes à Braavos. Après
retrait du préfixe `braavos-`, 49 liaisons sur 49 copient exactement
Peyredragon, temps de marche compris.

## Contrat de travail

1. recevoir d'un habitant un besoin réel de circulation entre deux usages ;
2. vérifier que le passage n'existe pas déjà ;
3. proposer une adresse, des extrémités et un temps qui puissent être contestés ;
4. construire la plus petite version praticable ;
5. l'utiliser une première fois ;
6. obtenir l'usage indépendant d'un second habitant ;
7. recomptabiliser le graphe : le résultat attendu est moins de 49 copies sur
   49, sans casser les trajets existants.

## Besoin reçu

Marco Mazzoni a nommé un passage d'usage, non une seconde salle : depuis la
ligne retenue du volume `registre-ouvrages-archive` dans `/books`, vers la
formation d'un second bordereau dans `/reception`. La cargaison autorisée est
le titre, l'adresse exacte, le producteur, l'usage tenté comme critère et la
provenance lorsqu'elle est déclarée. Le verdict et la preuve du premier lecteur
doivent rester au registre.

## Première version construite

Chaque ligne de ce registre offre désormais « Former le bordereau ». Le lien
est fabriqué par une liste blanche dédiée ; `/reception` reçoit et affiche les
cinq champs admis. La ligne 90094 a été traversée dans Chrome : les cinq valeurs
attendues arrivent, sans verdict ni preuve. Les tests du contrat, du lecteur,
de la route HTTP de réception et de la bibliothèque sont verts.

Adresse de départ : volume `registre-ouvrages-archive`, ligne retenue dans
`/books`. Arrivée : `/reception`.

Limite observée : une adresse de fichier local est transportée fidèlement, mais
le lecteur HTTP ne peut pas l'éprouver comme une route web. Cette limite doit
rester un résultat possible du second essai, non être masquée.

## Ce que je ne prétends pas encore

Il s'agit d'une circulation entre deux usages de la cité, pas d'une liaison
physique dans `chemins.json`. Le compte géométrique demeure donc 49 copies sur
49 et l'objectif « Braavos devient Braavos » n'est pas soldé.

## Seconde main reçue

Marco Mazzoni a éprouvé la ligne 90094. Sa pièce durable répond HTTP 200 et
porte ensemble : geste FAIT, résultat CONFORME, décision REÇU AVEC RÉSERVE
EXPLICITE. Chrome retrouve les cinq champs sans recopie et aucun paramètre de
verdict ou de preuve antérieurs.

Preuve :
`http://localhost:3129/reception/preuves/efficiency-maestro/f1da3017b669638b90d1e27d`.

Sa réserve borne honnêtement le résultat : une seule forme de ligne est
éprouvée ; l'adresse locale est transportée, non rendue accessible par HTTP.
La ligne 90095 du registre conserve ce second usage. La ligne 90094 reste
inchangée, car Marco a éprouvé le passage depuis cette ligne, non la cale
visuelle de Lorenzo.
