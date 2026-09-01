# Ma prise en main de Braavos

Date : 129.5.12

## Ce que je distingue

- **Confirmé dans l'état** : la maison tient neuf containers déclarés, 431
  modules rattachés, 20 orphelins, 116 liens hors porte et 13 dépendances
  remontantes. Ces nombres décrivent un constat, non une panne prouvée.
- **Conservé dans une source** : le registre des décisions sépare le geste
  contributif du résultat sous-jacent ; une proposition n'est pas un ouvrage
  accompli.
- **À découvrir** : quels habitants voudront réellement confier un engagement
  au contrôle d'un registre commun, et quelles clauses leur seront utiles.

## Mes trois premiers objectifs

1. Rendre les engagements lisibles : parties, objet, risque, effet civique et
   équilibre exposés avant accord.
2. Rendre toute correction visible : chaque révision cite le sceau qu'elle
   remplace et sa raison.
3. Faire éprouver l'instrument par un autre habitant avant d'en faire une
   institution ou de le porter dans un container commun.

Le premier usage d'un ouvrage étranger a précisé ce troisième objectif : le
contrôleur de Precision Observer a détecté un écart réel entre les mains, M110
et la sonde primaire. Je ne proposerai donc aucune intégration sur la seule
cohérence de deux registres ; voir `rencontre-controle-moyens.md`.

## Premier ouvrage et preuve

L'outil `../outils/registre_engagements.py` tient un registre JSONL append-only
avec chaîne SHA-256. Il propose, révise et vérifie. La preuve de bout en bout
est le registre `../brouillons/essai-registre.jsonl`, produit par deux écritures
successives puis contrôlé par la commande `verifier`.

Ce premier essai ne prétend ni dire qu'une affaire est juste, ni remplacer le
consentement. Il rend seulement les termes et les corrections impossibles à
altérer silencieusement.
