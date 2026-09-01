# Cartographie provisoire des motifs du dépôt — 129.5.12

Ref d'origine : `vmti3ishcw7c9`

Cette note ne prétend pas constituer un catalogue GoF. Elle distingue ce que
les registres établissent, le nom technique que l'on peut proposer pour le
reconnaître, et ce qui demeure seulement projeté.

## Motifs établis par les registres

| Motif observé | Nom technique proposé | Pièce accessible | Réserve |
|---|---|---|---|
| Neuf domaines sont déclarés comme containers, chacun avec une responsabilité, une porte, un porteur et un résultat. | Architecture modulaire à ports explicites ; possiblement *modular monolith*. | `plan-moyens-serenissima`, M101 à M110. | Le registre établit la séparation et les portes, pas l'étiquette anglaise ni le respect absolu des frontières. |
| L'état canonique est tenu séparément des rapports et graphes engendrés qui le lisent. | Source unique de vérité avec projections dérivées. | M102, M106 et M110 ; pages du plan des moyens. | Cela ne suffit pas à conclure CQRS : aucun registre n'établit deux modèles de commande et de lecture complets. |
| Les containers publient des portes nommées (`expose.py`, `index.js`, commandes ou routes) au lieu d'offrir chaque module intérieur. | Façade ou adaptateur de frontière. | Colonne « Porte » de M102 à M108. | « Façade » et « adaptateur » restent des hypothèses de classement tant qu'un audit du code n'a pas contrôlé leur rôle exact. |
| Une session ne travaille qu'après stimulus ; le routage peut réveiller les personnes présentes. | Système réactif piloté par événements ou messages. | `affaire-la-ville-qui-se-reveille`, état actuel et pages d'ouverture. | Le livre établit le caractère réactif, pas une implémentation canonique du patron Observer. |
| Les contrôles relisent le système sans le muter et rendent des écarts séparés des pannes. | Banc d'essai / sonde en lecture seule. | M109, M110 et `mains.json`. | C'est un motif opérationnel du dépôt, non un patron objet classique. |

## Motifs projetés, non encore acquis

- Bibliothèque JSON d'amorces et résolution depuis le contexte : conception
  pilotée par les données, clef 71110, action 71120 encore « à faire ».
- Tirage sans répétition dans un lot : stratégie de sélection, clef 71111,
  action 71121 encore « à faire ».
- Reçu factuel append-only : journal d'audit ou *event log* possible, clef
  71310, action 71320 encore « à faire ».

## Conclusion de travail

Nous avons donc une architecture modulaire, des portes, une vérité canonique,
des projections dérivées et un fonctionnement réactif établis dans les livres.
Nous n'avons pas encore de preuve suffisante pour annoncer Factory, Strategy,
Observer, Repository, CQRS ou Event Sourcing comme patrons effectivement
implantés. Il faut pour cela une seconde pièce : pour chaque nom, une adresse
de code, le problème résolu, les participants et un contre-exemple de frontière.
