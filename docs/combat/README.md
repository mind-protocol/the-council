# L'architecture du système de combat

Ce dossier décrit **ce que le moteur de bataille doit être**, module par module,
sans une ligne de code. Il est écrit pour qu'on puisse reprendre l'implémentation
de zéro sans reprendre les erreurs.

## Pourquoi il existe

Le moteur précédent tenait dans un fichier de onze mille lignes. Ce n'était pas
un accident de discipline : c'était le résultat mécanique d'une infrastructure où
**ajouter à un fichier existant coûtait moins cher que créer un module**. Huit
listes de scripts tenues à la main, aucune mesure de structure, aucune règle de
dépendance. Chaque décision locale était raisonnable ; la somme était ingérable.

Le document de refactor qui a précédé celui-ci avait une cible — cinq acteurs, une
table d'autorité, six contrats — et **aucune règle de construction**. Il disait qui
parle à qui, jamais qui a le droit d'importer qui. Résultat : chaque extraction
rejouait le même arbitrage, et un module d'entité s'est retrouvé à remonter
chercher l'écrivain des annales sans que rien ne l'interdise.

Ce dossier corrige ce trou-là en premier. **Les principes viennent avant les
modules, et ils sont vérifiables.**

## Comment le lire

Commencer par [`00-principes/`](00-principes/), dans l'ordre. Les huit fichiers y
tiennent en une page chacun et ils gouvernent tout le reste : un module qui les
contredit est faux, même s'il marche.

Le dernier, [`08-tensions-connues.md`](00-principes/08-tensions-connues.md), est
d'une autre nature : il liste les neuf frontières qui ont demandé un arbitrage et
dont rien ne garantit qu'il soit le bon. **À relire avant de contourner une
frontière qui résiste** — neuf fois sur dix, c'est la fiche qui a tort, pas le
code.

Ensuite les couches, dans l'ordre des numéros. **Le numéro est la règle** : un
module ne peut dépendre que de numéros strictement inférieurs au sien. Voir
[`01-regle-de-dependance.md`](00-principes/01-regle-de-dependance.md).

| couche | ce qu'elle tient |
|---|---|
| [`10-socle`](10-socle/) | ce qui ne dépend de rien : hasard, horloge, mesures, identité, formes, journal |
| [`20-monde`](20-monde/) | le terrain, le bâti, les seuils, les routes, le mouvement, les corps qui se touchent, les coups, la densité, les dangers |
| [`30-perception`](30-perception/) | ce qu'un corps peut apprendre du monde, et à quelle portée |
| [`40-combattant`](40-combattant/) | un homme : ses cinq couches, sa mémoire, son geste |
| [`50-unite`](50-unite/) | un groupe : qui en est, qui le mène, quelle forme, quand il rompt |
| [`60-transmission`](60-transmission/) | ordres, messages, porteurs, canaux |
| [`70-commandement`](70-commandement/) | croyances d'un chef, options, projection, décision |
| [`80-conduite`](80-conduite/) | l'armée : objectifs, missions, allocation, réserve |
| [`90-observation`](90-observation/) | sondes, étalon, traces, rendu — lit tout, n'écrit rien |

Le numéro vaut aussi **à l'intérieur** d'une couche : les modules du monde ont
un rang entre eux, et un module ne lit que des rangs inférieurs au sien. C'est le
trou qu'avait le document précédent, et il se rouvre partout où on l'oublie.

## La forme de chaque fiche

Toutes les fiches de module suivent le même gabarit, et l'ordre des sections
n'est pas décoratif :

1. **Ce que c'est** — une phrase.
2. **Ce qu'il possède** — les données dont il est le seul écrivain.
3. **Ce qu'il lit** — et de quelle couche.
4. **Ce qu'il produit** — ce que les autres peuvent lui demander.
5. **Invariants** — ce qui doit rester vrai, et qu'une sonde peut vérifier.
6. **Ce qu'il ne fait pas** — les responsabilités explicitement refusées. C'est
   la section qui empêche un module de grossir.
7. **Ce que l'ancien moteur faisait mal ici** — mesuré, pas supposé. Ce sont les
   fautes qu'on a payées et qu'on ne veut pas racheter.

La section 7 est la raison d'être de ce dossier. Chaque chiffre qui s'y trouve a
été relevé sur le moteur précédent, souvent au prix d'une demi-journée. Un
dossier d'architecture sans ces chiffres serait une liste de bonnes intentions.

## Ce que ce dossier n'est pas

- **Ce n'est pas une spécification d'API.** Aucune signature, aucun nom de
  fonction, aucun format de fichier. Ce sont des responsabilités et des
  frontières ; l'implémentation choisit ses noms.
- **Ce n'est pas un plan de travail.** Il ne dit pas dans quel ordre construire,
  ni combien de temps ça prend.
- **Ce n'est pas figé.** Un module qui se révèle mal découpé se re-découpe — mais
  on change la fiche AVANT le code, et jamais l'inverse.
