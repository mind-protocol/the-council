# `10-socle/mesures` — les grandeurs d'homme

## Ce que c'est

Les grandeurs physiques partagées, en mètres et en secondes : largeur d'épaule,
allures de marche, de charge et de fuite, accélération, freinage, allonges et
cadences d'armes, points de vie, portées.

## Ce qu'il possède

Les valeurs, et le fait qu'elles soient **au même endroit pour tout le monde**.

## Ce qu'il lit

Rien.

## Ce qu'il produit

Des valeurs nommées, et rien d'autre. Aucune fonction de décision.

## Invariants

- **Personne ne recopie un mètre.** Une grandeur utilisée par deux modules est
  déclarée une fois ici, jamais deux fois ailleurs.
- **Ce sont des mesures d'homme, pas des réglages de jeu.** Quand un chiffre
  paraît faux, on le corrige contre la réalité, pas contre l'envie que la
  bataille dure plus longtemps.
- Une allure est une **consigne**, pas une vitesse atteinte : ce qu'un corps
  atteint réellement dépend de son accélération, de son souffle et de ce qui le
  gêne. Les deux ne se confondent jamais.
- Une grandeur qui n'est employée nulle part est retirée. Une constante déclarée
  et jamais lue est un mensonge sur ce que le moteur sait faire.

## Ce qu'il ne fait pas

- Il ne calcule rien : ni vitesse effective, ni dégât, ni portée utile.
- Il ne contient aucun seuil de décision. « À partir de quelle distance un homme
  charge » n'est pas une mesure d'homme, c'est un choix de comportement, et il
  appartient à la couche qui décide.
- Il n'a aucune notion de camp, de métier ni d'unité.

## Ce que l'ancien moteur faisait mal ici

Le module existait et tenait son rôle : les allonges et les cadences y vivaient,
et une note y renvoyait explicitement pour éviter les copies.

Le défaut mesuré n'est pas dans les valeurs mais dans leur **emploi**. Une allure
de charge était déclarée et **n'était employée nulle part** sur le chemin d'une
bataille rangée : la cavalerie fermait cent mètres à 1,6 m/s et arrivait au
contact à 1,0, alors qu'un seuil de contre-charge attendait 2,2. Sur soixante-seize
coups de pique portés sur un cavalier, **zéro** l'a été sur un cavalier lancé.

La conséquence est instructive et vaut d'être retenue : un fantassin **en fuite**
atteignait 3,6 m/s, plus vite que la meilleure cavalerie du même moteur — parce
que la fuite passait par un chemin qui contournait à la fois le plafond
d'accélération et le bonus de monture.

**Une grandeur déclarée ne prouve rien.** Ce qui compte, c'est qu'un chemin de
code l'emploie, et une sonde doit pouvoir le dire.
