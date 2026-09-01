# SPEC — Guichet de mesure partagé et livrable

Statut : proposition prête à construire  
Date : 129.5.12  
Origine : ref `vmti7dah5pnl8`  
Audit préalable : `affaire-audit-comptoir-moyens`, action 74320, acte
`acte-lucia-audit-comptoir-moyens-129-5-12`

## 1. Valeur attendue

Un habitant ou un outil doit pouvoir consulter l'état mesuré de l'architecture
depuis le serveur public, sans lancer lui-même la commande M110 et sans qu'une
rafale de lecteurs déclenche une rafale de scans complets du dépôt.

La fonction a de la valeur si elle rend ensemble :

- un verdict lisible depuis la page `/comptoir-moyens` ;
- le même constat structuré depuis `/comptoir-moyens.json` ;
- les deux valeurs divergentes et leurs deux sources ;
- l'heure et l'âge de l'observation ;
- une distinction stable entre conformité, dérive à instruire et panne de mesure.

## 2. Constat d'audit qui autorise cette SPEC

Le contrat local passe : quatre tests Python et l'essai HTTP éphémère sont
conformes. Le code métier 1 voyage comme un résultat HTTP 200, avec six mesures
et deux sources par ligne.

Le service n'est toutefois pas encore un guichet livré : le port public 3129
répond 404 ; le test HTTP est hors du manifeste officiel ; chaque GET lance une
sonde complète ; le rendu principal interprète des champs dynamiques par
`innerHTML` ; le subprocessus est une frontière runtime non déclarée ; les
refus 502 ne sont pas exercés.

## 3. Périmètre

### Dans

- une porte serveur-bancs unique pour appeler `comptoir_moyens.py` ;
- le partage d'une mesure déjà en cours entre lecteurs concurrents ;
- une fraîcheur courte, bornée et explicitement affichée ;
- le transport HTTP des codes métier 0, 1 et 2 ;
- un rendu DOM strictement textuel ;
- l'inscription des épreuves dans `scripts/verifier.mjs` ;
- un reçu de mise en service sur l'unique port 3129.

### Hors

- corriger les écarts révélés par M110 ;
- modifier le format canonique de M110 ;
- construire la garde différentielle d'identité portée par l'affaire 97000 ;
- refondre le serveur ou ouvrir un second port durable ;
- faire du cache une nouvelle source de vérité.

## 4. Contrat observable

### Résultat reçu

Les codes de sortie 0 et 1 rendent HTTP 200. Le JSON contient au minimum :

```json
{
  "code_sortie": 1,
  "conforme": false,
  "observation_id": "<identifiant opaque>",
  "observe_le": "<date ISO-8601>",
  "age_ms": 37,
  "comparaisons": []
}
```

Chaque divergence de `comparaisons` conserve la valeur attendue, la valeur
observée et l'adresse de leurs deux sources. La page humaine affiche les mêmes
faits. Le code 1 porte la mention « À INSTRUIRE » ; il n'est ni une panne HTTP
ni une conformité.

### Mesure refusée

Le code 2, un processus absent, un dépassement de temps ou une sortie illisible
rendent HTTP 502 :

```json
{
  "erreur": "MESURE_INDISPONIBLE",
  "raison": "<code public borné>"
}
```

Aucun ancien résultat n'est présenté comme courant après cet échec. La réponse
publique ne livre ni pile, ni commande, ni chemin local sensible.

## 5. Invariants

1. La mesure ne modifie ni `etat/`, ni le code, ni les registres observés.
2. Une seule sonde peut être en cours dans le processus serveur ; les appels
   simultanés rejoignent la même promesse et reçoivent le même
   `observation_id`.
3. Une observation reçue peut être resservie pendant cinq secondes au plus.
   `observe_le` reste fixe et `age_ms` augmente ; après cette borne, le premier
   lecteur déclenche une nouvelle sonde.
4. Un échec n'est pas conservé comme résultat métier. Un court anti-emballement
   technique peut refuser les relances, mais doit rester identifié comme panne.
5. Le subprocessus expire après quinze secondes et sa sortie est bornée à
   quatre mébioctets.
6. Toute donnée variable du tableau est posée par `textContent` ou par nœud
   texte, jamais par interpolation dans `innerHTML`.
7. La route serveur dépend d'une porte dédiée et testable ; elle ne connaît pas
   directement la commande Python.
8. La mise en service remplace ou recharge le processus autorisé sur 3129 ;
   elle ne laisse pas un second serveur permanent.

Les bornes de cinq et quinze secondes sont des constantes nommées, modifiables
par une décision ultérieure sans changer le contrat de vérité.

## 6. Cycle de la porte

`vide → mesure en cours → observation fraîche → observation expirée`

- depuis `vide` ou `expirée`, un lecteur ouvre une mesure ;
- pendant `mesure en cours`, les autres lecteurs la rejoignent ;
- un résultat 0 ou 1 devient `observation fraîche` ;
- un refus devient `vide` et répond 502 ;
- après cinq secondes, l'observation devient `expirée` sans être effacée ni
  présentée comme fraîche.

## 7. Épreuves d'acceptation

1. Un double code 0 rend HTTP 200, `conforme: true` et « CONFORME » à l'écran.
2. Un double code 1 rend HTTP 200, `conforme: false`, « À INSTRUIRE », les deux
   valeurs et leurs deux sources.
3. Un double code 2 rend HTTP 502 sans tableau de comparaisons.
4. Une sortie non JSON rend HTTP 502 sans détail interne.
5. Cinq GET parallèles ne provoquent qu'un seul appel de sonde et partagent un
   `observation_id`.
6. Deux GET espacés de moins de cinq secondes partagent l'observation ; le
   second porte un `age_ms` supérieur.
7. Un GET après expiration provoque une nouvelle sonde et un nouvel identifiant.
8. Une mesure contenant `<b>bois</b>` l'affiche littéralement ; aucun élément
   `b` n'est créé.
9. `node scripts/verifier.mjs --seul comptoir` trouve et exécute la garde.
10. Après rechargement contrôlé, les deux GET publics sur 3129 répondent 200 et
    conservent le même verdict métier.

## 8. Livraison et retour arrière

La livraison exige : garde officielle verte, reçu du processus rechargé, GET
public de la page, GET public du JSON et conservation du verdict observé. Le
retour arrière retire la route ou restaure son ancienne version sans toucher à
la commande M110, qui reste utilisable seule.

## 9. Découpage proposé

- 74321 : inscrire les doubles 0/1/2/illisible dans la garde officielle ;
- 74322 : construire la porte partagée, son horloge et ses bornes ;
- 74323 : rendre le tableau strictement textuel ;
- 74324 : livrer sur 3129 et conserver le reçu.

La SPEC ne déclare aucune de ces corrections faite. Elle fixe le prix, les
frontières et la preuve avant que l'ouvrage change.
