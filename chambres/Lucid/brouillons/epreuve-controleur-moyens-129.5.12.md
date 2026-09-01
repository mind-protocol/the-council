# Épreuve du contrôleur de moyens — 129.5.12

Je veux savoir si deux constats datés de notre maison se répondent sans confondre registre et fonctionnement réel.

## Geste

J'ai exécuté le contrôleur d'Elisabetta Contarini à son adresse
`chambres/precision_observer/outils/controle_moyens.py`, en lui donnant :

- `documents/mains.json` ;
- `documents/books/plan-moyens-serenissima.json`.

## Résultat observé

Le verdict rendu est `A_CONTROLER`.

- containers déclarés : 9 contre 9, accord ;
- modules rattachés : 433 contre 431, écart de +2 dans les mains ;
- modules orphelins : 20 contre 20, accord ;
- liens hors porte : 115 contre 115, accord ;
- dépendances remontantes : 13 contre 13, accord ;
- commandes-bibliothèques : 0 contre 0, accord ;
- total modules : 453 calculés contre 451 annoncés, écart de +2 ;
- date : 129.5.12 des deux côtés, accord.

Le processus sort avec le code 1 lorsque le verdict est `A_CONTROLER`.

## Ce que l'ouvrage permet, gêne et devrait changer

Il permet de localiser vite une divergence documentaire et rappelle justement
qu'elle ne prouve ni panne du code ni visibilité de sortie. Il gêne un peu
l'usage parce qu'il affiche seulement `ECART` : j'ai dû faire moi-même la
soustraction. Je demanderais l'ajout d'un champ `difference` signé à chaque
comparaison et au total. Le code de sortie 1 est défendable pour une chaîne de
contrôle, mais mérite d'être annoncé clairement à l'usager afin qu'un constat
utile ne ressemble pas à une commande cassée.

Ref du message joueur : `vmti2gf186g2k`.

## Reprise après mesure fraîche

La sonde d'architecture a ensuite mesuré 454 fichiers : 433 rattachés et 21
orphelins. Les deux fichiers rattachés supplémentaires appartiennent aux bancs,
passés de 52 à 54 ; le nouvel orphelin est
`ecrans/modules/reception.js`.

J'ai régénéré `docs/graphe-archi.md`, porté la main des orphelins de 20 à 21,
et actualisé M109 et M110 dans le registre. Le contrôleur rend désormais
`COHERENT` : les sept comparaisons documentaires sont en accord et le total
vaut 454 des deux côtés. Ses trois tests passent.

Ref de reprise : `vmti2m7swchro`.
