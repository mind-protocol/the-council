# Matrice d'audit — terminaison durable des travaux

Ref : `vmti7dah5pnl8`  
Affaire : `affaire-identite-durable-travaux`  
Action : `87220`

## Valeur cherchée

Une reprise fiable exige que la première conclusion d'une tentative reste
intacte. Sans cette propriété, une couche tardive peut effacer l'identifiant du
calcul, changer un succès en échec, remplacer l'ouvrage durable ou faire croire
qu'un travail est clos autrement qu'il ne l'a été.

## Chemins observés

| Chemin | Premier écrivain | Second écrivain | État présent |
|---|---|---|---|
| CALL, succès du fournisseur et dépôt réussi | `mission._terme` | aucun | une terminaison réussie avec terme |
| CALL, échec du fournisseur | `runtime.appeler` avec `compute_event_id` | `mission.appeler` avec `None` | double terminaison ; l'événement est perdu |
| CALL, succès compute puis échec de matérialisation du rapport | aucun | aucun | tentative laissée ouverte |
| CAST, succès et dépôt du vécu réussi | `runtime_worker` | aucun | une terminaison réussie avec terme |
| CAST, succès mais dépôt du vécu impossible | `runtime_worker` | aucun | tentative réussie sans terme |
| CAST, échec du fournisseur | `runtime.appeler` avec `compute_event_id` | `runtime_worker` avec `None` | double terminaison ; l'événement est perdu |
| Échec après admission mais avant entrée dans `runtime.appeler` | aucun propriétaire général | aucun | tentative susceptible de rester ouverte |

## Contre-épreuve sur registre jetable

1. Une tentative terminée `failed` avec `compute-event-1`, rejouée ensuite
   `failed` avec `None`, conserve `failed` mais remplace l'événement par `null`.
   Verdict mesuré : `compute_event_lost = true`.
2. Un terme `succeeded / compute-event-A / artifact-A`, suivi d'un terme
   conflictuel `failed / compute-event-B / artifact-B`, est remplacé en entier.
   Verdict mesuré : `term_overwritten = true`.

Le registre accepte donc aujourd'hui une réécriture terminale. L'écart n'est
pas seulement une duplication de fonctions : il détruit une preuve déjà
inscrite.

## Conclusion d'audit

L'invariant requis est une terminaison monotone et exactement une fois au sens
sémantique : la première transition gagne ; sa répétition exactement identique
est un succès idempotent ; toute répétition différente est refusée sans aucune
mutation. Chaque branche d'orchestration doit en outre posséder un seul auteur
nommé, et les échecs postérieurs au calcul doivent terminer la tentative sans
inventer un terme durable.
