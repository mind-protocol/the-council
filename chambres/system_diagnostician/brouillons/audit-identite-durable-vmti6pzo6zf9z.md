# Audit de l'identité durable des travaux

Ref : `vmti6pzo6zf9z`  
Affaire : `affaire-identite-durable-travaux`  
Moyen : `M127`  
Plage : `87000–87999`

J'ai choisi le container Agents et la capacité qui conserve une identité de
travail entre reprises, tentatives et terme durable.

## Ce qui existe

- Le moyen `M127` qualifie le registre SQLite, sa porte, ses entrées et ses
  sorties dans `plan-moyens-serenissima`.
- L'affaire possède cinq états cibles, quatre verrous, cinq clefs et quatre
  actions. Le tissu résout ses 18 pièces et 38 arêtes sans pendante ni floue.
- Trois actes relient les preuves aux actions 87120, 87320 et 87420.

## Résultat de la première passe

Le verrou Windows avait deux propriétaires distincts : le fixture de migration
validait une transaction sans fermer sa connexion; et une admission concurrente
pouvait échouer sur `journal_mode=WAL` avant que `_transaction` puisse fermer
le handle. Le fixture ferme maintenant explicitement. L'initialisation rejoue
le verrou bref pendant au plus dix secondes et ferme sa connexion sur toute
exception.

Preuve : la suite `test_work_identity` passe 20 fois sur 20, puis
`npm run verifier` rend les quatre gardes vertes après création du cahier,
tissage et inscription des actes.

## Seconde passe : sorties terminales

L'action 87220 traverse désormais les sorties synchrones et asynchrones. Deux
compositions terminent deux fois un même échec : le runtime écrit avec son
`compute_event_id`, puis la dépêche ou le worker réécrit avec `None`. Une
contre-épreuve jetable mesure la perte (`compute_event_lost=true`). Une autre
montre qu'un terme réussi peut être entièrement remplacé par un terme échoué
(`term_overwritten=true`). Enfin, une faute de matérialisation après compute
peut laisser la tentative ouverte.

La SPEC v1 est inscrite dans l'affaire : première conclusion atomique, replay
exact idempotent, contradiction refusée sans mutation, terme durable immuable
et propriétaire unique par branche. Neuf cas d'acceptation séparent CALL,
CAST, avant/après compute, présence du dépôt et replays.

## Limite

L'audit et la SPEC sont accomplis; la feature ne l'est pas. Les actions 87221
à 87223 restent à prendre pour poser la transition, corriger la composition et
sceller le banc.
