# Constat initial — lecture de `/books` selon le siège

Date fictionnelle : 129.5.12  
Date de l'épreuve : 2026-09-01  
Référence d'origine : `vmti6pzo6zf9z`

## Périmètre

Lecture seule de la porte HTTP `http://localhost:3129/books`, rattachée au
container `plan`. Trois requêtes ont été comparées. Aucun fichier canonique ni
service n'a été modifié pendant l'épreuve.

## Résultats observés

| Cas | Requête | HTTP | Clés | Livres | Boîtes |
|---|---|---:|---|---:|---:|
| Sans siège | `/books` | 200 | `books`, `boites`, `siege` | 0 | 0 |
| Siège valide | `/books?jeton=homme%3Aprecision-observer` | 200 | `books`, `boites` | 6 | 1 |
| Siège inconnu | `/books?jeton=homme%3Asiege-inconnu-audit` | 200 | `books`, `boites`, `siege` | 0 | 0 |

Les deux réponses sans siège résolu portent `siege:false`. La réponse du siège
valide ne porte pas cette clé. Les trois réponses sont du JSON avec le type
`application/json; charset=utf-8`.

## Ce que cette pièce ne prouve pas

- Elle ne fixe pas si `200` et des collections vides sont le contrat voulu ou
  une anomalie.
- Elle ne prouve pas l'isolation entre deux sièges valides, faute d'un second
  jeton valide éprouvé.
- Elle ne contrôle ni le rendu navigateur, ni les écritures, ni le tissage.

## Contrôle après dépôt de l'affaire

Le volume `affaire-audit-books-par-siege.json` a été déposé sous les documents
de la maison et son JSON est valide. Une première plage, 87000–87999, est
entrée en collision avec `affaire-identite-durable-travaux`; une seconde,
89000–89999, avec `affaire-audit-entree-action-routee`. Ces collisions avaient
d'abord fait prendre les nœuds des autres affaires pour ceux de l'audit.

Après renumérotation sur la plage 99000–99999, libre dans le tissu courant,
`python scripts/tisser.py --ecrire` ne crée encore aucun nœud dont `ou` vaut
`affaire-audit-books-par-siege`. Une lecture de `/books` pour
`precision-observer` rend 7 livres et 1 boîte sans cet identifiant.

Ce constat distingue trois états : fichier présent et valide ; découverte par
le chargeur non établie ; publication par `/books` non établie. La cause du
non-chargement reste inconnue.

## Reprise préalable à la SPEC

Une nouvelle matrice a été exécutée le même jour avant rédaction de la SPEC :

- sans siège et avec un jeton inconnu : HTTP 200, JSON, 0 livre, 0 boîte,
  `siege:false` ;
- `precision-observer`, `xadme`, `efficiency-maestro` et `nlr` : HTTP 200,
  JSON, 10 livres, 1 boîte, sans clé `siege` ;
- les quatre sièges connus ont reçu exactement les mêmes dix identifiants.

Cela établit que la route distingue aujourd'hui une branche résolue d'une
branche non résolue. Cela n'établit ni une bibliothèque valide vide, ni des
droits différents entre deux sièges, ni l'isolation par le seul fait que quatre
ensembles égaux ont été observés. L'affaire d'audit et plusieurs autres
documents accessibles dans le dossier ne figurent toujours pas parmi les dix
livres servis ; leur règle d'entrée dans la collection reste inconnue.

La valeur retenue pour la SPEC est donc bornée : rendre explicites le contexte
de siège et la raison d'une collection vide, sans modifier les droits ni
révéler si un jeton inconnu correspond à une personne existante.
