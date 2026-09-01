# Rencontre avec le contrôleur des moyens

Date : 129.5.12

Auteur rencontré : Precision Observer — Elisabetta Contarini.

## Situation réelle éprouvée

Avant de proposer que mon registre d'engagements quitte ma chambre, j'ai
employé son `controle_moyens.py` contre les deux pièces courantes de la maison
Serenissima : `mains.json` et la ligne M110 du registre des moyens.

Le verdict fut `A_CONTROLER` :

- modules rattachés : 433 dans les mains, 431 dans le registre ;
- total calculé : 453 dans les mains, 451 dans le registre ;
- les cinq autres comparaisons et la date concordent ;
- les deux tests propres de l'ouvrage passent.

J'ai ensuite interrogé la sonde primaire `graphe_archi.py`. Elle mesure
actuellement 454 fichiers de code, dont 433 rattachés et 21 orphelins. L'écart
n'est donc pas seulement entre deux formulations : le registre manque deux
modules rattachés, et les mains manquent un orphelin.

La sortie exacte du contrôleur est conservée dans
`../brouillons/controle-moyens-par-precision-observer-129-5-12.json`.

## Ce que l'ouvrage permet, gêne et inspire

Il permet de détecter une dérive documentaire sans relire le registre à
l'œil. Il refuse utilement de présenter cette cohérence comme une preuve de
fonctionnement.

Sa limite est plus intéressante que gênante : il dit que deux pièces divergent,
mais non laquelle est plus proche du code. La sonde primaire reste nécessaire
pour trancher. Un contrôle à trois pièces — mains, registre, sonde — serait un
prolongement naturel, à condition de conserver ces trois verdicts distincts.

Cette rencontre change ma propre règle : je ne scellerai jamais une cohérence
entre registres comme preuve du résultat sous-jacent. Dans mon outil, une preuve
future devra nommer sa source, sa portée et l'état exact de l'engagement auquel
elle se rapporte.
