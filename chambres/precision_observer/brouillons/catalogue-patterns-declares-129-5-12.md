# Patterns du dépôt — premier état prudent

Date : 129.5.12  
Origine : question de Nicolas Lester Reynolds, ref `vmti3ishcw7c9`

## Réponse courte

L'architecture du dépôt est déjà décrite : containers, rangs, portes,
autorité canonique, sorties dérivées et sondes. Aucun document accessible ne
prouve encore qu'une personne ait dressé un catalogue des design patterns
d'implémentation au sens strict.

## Catalogue initial

| Candidat | Statut | Ce qui l'établit | Ce qui reste inconnu |
|---|---|---|---|
| Containers à responsabilité bornée | DÉCLARÉ | M101 à M109 donnent à chaque container une intention, une matière, une porte et une sortie | La conformité de chaque module à cette responsabilité |
| Porte explicite par container | DÉCLARÉ | Le manifeste et M101–M109 nomment des portes Python ou Node ; M110 compte 115 liens hors porte | Si l'implémentation relève réellement de Ports and Adapters / Hexagonal Architecture |
| État canonique et vues dérivées | DÉCLARÉ | M102 tient la vérité canonique ; M106 produit un tissu dérivé | Les mécanismes concrets de transaction, cache ou synchronisation |
| Sonde de lecture sans mutation | DÉCLARÉ COMME RESPONSABILITÉ | M109 lit sans muter ; M110 confronte manifeste et code | L'emploi d'Observer, Visitor ou d'un autre pattern dans le code |
| Activation réactive | COMPORTEMENT ÉTABLI | L'affaire « La ville qui se réveille » établit qu'une session appelée travaille et qu'aucune session ne continue secrètement | Le pattern d'implémentation : Event Bus, Queue, Mediator ou autre |
| Séparation geste / résultat / décision | PROTOCOLE DÉCLARÉ | Le registre des décisions rend ces trois états obligatoires | Sa traduction en classes, états ou commandes dans le code |
| Registre d'ouvrages avec verdicts indépendants | PROTOCOLE DÉCLARÉ | Le registre conserve adresse, usage, preuve, verdict et limite ; un second lecteur ajoute son verdict sans effacer le premier | L'éventuel Event Sourcing ou append-only réel de l'infrastructure |

## Conclusion de mesure

Nous possédons un inventaire des styles architecturaux et protocoles déclarés,
pas encore un catalogue vérifié des patterns de code. Les noms `Adapter`,
`Observer`, `Mediator`, `State` ou `Event Sourcing` restent des hypothèses tant
qu'un lecteur du code n'a pas cité leurs participants et leur flux exact.

## Épreuve suivante proposée

Choisir un seul container, prendre sa porte déclarée, puis relever pour un flux
réel : appelant, interface, implémentation, état traversé et sortie observable.
Un pattern ne sera nommé que si ces rôles sont tous retrouvés.
